# help functions for the project
import os
import bpy
import json
import numpy as np
from collections import deque
from . import variables as vb

def build_graph(tree):

    incoming = {node: 0 for node in tree.nodes}
    adjacency = {node: [] for node in tree.nodes}

    for link in tree.links:
        src = link.from_node
        dst = link.to_node

        adjacency[src].append(dst)
        incoming[dst] += 1

    return incoming, adjacency

def topological_sort(tree):

    incoming, adjacency = build_graph(tree)

    queue = deque([n for n in tree.nodes if incoming[n] == 0])
    order = []

    while queue:

        node = queue.popleft()
        order.append(node)

        for nxt in adjacency[node]:

            incoming[nxt] -= 1

            if incoming[nxt] == 0:
                queue.append(nxt)

    return order

def build_node_order(tree):

    topo = topological_sort(tree)

    # group nodes with similar depth
    topo.sort(key=lambda n: (n.location.x, -n.location.y))

    return topo

def build_link_order(tree, node_order):

    node_index = {n: i for i, n in enumerate(node_order)}

    links = []
    for link in tree.links:

        links.append({
            "from_socket": link.from_socket,
            "to_socket": link.to_socket,
            "from_node": link.from_node,
            "to_node": link.to_node,
        })

    links.sort(key=lambda l: node_index.get(l["from_node"], -1))

    return links

def socket_location(node, socket, is_output=False, offset=(0.0, 0.0)):
    """
    Estimate the location of a socket in node editor coordinates.

    node: bpy.types.Node
    socket: bpy.types.NodeSocket
    is_output: True if output socket
    x_offset/y_offset: manual correction if needed
    """

    HEADER = 24
    SOCKET_STEP = 22

    # base node location
    nx, ny = node.location

    # reroute nodes are special
    if node.bl_idname == "NodeReroute":
        return (nx, ny)

    # choose socket list
    sockets = node.outputs if is_output else node.inputs

    # only count visible sockets
    visible = [s for s in sockets if not s.hide]

    try:
        index = visible.index(socket)
    except ValueError:
        index = 0

    # vertical position
    y = ny - HEADER - SOCKET_STEP * (index + 0.5)

    # horizontal position
    if is_output:
        x = nx + node.width
    else:
        x = nx

    return (x + offset[0], y + offset[1])

def copy_float_curve(src_mapping, dst_mapping):

    src_curve = src_mapping.curves[0]
    dst_curve = dst_mapping.curves[0]
    dst_mapping.clip_min_x = src_mapping.clip_min_x
    dst_mapping.clip_max_x = src_mapping.clip_max_x
    dst_mapping.clip_min_y = src_mapping.clip_min_y
    dst_mapping.clip_max_y = src_mapping.clip_max_y
    dst_mapping.use_clip = src_mapping.use_clip

    # remove extra points (keep at least two)
    while len(dst_curve.points) > 2:
        dst_curve.points.remove(dst_curve.points[-1])

    # copy first two points
    for i in range(2):
        dst_curve.points[i].location = src_curve.points[i].location
        dst_curve.points[i].handle_type = src_curve.points[i].handle_type

    # add remaining points
    for p in src_curve.points[2:]:
        new = dst_curve.points.new(p.location[0], p.location[1])
        new.handle_type = p.handle_type

    dst_mapping.update()
    dst_mapping.reset_view()

def copy_node(src_node, dst_tree):
    # create node of same type
    new_node = dst_tree.nodes.new(type=src_node.bl_idname)

    # basic properties
    #new_node.location = src_node.location
    new_node.label = src_node.label
    new_node.name = src_node.name
    new_node.width = src_node.width
    new_node.hide = src_node.hide

    if src_node.bl_idname == "GeometryNodeGroup":
        new_node.node_tree = src_node.node_tree

    # copy custom properties
    for prop in src_node.bl_rna.properties:
        if prop.is_readonly:
            continue
        identifier = prop.identifier
        if identifier in {"name", "location", "width"}:
            continue

        try:
            setattr(new_node, identifier, getattr(src_node, identifier))
        except:
            pass

    return new_node

def get_next_uniq_key(base_key="node_name", existing_keys = []):
    max_index = -1

    for value in existing_keys:

        if value == base_key:
            max_index = max(max_index, 0)
        elif value.startswith(base_key + "."):
            try:
                num = int(value.split(".")[-1])
                max_index = max(max_index, num)
            except ValueError:
                pass

    if max_index < 0:
        return base_key

    return f"{base_key}.{max_index + 1:03d}"

def annotation_to_gpencil(note, gpencil):
    # backup the annotation to a grease pencil data block
    for layer in note.layers:
        if gpencil.layers.get(layer.info) is None:
            gpencil.layers.new(layer.info)
        for f_idx, frame in enumerate(layer.frames):
            anim_mode = 0
            if frame.frame_number == vb._ANIM_FRAME:
                anim_mode = 1
                continue
            f_idx = f_idx - anim_mode
            if f_idx >= len(gpencil.layers[layer.info].frames):
                gpencil.layers[layer.info].frames.new(frame.frame_number)
            # clear existing strokes in the frame before adding new ones
            drawing = gpencil.layers[layer.info].frames[f_idx].drawing
            if len(drawing.strokes) > 0:
                drawing.remove_strokes(indices=[i for i in range(len(drawing.strokes))])

            for s_idx, stroke in enumerate(frame.strokes):
                drawing.add_strokes([len(stroke.points)])
                start = drawing.curve_offsets[s_idx].value
                position = drawing.attributes["position"].data
                for i, pt in enumerate(stroke.points):
                    position[start+i].vector = (pt.co.x, pt.co.y, pt.co.z)
    return gpencil

def get_annotation_write_symbol():
    data_filepath = os.path.join(os.path.dirname(__file__), "write_symbol.json")
    try:
        with open(data_filepath, "r", encoding="utf-8") as f:
            vb._write_symbols = json.load(f)
    except Exception as e:
        print(f"Error loading wirte_symbol.json: {e}")

def text_to_curves(text, font=None, step=0.04):
    # use geometry nodes to evalue string to curves
    mesh_name = "nodetree_emptyMesh"
    obj_name = "nodetree_emptyMeshObject"
    geoMd_name = "emptyNodeTreeGeoNodes"
    nodeTree_name = "emptyNodeTreeNodeGroup"
    if bpy.data.objects.get(obj_name) is None:
        if bpy.data.meshes.get(mesh_name) is None:
            mesh = bpy.data.meshes.new(name=mesh_name)
        obj = bpy.data.objects.new(name=obj_name, object_data=mesh)

    obj = bpy.data.objects[obj_name]
    nodegroup =  bpy.data.node_groups.get(nodeTree_name)
    if nodegroup is None:
        nodegroup = string_to_curves_node_group(nodeTree_name)
    geometryMd = obj.modifiers.get(geoMd_name)
    if geometryMd is None:
        geometryMd = obj.modifiers.new(name=geoMd_name, type='NODES')
        geometryMd.node_group = nodegroup

    bpy.context.collection.objects.link(obj)
    string_node = nodegroup.nodes["String to Curves"]
    string_node.inputs['String'].default_value = text
    if font is not None:
        string_node.inputs["Font"].default_value = font
    curve_to_points_node = nodegroup.nodes["Curve to Points"]
    curve_to_points_node.inputs['Length'].default_value = step

    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)
    eval_geo = obj_eval.evaluated_geometry()
    curves = eval_geo.curves
    position = curves.attributes["position"]
    offsets = curves.curve_offset_data
    # Read all positions efficiently
    co = np.empty(len(position.data) * 3, dtype=np.float32)
    position.data.foreach_get("vector", co)
    co = co.reshape(-1, 3)
    curve_points = {}
    for curve_index in range(len(offsets)):
        start = offsets[curve_index].value
        if curve_index == len(offsets) - 1:
            end = len(position.data)
        else:
            end = offsets[curve_index + 1].value
        curve_points[curve_index] = [pt_co for pt_co in co[start:end]]
    bpy.context.collection.objects.unlink(obj)

    return curve_points

def string_to_curves_node_group(node_tree_name):
    """Initialize Geometry Nodes node group"""
    node_group = bpy.data.node_groups.new(type='GeometryNodeTree', name=node_tree_name)

    # node_group interface
    # Socket Geometry
    socket_output = node_group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    # Socket Geometry
    socket_input = node_group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')

    # Initialize node_group nodes
    # Node String to Curves
    string_to_curves = node_group.nodes.new("GeometryNodeStringToCurves")
    string_to_curves.location.x = -400
    # Node Realize Instances
    realize_instances = node_group.nodes.new("GeometryNodeRealizeInstances")
    realize_instances.location.x = -200
    # Node For Each Geometry Element Output
    for_each_geometry_element_output = node_group.nodes.new("GeometryNodeForeachGeometryElementOutput")
    for_each_geometry_element_output.domain = 'CURVE'
    for_each_geometry_element_output.location.x = 0
    # Node For Each Geometry Element Input
    for_each_geometry_element_input = node_group.nodes.new("GeometryNodeForeachGeometryElementInput")
    for_each_geometry_element_input.location.x = 200
    # Node Curve to Points
    curve_to_points = node_group.nodes.new("GeometryNodeCurveToPoints")
    # Length
    curve_to_points.mode = 'LENGTH'
    curve_to_points.inputs['Length'].default_value = 0.04
    curve_to_points.location.x = 400
    # Node Points to Curves
    points_to_curves = node_group.nodes.new("GeometryNodePointsToCurves")
    points_to_curves.location.x = 600
    # Node Group Output
    group_output = node_group.nodes.new("NodeGroupOutput")
    group_output.location.x = 800
    # Process zone input For Each Geometry Element Input
    for_each_geometry_element_input.pair_with_output(for_each_geometry_element_output)

    # Initialize node_group links
    # string_to_curves.Curve Instances -> realize_instances.Geometry
    node_group.links.new(
        node_group.nodes["String to Curves"].outputs[0],
        node_group.nodes["Realize Instances"].inputs[0]
    )
    # realize_instances.Geometry -> for_each_geometry_element_input.Geometry
    node_group.links.new(
        node_group.nodes["Realize Instances"].outputs[0],
        node_group.nodes["For Each Geometry Element Input"].inputs[0]
    )
    # for_each_geometry_element_input.Element -> curve_to_points.Curve
    node_group.links.new(
        node_group.nodes["For Each Geometry Element Input"].outputs[1],
        node_group.nodes["Curve to Points"].inputs[0]
    )
    # curve_to_points.Points -> points_to_curves.Points
    node_group.links.new(
        node_group.nodes["Curve to Points"].outputs[0],
        node_group.nodes["Points to Curves"].inputs[0]
    )
    # points_to_curves.Curves -> for_each_geometry_element_output.Geometry
    node_group.links.new(
        node_group.nodes["Points to Curves"].outputs[0],
        node_group.nodes["For Each Geometry Element Output"].inputs[1]
    )
    # for_each_geometry_element_output.Geometry -> group_output.Geometry
    node_group.links.new(
        node_group.nodes["For Each Geometry Element Output"].outputs[2],
        node_group.nodes["Group Output"].inputs[0]
    )

    return node_group

def stroke_mode(layer, frame, stroke, start, end):
    for stroke in strokes[f'{layer}.{frame}.{stroke}']:
        if current <  stroke.end:
            stroke.anim_mode = True
            break

