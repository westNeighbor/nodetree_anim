# all data operations
import bpy
import random
import math
import numpy as np
from .utility import topological_sort, build_node_order, build_link_order, get_next_uniq_key, copy_float_curve, copy_node, get_annotation_write_symbol
from . import variables as vb

class NODETREE_OT_Refresh_NodeList(bpy.types.Operator):
    bl_idname = "nodetree_anim.refresh_nodelist"
    bl_label = "Refresh Node List"
    bl_description = "Refresh node list from node tree"
    bl_options = {'REGISTER', 'UNDO'}

    renew: bpy.props.EnumProperty(
        items=[("REFRESH", "Refresh List", "Refresh the exisiting list by adding new and deleting nonexists"),
               ("REBUILD", "Rebuild List", "Rebuild the list from scrath"),
              ],
        default="REFRESH",
    )
    def execute(self, context):
        props = context.scene.nodetree_node_props
        space = context.space_data
        node_tree = None
        if space and space.type == 'NODE_EDITOR':
            node_tree = space.edit_tree
        if node_tree is None:
            self.report("WARNING", "no node tree found!")
            return {'CANCELED'}
        anim_props = context.scene.nodetree_anim_props
        anim_props.node_tree = node_tree
        if bpy.data.node_groups.get(f"{node_tree.name}_AnimCurves") is None:
            anim_curve_tree = bpy.data.node_groups.new(f"{node_tree.name}_AnimCurves", 'GeometryNodeTree')
            anim_curve_tree.use_fake_user = True
        anim_curve_tree = bpy.data.node_groups[f"{node_tree.name}_AnimCurves"]
        if anim_props.anim_option == 'MANUAL':
            if len(props.nodes) > 0:
                props.nodes.clear()
            for node in node_tree.nodes:
                item = props.nodes.add()
                item.name = node.name
            if len(props.nodes) > 0 and props.node_index < len(props.nodes):
               node_name = props.nodes[props.node_index].name
               node = node_tree.nodes[node_name]
               if props.add_anim == "NODEANIM":
                   if anim_curve_tree.nodes.get('node_anim_curve') is None:
                       anim_curve_tree.nodes.new('ShaderNodeFloatCurve').name = f"node_anim_curve"
                   if props.node_anim_type == 'FLY_IN':
                       for idx, path in enumerate(["pathx", "pathy"]):
                           path_multiplier = props.pathx_multiplier if idx == 0 else props.pathy_multiplier
                           if anim_curve_tree.nodes.get(f'node_{path}_curve') is None:
                               anim_curve_tree.nodes.new('ShaderNodeFloatCurve').name = f'node_{path}_curve'
                           fly_curve = anim_curve_tree.nodes[f'node_{path}_curve']
                           max_y = max(abs(props.start_pos[idx]), abs(node.location[idx]))
                           mini_range = 0.1
                           fly_curve.mapping.clip_min_y = -max(max_y*2/path_multiplier, mini_range)
                           fly_curve.mapping.clip_max_y = max(max_y*2/path_multiplier, mini_range)
                           fly_curve.mapping.curves[0].points[0].location[1] = props.start_pos[idx]/path_multiplier
                           fly_curve.mapping.curves[0].points[-1].location[1] = node.location[idx]/path_multiplier
                           fly_curve.mapping.update()
                           fly_curve.mapping.reset_view()
                   if props.node_anim_type == 'SHRINK':
                       if anim_curve_tree.nodes.get('node_shrink_curve') is None:
                           anim_curve_tree.nodes.new('ShaderNodeFloatCurve').name = 'node_shrink_curve'
                       shrink_node = anim_curve_tree.nodes['node_shrink_curve']
                       shrink_node.mapping.clip_min_y = 0.5
                       shrink_node.mapping.clip_max_y = 5.0
                       shrink_node.mapping.curves[0].points[0].location[1] = 2.0
                       shrink_node.mapping.curves[0].points[-1].location[1] = 1.0
                       shrink_node.mapping.update()
                       shrink_node.mapping.reset_view()
               elif props.add_anim == "LINKANIM":
                   if anim_curve_tree.nodes.get('node.link_anim_curve') is None:
                       anim_curve_tree.nodes.new('ShaderNodeFloatCurve').name = f"node.link_anim_curve"
               elif props.add_anim == 'VALUEANIM':
                   if anim_curve_tree.nodes.get('node.value_anim_curve') is None:
                       anim_curve_tree.nodes.new('ShaderNodeFloatCurve').name = 'node.value_anim_curve'
                   if len(props.values) > 0 and props.value_index < len(props.values):
                       if props.values[props.value_index].is_output:
                           socket = node.outputs[f"{props.values[props.value_index].name}"]
                           subtype = socket.bl_rna.properties["default_value"].subtype
                           node[f"output_{props.values[props.value_index].name}_start"] = socket.default_value
                           node[f"output_{props.values[props.value_index].name}_end"] = socket.default_value
                           ui = node.id_properties_ui(f"output_{props.values[props.value_index].name}_start")
                           ui.update(subtype=subtype)
                           ui = node.id_properties_ui(f"output_{props.values[props.value_index].name}_end")
                           ui.update(subtype=subtype)
                       else:
                           socket = node.inputs[f"{props.values[props.value_index].name}"]
                           subtype = socket.bl_rna.properties["default_value"].subtype
                           node[f"input_{props.values[props.value_index].name}_start"] = socket.default_value
                           node[f"input_{props.values[props.value_index].name}_end"] = socket.default_value
                           ui = node.id_properties_ui(f"input_{props.values[props.value_index].name}_start")
                           ui.update(subtype=subtype)
                           ui = node.id_properties_ui(f"input_{props.values[props.value_index].name}_end")
                           ui.update(subtype=subtype)
        elif anim_props.anim_option == 'BULK':
            if anim_props.bulk_anim_option == 'NODES':
                if anim_curve_tree.nodes.get('bulk_node_anim_curve') is None:
                    anim_curve_tree.nodes.new('ShaderNodeFloatCurve').name = f"bulk_node_anim_curve"
                for idx, path in enumerate(["pathx", "pathy"]):
                    if anim_curve_tree.nodes.get(f'bulk_node_{path}_curve') is None:
                        anim_curve_tree.nodes.new('ShaderNodeFloatCurve').name = f"bulk_node_{path}_curve"
                if anim_curve_tree.nodes.get('bulk_node_shrink_curve') is None:
                    anim_curve_tree.nodes.new('ShaderNodeFloatCurve').name = f"bulk_node_shrink_curve"
                shrink_node = anim_curve_tree.nodes['bulk_node_shrink_curve']
                shrink_node.mapping.clip_min_y = 0.5
                shrink_node.mapping.clip_max_y = 5.0
                shrink_node.mapping.curves[0].points[0].location[1] = anim_props.init_size
                shrink_node.mapping.curves[0].points[-1].location[1] = 1.0
                shrink_node.mapping.update()
                shrink_node.mapping.reset_view()
                if node_tree is not None:
                    #ordered_nodes = topological_sort(node_tree)
                    ordered_nodes = build_node_order(node_tree)
                    if self.renew=="REBUILD" or len(anim_props.nodes) == 0:
                        anim_props.node_tree = node_tree
                        anim_props.nodes.clear()
                        for node in ordered_nodes:
                            item = anim_props.nodes.add()
                            item.name = node.name
                            item.start_frame = anim_props.start_frame if len(anim_props.nodes) == 1 else n_start
                            item.end_frame = item.start_frame + anim_props.node_anim_length
                            item.anim_type = anim_props.node_anim_type
                            item.sync = anim_props.sync_node
                            item.stagger_time = anim_props.node_anim_stagger
                            item.node_name = node.name
                            item.start_pos = anim_props.start_pos
                            item.path_multiplier = anim_props.path_multiplier
                            item.org_size = (node.width, node.height)
                            item.org_pos = node.location
                            item.init_size = anim_props.init_size
                            n_start = item.stagger_time + item.end_frame
                    else:
                        for idx, node in enumerate(anim_props.nodes):
                            if node_tree.nodes.get(node.name) is None:
                                anim_props.nodes.remove(idx)
                        for node in ordered_nodes:
                            if anim_props.nodes.get(node.name) is None:
                                pidx = len(anim_props.nodes) - 1
                                item = anim_props.nodes.add()
                                item.name = node.name
                                item.node_name = node.name
                                if pidx >=0:
                                    pitem = anim_props.nodes[pidx]
                                    item.start_frame = pitem.end_frame + pitem.stagger_time
                                else:
                                    item.start_frame = anim_props.start_frame
                                item.end_frame = item.start_frame + anim_props.node_anim_length
                                item.anim_type = anim_props.node_anim_type
                                item.stagger_time = anim_props.node_anim_stagger
                                item.sync = anim_props.sync_node
                                item.start_pos = anim_props.start_pos
                                item.path_multiplier = anim_props.path_multiplier
                                item.org_size = (node.width, node.height)
                                item.org_pos = node.location
                                item.init_size = anim_props.init_size
            elif anim_props.bulk_anim_option == 'LINKS':
                if anim_curve_tree.nodes.get('bulk_node.link_anim_curve') is None:
                    anim_curve_tree.nodes.new('ShaderNodeFloatCurve').name = f"bulk_node.link_anim_curve"
                if node_tree is not None:
                    ordered_nodes = build_node_order(node_tree)
                    ordered_links = build_link_order(node_tree, ordered_nodes)
                    if self.renew=="REBUILD" or len(anim_props.links) == 0:
                        anim_props.node_tree = node_tree
                        anim_props.links.clear()
                        for link in ordered_links:
                            item = anim_props.links.add()
                            item.name = f"{link['from_node'].name}.{link['from_socket'].identifier}.{link['to_socket'].identifier}"
                            item.start_frame = anim_props.start_frame if len(anim_props.links) == 1 else n_start
                            item.end_frame = item.start_frame + anim_props.link_anim_length
                            item.anim_type = anim_props.link_anim_type
                            item.stagger_time = anim_props.link_anim_stagger
                            n_start = item.stagger_time + item.end_frame
                            item.from_node = link["from_node"].name
                            item.to_node = link["to_node"].name
                            item.from_socket = link["from_socket"].name
                            item.to_socket = link["to_socket"].name
                            item.from_socket_id = link["from_socket"].identifier
                            item.to_socket_id = link["to_socket"].identifier
                            item.start_offset = anim_props.start_offset
                            item.end_offset = anim_props.end_offset
                    else:
                        for idx, link in enumerate(anim_props.links):
                            is_existing = False
                            for tlink in node_tree.links:
                                if link.from_node == tlink.from_node.name and link.from_socket_id == tlink.from_socket.identifier and link.to_node == tlink.to_node.name and link.to_socket_id == tlink.to_socket.identifier:
                                    is_existing = True
                                    break
                            if not is_existing:
                                anim_props.links.remove(idx)
                        for link in ordered_links:
                            id_name = f"{link['from_node'].name}.{link['from_socket'].identifier}.{link['to_socket'].identifier}"
                            if anim_props.links.get(id_name) is None:
                                pidx = len(anim_props.links) - 1
                                item = anim_props.links.add()
                                item.name = id_name
                                if pidx >= 0:
                                    pitem = anim_props.links[pidx]
                                    item.start_frame = pitem.end_frame + pitem.stagger_time
                                else:
                                    item.start_frame = anim_props.start_frame
                                item.end_frame = item.start_frame + anim_props.link_anim_length
                                item.anim_type = anim_props.link_anim_type
                                item.stagger_time = anim_props.link_anim_stagger
                                item.from_node = link["from_node"].name
                                item.to_node = link["to_node"].name
                                item.from_socket = link["from_socket"].name
                                item.to_socket = link["to_socket"].name
                                item.from_socket_id = link["from_socket"].identifier
                                item.to_socket_id = link["to_socket"].identifier
                                item.start_offset = anim_props.start_offset
                                item.end_offset = anim_props.end_offset
            elif anim_props.bulk_anim_option == 'VIEWS':
                if anim_curve_tree.nodes.get('bulk_node.view_anim_curve') is None:
                    anim_curve_tree.nodes.new('ShaderNodeFloatCurve').name = f"bulk_node.view_anim_curve"

        return {'FINISHED'}

class NODETREE_OT_Build_Anim(bpy.types.Operator):
    bl_idname = "nodetree_anim.build_anim"
    bl_label = "Build Animation"
    bl_description = "Build animation from node tree"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        node_tree = None
        space = context.space_data
        if space and space.type == 'NODE_EDITOR':
            node_tree = space.edit_tree
        if node_tree is None:
            self.report("WARNING", "no node tree found!")
            return {'CANCELED'}
        anim_props = context.scene.nodetree_anim_props
        if anim_props.anim_option == 'BULK':
            if anim_props.bulk_anim_option == 'NODES':
                node_tracking = context.scene.nodetree_anim_node_tracking
                item = node_tracking.get(node_tree.name)
                if item is None:
                    item = node_tracking.add()
                    item.name = node_tree.name
                for node in anim_props.nodes:
                    existing_nitem = [ n.name for n in item.anim_nodes if n.node_name == node.node_name]
                    uniq_name = get_next_uniq_key(node.node_name, existing_nitem)
                    nitem  = item.anim_nodes.add()
                    nitem.name = uniq_name
                    nitem.node_name = node.node_name
                    nitem.start_frame = node.start_frame
                    nitem.end_frame = node.end_frame
                    nitem.anim_type = node.anim_type
                    nitem.start_pos = node.start_pos
                    nitem.org_pos = node.org_pos
                    nitem.org_size = node.org_size
                    nitem.pathx_multiplier = node.path_multiplier[0]
                    nitem.pathy_multiplier = node.path_multiplier[1]
                    anim_curve_tree = bpy.data.node_groups.get(f"{node_tree.name}_AnimCurves")
                    if anim_curve_tree is None:
                        anim_curve_tree = bpy.data.node_groups.new(f"{node_tree.name}_AnimCurves", 'GeometryNodeTree')
                        anim_curve_tree.use_fake_user = True
                    if anim_curve_tree.nodes.get(f"{uniq_name}_anim_curve") is None:
                        anim_curve_tree.nodes.new('ShaderNodeFloatCurve').name = f"{uniq_name}_anim_curve"
                    curve_node = anim_curve_tree.nodes[f"{uniq_name}_anim_curve"]
                    set_curve_node = anim_curve_tree.nodes.get("bulk_node_anim_curve")
                    if set_curve_node is not None:
                        copy_float_curve(set_curve_node.mapping, curve_node.mapping)

                    if node.anim_type == "FLY_IN":
                        nitem.sync = node.sync
                        for idx, path in enumerate(["pathx", "pathy"]):
                            if anim_curve_tree.nodes.get(f"{uniq_name}_{path}_curve") is None:
                                anim_curve_tree.nodes.new('ShaderNodeFloatCurve').name = f"{uniq_name}_{path}_curve"
                            fly_curve =  anim_curve_tree.nodes[f"{uniq_name}_{path}_curve"]
                            max_y = max(abs(nitem.start_pos[idx]), abs(nitem.org_pos[idx]))
                            mini_range = 0.1
                            fly_curve.mapping.clip_min_y = -max(max_y*2/node.path_multiplier[idx], mini_range)
                            fly_curve.mapping.clip_max_y = max(max_y*2/node.path_multiplier[idx], mini_range)
                            fly_curve.mapping.curves[0].points[0].location[1] = nitem.start_pos[idx]/node.path_multiplier[idx]
                            fly_curve.mapping.curves[0].points[-1].location[1] = nitem.org_pos[idx]/node.path_multiplier[idx]
                            fly_curve.mapping.update()
                            fly_curve.mapping.reset_view()
                    elif node.anim_type == "SHRINK":
                        nitem.sync = node.sync
                        if anim_curve_tree.nodes.get(f"{uniq_name}_shrink_curve") is None:
                            anim_curve_tree.nodes.new('ShaderNodeFloatCurve').name = f"{uniq_name}_shrink_curve"
                        shrink_node =  anim_curve_tree.nodes[f"{uniq_name}_shrink_curve"]
                        shrink_node.mapping.clip_min_y = 0.5
                        shrink_node.mapping.clip_max_y = 5.0
                        shrink_node.mapping.curves[0].points[0].location[1] = node.init_size
                        shrink_node.mapping.curves[0].points[-1].location[1] = 1.0
                        shrink_node.mapping.update()
                        shrink_node.mapping.reset_view()
                self.report({'INFO'}, f"Added animation for node list in node tree '{node_tree.name}'")
            elif anim_props.bulk_anim_option == 'LINKS':
                link_tracking = context.scene.nodetree_anim_link_tracking
                item = link_tracking.get(node_tree.name)
                for link in anim_props.links:
                    node_name = link.from_node
                    to_node = link.to_node
                    from_socket = link.from_socket
                    to_socket = link.to_socket
                    nitem = None
                    if item is None:
                        item = link_tracking.add()
                        item.name = node_tree.name
                        nitem = item.anim_links.add()
                        nitem.name = node_name
                        nitem.node_name = node_name
                    else:
                        nitem = item.anim_links.get(node_name)
                        if nitem is None:
                            nitem = item.anim_links.add()
                            nitem.name = node_name
                            nitem.node_name = node_name
                    existing_nnitem = [ n.name for n in nitem.node_links if n.from_socket == from_socket and n.to_socket == to_socket]
                    uniq_name = get_next_uniq_key(f"{node_name} {from_socket} -> {to_socket} {to_node}", existing_nnitem)
                    nnitem = nitem.node_links.add()
                    nnitem.name = uniq_name
                    nnitem.from_node = node_name
                    nnitem.to_node =  to_node
                    nnitem.from_socket = from_socket
                    nnitem.to_socket = to_socket
                    nnitem.start_frame = link.start_frame
                    nnitem.end_frame = link.end_frame
                    nnitem.anim_type = link.anim_type
                    nnitem.start_offset = link.start_offset
                    nnitem.end_offset = link.end_offset
                    anim_curve_tree = bpy.data.node_groups.get(f"{node_tree.name}_AnimCurves")
                    if anim_curve_tree is None:
                        anim_curve_tree = bpy.data.node_groups.new(f"{node_tree.name}_AnimCurves", 'GeometryNodeTree')
                        anim_curve_tree.use_fake_user = True
                    curve_node = anim_curve_tree.nodes.get(f"{uniq_name}_anim_curve")
                    if curve_node is None:
                        curve_node = anim_curve_tree.nodes.new('ShaderNodeFloatCurve')
                        curve_node.name = f"{uniq_name}_anim_curve"
                    set_curve_node = anim_curve_tree.nodes.get("bulk_node.link_anim_curve")
                    if set_curve_node:
                        copy_float_curve(set_curve_node.mapping, curve_node.mapping)
                self.report({'INFO'}, f"Added animation for link list in node tree '{node_tree.name}'")
            elif anim_props.bulk_anim_option == 'VIEWS':
                view_tracking = context.scene.nodetree_anim_view_tracking
                item = view_tracking.get(node_tree.name)
                if item is None:
                    item = view_tracking.add()
                    item.name = node_tree.name
                for view in anim_props.views:
                    nitem  = item.anim_views.add()
                    nitem.name = view.name
                    nitem.start_frame = view.start_frame
                    nitem.end_frame = view.end_frame
                    nitem.anim_type = view.anim_type
                    nitem.view_offset = view.view_offset
                    nitem.view_zoom = view.view_zoom
                    nitem.sync = view.sync
                    anim_curve_tree = bpy.data.node_groups.get(f"{node_tree.name}_AnimCurves")
                    if anim_curve_tree is None:
                        anim_curve_tree = bpy.data.node_groups.new(f"{node_tree.name}_AnimCurves", 'GeometryNodeTree')
                        anim_curve_tree.use_fake_user = True
                    if anim_curve_tree.nodes.get(f"{nitem.name}_anim_curve") is None:
                        anim_curve_tree.nodes.new('ShaderNodeFloatCurve').name = f"{nitem.name}_anim_curve"
                    curve_node = anim_curve_tree.nodes[f"{nitem.name}_anim_curve"]
                    set_curve_node = anim_curve_tree.nodes.get("bulk_node.view_anim_curve")
                    if set_curve_node is not None:
                        copy_float_curve(set_curve_node.mapping, curve_node.mapping)
                self.report({'INFO'}, f"Added animation for view list in node tree '{node_tree.name}'")

        return {'FINISHED'}

class NODETREE_OT_List_MoveUp(bpy.types.Operator):
    bl_idname = "nodetree_anim.list_moveup"
    bl_label = "Move Up"
    bl_description = "Move up the selected item in the list"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        anim_props = context.scene.nodetree_anim_props
        if anim_props.anim_option == 'BULK':
            if anim_props.bulk_anim_option == 'NODES':
                if anim_props.node_index > 0:
                    anim_props.nodes.move(anim_props.node_index, anim_props.node_index-1)
                    anim_props.node_index -= 1
                    c_item = anim_props.nodes[anim_props.node_index]
                    c_anim_len = c_item.end_frame - c_item.start_frame
                    n_item = anim_props.nodes[anim_props.node_index + 1]
                    c_item.start_frame = n_item.start_frame
                    c_item.end_frame = c_item.start_frame + c_anim_len
            elif anim_props.bulk_anim_option == 'LINKS':
                if anim_props.link_index > 0:
                    anim_props.nodes.move(anim_props.link_index, anim_props.link_index-1)
                    anim_props.link_index -= 1
                    c_item = anim_props.links[anim_props.link_index]
                    c_anim_len = c_item.end_frame - c_item.start_frame
                    n_item = anim_props.links[anim_props.link_index + 1]
                    c_item.start_frame = n_item.start_frame
                    c_item.end_frame = c_item.start_frame + c_anim_len
            elif anim_props.bulk_anim_option == 'VIEWS':
                if anim_props.view_index > 0:
                    anim_props.nodes.move(anim_props.view_index, anim_props.view_index-1)
                    anim_props.view_index -= 1
                    c_item = anim_props.views[anim_props.view_index]
                    c_anim_len = c_item.end_frame - c_item.start_frame
                    n_item = anim_props.views[anim_props.view_index + 1]
                    c_item.start_frame = n_item.start_frame
                    c_item.end_frame = c_item.start_frame + c_anim_len
                    c_item.name = f"{anim_props.view_index}"
                    n_item.name = f"{anim_props.view_index + 1}"
        return {'FINISHED'}

class NODETREE_OT_List_MoveDown(bpy.types.Operator):
    bl_idname = "nodetree_anim.list_movedown"
    bl_label = "Move Down"
    bl_description = "Move down the selected item in the list"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        anim_props = context.scene.nodetree_anim_props
        if anim_props.anim_option == 'BULK':
            if anim_props.bulk_anim_option == 'NODES':
                if anim_props.node_index < len(anim_props.nodes) - 1:
                    anim_props.nodes.move(anim_props.node_index, anim_props.node_index+1)
                    anim_props.node_index += 1
                    c_item = anim_props.nodes[anim_props.node_index]
                    p_item = anim_props.nodes[anim_props.node_index - 1]
                    p_anim_len = p_item.end_frame - p_item.start_frame
                    p_item.start_frame = c_item.start_frame
                    p_item.end_frame = p_item.start_frame + p_anim_len
            elif anim_props.bulk_anim_option == 'LINKS':
                if anim_props.link_index < len(anim_props.links) - 1:
                    anim_props.links.move(anim_props.link_index, anim_props.link_index+1)
                    anim_props.link_index += 1
                    c_item = anim_props.links[anim_props.link_index]
                    p_item = anim_props.links[anim_props.link_index - 1]
                    p_anim_len = p_item.end_frame - p_item.start_frame
                    p_item.start_frame = c_item.start_frame
                    p_item.end_frame = p_item.start_frame + p_anim_len
            elif anim_props.bulk_anim_option == 'VIEWS':
                if anim_props.view_index < len(anim_props.views) - 1:
                    anim_props.views.move(anim_props.view_index, anim_props.view_index+1)
                    anim_props.view_index += 1
                    c_item = anim_props.views[anim_props.view_index]
                    p_item = anim_props.views[anim_props.view_index - 1]
                    c_item.name = f"{anim_props.view_index}"
                    p_item.name = f"{anim_props.view_index - 1}"
                    p_anim_len = p_item.end_frame - p_item.start_frame
                    p_item.start_frame = c_item.start_frame
                    p_item.end_frame = p_item.start_frame + p_anim_len
        return {'FINISHED'}

class NODETREE_OT_List_AddItem(bpy.types.Operator):
    bl_idname = "nodetree_anim.list_additem"
    bl_label = "Add Item"
    bl_description = "Add an item to the list"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        anim_props = context.scene.nodetree_anim_props
        node_tree = anim_props.node_tree
        item = anim_props.views.add()
        start_frame = anim_props.start_frame
        if len(anim_props.views) > 1:
            start_frame = anim_props.views[-1].end_frame + anim_props.views[-1].stagger_time
        item.name = "0" if len(anim_props.views) == 1 else f"{int(anim_props.views[-2].name)+1}"
        item.start_frame = start_frame if len(anim_props.views)==1 else anim_props.views[-2].end_frame + anim_props.views[-2].stagger_time
        item.end_frame = item.start_frame + anim_props.view_anim_length
        item.stagger_time = anim_props.view_anim_stagger
        item.anim_type = anim_props.view_anim_type
        item.view_offset = anim_props.view_offset
        item.view_zoom = anim_props.view_zoom
        item.sync = anim_props.view_sync
        return {'FINISHED'}

class NODETREE_OT_List_DelItem(bpy.types.Operator):
    bl_idname = "nodetree_anim.list_delitem"
    bl_label = "Del Item"
    bl_description = "Delete an item from the list"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        anim_props = context.scene.nodetree_anim_props
        if anim_props.anim_option == 'BULK':
            if anim_props.bulk_anim_option == 'NODES':
                anim_props.nodes.remove(anim_props.node_index)
            elif anim_props.bulk_anim_option == 'LINKS':
                anim_props.links.remove(anim_props.link_index)
            elif anim_props.bulk_anim_option == 'VIEWS':
                anim_props.views.remove(anim_props.view_index)
        return {'FINISHED'}

class NODETREE_OT_Add_Node_Anim(bpy.types.Operator):
    bl_idname = "nodetree_anim.add_node_anim"
    bl_label = "Add Node Animation"
    bl_description = "add an animation from node"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        node_props = context.scene.nodetree_node_props
        node_tracking = context.scene.nodetree_anim_node_tracking
        node_tree = None
        space = context.space_data
        if space and space.type == 'NODE_EDITOR':
            node_tree = space.edit_tree
        if node_tree is None:
            self.report("WARNING", "no node tree found!")
            return {'CANCELED'}
        node_name = node_props.nodes[node_props.node_index].name
        item = node_tracking.get(node_tree.name)
        if item is None:
            item = node_tracking.add()
            item.name = node_tree.name
        existing_nitem = [ n.name for n in item.anim_nodes if n.node_name == node_name]
        uniq_name = get_next_uniq_key(node_name, existing_nitem)
        nitem  = item.anim_nodes.add()
        nitem.name = uniq_name
        nitem.node_name = node_name
        nitem.start_frame = node_props.anim_start_frame
        nitem.end_frame = node_props.anim_end_frame
        nitem.anim_type = node_props.node_anim_type
        nitem.start_pos = node_props.start_pos
        nitem.org_pos = node_tree.nodes[node_name].location
        nitem.org_size = (node_tree.nodes[node_name].width, node_tree.nodes[node_name].height)
        nitem.pathx_multiplier = node_props.pathx_multiplier
        nitem.pathy_multiplier = node_props.pathy_multiplier
        anim_curve_tree = bpy.data.node_groups.get(f"{node_tree.name}_AnimCurves")
        if anim_curve_tree is None:
            anim_curve_tree = bpy.data.node_groups.new(f"{node_tree.name}_AnimCurves", 'GeometryNodeTree')
            anim_curve_tree.use_fake_user = True
        if anim_curve_tree.nodes.get(f"{uniq_name}_anim_curve") is None:
            anim_curve_tree.nodes.new('ShaderNodeFloatCurve').name = f"{uniq_name}_anim_curve"
        curve_node = anim_curve_tree.nodes[f"{uniq_name}_anim_curve"]
        set_curve_node = anim_curve_tree.nodes.get("node_anim_curve")
        if set_curve_node is not None:
            copy_float_curve(set_curve_node.mapping, curve_node.mapping)
        if node_props.add_anim == "NODEANIM":
            if node_props.node_anim_type == "FLY_IN":
                nitem.sync = node_props.sync_node_path
                for path in ["pathx", "pathy"]:
                    if anim_curve_tree.nodes.get(f"{uniq_name}_{path}_curve") is None:
                        anim_curve_tree.nodes.new('ShaderNodeFloatCurve').name = f"{uniq_name}_{path}_curve"
                    curve_node =  anim_curve_tree.nodes[f"{uniq_name}_{path}_curve"]
                    set_curve_node = anim_curve_tree.nodes.get(f"node_{path}_curve")
                    if set_curve_node is not None:
                        copy_float_curve(set_curve_node.mapping, curve_node.mapping)
            elif node_props.node_anim_type == "SHRINK":
                nitem.sync = node_props.sync_node_shrink
                if anim_curve_tree.nodes.get(f"{uniq_name}_shrink_curve") is None:
                    anim_curve_tree.nodes.new('ShaderNodeFloatCurve').name = f"{uniq_name}_shrink_curve"
                curve_node =  anim_curve_tree.nodes[f"{uniq_name}_shrink_curve"]
                set_curve_node = anim_curve_tree.nodes.get(f"node_shrink_curve")
                if set_curve_node is not None:
                    copy_float_curve(set_curve_node.mapping, curve_node.mapping)
        self.report({'INFO'}, f"Added animation for node '{node_name}' in node tree '{node_tree.name}'")
        return {'FINISHED'}

class NODETREE_OT_Add_Link_Anim(bpy.types.Operator):
    bl_idname = "nodetree_anim.add_link_anim"
    bl_label = "Add Link Animation"
    bl_description = "Add an animation from link"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        node_props = context.scene.nodetree_node_props
        link_tracking = context.scene.nodetree_anim_link_tracking
        node_tree = None
        space = context.space_data
        if space and space.type == 'NODE_EDITOR':
            node_tree = space.edit_tree
        if node_tree is None:
            self.report("WARNING", "no node tree found!")
            return {'CANCELED'}
        if node_props.build_link_type == "NEWLINK":
            node_name = node_props.from_node
            to_node = node_props.to_node
            from_socket = node_props.from_socket
            to_socket = node_props.to_socket
            if any(x is None for x in [node_name, to_node, from_socket, to_socket]):
                self.report("WARNING", "node or socket can't be None!")
                return {'CANCELED'}
        else:
            node_name = node_props.nodes[node_props.node_index].name
            to_node = node_props.links[node_props.link_index].to_node
            from_socket = node_props.links[node_props.link_index].from_socket
            to_socket = node_props.links[node_props.link_index].to_socket
        item = link_tracking.get(node_tree.name)
        nitem = None
        if item is None:
            item = link_tracking.add()
            item.name = node_tree.name
            nitem = item.anim_links.add()
            nitem.name = node_name
            nitem.node_name = node_name
        else:
            nitem = item.anim_links.get(node_name)
            if nitem is None:
                nitem = item.anim_links.add()
                nitem.name = node_name
                nitem.node_name = node_name
        existing_nnitem = [ n.name for n in nitem.node_links if n.from_socket == from_socket and n.to_socket == to_socket]
        uniq_name = get_next_uniq_key(f"{node_name} {from_socket} -> {to_socket} {to_node}", existing_nnitem)
        nnitem = nitem.node_links.add()
        nnitem.name = uniq_name
        nnitem.from_node = node_name
        nnitem.to_node =  to_node
        nnitem.from_socket = from_socket
        nnitem.to_socket = to_socket
        nnitem.start_frame = node_props.anim_start_frame
        nnitem.end_frame = node_props.anim_end_frame
        nnitem.anim_type = node_props.link_anim_type
        anim_curve_tree = bpy.data.node_groups.get(f"{node_tree.name}_AnimCurves")
        if anim_curve_tree is None:
            anim_curve_tree = bpy.data.node_groups.new(f"{node_tree.name}_AnimCurves", 'GeometryNodeTree')
            anim_curve_tree.use_fake_user = True
        curve_node = anim_curve_tree.nodes.get(f"{uniq_name}_anim_curve")
        if curve_node is None:
            curve_node = anim_curve_tree.nodes.new('ShaderNodeFloatCurve')
            curve_node.name = f"{uniq_name}_anim_curve"
        set_curve_node = anim_curve_tree.nodes.get("node.link_anim_curve")
        if set_curve_node:
            copy_float_curve(set_curve_node.mapping, curve_node.mapping)
        self.report({'INFO'}, f"Added animation for link {nnitem.from_node}.{nnitem.from_socket} -> {nnitem.to_node}.{nnitem.to_socket}")
        return {'FINISHED'}

class NODETREE_OT_Add_Value_Anim(bpy.types.Operator):
    bl_idname = "nodetree_anim.add_value_anim"
    bl_label = "Add Value Animation"
    bl_description = "Add an animation for Value"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        node_props = context.scene.nodetree_node_props
        value_tracking = context.scene.nodetree_anim_value_tracking
        node_tree = None
        space = context.space_data
        if space and space.type == 'NODE_EDITOR':
            node_tree = space.edit_tree
        if node_tree is None:
            self.report("WARNING", "no node tree found!")
            return {'CANCELED'}
        node_name = node_props.nodes[node_props.node_index].name
        socket_name = node_props.values[node_props.value_index].name
        is_output = node_props.values[node_props.value_index].is_output
        socket_type = "inputs"
        if is_output:
            socket_type = "outputs"
        item = value_tracking.get(node_tree.name)
        nitem = None
        if item is None:
            item = value_tracking.add()
            item.name = node_tree.name
            nitem = item.anim_values.add()
            nitem.name = node_name
            nitem.node_name = node_name
        else:
            nitem = item.anim_values.get(node_name)
            if nitem is None:
                nitem = item.anim_values.add()
                nitem.name = node_name
                nitem.node_name = node_name
        existing_nnitem = [ n.name for n in nitem.node_values if n.socket_name == socket_name and n.is_output == is_output]
        uniq_name = get_next_uniq_key(f"{node_name} {is_output}.{socket_name}", existing_nnitem)
        nnitem = nitem.node_values.add()
        nnitem.name = uniq_name
        nnitem.socket_name = socket_name
        nnitem.is_output = is_output
        nnitem.start_frame = node_props.anim_start_frame
        nnitem.end_frame = node_props.anim_end_frame
        nnitem.sync = node_props.sync_value
        anim_curve_tree = bpy.data.node_groups.get(f"{node_tree.name}_AnimCurves")
        if anim_curve_tree is None:
            anim_curve_tree = bpy.data.node_groups.new(f"{node_tree.name}_AnimCurves", 'GeometryNodeTree')
            anim_curve_tree.use_fake_user = True
        curve_node = anim_curve_tree.nodes.get(f"{uniq_name}_anim_curve")
        if curve_node is None:
            curve_node = anim_curve_tree.nodes.new('ShaderNodeFloatCurve')
            curve_node.name = f"{uniq_name}_anim_curve"
        set_curve_node = anim_curve_tree.nodes.get("node.value_anim_curve")
        if set_curve_node:
            copy_float_curve(set_curve_node.mapping, curve_node.mapping)
        self.report({'INFO'}, f"Added animation for value '{nnitem.socket_name}' in node '{node_name}' {socket_type}")
        return {'FINISHED'}

class NODETREE_OT_Add_Annotate_Anim(bpy.types.Operator):
    bl_idname = "nodetree_anim.add_annotation_anim"
    bl_label = "Add Annotate Animation"
    bl_description = "Add an animation for Annotation"
    bl_options = {'REGISTER', 'UNDO'}

    @staticmethod
    def prepare_anim(context, note_layer, anim_strokes):
        anim_frame = note_layer.frames[-1].frame_number + 1
        frame = note_layer.frames.new(anim_frame, active=True)
        #current_frame = context.scene.frame_current
        #context.scene.frame_set(anim_frame)
        note_layer.lock_frame = True
        note_layer.lock = True
        #context.scene.frame_current = current_frame
        for anim_stroke in anim_strokes:
            if anim_stroke.layer == note_layer.info:
                # adding anim strokes
                if anim_stroke.anim_idx < 0:
                    stroke = frame.strokes.new()
                    stroke.display_mode = '2DSPACE'
                    anim_stroke.anim_idx = len(frame.strokes) - 1
                    stroke.points.add(count=1)
                    stroke.points[-1].co = (-1000000., -1000000., 0.0)
                # adding symbol strokes
                for stroke_anim in anim_stroke.stroke_anims:
                    if stroke_anim.write_symbol != "NONE":
                        if not vb._write_symbols:
                            get_annotation_write_symbol()
                        write_symbol = vb._write_symbols.get(stroke_anim.write_symbol)
                        if (stroke_anim.end_frame-stroke_anim.start_frame)>1 and stroke_anim.symbol_idx < 0 and write_symbol:
                            for i in range(len(write_symbol)):
                                symbol_stroke = frame.strokes.new()
                                symbol_stroke.display_mode = '2DSPACE'
                                if i == 0:
                                    stroke_anim.symbol_idx = len(frame.strokes) - 1
                                symbol_stroke.points.add(count=1)
                                symbol_stroke.points[-1].co = (-1000000., -1000000., 0.0)

    @staticmethod
    def split_range(start, end, n):
        length = end - start + 1

        if length <= 1:
            return [(start, end)] * n

        ranges = []

        for i in range(n):
            a = start + (i * length) // n
            b = start + ((i + 1) * length) // n - 1

            # Prevent singleton ranges by overlapping
            if b <= a:
                if a < end:
                    b = a + 1
                else:
                    a = end - 1
                    b = end

            ranges.append((a, b))

        return ranges

    def execute(self, context):
        note_props = context.scene.nodetree_note_props
        note_tracking = context.scene.nodetree_anim_note_tracking
        note = context.annotation_data
        if note is None:
            self.report({'INFO'}, "No annotation data.")
            return {'FINISHED'}
        item =  note_tracking.anim_annotations.get(note.name)
        if item is None:
            item = note_tracking.anim_annotations.add()
        item.name = note.name

        node_tree = context.space_data.edit_tree
        if note_props.anim_level == 'LAYER':
            for layer in note.layers:
                anim_mode = 1 if layer.lock else 0
                track_layer = note_props.layers.get(layer.info)
                if track_layer is not None:
                    n_stroke = sum(len(layer.frames[idx].strokes) for idx in range(len(layer.frames)-anim_mode))
                    if track_layer.select:
                        start_end = self.split_range(track_layer.start_frame, track_layer.end_frame, n_stroke)
                    else:
                        end_idx = len(layer.frames)-anim_mode
                        start_end = [(frame.frame_number-1, frame.frame_number) for frame in layer.frames[:end_idx] for _ in frame.strokes]
                    range_idx = 0
                    for f_idx in range(len(layer.frames)-anim_mode):
                        for s_idx, stroke in enumerate(layer.frames[f_idx].strokes):
                            anim_stroke = item.anim_strokes.get(f"{layer.info}.{f_idx}.{s_idx}")
                            if anim_stroke is None:
                                anim_stroke = item.anim_strokes.add()
                                anim_stroke.name = f"{layer.info}.{f_idx}.{s_idx}"
                                anim_stroke.layer = layer.info
                                anim_stroke.frame = f_idx
                                anim_stroke.stroke = s_idx
                                anim_stroke.idx = len(item.anim_strokes) - 1
                            stroke_anim = anim_stroke.stroke_anims.get(f"{start_end[range_idx][0]}.{start_end[range_idx][1]}")
                            if not track_layer.select and len(anim_stroke.stroke_anims) > 0:
                                continue
                            if stroke_anim is None:
                                stroke_anim = anim_stroke.stroke_anims.add()
                                stroke_anim.name = f"{start_end[range_idx][0]}.{start_end[range_idx][1]}"
                            else:
                                self.report({"ERROR"}, f"stroke: layer:{layer.info}->frame:{layer.frames[f_idx].frame_number}->stroke:{s_idx} for anim range: {stroke_anim.start_frame} to {stroke_anim.end_frame} already exists, remove it first to add new.")
                                return {'CANCELLED'}

                            stroke_anim.idx = len(anim_stroke.stroke_anims)-1
                            stroke_anim.start_frame = start_end[range_idx][0]
                            stroke_anim.end_frame  = start_end[range_idx][1]
                            stroke_anim.anim_type = track_layer.anim_type
                            stroke_anim.write_symbol = track_layer.write_symbol
                            stroke_anim.symbol_scale = (track_layer.symbol_scale, track_layer.symbol_scale)
                            stroke_anim.symbol_shift =  track_layer.symbol_shift
                            anim_curve_tree = bpy.data.node_groups.get(f"{node_tree.name}_AnimCurves")
                            if anim_curve_tree is None:
                                anim_curve_tree = bpy.data.node_groups.new(f"{node_tree.name}_AnimCurves", 'GeometryNodeTree')
                                anim_curve_tree.use_fake_user = True
                            if anim_curve_tree.nodes.get(f"{anim_stroke.name}.{stroke_anim.name}_anim_curve") is None:
                                anim_curve_tree.nodes.new('ShaderNodeFloatCurve').name = f"{anim_stroke.name}.{stroke_anim.name}_anim_curve"
                            curve_node = anim_curve_tree.nodes[f"{anim_stroke.name}.{stroke_anim.name}_anim_curve"]
                            set_curve_node = anim_curve_tree.nodes.get("annotation_anim_curve")
                            if set_curve_node is not None:
                                copy_float_curve(set_curve_node.mapping, curve_node.mapping)

                            range_idx += 1
                            # sort by the start_frame
                            if len(anim_stroke.stroke_anims) > 1:
                                source_idx = stroke_anim.idx
                                target_idx = stroke_anim.idx
                                for anim in anim_stroke.stroke_anims[:-1]:
                                    if anim.start_frame > stroke_anim.start_frame:
                                        target_idx = anim.idx
                                        break
                                if source_idx != target_idx:
                                    anim_stroke.stroke_anims.move(source_idx, target_idx)
                                    # also update the index
                                    for idx, anim in enumerate(anim_stroke.stroke_anims[target_idx:]):
                                        anim.idx =  idx
                    # create a new frame for the animation data
                    if not layer.lock:
                        self.prepare_anim(context, layer, item.anim_strokes)
        elif note_props.anim_level == 'FRAME':
            for layer in note.layers:
                new_anim_layer = False
                anim_mode = 1 if layer.lock else 0
                for f_idx in range(len(layer.frames)-anim_mode):
                    track_frame = note_props.frames.get(f'{layer.info}.{f_idx}')
                    if track_frame is not None:
                        if not layer.lock:
                            new_anim_layer = True
                        n_stroke = len(layer.frames[f_idx].strokes)
                        if track_frame.select:
                            start_end = self.split_range(track_frame.start_frame, track_frame.end_frame, n_stroke)
                        else:
                            frame = layer.frames[f_idx]
                            start_end = [(frame.frame_number-1, frame.frame_number)]*len(frame.strokes)
                        for s_idx, stroke in enumerate(layer.frames[f_idx].strokes):
                            anim_stroke =  item.anim_strokes.get(f"{layer.info}.{f_idx}.{s_idx}")
                            if anim_stroke is None:
                                anim_stroke = item.anim_strokes.add()
                                anim_stroke.name = f"{layer.info}.{f_idx}.{s_idx}"
                                anim_stroke.layer = layer.info
                                anim_stroke.frame = f_idx
                                anim_stroke.stroke = s_idx
                                anim_stroke.idx = len(item.anim_strokes) - 1
                            stroke_anim = anim_stroke.stroke_anims.get(f"{start_end[s_idx][0]}.{start_end[s_idx][1]}")
                            if not track_frame.select and len(anim_stroke.stroke_anims) > 0:
                                continue
                            if stroke_anim is None:
                                stroke_anim = anim_stroke.stroke_anims.add()
                                stroke_anim.name = f"{start_end[s_idx][0]}.{start_end[s_idx][1]}"
                            else:
                                self.report({"ERROR"}, f"stroke: layer:{layer.info}->frame:{layer.frames[f_idx].frame_number}->stroke:{s_idx} for anim range: {stroke_anim.start_frame} to {stroke_anim.end_frame} already exists, remove it first to add new.")
                                return {'CANCELLED'}

                            stroke_anim.idx = len(anim_stroke.stroke_anims)-1
                            stroke_anim.start_frame = start_end[s_idx][0]
                            stroke_anim.end_frame  = start_end[s_idx][1]
                            stroke_anim.anim_type = track_frame.anim_type
                            stroke_anim.write_symbol = track_frame.write_symbol
                            stroke_anim.symbol_scale = (track_frame.symbol_scale, track_frame.symbol_scale)
                            stroke_anim.symbol_shift =  track_frame.symbol_shift

                            anim_curve_tree = bpy.data.node_groups.get(f"{node_tree.name}_AnimCurves")
                            if anim_curve_tree is None:
                                anim_curve_tree = bpy.data.node_groups.new(f"{node_tree.name}_AnimCurves", 'GeometryNodeTree')
                                anim_curve_tree.use_fake_user = True
                            if anim_curve_tree.nodes.get(f"{anim_stroke.name}.{stroke_anim.name}_anim_curve") is None:
                                anim_curve_tree.nodes.new('ShaderNodeFloatCurve').name = f"{anim_stroke.name}.{stroke_anim.name}_anim_curve"
                            curve_node = anim_curve_tree.nodes[f"{anim_stroke.name}.{stroke_anim.name}_anim_curve"]
                            set_curve_node = anim_curve_tree.nodes.get("annotation_anim_curve")
                            if set_curve_node is not None:
                                copy_float_curve(set_curve_node.mapping, curve_node.mapping)

                            # sort by the start_frame
                            if len(anim_stroke.stroke_anims) > 1:
                                source_idx = stroke_anim.idx
                                target_idx = stroke_anim.idx
                                for anim in anim_stroke.stroke_anims[:-1]:
                                    if anim.start_frame > stroke_anim.start_frame:
                                        target_idx = anim.idx
                                        break
                                if source_idx != target_idx:
                                    anim_stroke.stroke_anims.move(source_idx, target_idx)
                                    # also update the index
                                    for idx, anim in enumerate(anim_stroke.stroke_anims[target_idx:]):
                                        anim.idx =  idx
                # create a new frame for the animation data
                if new_anim_layer:
                    self.prepare_anim(context, layer, item.anim_strokes)
        elif note_props.anim_level == 'STROKE':
            for layer in note.layers:
                new_anim_layer = False
                anim_mode = 1 if layer.lock else 0
                for f_idx in range(len(layer.frames)-anim_mode):
                    for s_idx, stroke in enumerate(layer.frames[f_idx].strokes):
                        track_stroke = note_props.strokes.get(f'{layer.info}.{f_idx}.{s_idx}')
                        if track_stroke is not None:
                            if not layer.lock:
                                new_anim_layer = True
                            start_end = (track_stroke.start_frame, track_stroke.end_frame) if track_stroke.select else (layer.frames[f_idx].frame_number - 1, layer.frames[f_idx].frame_number)
                            anim_stroke = item.anim_strokes.get(f"{layer.info}.{f_idx}.{s_idx}")
                            if anim_stroke is None:
                                anim_stroke = item.anim_strokes.add()
                                anim_stroke.name = f"{layer.info}.{f_idx}.{s_idx}"
                                anim_stroke.layer = layer.info
                                anim_stroke.frame = f_idx
                                anim_stroke.stroke = s_idx
                                anim_stroke.idx = len(item.anim_strokes) - 1
                            stroke_anim = anim_stroke.stroke_anims.get(f"{start_end[0]}.{start_end[1]}")
                            if not track_stroke.select and len(anim_stroke.stroke_anims) > 0:
                                continue
                            if stroke_anim is None:
                                stroke_anim = anim_stroke.stroke_anims.add()
                                stroke_anim.name = f"{start_end[0]}.{start_end[1]}"
                            else:
                                self.report({"ERROR"}, f"stroke: layer:{layer.info}->frame:{layer.frames[f_idx].frame_number}->stroke:{s_idx} for anim range: {stroke_anim.start_frame} to {stroke_anim.end_frame} already exists, remove it first to add new.")
                                return {'CANCELLED'}

                            stroke_anim.idx = len(anim_stroke.stroke_anims)-1
                            stroke_anim.start_frame = start_end[0]
                            stroke_anim.end_frame  = start_end[1]
                            stroke_anim.anim_type = track_stroke.anim_type
                            stroke_anim.write_symbol = track_stroke.write_symbol
                            stroke_anim.symbol_scale = (track_stroke.symbol_scale, track_stroke.symbol_scale)
                            stroke_anim.symbol_shift =  track_stroke.symbol_shift

                            anim_curve_tree = bpy.data.node_groups.get(f"{node_tree.name}_AnimCurves")
                            if anim_curve_tree is None:
                                anim_curve_tree = bpy.data.node_groups.new(f"{node_tree.name}_AnimCurves", 'GeometryNodeTree')
                                anim_curve_tree.use_fake_user = True
                            if anim_curve_tree.nodes.get(f"{anim_stroke.name}.{stroke_anim.name}_anim_curve") is None:
                                anim_curve_tree.nodes.new('ShaderNodeFloatCurve').name = f"{anim_stroke.name}.{stroke_anim.name}_anim_curve"
                            curve_node = anim_curve_tree.nodes[f"{anim_stroke.name}.{stroke_anim.name}_anim_curve"]
                            set_curve_node = anim_curve_tree.nodes.get("annotation_anim_curve")
                            if set_curve_node is not None:
                                copy_float_curve(set_curve_node.mapping, curve_node.mapping)

                            # sort by the start_frame
                            if len(anim_stroke.stroke_anims) > 1:
                                source_idx = stroke_anim.idx
                                target_idx = stroke_anim.idx
                                for anim in anim_stroke.stroke_anims[:-1]:
                                    if anim.start_frame > stroke_anim.start_frame:
                                        target_idx = anim.idx
                                        break
                                if source_idx != target_idx:
                                    anim_stroke.stroke_anims.move(source_idx, target_idx)
                                    # also update the index
                                    for idx, anim in enumerate(anim_stroke.stroke_anims[target_idx:]):
                                        anim.idx =  idx
                # create a new frame for the animation data
                if new_anim_layer:
                    self.prepare_anim(context, layer, item.anim_strokes)

        self.report({'INFO'}, f"Adding annotation animation for '{note.name}'")
        return {'FINISHED'}

class NODETREE_OT_Refresh_Annotation(bpy.types.Operator):
    bl_idname = "nodetree_anim.refresh_annotation"
    bl_label = "Refresh Annotation"
    bl_description = "Update Annotation Data"
    bl_options = {'REGISTER', 'UNDO'}

    option: bpy.props.EnumProperty(
        name="Option",
        description="Refresh option",
        items=[
            ('REFRESH', "Refresh Annotation", "Refresh all annotation data", "FILE_REFRESH", 0),
            ('RESTORE', "Restore Annotation", "Restore annotation data", "LOOP_BACK", 1),
        ],
        default='REFRESH',
    )
    def execute(self, context):
        if self.option == 'REFRESH':
            note_props = context.scene.nodetree_note_props
            note = context.annotation_data
            if note is not None:
                note_props.update_level(context)
        elif self.option == 'RESTORE':
            note_tracking = context.scene.nodetree_anim_note_tracking
            note = context.annotation_data
            if note is not None:
                for layer in note.layers:
                    if layer.lock:
                        layer.lock = False
                        layer.lock_frame = False
                        layer.frames.remove(layer.frames[-1])
                item =  note_tracking.anim_annotations.get(note.name)
                if item is not None:
                    item.anim_strokes.clear()
        return {'FINISHED'}

class NODETREE_OT_DelAnim(bpy.types.Operator):
    bl_idname = "nodetree_anim.del_anim"
    bl_label = "Del Anim"
    bl_description = "Delete an animation for node or link"
    bl_options = {'REGISTER', 'UNDO'}

    key_name: bpy.props.StringProperty()
    anim_type: bpy.props.StringProperty()
    def execute(self, context):
        if self.anim_type == 'NODEANIM':
            node_tracking = context.scene.nodetree_anim_node_tracking
            tree_name = self.key_name.split('**')[0]
            node_name = self.key_name.split('**')[1]
            index = int(self.key_name.split('**')[2])
            item = node_tracking.get(tree_name)
            if item:
                node_tree = bpy.data.node_groups[f"{tree_name}_AnimCurves"]
                curve_node = node_tree.nodes.get(f"{item.anim_nodes[index]['name']}_anim_curve")
                if curve_node:
                    node_tree.nodes.remove(curve_node)
                if item.anim_nodes[index]['anim_type'] == 'FLY_IN':
                    pathx_node = node_tree.nodes.get(f"{item.anim_nodes[index]['name']}_pathx_curve")
                    pathy_node = node_tree.nodes.get(f"{item.anim_nodes[index]['name']}_pathy_curve")
                    if pathx_node:
                        node_tree.nodes.remove(pathx_node)
                    if pathy_node:
                        node_tree.nodes.remove(pathy_node)
                else:
                    shrink_node = node_tree.nodes.get(f"{item.anim_nodes[index]['name']}_shrink_curve")
                    if shrink_node:
                        node_tree.nodes.remove(shrink_node)
                item.anim_nodes.remove(index)
            else:
                self.report({'WARNING'}, f"No node animation tracking for node tree {tree_name}")
        elif self.anim_type == 'LINKANIM':
            tree_name = self.key_name.split('**')[0]
            node_name = self.key_name.split('**')[1]
            index = int(self.key_name.split('**')[2])
            link_tracking = context.scene.nodetree_anim_link_tracking
            item = link_tracking.get(tree_name)
            node_tree = bpy.data.node_groups[f"{tree_name}_AnimCurves"]
            if item:
                nitem = item.anim_links.get(node_name)
                if nitem:
                    curve_node = node_tree.nodes.get(f"{nitem.node_links[index]['name']}_anim_curve")
                    if curve_node:
                        node_tree.nodes.remove(curve_node)
                    nitem.node_links.remove(index)
                else:
                    self.report({'WARNING'}, f"No link animation tracking for node {node_name}")
            else:
                self.report({'WARNING'}, f"No link animation tracking for node tree {tree_name}")
        elif self.anim_type == 'VALUEANIM':
            tree_name = self.key_name.split('**')[0]
            node_name = self.key_name.split('**')[1]
            index = int(self.key_name.split('**')[2])
            value_tracking = context.scene.nodetree_anim_value_tracking
            item = value_tracking.get(tree_name)
            node_tree = bpy.data.node_groups[f"{tree_name}_AnimCurves"]
            if item:
                nitem = item.anim_values.get(node_name)
                if nitem:
                    curve_node = node_tree.nodes.get(f"{nitem.node_values[index]['name']}_anim_curve")
                    if curve_node:
                        node_tree.nodes.remove(curve_node)
                    #keys = []
                    #node_tree = context.space_data.edit_tree
                    #if nitem.node_values[index]['is_output']:
                    #    keys = [f"output_{nitem.node_values[index]['socket_name']}_start", f"output_{nitem.node_values[index]['socket_name']}_end" ]
                    #else:
                    #    keys = [f"input_{nitem.node_values[index]['socket_name']}_start", f"input_{nitem.node_values[index]['socket_name']}_end" ]
                    #node = node_tree.nodes[node_name]
                    #for key in keys:
                    #    if key in node:
                    #        del node[key]
                    #        #ui = node.id_properties_ui(key)
                    #        #if ui:
                    #        #    ui.clear()
                    nitem.node_values.remove(index)
                else:
                    self.report({'WARNING'}, f"No value animation tracking for node {node_name}")
            else:
                self.report({'WARNING'}, f"No value animation tracking for node tree {tree_name}")
        elif self.anim_type == 'VIEWANIM':
            tree_name = self.key_name.split('**')[0]
            node_name = self.key_name.split('**')[1]
            index = int(self.key_name.split('**')[2])
            view_tracking = context.scene.nodetree_anim_view_tracking
            item = view_tracking.get(tree_name)
            node_tree = bpy.data.node_groups[f"{tree_name}_AnimCurves"]
            if item:
                curve_node = node_tree.nodes.get(f"{item.anim_views[index]['name']}_anim_curve")
                if curve_node:
                    node_tree.nodes.remove(curve_node)
                item.anim_views.remove(index)
            else:
                self.report({'WARNING'}, f"No view animation tracking for node tree {tree_name}")
        elif self.anim_type == 'STROKEANIM':
            anim_strokes = context.scene.nodetree_anim_note_tracking.anim_annotations[context.annotation_data.name].anim_strokes
            node_tree = context.space_data.edit_tree
            anim_tree = bpy.data.node_groups[f"{node_tree.name}_AnimCurves"]
            level = self.key_name.split('**')[0]
            stroke_id = self.key_name.split('**')[1]
            anim_id = self.key_name.split('**')[2]
            anim_stroke = anim_strokes[stroke_id]
            if len(anim_stroke.stroke_anims) < 2:
                level = 'STROKE'
            if not vb._write_symbols:
                get_annotation_write_symbol()
            if level == 'STROKE':
                remove_idx = []
                for anim in anim_stroke.stroke_anims:
                    if anim.symbol_idx >= 0:
                        write_symbol = vb._write_symbols[anim.write_symbol]
                        remove_idx.append((anim.symbol_idx, anim.symbol_idx + len(write_symbol)))
                    # remove anim curve
                    curve_node = anim_tree.nodes.get(f"{anim_stroke.name}.{anim.name}_anim_curve")
                    if curve_node:
                        anim_tree.nodes.remove(curve_node)
                remove_idx.append((anim_stroke.anim_idx, anim_stroke.anim_idx + 1))
                # remove the tracking
                anim_stroke.stroke_anims.clear()
                # clean the strokes
                anim_frame = context.annotation_data.layers[anim_stroke.layer].frames[-1]
                for remove_start, remove_end in remove_idx:
                    for _ in range(remove_end - remove_start):
                        stroke = anim_frame.strokes[remove_start]
                        anim_frame.strokes.remove(stroke)
                    # update idx
                    for stroke in anim_strokes:
                        if stroke.layer == anim_stroke.layer:
                            if stroke.anim_idx >= remove_end:
                                stroke.anim_idx -= (remove_end - remove_start)
                            for anim in stroke.stroke_anims:
                                if anim.symbol_idx >= remove_end:
                                    anim.symbol_idx -= (remove_end - remove_start)
                # update idx
                for stroke in anim_strokes[anim_stroke.idx+1:]:
                    stroke.idx -= 1
                anim_strokes.remove(anim_stroke.idx)
            if level == 'ANIM':
                remove_idx = []
                anim = anim_stroke.stroke_anims[anim_id]
                if anim.symbol_idx >= 0:
                    write_symbol = vb._write_symbols[anim.write_symbol]
                    remove_idx.append((anim.symbol_idx, anim.symbol_idx + len(write_symbol)))
                # remove anim curve
                curve_node = anim_tree.nodes.get(f"{anim_stroke.name}.{anim.name}_anim_curve")
                if curve_node:
                    anim_tree.nodes.remove(curve_node)
                # remove the tracking
                anim_stroke.stroke_anims.remove(anim.idx)
                # clean the strokes
                anim_frame = context.annotation_data.layers[anim_stroke.layer].frames[-1]
                for remove_start, remove_end in remove_idx:
                    for _ in range(remove_end - remove_start):
                        stroke = anim_frame.strokes[remove_start]
                        anim_frame.strokes.remove(stroke)
                    # update idx
                    for stroke in anim_strokes:
                        if stroke.layer == anim_stroke.layer:
                            if stroke.anim_idx >= remove_end:
                                stroke.anim_idx -= (remove_end - remove_start)
                            for idx, anim in enumerate(stroke.stroke_anims):
                                if stroke.name == anim_stroke.name:
                                    aim.idx = idx
                                if anim.symbol_idx >= remove_end:
                                    anim.symbol_idx -= (remove_end - remove_start)

        return {'FINISHED'}

classes = (
    NODETREE_OT_Build_Anim,
    NODETREE_OT_List_AddItem,
    NODETREE_OT_List_DelItem,
    NODETREE_OT_List_MoveUp,
    NODETREE_OT_List_MoveDown,
    NODETREE_OT_Refresh_NodeList,
    NODETREE_OT_Add_Node_Anim,
    NODETREE_OT_Add_Link_Anim,
    NODETREE_OT_Add_Value_Anim,
    NODETREE_OT_Refresh_Annotation,
    NODETREE_OT_Add_Annotate_Anim,
    NODETREE_OT_DelAnim,
)
register, unregister = bpy.utils.register_classes_factory(classes)
