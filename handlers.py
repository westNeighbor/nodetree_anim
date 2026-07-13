import bpy
import time
from .utility import socket_location, get_annotation_write_symbol
from . import variables as vb

def all_handlers():
    """return a list of handler stored in .blend"""

    return_list = []
    for oh in bpy.app.handlers:
        try:
            for h in oh:
                return_list.append(h)
        except:
            pass
    return return_list


def register_handlers(status):
    """register dispatch for handlers"""

    if (status == "register"):

        all_handler_names = [h.__name__ for h in all_handlers()]

        # frame_change
        if "nodetree_frame_pre" not in all_handler_names:
            bpy.app.handlers.frame_change_pre.append(nodetree_frame_pre)

        return None

    elif (status == "unregister"):

        for h in all_handlers():

            # frame_change
            if (h.__name__ == "nodetree_frame_pre"):
                bpy.app.handlers.frame_change_pre.remove(h)

    return None

@bpy.app.handlers.persistent
def nodetree_frame_pre(scene):  # used for scene driven properties live udpating!
    note_tracking = scene.nodetree_anim_note_tracking
    node_tracking = scene.nodetree_anim_node_tracking
    link_tracking = scene.nodetree_anim_link_tracking
    value_tracking = scene.nodetree_anim_value_tracking
    view_tracking = scene.nodetree_anim_view_tracking
    node_props = scene.nodetree_node_props
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'NODE_EDITOR':
                space = area.spaces.active
                node_tree = space.edit_tree
                if node_tree and node_tracking.get(node_tree.name):
                    tracking = node_tracking[node_tree.name]
                    for item in tracking.anim_nodes:
                        anim_curve_node = bpy.data.node_groups[f'{node_tree.name}_AnimCurves'].nodes[f'{item.name}_anim_curve']
                        mapping = anim_curve_node.mapping
                        mapping.update()
                        curve = mapping.curves[0]
                        frame = scene.frame_current
                        if frame < item.start_frame or frame > item.end_frame:
                            if frame < item.start_frame and item.sync:
                                if item.anim_type == 'FLY_IN':
                                    node_tree.nodes[item.node_name].location = item.start_pos
                                if item.anim_type == 'SHRINK':
                                    shrink= bpy.data.node_groups[f'{node_tree.name}_AnimCurves'].nodes[f'{item.name}_shrink_curve']
                                    mapping = shrink.mapping
                                    mapping.update()
                                    curve = mapping.curves[0]
                                    value = mapping.evaluate(curve, 0)
                                    node_tree.nodes[item.node_name].width = item.org_size[0]*value
                            continue
                        t = (frame - item.start_frame) / (item.end_frame - item.start_frame)
                        map_t = mapping.evaluate(curve, t)
                        if item.anim_type == 'FLY_IN':
                            path = [bpy.data.node_groups[f'{node_tree.name}_AnimCurves'].nodes[f'{item.name}_pathx_curve'], bpy.data.node_groups[f'{node_tree.name}_AnimCurves'].nodes[f'{item.name}_pathy_curve']]
                            multiplier = [item.pathx_multiplier, item.pathy_multiplier]
                            for i, xy in enumerate(path):
                                mapping = xy.mapping
                                mapping.update()
                                curve = mapping.curves[0]
                                value = mapping.evaluate(curve, map_t)
                                node_tree.nodes[f"{item.node_name}"].location[i] = value * multiplier[i]
                        if item.anim_type == 'SHRINK':
                            shrink= bpy.data.node_groups[f'{node_tree.name}_AnimCurves'].nodes[f'{item.name}_shrink_curve']
                            mapping = shrink.mapping
                            mapping.update()
                            curve = mapping.curves[0]
                            value = mapping.evaluate(curve, map_t)
                            node_tree.nodes[f"{item.node_name}"].height = item.org_size[1]*value
                            node_tree.nodes[f"{item.node_name}"].width = item.org_size[0]*value
                if node_tree and  link_tracking.get(node_tree.name):
                    tracking = link_tracking[node_tree.name]
                    for node in tracking.anim_links:
                        for link in node.node_links:
                            from_node = node_tree.nodes[f"{link.from_node}"]
                            from_socket = from_node.outputs[f"{link.from_socket}"]
                            to_node = node_tree.nodes[f"{link.to_node}"]
                            to_socket = to_node.inputs[f"{link.to_socket}"]
                            start_location = socket_location(from_node, from_socket, True, link.start_offset)
                            end_location = socket_location(to_node, to_socket, False, link.end_offset)
                            if link.anim_type == "REVERSE_GROW":
                                end_location = socket_location(from_node, from_socket, True)
                                start_location = socket_location(to_node, to_socket, False)
                            frame = scene.frame_current
                            if frame <= link.start_frame:
                                if frame == link.start_frame:
                                    if node_tree.nodes.get(f"{link.name}_reroute") is None:
                                        node_tree.nodes.new("NodeReroute").name = f"{link.name}_reroute"
                                    reroute = node_tree.nodes[f"{link.name}_reroute"]
                                    reroute.location = start_location
                                    node_tree.links.new(from_socket, reroute.inputs[0])
                                    if link.anim_type == "REVERSE_GROW":
                                        for check_link in from_socket.links:
                                            if check_link.to_socket.name == to_socket.name:
                                                node_tree.links.remove(check_link)
                                if link.anim_type == "GROW":
                                    for check_link in from_socket.links:
                                        if check_link.to_socket.name == to_socket.name and check_link.to_node.name == to_node.name:
                                            node_tree.links.remove(check_link)
                            elif frame > link.end_frame:
                                if frame == link.end_frame + 1:
                                    if from_socket.type == "CUSTOM":
                                        if from_socket.node.bl_idname == "NodeGroupInput" or from_socket.node.bl_idname == "NodeGroupOutput":
                                            node_tree.interface.new_socket(name=f"{to_socket.name}", in_out='INPUT' if from_socket.is_output else 'OUTPUT', socket_type=f'{to_socket.bl_idname}')
                                            from_socket = from_socket.node.outputs[f'{to_socket.name}'] if from_socket.is_output else from_socket.node.inputs[f'{to_socket.name}']
                                        else:
                                            from_socket.node.enum_items.new(f"{to_socket.name}")
                                            from_socket = from_socket.node.inputs[f'{to_socket.name}']
                                    if to_socket.type == "CUSTOM":
                                        if to_socket.node.bl_idname == "NodeGroupInput" or to_socket.node.bl_idname == "NodeGroupOutput":
                                            node_tree.interface.new_socket(name=f"{from_socket.name}", in_out='INPUT' if to_socket.is_output else 'OUTPUT', socket_type=f'{from_socket.bl_idname}')
                                            to_socket = to_socket.node.outputs[f'{from_socket.name}'] if to_socket.is_output else to_socket.node.inputs[f'{from_socket.name}']
                                        else:
                                            to_socket.node.enum_items.new(f"{from_socket.name}")
                                            to_socket = to_socket.node.inputs[f'{from_socket.name}']
                                    if link.anim_type == "GROW":
                                        node_tree.links.new(from_socket, to_socket)
                                    reroute = node_tree.nodes.get(f"{link.name}_reroute")
                                    if reroute is not None:
                                        node_tree.nodes.remove(reroute)
                            else:
                                t = (frame - link.start_frame) / (link.end_frame - link.start_frame)
                                anim_curve_node = bpy.data.node_groups[f'{node_tree.name}_AnimCurves'].nodes[f'{link.name}_anim_curve']
                                mapping = anim_curve_node.mapping
                                mapping.update()
                                curve = mapping.curves[0]
                                value = mapping.evaluate(curve, t)
                                reroute = node_tree.nodes.get(f"{link.name}_reroute")
                                if reroute is not None:
                                    reroute.location[0] = start_location[0] + value*(end_location[0] - start_location[0])
                                    reroute.location[1] = start_location[1] + value*(end_location[1] - start_location[1])
                if node_tree and value_tracking.get(node_tree.name):
                    tracking = value_tracking[node_tree.name]
                    for node in tracking.anim_values:
                        for value in node.node_values:
                            vnode = node_tree.nodes[f"{node.node_name}"]
                            frame = scene.frame_current
                            if frame < value.start_frame or frame > value.end_frame:
                                if frame < value.start_frame and value.sync:
                                    if value.is_output:
                                        vnode.outputs[value.socket_name].default_value = vnode[f"output_{value.socket_name}_start"]
                                    else:
                                        vnode.inputs[value.socket_name].default_value = vnode[f"input_{value.socket_name}_start"]
                                continue
                            t = (frame - value.start_frame) / (value.end_frame - value.start_frame)
                            anim_curve_node = bpy.data.node_groups[f'{node_tree.name}_AnimCurves'].nodes[f'{value.name}_anim_curve']
                            mapping = anim_curve_node.mapping
                            mapping.update()
                            curve = mapping.curves[0]
                            map_t = mapping.evaluate(curve, t)
                            if value.is_output:
                                begin_value = vnode[f"output_{value.socket_name}_start"]
                                end_value = vnode[f"output_{value.socket_name}_start"]
                                if hasattr(begin_value, "__len__"):
                                    for i in range(len(begin_value)):
                                        vnode.outputs[value.socket_name].default_value[i] = begin_value[i] + map_t*(end_value[i]-begin_value[i])
                                else:
                                    vnode.outputs[value.socket_name].default_value = begin_value + map_t*(end_value-begin_value)
                            else:
                                begin_value = vnode[f"input_{value.socket_name}_start"]
                                end_value = vnode[f"input_{value.socket_name}_end"]
                                if hasattr(begin_value, "__len__"):
                                    for i in range(len(begin_value)):
                                        vnode.inputs[value.socket_name].default_value[i] = begin_value[i] + map_t*(end_value[i]-begin_value[i])
                                else:
                                    vnode.inputs[value.socket_name].default_value = begin_value + map_t*(end_value-begin_value)
                if node_tree and  view_tracking.get(node_tree.name):
                    tracking = view_tracking[node_tree.name]
                    for view in tracking.anim_views:
                        frame = scene.frame_current
                        if frame < view.start_frame or frame > view.end_frame:
                            continue
                        t = (frame - view.start_frame) / (view.end_frame - view.start_frame)
                        anim_curve_node = bpy.data.node_groups[f'{node_tree.name}_AnimCurves'].nodes[f'{view.name}_anim_curve']
                        mapping = anim_curve_node.mapping
                        mapping.update()
                        curve = mapping.curves[0]
                        map_t = mapping.evaluate(curve, t)
                        for region in area.regions:
                            if region.type == 'WINDOW':
                                override ={
                                    'window': window,
                                    'screen': window.screen,
                                    'area': area,
                                    'region': region,
                                }
                                v2d = region.view2d
                                with bpy.context.temp_override(
                                    area=area,
                                    region=region,
                                    space_data=space,
                                ):
                                    if view.anim_type == "FOLLOW":
                                        deltax = map_t*(view.view_offset[0])
                                        deltay = map_t*(view.view_offset[1])
                                        bpy.ops.view2d.pan(deltax=int(deltax-view.prev_xy[0]), deltay=int(deltay-view.prev_xy[1]))
                                        view.prev_xy = (deltax, deltay)
                                    elif view.anim_type == "ZOOM":
                                        deltax = map_t*(view.view_zoom[0])
                                        deltay = map_t*(view.view_zoom[1])
                                        #print(f"{deltax-view.prev_zoom[0]=}, {deltay-view.prev_zoom[1]=}")
                                        bpy.ops.view2d.zoom(deltax=deltax-view.prev_zoom[0], deltay=deltay-view.prev_zoom[1])
                                        view.prev_zoom = (deltax, deltay)
                if node_tree.annotation and  note_tracking.anim_annotations.get(node_tree.annotation.name):
                    note = node_tree.annotation
                    anim_strokes = note_tracking.anim_annotations[node_tree.annotation.name].anim_strokes
                    for anim_stroke in anim_strokes:
                        anim_stroke.update_active_anim(bpy.context)
                        if anim_stroke.active_anim < 0:
                            continue
                        stroke_anim = anim_stroke.stroke_anims[anim_stroke.active_anim]
                        frame = scene.frame_current
                        t = (frame - stroke_anim.start_frame) / (stroke_anim.end_frame - stroke_anim.start_frame)
                        anim_curve_node = bpy.data.node_groups[f'{node_tree.name}_AnimCurves'].nodes[f'{anim_stroke.name}.{stroke_anim.name}_anim_curve']
                        mapping = anim_curve_node.mapping
                        mapping.update()
                        curve = mapping.curves[0]
                        t = mapping.evaluate(curve, t)
                        anim_frame = note.layers[anim_stroke.layer].frames[-1]
                        if stroke_anim.anim_type == "WRITE_ON" or stroke_anim.anim_type == "WRITE_OFF":
                            default_shift = {"WRITING_HAND": (-2.5, -5), "PEN": (-14.0, 16.0), "PENCIL": (-6.0, 10), "FOUNTAIN_PEN": (-14.0, 16.0)}
                            # adding anim stroke
                            if anim_stroke.anim_idx < 0:
                                stroke = anim_frame.strokes.new()
                                stroke.display_mode = '2DSPACE'
                                anim_stroke.anim_idx = len(anim_frame.strokes) - 1
                                stroke.points.add(count=1)
                                stroke.points[-1].co = (-1000000., -1000000., 0.0)
                            # adding symbol strokes
                            if stroke_anim.write_symbol != "NONE":
                                if not vb._write_symbols:
                                    get_annotation_write_symbol()
                                write_symbol = vb._write_symbols.get(stroke_anim.write_symbol)
                                if (stroke_anim.end_frame-stroke_anim.start_frame)>1 and stroke_anim.symbol_idx < 0 and write_symbol:
                                    for i in range(len(write_symbol)):
                                        symbol_stroke = anim_frame.strokes.new()
                                        symbol_stroke.display_mode = '2DSPACE'
                                        if i == 0:
                                            stroke_anim.symbol_idx = len(anim_frame.strokes) - 1
                                        symbol_stroke.points.add(count=1)
                                        symbol_stroke.points[-1].co = (-1000000., -1000000., 0.0)

                            # retrieve all the anim data
                            stroke_points = [point.co for point in note.layers[anim_stroke.layer].frames[anim_stroke.frame].strokes[anim_stroke.stroke].points]

                            if t < 0:
                                if stroke_anim.anim_type == "WRITE_ON":
                                    # remove stroke points
                                    stroke = anim_frame.strokes[anim_stroke.anim_idx]
                                    while len(stroke.points) > 1:
                                        stroke.points.remove(len(stroke.points) - 1)
                                    stroke.points[-1].co = (-1000000., -1000000., 0.0)
                                else:
                                    # add stroke points
                                    stroke = anim_frame.strokes[anim_stroke.anim_idx]
                                    while len(stroke.points) < len(stroke_points):
                                        stroke.points.add(count=1)
                                    for p_idx, point in enumerate(stroke_points):
                                        stroke.points[p_idx].co = (point.x, point.y, point.z)
                                # remove symbol points if they exist
                                if stroke_anim.symbol_idx >= 0:
                                    for i in range(stroke_anim.symbol_idx, stroke_anim.symbol_idx+len(write_symbol)):
                                        symbol_stroke = anim_frame.strokes[i]
                                        while len(symbol_stroke.points) > 1:
                                            symbol_stroke.points.remove(len(symbol_stroke.points) - 1)
                                        symbol_stroke.points[-1].co = (-1000000., -1000000., 0.0)
                                continue
                            elif t > 1:
                                if stroke_anim.anim_type == "WRITE_OFF":
                                    # remove stroke points
                                    stroke = anim_frame.strokes[anim_stroke.anim_idx]
                                    while len(stroke.points) > 1:
                                        stroke.points.remove(len(stroke.points) - 1)
                                    stroke.points[-1].co = (-1000000., -1000000., 0.0)
                                else:
                                    # add stroke points
                                    stroke = anim_frame.strokes[anim_stroke.anim_idx]
                                    while len(stroke.points) < len(stroke_points):
                                        stroke.points.add(count=1)
                                    for p_idx, point in enumerate(stroke_points):
                                        stroke.points[p_idx].co = (point.x, point.y, point.z)
                                # remove symbol points if they exist
                                if stroke_anim.symbol_idx >= 0:
                                    for i in range(stroke_anim.symbol_idx, stroke_anim.symbol_idx+len(write_symbol)):
                                        symbol_stroke = anim_frame.strokes[i]
                                        while len(symbol_stroke.points) > 1:
                                            symbol_stroke.points.remove(len(symbol_stroke.points) - 1)
                                        symbol_stroke.points[-1].co = (-1000000., -1000000., 0.0)
                                continue

                            # deal with the anim stroke points
                            if stroke_anim.anim_type == "WRITE_OFF":
                                t = 1.0 - t
                            t_index = int(t * (len(stroke_points) - 1))
                            if t_index<0:
                                t_index = 0
                            stroke = anim_frame.strokes[anim_stroke.anim_idx]
                            while len(stroke.points) > t_index+1:
                                stroke.points.remove(len(stroke.points) - 1)
                            while len(stroke.points) < t_index+1:
                                stroke.points.add(count=1)
                            for p_idx, point in enumerate(stroke_points[:t_index+1]):
                                stroke.points[p_idx].co = (point.x, point.y, point.z)

                            # moving the symbol strokes to the end of the stroke position
                            if stroke_anim.symbol_idx >= 0:
                                for i, stroke_co in enumerate(write_symbol):
                                    symbol_stroke = anim_frame.strokes[stroke_anim.symbol_idx + i]
                                    while len(symbol_stroke.points) < len(stroke_co):
                                        symbol_stroke.points.add(count=1)
                                    for j, co in enumerate(stroke_co):
                                        symbol_stroke.points[j].co = (co[0]*100.0*stroke_anim.symbol_scale[0] + stroke.points[-1].co.x + stroke_anim.symbol_shift[0] + default_shift[stroke_anim.write_symbol][0], co[1]*100.0*stroke_anim.symbol_scale[1] + stroke.points[-1].co.y + stroke_anim.symbol_shift[1] + default_shift[stroke_anim.write_symbol][1], 0.0)
                        elif stroke_anim.anim_type == "MORPH":
                            pass
