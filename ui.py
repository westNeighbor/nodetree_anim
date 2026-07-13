import bpy
from bl_ui.properties_grease_pencil_common import AnnotationDataPanel,GPENCIL_UL_annotation_layer
from bl_ui.space_toolsystem_common import ToolSelectPanelHelper

def draw_tool_button(layout, context, tool_id, label=""):
    cls = ToolSelectPanelHelper._tool_class_from_space_type(
        context.space_data.type
    )
    tool, _ = cls._tool_get_by_id(context, tool_id)

    if tool is None:
        return

    tool_active_id = getattr(
        ToolSelectPanelHelper._tool_active_from_context(context, context.space_data.type),
        "idname", None,
    )
    is_active = (tool.idname == tool_active_id)
    layout.operator(
        "wm.tool_set_by_id",
        text=label,
        depress=is_active,
        icon_value=ToolSelectPanelHelper._icon_value_from_icon_handle(tool.icon),
    ).name = tool.idname

def update_panel_category(self, context):
    bpy.utils.unregister_class(NODETREE_ANIM_PT_main_panel)
    prefs = bpy.context.preferences.addons[__package__].preferences
    NODETREE_ANIM_PT_main_panel.bl_category = prefs.panel_category
    bpy.utils.register_class(NODETREE_ANIM_PT_main_panel)

class NODETREE_ANIM_UL_nodes(bpy.types.UIList):

    def draw_item( self, context, layout, data, item, icon, active_data, active_propname, index):
        space = context.space_data
        node_tree = None
        if space and space.type == 'NODE_EDITOR':
            node_tree = space.edit_tree
        if node_tree is not None and item:
            props = context.scene.nodetree_anim_props
            if props.anim_option == 'MANUAL':
                if item.type == 'node':
                    if node_tree.nodes.get(item.name) is not None:
                        layout.label(text=item.name, icon='NODE_SEL' if index == data.node_index else 'NODE')
                elif item.type == 'link':
                    if node_tree.nodes.get(item.from_node) is not None and  node_tree.nodes.get(item.to_node) is not None:
                        row = layout.row(align=True)
                        row.enabled = False
                        row.label(text="", icon='NODE_SEL')
                        icon_type = f'NODE_SOCKET_{node_tree.nodes[item.from_node].outputs[item.from_socket].type}'
                        row.label(text=item.from_socket, icon= icon_type if icon_type != 'NODE_SOCKET_VALUE' else 'NODE_SOCKET_FLOAT')
                        icon_type = f'NODE_SOCKET_{node_tree.nodes[item.to_node].inputs[item.to_socket].type}'
                        row.label(text=item.to_socket, icon= icon_type if icon_type != 'NODE_SOCKET_VALUE' else 'NODE_SOCKET_FLOAT')
                        row.label(text=item.to_node, icon="NODE")
                else:
                    row = layout.row(align=True)
                    row.enabled = False
                    if item.is_output:
                        row.label(text=item.name)
                        icon_type = f'NODE_SOCKET_{node_tree.nodes[data.node_index].outputs[item.name].type}'
                        row.label(text="", icon=icon_type if icon_type != 'NODE_SOCKET_VALUE' else 'NODE_SOCKET_FLOAT')
                    else:
                        icon_type = f'NODE_SOCKET_{node_tree.nodes[data.node_index].inputs[item.name].type}'
                        row.label(text="", icon=icon_type if icon_type != 'NODE_SOCKET_VALUE' else 'NODE_SOCKET_FLOAT')
                        row.label(text=item.name)
            elif props.anim_option == 'BULK':
                if props.bulk_anim_option == 'NODES':
                    if node_tree.nodes.get(item.name) is not None:
                        col = layout.column(align=True)
                        col.label(text=item.node_name, icon="NODE")
                        row = col.row(align=True)
                        row.prop(item, "start_frame", text="Start")
                        row.prop(item, "end_frame", text="End")
                        row.prop(item, "stagger_time", text="Stagger")
                        row.prop(item, "anim_type", text="")
                        row.prop(item, "sync", text="Sync")
                        header, panel = col.panel(f"{item.name}_path_control", default_closed=True)
                        if item.anim_type == 'FLY_IN':
                            header.label(text="Path Anim Setting")
                            if panel:
                                row = panel.row(align=True)
                                col = row.column(align=True)
                                col.prop(item, "start_pos", text="Start Position")
                                col = row.column(align=True)
                                col.prop(item, "path_multiplier", text="Path Multiplier")
                        else:
                            header.label(text="Shrink Anim Setting")
                            if panel:
                                panel.prop(item, "init_size", text="Start Size")
                elif props.bulk_anim_option == 'LINKS':
                    if node_tree.nodes.get(item.from_node) is not None and node_tree.nodes.get(item.to_node) is not None:
                        col = layout.column(align=True)
                        row = col.row(align=True)
                        row.label(text=item.from_node, icon="NODE")
                        socket = node_tree.nodes[item.from_node].outputs[item.from_socket]
                        icon_type = f'NODE_SOCKET_{socket.type}' if socket.type != 'VALUE' else 'NODE_SOCKET_FLOAT'
                        row.label(text=item.from_socket, icon=icon_type)
                        socket = node_tree.nodes[item.to_node].inputs[item.to_socket]
                        icon_type = f'NODE_SOCKET_{socket.type}' if socket.type != 'VALUE' else 'NODE_SOCKET_FLOAT'
                        row.label(text=item.to_socket, icon=icon_type)
                        row.label(text=item.to_node, icon="NODE")
                        row = col.row(align=True)
                        row.prop(item, "start_frame", text="Start")
                        row.prop(item, "end_frame", text="End")
                        row.prop(item, "stagger_time", text="Stagger")
                        row.prop(item, "anim_type", text="")
                        header, panel = col.panel(f"{item.name}_offset_control", default_closed=True)
                        header.label(text="Offset Setting")
                        if panel:
                            row = panel.row(align=True)
                            col = row.column(align=True)
                            col.prop(item, "start_offset", text="Start Offset")
                            col = row.column(align=True)
                            col.prop(item, "end_offset", text="End Offset")
                elif props.bulk_anim_option == 'VIEWS':
                    col = layout.column(align=True)
                    row = col.row(align=True)
                    icon = "CON_FOLLOWPATH" if item.anim_type == "FOLLOW" else "VIEWZOOM"
                    row.label(text=f"View Anim {item.name}", icon=icon)
                    row = col.row(align=True)
                    row.prop(item, "start_frame", text="Start")
                    row.prop(item, "end_frame", text="End")
                    row.prop(item, "stagger_time", text="Stagger")
                    row.prop(item, "anim_type", text="")
                    header, panel = col.panel(f"{item.name}_offset_control", default_closed=True)
                    if item.anim_type == "FOLLOW":
                        header.label(text="Offset Setting")
                        if panel:
                            panel.prop(item, "view_offset", text="Move size")
                    else:
                        header.label(text="Zoom Setting")
                        if panel:
                            panel.prop(item, "view_zoom", text="Zoom size")
            elif props.anim_option == 'DRAW':
                note_props = context.scene.nodetree_note_props
                note = context.annotation_data
                if note is not None:
                    if note_props.anim_level == 'LAYER':
                        if note_props.layers.get(item.info):
                            col = layout.column(align=True)
                            row = col.column(align=True)
                            row.label(text=item.info, icon="RENDERLAYERS")
                            row = col.row(align=True)
                            row.prop(note_props.layers[item.info], "start_frame", text="Start")
                            row.prop(note_props.layers[item.info], "end_frame", text="End")
                            row.prop(note_props.layers[item.info], "stagger_time", text="Stagger")
                            row.prop(note_props.layers[item.info], "anim_type", text="")
                            row.prop(note_props.layers[item.info], "write_symbol", text="")
                            row.prop(note_props.layers[item.info], "select", text="")
                            if note_props.layers[item.info].write_symbol != "NONE":
                                header, panel = col.panel(f"{item.info}_symbol_control", default_closed=True)
                                header.label(text="Symbol control")
                                if panel:
                                    row = panel.row(align=True)
                                    row.prop(note_props.layers[item.info], "symbol_scale", text="Symbol Scale")
                                    row.prop(note_props.layers[item.info], "symbol_shift", index=0, text="Symbol Shift X")
                                    row.prop(note_props.layers[item.info], "symbol_shift", index=1, text="Symbol Shift Y")
                    elif note_props.anim_level == 'FRAME':
                        col = layout.column(align=True)
                        row = col.row(align=True)
                        row.column(align=True).label(text=item.info, icon="RENDERLAYERS")
                        row.column(align=True).label(text=" ")
                        row.column(align=True).label(text=" ")
                        anim_mode = 1 if item.lock else 0
                        for f_idx in range(len(item.frames)-anim_mode):
                            row = col.row(align=True)
                            row.label(text=f'{item.frames[f_idx].frame_number}', icon="GP_MULTIFRAME_EDITING")
                            if note_props.frames.get(f'{item.info}.{f_idx}'):
                                row.prop(note_props.frames[f'{item.info}.{f_idx}'], "start_frame", text="Start")
                                row.prop(note_props.frames[f'{item.info}.{f_idx}'], "end_frame", text="End")
                                row.prop(note_props.frames[f'{item.info}.{f_idx}'], "stagger_time", text="Stagger")
                                row.prop(note_props.frames[f'{item.info}.{f_idx}'], "anim_type", text="")
                                row.prop(note_props.frames[f'{item.info}.{f_idx}'], "write_symbol", text="")
                                row.prop(note_props.frames[f'{item.info}.{f_idx}'], "select", text="")
                                if note_props.frames[f'{item.info}.{f_idx}'].write_symbol != 'NONE':
                                    header, panel = col.panel(f"{item.info}.{f_idx}_symbol_control", default_closed=True)
                                    header.label(text="Symbol control")
                                    if panel:
                                        row = panel.row(align=True)
                                        row.prop(note_props.frames[f'{item.info}.{f_idx}'], "symbol_scale", text="Symbol Scale")
                                        row.prop(note_props.frames[f'{item.info}.{f_idx}'], "symbol_shift", index=0, text="Symbol Shift X")
                                        row.prop(note_props.frames[f'{item.info}.{f_idx}'], "symbol_shift", index=1, text="Symbol Shift Y")
                    elif note_props.anim_level == 'STROKE':
                        col = layout.column(align=True)
                        anim_mode = 1 if item.lock else 0
                        for f_idx in range(len(item.frames)-anim_mode):
                            row = col.row(align=True)
                            row.column(align=True).label(text=item.info if f_idx==0 else " ", icon="RENDERLAYERS" if f_idx==0 else "BLANK1")
                            row.column(align=True).label(text=f'{item.frames[f_idx].frame_number}', icon="GP_MULTIFRAME_EDITING")
                            row.column(align=True).label(text=" ")
                            for s_idx, stroke in enumerate(item.frames[f_idx].strokes):
                                row = col.row(align=True)
                                if note_props.strokes.get(f'{item.info}.{f_idx}.{s_idx}'):
                                    row.label(text=f'{note_props.strokes[f"{item.info}.{f_idx}.{s_idx}"].stroke}', icon="GP_SELECT_STROKES")
                                    row.prop(note_props.strokes[f'{item.info}.{f_idx}.{s_idx}'], "start_frame", text="Start")
                                    row.prop(note_props.strokes[f'{item.info}.{f_idx}.{s_idx}'], "end_frame", text="End")
                                    row.prop(note_props.strokes[f'{item.info}.{f_idx}.{s_idx}'], "stagger_time", text="Stagger")
                                    row.prop(note_props.strokes[f'{item.info}.{f_idx}.{s_idx}'], "anim_type", text="")
                                    row.prop(note_props.strokes[f'{item.info}.{f_idx}.{s_idx}'], "write_symbol", text="")
                                    row.prop(note_props.strokes[f'{item.info}.{f_idx}.{s_idx}'], "select", text="")
                                    if note_props.strokes[f'{item.info}.{f_idx}.{s_idx}'].write_symbol != 'NONE':
                                        header, panel = col.panel(f"{item.info}.{f_idx}.{s_idx}_symbol_control", default_closed=True)
                                        header.label(text="Symbol control")
                                        if panel:
                                            row = panel.row(align=True)
                                            row.prop(note_props.strokes[f'{item.info}.{f_idx}.{s_idx}'], "symbol_scale", text="Symbol Scale")
                                            row.prop(note_props.strokes[f'{item.info}.{f_idx}.{s_idx}'], "symbol_shift", index=0, text="Symbol Shift X")
                                            row.prop(note_props.strokes[f'{item.info}.{f_idx}.{s_idx}'], "symbol_shift", index=1, text="Symbol Shift Y")


class NODETREE_ANIM_PT_main_panel(bpy.types.Panel, AnnotationDataPanel):
    bl_label = "NodeTree Anim"
    bl_idname = "NODETREE_ANIM_PT_main_panel"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Nodetree Anim'
    bl_options = set()

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = True  # False for no animation.

        space = context.space_data
        if space and space.type == 'NODE_EDITOR':
            node_tree = space.edit_tree
            if node_tree:
                panel = layout.column()
                panel.enabled = False
                panel.prop(node_tree, "name", text="Nodetree to animate", icon='NODETREE')
                props = context.scene.nodetree_anim_props
                row = layout.row()
                row.prop(props, "anim_option", expand=True)
                if props.anim_option == 'BULK':
                    layout.prop(props, "bulk_anim_option", expand=True)
                    layout.prop(props, "start_frame", text="Anim Start Frame")
                    if props.bulk_anim_option == 'NODES':
                        row = layout.row()
                        row.prop(props, "node_anim_type", text="Node Anim")
                        row.prop(props, "sync_node", text="Sync Before Start")
                        row = layout.row(align=True)
                        row.prop(props, "node_anim_length", text="Anim Length")
                        row.prop(props, "node_anim_stagger", text="Stagger Length")
                        row = layout.row(align=True)
                        col = row.column(align=True)
                        col.prop(props, "start_pos", text="Start Position")
                        col = row.column(align=True)
                        col.prop(props, "path_multiplier", text="Path Multiplier")
                        layout.prop(props, "init_size", text="Start Size")
                        row = layout.row(align=True)
                        op = row.operator("nodetree_anim.refresh_nodelist", text="Refresh Node List")
                        op.renew = 'REFRESH'
                        op = row.operator("nodetree_anim.refresh_nodelist", text="Rebuild Node List")
                        op.renew = 'REBUILD'
                        row = layout.row(align=True)
                        row.template_list("NODETREE_ANIM_UL_nodes", "", props, "nodes", props, "node_index")
                        col = row.column(align=True)
                        col.operator("nodetree_anim.list_moveup", icon="TRIA_UP", text="")
                        col.operator("nodetree_anim.list_movedown", icon="TRIA_DOWN", text="")
                        col.separator()
                        col.operator("nodetree_anim.list_delitem", icon="REMOVE", text="")
                        if bpy.data.node_groups.get(f"{node_tree.name}_AnimCurves") and bpy.data.node_groups[f"{node_tree.name}_AnimCurves"].nodes.get(f"bulk_node_anim_curve"):
                            curve_node = bpy.data.node_groups[f"{node_tree.name}_AnimCurves"].nodes[f"bulk_node_anim_curve"]
                            header, panel = layout.panel("Node Anim Setting", default_closed=True)
                            header.label(text="Node Anim Curve")
                            if panel:
                                panel.template_curve_mapping(curve_node, "mapping")

                        layout.operator("nodetree_anim.build_anim", text="Build Nodes Anim")
                    elif props.bulk_anim_option == 'LINKS':
                        layout.prop(props, "link_anim_type", text="Link Anim")
                        row = layout.row(align=True)
                        row.prop(props, "link_anim_length", text="Anim Length")
                        row.prop(props, "link_anim_stagger", text="Stagger Length")
                        row = layout.row(align=True)
                        col = row.column(align=True)
                        col.prop(props, "start_offset", text="Start Offset")
                        col = row.column(align=True)
                        col.prop(props, "end_offset", text="End Offset")
                        row = layout.row(align=True)
                        op = row.operator("nodetree_anim.refresh_nodelist", text="Refresh Link List")
                        op.renew = 'REFRESH'
                        op = row.operator("nodetree_anim.refresh_nodelist", text="Rebuild Link List")
                        op.renew = 'REBUILD'
                        row = layout.row(align=True)
                        row.template_list("NODETREE_ANIM_UL_nodes", "", props, "links", props, "link_index")
                        col = row.column(align=True)
                        col.operator("nodetree_anim.list_moveup", icon="TRIA_UP", text="")
                        col.operator("nodetree_anim.list_movedown", icon="TRIA_DOWN", text="")
                        col.separator()
                        col.operator("nodetree_anim.list_delitem", icon="REMOVE", text="")
                        if bpy.data.node_groups.get(f"{node_tree.name}_AnimCurves") and bpy.data.node_groups[f"{node_tree.name}_AnimCurves"].nodes.get(f"bulk_node.link_anim_curve"):
                            curve_node = bpy.data.node_groups[f"{node_tree.name}_AnimCurves"].nodes[f"bulk_node.link_anim_curve"]
                            header, panel = layout.panel("Link Anim Setting", default_closed=True)
                            header.label(text="Link Anim Curve")
                            if panel:
                                panel.template_curve_mapping(curve_node, "mapping")

                        layout.operator("nodetree_anim.build_anim", text="Build Links Anim")
                    elif props.bulk_anim_option == 'VIEWS':
                        row = layout.row(align=True)
                        row.prop(props, "view_anim_length", text="Anim Length")
                        row.prop(props, "view_anim_stagger", text="Stagger Length")
                        row = layout.row()
                        row.label(text="Adjust view")
                        row.operator("view2d.scroll_left", text="", icon="EVENT_LEFT_ARROW")
                        row.operator("view2d.scroll_right", text="", icon="EVENT_RIGHT_ARROW")
                        row.operator("view2d.scroll_up", text="", icon="EVENT_UP_ARROW")
                        row.operator("view2d.scroll_down", text="", icon="EVENT_DOWN_ARROW")
                        row.operator("view2d.reset", text="", icon="EVENT_PAD_ROTATE")
                        if props.view_anim_type == 'FOLLOW':
                            row = layout.row(align=True)
                            row.prop(props, "view_offset", text="Move Size")
                        elif props.view_anim_type == 'ZOOM':
                            row = layout.row(align=True)
                            row.prop(props, "view_zoom", text="Zoom Size")
                        layout.prop(props, "view_anim_type", text="View Anim")
                        row = layout.row(align=True)
                        row.template_list("NODETREE_ANIM_UL_nodes", "", props, "views", props, "view_index")
                        col = row.column(align=True)
                        col.operator("nodetree_anim.list_moveup", icon="TRIA_UP", text="")
                        col.operator("nodetree_anim.list_movedown", icon="TRIA_DOWN", text="")
                        col.separator()
                        col.operator("nodetree_anim.list_additem", icon="ADD", text="")
                        col.operator("nodetree_anim.list_delitem", icon="REMOVE", text="")
                        if bpy.data.node_groups.get(f"{node_tree.name}_AnimCurves") and bpy.data.node_groups[f"{node_tree.name}_AnimCurves"].nodes.get(f"bulk_node.view_anim_curve"):
                            curve_node = bpy.data.node_groups[f"{node_tree.name}_AnimCurves"].nodes[f"bulk_node.view_anim_curve"]
                            header, panel = layout.panel("View Anim Setting", default_closed=True)
                            header.label(text="View Anim Curve")
                            if panel:
                                panel.template_curve_mapping(curve_node, "mapping")

                        layout.operator("nodetree_anim.build_anim", text="Build Views Anim")
                elif props.anim_option == 'MANUAL':
                    node_props = context.scene.nodetree_node_props
                    layout.operator("nodetree_anim.refresh_nodelist", text="Refresh Node List")
                    split = layout.split(factor=0.9)
                    split.template_list("NODETREE_ANIM_UL_nodes", "", node_props, "nodes", node_props, "node_index")
                    split.prop(node_props, "locate", text="", toggle=False, icon='ZOOM_SELECTED')
                    if node_tree and len(node_props.nodes) > 0:
                        node_name = node_props.nodes[node_props.node_index].name
                        sel_node = node_tree.nodes.get(node_name)
                        if sel_node:
                            row = layout.row()
                            row.prop(node_props, "add_anim", expand=True)
                            if node_props.add_anim == 'NODEANIM':
                                layout.prop(node_props, "node_anim_type", text="Anim Type")
                                row = layout.row()
                                row.prop(node_props, "anim_start_frame", text="Start Frame")
                                row.prop(node_props, "anim_end_frame", text="End Frame")
                                if bpy.data.node_groups.get(f"{node_tree.name}_AnimCurves") and bpy.data.node_groups[f"{node_tree.name}_AnimCurves"].nodes.get(f"node_anim_curve"):
                                    curve_node = bpy.data.node_groups[f"{node_tree.name}_AnimCurves"].nodes[f"node_anim_curve"]
                                    header, panel = layout.panel("Manual Node Anim Setting", default_closed=True)
                                    header.label(text="Anim Curve")
                                    if panel:
                                        panel.template_curve_mapping(curve_node, "mapping")
                                layout.separator()
                                if node_props.node_anim_type == 'FLY_IN':
                                    layout.prop(node_props, "start_pos", text="Start Pos")
                                    layout.prop(node_props, "sync_node_path", text="Sync beginning position before start")
                                    path_x = bpy.data.node_groups[f"{node_tree.name}_AnimCurves"].nodes[f"node_pathx_curve"]
                                    path_y = bpy.data.node_groups[f"{node_tree.name}_AnimCurves"].nodes[f"node_pathy_curve"]
                                    header, panel = layout.panel("Manual Node Pathx Setting", default_closed=True)
                                    split = header.split(factor=0.6)
                                    split.label(text="Path Anim Curve in x:")
                                    split.prop(node_props, "pathx_multiplier", text="Multiplier")
                                    if panel:
                                        panel.template_curve_mapping(path_x, "mapping")
                                    header, panel = layout.panel("Manual Node Pathy Setting", default_closed=True)
                                    split = header.split(factor=0.6)
                                    split.label(text="Path Anim Curve in y:")
                                    split.prop(node_props, "pathy_multiplier", text="Multiplier")
                                    if panel:
                                        panel.template_curve_mapping(path_y, "mapping")
                                elif node_props.node_anim_type == 'SHRINK':
                                    layout.prop(node_props, "sync_node_shrink", text="Sync beginning size before start")
                                    shrink_curve = bpy.data.node_groups[f"{node_tree.name}_AnimCurves"].nodes[f"node_shrink_curve"]
                                    header, panel = layout.panel("Manual Node Shrink Anim Setting", default_closed=True)
                                    header.label(text="Shrink Anim Curve:")
                                    if panel:
                                        panel.template_curve_mapping(shrink_curve, "mapping")
                                layout.separator()
                                layout.operator("nodetree_anim.add_node_anim", text="Add Node Animation")

                            elif node_props.add_anim == 'LINKANIM':
                                layout.prop(node_props, "build_link_type", expand=True)
                                if node_props.build_link_type == "SELECTLINK":
                                    row = layout.row(align=True)
                                    row.label(text="", icon='NODE_SEL')
                                    row.label(text="From Socket", icon="REC")
                                    row.label(text="To Socket", icon="REC")
                                    row.label(text="To Node", icon="NODE")
                                    layout.template_list("NODETREE_ANIM_UL_nodes", "", node_props, "links", node_props, "link_index")
                                else:
                                    row = layout.row(align=True)
                                    row.prop(node_props, "from_node")
                                    row.prop(node_props, "to_node")
                                    row = layout.row(align=True)
                                    row.prop(node_props, "from_socket")
                                    row.prop(node_props, "to_socket")
                                if len(node_props.links) > 0 or node_props.build_link_type == "NEWLINK":
                                    layout.prop(node_props, "link_anim_type", text="Anim Type")
                                    row = layout.row(align=True)
                                    row.prop(node_props, "anim_start_frame", text="Start Frame")
                                    row.prop(node_props, "anim_end_frame", text="End Frame")
                                    if bpy.data.node_groups.get(f"{node_tree.name}_AnimCurves") and bpy.data.node_groups[f"{node_tree.name}_AnimCurves"].nodes.get(f"node.link_anim_curve"):
                                        curve_node = bpy.data.node_groups[f"{node_tree.name}_AnimCurves"].nodes[f"node.link_anim_curve"]
                                        header, panel = layout.panel("Manual Link Anim Setting", default_closed=True)
                                        header.label(text="Anim Curve")
                                        if panel:
                                            panel.template_curve_mapping(curve_node, "mapping")
                                    layout.operator("nodetree_anim.add_link_anim", text="Add Link Animation")
                            elif node_props.add_anim == 'VALUEANIM':
                                layout.label(text="Input/Output Value Anim")
                                layout.template_list("NODETREE_ANIM_UL_nodes", "", node_props, "values", node_props, "value_index")
                                if len(node_props.values) > 0 and node_props.value_index < len(node_props.values):
                                    row = layout.row(align=True)
                                    row.prop(node_props, "anim_start_frame", text="Start Frame")
                                    row.prop(node_props, "anim_end_frame", text="End Frame")
                                    row = layout.row(align=True)
                                    value_prop = f"input_{node_props.values[node_props.value_index].name}"
                                    if node_props.values[node_props.value_index].is_output:
                                        value_prop = f"output_{node_props.values[node_props.value_index].name}"
                                    col = row.column()
                                    col.prop(sel_node, f'["{value_prop}_start"]', text="Start Value")
                                    col = row.column()
                                    col.prop(sel_node, f'["{value_prop}_end"]', text="End Value")
                                    layout.prop(node_props, "sync_value", text="Sync beginning value before start")
                                    if bpy.data.node_groups.get(f"{node_tree.name}_AnimCurves") and bpy.data.node_groups[f"{node_tree.name}_AnimCurves"].nodes.get(f"node.value_anim_curve"):
                                        curve_node = bpy.data.node_groups[f"{node_tree.name}_AnimCurves"].nodes[f"node.value_anim_curve"]
                                        header, panel = layout.panel("Manual Value Anim Setting", default_closed=True)
                                        header.label(text="Anim Curve")
                                        if panel:
                                            panel.template_curve_mapping(curve_node, "mapping")
                                    layout.operator("nodetree_anim.add_value_anim", text="Add Value Animation")
                elif props.anim_option == 'DRAW':
                    header, panel = layout.panel("add_annotation", default_closed=True)
                    header.label(text="Add Annotation")
                    note_props = context.scene.nodetree_note_props
                    if panel:
                        row = panel.row(align=True)
                        row.prop(note_props, "note_source", expand=True)
                        if note_props.note_source == "FREEDRAW":
                            row = panel.row(align=True)
                            draw_tool_button(row, context, "builtin.select", label="Select")
                            draw_tool_button(row, context, "builtin.annotate", label="Draw")
                            draw_tool_button(row, context, "builtin.annotate_line", label="Line")
                            draw_tool_button(row, context, "builtin.annotate_polygon", label="Polygon")
                            draw_tool_button(row, context, "builtin.annotate_eraser", label="Erase")
                        elif note_props.note_source == "INPUTTEXT":
                            row = panel.row(align=True)
                            row.prop(note_props, "text_position", text="X", index=0)
                            row.prop(note_props, "text_position", text="Y", index=1)
                            row = panel.row(align=True)
                            row.prop(note_props, "text_size", text="Size")
                            row.prop(note_props, "text_step", text="Step")
                            col = panel.column(align=True)
                            col.template_ID(data=note_props, property="text_font", open="font.open", unlink="font.unlink")
                            col.textbox(note_props, "text_body", placeholder="input text to annotation")
                        tool_settings = context.tool_settings
                        panel.prop(tool_settings, "annotation_stroke_placement_view2d", text="Placement")
                        tool = ToolSelectPanelHelper._tool_active_from_context(context, context.space_data.type)
                        if tool is not None:
                            tool_props = tool.operator_properties("gpencil.annotate")
                            if tool.idname == "builtin.annotate_line":
                                row = panel.row(align=True)
                                row.prop(tool_props, "arrowstyle_start", text="Style Start")
                                row.prop(tool_props, "arrowstyle_end", text="End")
                            elif tool.idname == "builtin.annotate":
                                panel.prop(tool_props, "use_stabilizer", text="Stabilize Stroke")
                                col = panel.column(align=False)
                                col.active = tool_props.use_stabilizer
                                col.prop(tool_props, "stabilizer_radius", text="Radius", slider=True)
                                col.prop(tool_props, "stabilizer_factor", text="Factor", slider=True)
                            elif tool.idname == "builtin.annotate_eraser":
                                panel.prop(context.preferences.edit, "grease_pencil_eraser_radius", text="Radius")
                        AnnotationDataPanel.draw(self, context)
                    note = context.annotation_data
                    header, panel = layout.panel("build_annotation_anim", default_closed=False)
                    header.label(text="Build Annotatation Anim")
                    if panel:
                        if note is not None:
                            panel.prop(note_props, "anim_start", text="Anim Start Frame")
                            row = panel.row(align=True)
                            row.prop(note_props, "anim_level", text="Level")
                            row.prop(note_props, "anim_type", text="Type")
                            if note_props.anim_type == 'WRITE_ON' or note_props.anim_type == 'WRITE_OFF':
                                row = panel.row(align=True)
                                row.prop(note_props, "write_symbol", expand=True)
                                if note_props.write_symbol != "NONE":
                                    row = panel.row(align=True)
                                    row.prop(note_props, "symbol_scale", text="Symbol Scale")
                                    row.prop(note_props, "symbol_shift", index=0, text="Symbol Shift X")
                                    row.prop(note_props, "symbol_shift", index=1, text="Symbol Shift Y")
                            row = panel.row(align=True)
                            row.prop(note_props, "anim_length", text="Anim Length")
                            row.prop(note_props, "anim_stagger", text="Stagger Length")
                            row = panel.row(align=True)
                            row.operator("nodetree_anim.refresh_annotation", icon="FILE_REFRESH").option = 'REFRESH'
                            row.operator("nodetree_anim.refresh_annotation", text="Restore Annotation", icon="LOOP_BACK").option = 'RESTORE'
                            panel.template_list("NODETREE_ANIM_UL_nodes", "", note, "layers", note.layers, "active_index")
                            cheader, cpanel = panel.panel(f"annotation_anim_curve", default_closed=True)
                            cheader.label(text="Annotation Anim Curve")
                            if cpanel:
                                if bpy.data.node_groups.get(f"{node_tree.name}_AnimCurves"):
                                    curve_node = bpy.data.node_groups[f"{node_tree.name}_AnimCurves"].nodes.get(f"annotation_anim_curve")
                                    if curve_node:
                                        cpanel.template_curve_mapping(curve_node, "mapping")
                            panel.operator("nodetree_anim.add_annotation_anim", text="Add Annotation Anim", icon="ANIM")
                            panel.separator()
                    note_tracking = None
                    if note:
                        note_tracking = context.scene.nodetree_anim_note_tracking.anim_annotations.get(note.name)
                    header, panel = layout.panel("annotation_anim_control", default_closed=True)
                    header.label(text="Annotatation Anim Control")
                    if panel:
                        if note_tracking is not None:
                            for anim_stroke in note_tracking.anim_strokes:
                                if len(anim_stroke.stroke_anims) == 0:
                                    continue
                                subheader, subpanel = panel.panel(f"{anim_stroke.name}.annotation_anim_control", default_closed=True)
                                row = subheader.row(align=True)
                                row.label(text=f"{anim_stroke.layer}", icon="RENDERLAYERS")
                                frame_number = note.layers[anim_stroke.layer].frames[anim_stroke.frame].frame_number
                                row.label(text=f"{frame_number}", icon="GP_MULTIFRAME_EDITING")
                                row.label(text=f"{anim_stroke.stroke}", icon="GP_SELECT_STROKES")
                                op = row.operator("nodetree_anim.del_anim", text="", icon="PANEL_CLOSE")
                                op.anim_type = "STROKEANIM"
                                op.key_name = f"STROKE**{anim_stroke.name}**"
                                if subpanel:
                                    for stroke_anim in anim_stroke.stroke_anims:
                                        ssubheader, ssubpanel = panel.panel(f"{anim_stroke.name}.{stroke_anim.name}.annotation_anim_control", default_closed=True)
                                        row = ssubheader.row(align=True)
                                        row.label(text=f"Anim range: {stroke_anim.start_frame} - > {stroke_anim.end_frame}")
                                        op = row.operator("nodetree_anim.del_anim", text="", icon="PANEL_CLOSE")
                                        op.anim_type = "STROKEANIM"
                                        op.key_name = f"ANIM**{anim_stroke.name}**{stroke_anim.name}"
                                        if ssubpanel:
                                            split = ssubpanel.split(factor=0.7)
                                            split.enabled = False
                                            split.prop(stroke_anim, "anim_type", text="Anim Type")
                                            if stroke_anim.symbol_idx >= 0:
                                                symbol ={"NONE": " ", "WRITING_HAND": "✍", "PENCIL": "🖉", "PEN": "🖊", "FOUNTAIN_PEN": "🖋"}
                                                split.label(text=symbol[stroke_anim.write_symbol])
                                                row = ssubpanel.row(align=True)
                                                col = row.column(align=True)
                                                col.prop(stroke_anim, "symbol_scale", text="Symbol Scale")
                                                col = row.column(align=True)
                                                col.prop(stroke_anim, "symbol_shift", text="Symbol Shift")
                                            row = ssubpanel.row(align=True)
                                            row.prop(stroke_anim, "start_frame", text="Start Frame")
                                            row.prop(stroke_anim, "end_frame", text="End Frame")
                                            curve_node = bpy.data.node_groups[f"{node_tree.name}_AnimCurves"].nodes.get(f"{anim_stroke.name}.{stroke_anim.name}_anim_curve")
                                            if curve_node:
                                                ssubpanel.template_curve_mapping(curve_node, "mapping")

                if props.anim_option == 'BULK' or props.anim_option == 'MANUAL':
                    node_tracking = context.scene.nodetree_anim_node_tracking
                    header, panel = layout.panel("node_tracking_settings", default_closed=False)
                    header.label(text="Node Anim Settings")
                    if panel:
                        if node_tracking.get(node_tree.name) is not None:
                            for idx, node in enumerate(node_tracking[node_tree.name].anim_nodes):
                                subheader, subpanel = panel.panel(f"{node.node_name}.node_tracking_settings", default_closed=True)
                                row = subheader.row(align=True)
                                row.label(text=f"{node.node_name}", icon="NODE")
                                col = row.column(align=True)
                                op = col.operator("nodetree_anim.del_anim", text="", icon="PANEL_CLOSE")
                                op.key_name = f"{node_tree.name}**{node.node_name}**{idx}"
                                op.anim_type = "NODEANIM"
                                if subpanel:
                                    row = subpanel.row(align=True)
                                    row.prop(node, "start_frame")
                                    row.prop(node, "end_frame")
                                    curve_node = bpy.data.node_groups[f"{node_tree.name}_AnimCurves"].nodes.get(f"{node.name}_anim_curve")
                                    if curve_node:
                                        subpanel.label(text="Anim Curve")
                                        subpanel.template_curve_mapping(curve_node, "mapping")
                                    if node.anim_type == 'FLY_IN':
                                        subpanel.prop(node, "sync", text="Sync beginning position before start")
                                    else:
                                        subpanel.prop(node, "sync", text="Sync beginning size before start")
                                    for path in ["pathx", "pathy"]:
                                        curve_node = bpy.data.node_groups[f"{node_tree.name}_AnimCurves"].nodes.get(f"{node.name}_{path}_curve")
                                        if curve_node:
                                            split = subpanel.split(factor=0.6)
                                            direction = "x" if path == "pathx" else "y"
                                            split.label(text=f"Path Anim Curve in {direction}:")
                                            split.prop(node, f"{path}_multiplier", text="Multiplier")
                                            subpanel.template_curve_mapping(curve_node, "mapping")
                                    curve_node = bpy.data.node_groups[f"{node_tree.name}_AnimCurves"].nodes.get(f"{node.name}_shrink_curve")
                                    if curve_node:
                                        subpanel.label(text="Shrink Anim Curve")
                                        subpanel.template_curve_mapping(curve_node, "mapping")
                    link_tracking = context.scene.nodetree_anim_link_tracking
                    header, panel = layout.panel("link_tracking_settings", default_closed=False)
                    header.label(text="Link Anim Settings")
                    if panel:
                        if link_tracking.get(node_tree.name) is not None:
                            for node in link_tracking[node_tree.name].anim_links:
                                if len(node.node_links) > 0:
                                    subheader, subpanel = panel.panel(f"{node.node_name}.link_tracking_settings", default_closed=True)
                                    subheader.label(text=f"{node.node_name}", icon="NODE")
                                    if subpanel:
                                        for idx, link in enumerate(node.node_links):
                                            split = subpanel.split(factor=0.7)
                                            split.label(text=f"[{link.from_socket} -> {link.to_socket}] {link.to_node}", icon="LINKED")
                                            row = split.row(align=True)
                                            row.prop(link, "hide", text="hide")
                                            op = row.operator("nodetree_anim.del_anim", text="", icon="PANEL_CLOSE")
                                            op.key_name = f"{node_tree.name}**{node.node_name}**{idx}"
                                            op.anim_type = "LINKANIM"
                                            if not link.hide:
                                                row = subpanel.row(align=True)
                                                row.prop(link, "start_frame", text="Start Frame")
                                                row.prop(link, "end_frame", text="End Frame")
                                                row = subpanel.row(align=True)
                                                col = row.column()
                                                col.prop(link, "start_offset", text="Start Offset")
                                                col = row.column()
                                                col.prop(link, "end_offset", text="End Offset")
                                                curve_node = bpy.data.node_groups[f"{node_tree.name}_AnimCurves"].nodes.get(f"{link.name}_anim_curve")
                                                if curve_node:
                                                    subpanel.label(text="Anim Curve")
                                                    subpanel.template_curve_mapping(curve_node, "mapping")
                    value_tracking = context.scene.nodetree_anim_value_tracking
                    header, panel = layout.panel("value_tracking_settings", default_closed=False)
                    header.label(text="Value Anim Settings")
                    if panel:
                        if value_tracking.get(node_tree.name) is not None:
                            for node in value_tracking[node_tree.name].anim_values:
                                if len(node.node_values) > 0:
                                    subheader, subpanel = panel.panel(f"{node.node_name}.value_tracking_settings", default_closed=True)
                                    subheader.label(text=f"{node.node_name}", icon="NODE")
                                    if subpanel:
                                        for idx, value in enumerate(node.node_values):
                                            socket = node_tree.nodes[node.node_name].inputs[value.socket_name]
                                            value_prop = f"input_{value.socket_name}"
                                            if value.is_output:
                                                socket = node_tree.nodes[node.node_name].outputs[value.socket_name]
                                                value_prop = f"output_{value.socket_name}"
                                            icon_type = f'NODE_SOCKET_{socket.type}' if socket.type != 'VALUE' else 'NODE_SOCKET_FLOAT'
                                            split = subpanel.split(factor=0.7)
                                            split.label(text=f"{value.socket_name}", icon=icon_type)
                                            row = split.row(align=True)
                                            row.prop(value, "hide", text="hide")
                                            op = row.operator("nodetree_anim.del_anim", text="", icon="PANEL_CLOSE")
                                            op.key_name = f"{node_tree.name}**{node.node_name}**{idx}"
                                            op.anim_type = "VALUEANIM"
                                            if not value.hide:
                                                row = subpanel.row(align=True)
                                                row.prop(value, "start_frame", text="Start Frame")
                                                row.prop(value, "end_frame", text="End Frame")
                                                row = subpanel.row(align=True)
                                                col = row.column()
                                                col.prop(node_tree.nodes[node.node_name], f'["{value_prop}_start"]', text="Start Value")
                                                col = row.column()
                                                col.prop(node_tree.nodes[node.node_name], f'["{value_prop}_end"]', text="End Value")
                                                curve_node = bpy.data.node_groups[f"{node_tree.name}_AnimCurves"].nodes.get(f"{value.name}_anim_curve")
                                                subpanel.prop(value, "sync", text="Sync beginning value before start")
                                                if curve_node:
                                                    subpanel.label(text="Anim Curve")
                                                    subpanel.template_curve_mapping(curve_node, "mapping")
                    view_tracking = context.scene.nodetree_anim_view_tracking
                    header, panel = layout.panel("view_tracking_settings", default_closed=False)
                    header.label(text="View Anim Settings")
                    if panel:
                        if view_tracking.get(node_tree.name) is not None:
                            for idx, view in enumerate(view_tracking[node_tree.name].anim_views):
                                subheader, subpanel = panel.panel(f"{view.name}.view_tracking_settings", default_closed=True)
                                row = subheader.row(align=True)
                                icon = "CON_FOLLOWPATH" if view.anim_type == 'FOLLOW' else 'VIEWZOOM'
                                view_type = "move" if view.anim_type == 'FOLLOW' else 'zoom'
                                row.label(text=f"{view.name} view {view_type}", icon=icon)
                                col = row.column(align=True)
                                op = col.operator("nodetree_anim.del_anim", text="", icon="PANEL_CLOSE")
                                op.key_name = f"{node_tree.name}**{view.name}**{idx}"
                                op.anim_type = "VIEWANIM"
                                if subpanel:
                                    row = subpanel.row(align=True)
                                    row.prop(view, "start_frame", text="Start Frame")
                                    row.prop(view, "end_frame", text="End Frame")
                                    row = subpanel.row(align=True)
                                    if view.anim_type == 'FOLLOW':
                                        subpanel.prop(view, "view_offset", text="Move Size")
                                    else:
                                        row.prop(view, "view_zoom", text="Zoom Size")
                                    curve_node = bpy.data.node_groups[f"{node_tree.name}_AnimCurves"].nodes.get(f"{view.name}_anim_curve")
                                    if curve_node:
                                        subpanel.label(text="Anim Curve")
                                        subpanel.template_curve_mapping(curve_node, "mapping")
            else:
                layout.label(text="No nodetree detected in the node editor.")

classes = (
    NODETREE_ANIM_PT_main_panel,
    NODETREE_ANIM_UL_nodes,
)
register, unregister = bpy.utils.register_classes_factory(classes)
