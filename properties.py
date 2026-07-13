import bpy
from bpy.props import *
from . import variables as vb
from .utility import copy_node, text_to_curves

def frame_node_in_editor(context, node):
    for area in context.screen.areas:
        if area.type == 'NODE_EDITOR':
            space = area.spaces.active
            tree = space.edit_tree   # current level node tree
            # Only frame if node belongs to this tree
            if node.id_data != tree:
                return
            for region in area.regions:
                if region.type == 'WINDOW':
                    with context.temp_override(
                        area=area,
                        region=region,
                        space_data=space,
                    ):
                        bpy.ops.node.view_selected()
                    return

class NODETREE_ANIM_ViewSelItem(bpy.types.PropertyGroup):
    def update_time(self, context):
        anim_props = context.scene.nodetree_anim_props
        if anim_props.anim_option == 'BULK' and anim_props.bulk_anim_option == 'VIEWS':
            if anim_props.is_updating:
                return
            anim_props.is_updating = True
            update = False
            cidx = -1
            n_len = 0
            for idx, item in enumerate(anim_props.views):
                if item.name == self.name:
                    update = True
                    cidx = idx
                if update:
                    if idx > cidx:
                        n_len = item.end_frame - item.start_frame
                        item.start_frame = n_start
                        item.end_frame = item.start_frame + n_len
                    n_start = item.end_frame + item.stagger_time
                if idx == len(anim_props.views) - 1:
                    anim_props.is_updating = False
    start_frame: IntProperty(description="Anim Start Time")
    end_frame: IntProperty(description="Anim End Time", update=update_time)
    stagger_time: IntProperty(description="Stagger Time", update=update_time)
    anim_type: EnumProperty(
        name="View Anim Type",
        description="Type of animation to choose",
        items=[
            ('FOLLOW', "Follow", "follow view animation", "CON_FOLLOWPATH", 0),
            ("ZOOM", "Zoom", "zoom in or zoom out view animation", "VIEWZOOM", 1),
        ],
        default='FOLLOW',
    )
    sync: BoolProperty(default=True, description="Sync node initial status to anim start status, like position or shrink")
    view_offset: IntVectorProperty(size=2)
    view_zoom: FloatVectorProperty(size=2)
    select: BoolProperty(default=True)

class NODETREE_ANIM_NodeSelItem(bpy.types.PropertyGroup):
    node_name: StringProperty()
    def update_time(self, context):
        anim_props = context.scene.nodetree_anim_props
        if anim_props.anim_option == 'BULK' and anim_props.bulk_anim_option == 'NODES':
            if anim_props.is_updating:
                return
            anim_props.is_updating = True
            update = False
            cidx = -1
            n_len = 0
            for idx, item in enumerate(anim_props.nodes):
                if item.node_name == self.node_name:
                    update = True
                    cidx = idx
                if update:
                    if idx > cidx:
                        n_len = item.end_frame - item.start_frame
                        item.start_frame = n_start
                        item.end_frame = item.start_frame + n_len
                    n_start = item.end_frame + item.stagger_time
                if idx == len(anim_props.nodes) - 1:
                    anim_props.is_updating = False
    start_frame: IntProperty(description="Anim Start Time")
    end_frame: IntProperty(description="Anim End Time", update=update_time)
    stagger_time: IntProperty(description="Stagger Time", update=update_time)
    anim_type: EnumProperty(
        name="Node Anim Type",
        description="Type of animation to choose",
        items=[
            ('FLY_IN', "Fly In", "flying in animation"),
            ("SHRINK", "Shrink", "Shrink animation"),
        ],
        default='FLY_IN',
    )
    sync: BoolProperty(default=True, description="Sync node initial status to anim start status, like position or shrink")
    org_pos: FloatVectorProperty(size=2)
    org_size: FloatVectorProperty(size=2)
    start_pos: FloatVectorProperty(size=2)
    path_multiplier: FloatVectorProperty(size=2, default=(1000.0, 1000.0))
    init_size: FloatProperty(default=1.0, min=0.0, max=5.0)
    select: BoolProperty(default=True)

class NODETREE_ANIM_LinkSelItem(bpy.types.PropertyGroup):
    from_node: StringProperty()
    to_node: StringProperty()
    from_socket: StringProperty()
    from_socket_id: StringProperty()
    to_socket: StringProperty()
    to_socket_id: StringProperty()
    def update_time(self, context):
        anim_props = context.scene.nodetree_anim_props
        if anim_props.anim_option == 'BULK' and anim_props.bulk_anim_option == 'LINKS':
            if anim_props.is_updating:
                return
            anim_props.is_updating = True
            update = False
            cidx = -1
            n_len = 0
            for idx, item in enumerate(anim_props.links):
                if item.from_node == self.from_node and item.from_socket_id == self.from_socket_id and item.to_node == self.to_node and item.to_socket_id == self.to_socket_id:
                    update = True
                    cidx = idx
                if update:
                    if idx > cidx:
                        n_len = item.end_frame - item.start_frame
                        item.start_frame = n_start
                        item.end_frame = item.start_frame + n_len
                    n_start = item.end_frame + item.stagger_time
                if idx == len(anim_props.links) - 1:
                    anim_props.is_updating = False
    start_frame: IntProperty(description="Anim Start Time")
    end_frame: IntProperty(description="Anim End Time", update=update_time)
    stagger_time: IntProperty(description="Stagger Time", update=update_time)
    anim_type: EnumProperty(
        name="Noodle Anim Type",
        description="Type of animation to choose",
        items=[ ("GROW", "Grow", "Grow animation"),
                ("REVERSE_GROW", "Reverse Grow", "Reverse Grow animation"),
              ],
        default='GROW',
    )
    start_offset: FloatVectorProperty(size=2)
    end_offset: FloatVectorProperty(size=2)
    select: BoolProperty(default=True)

class NODETREE_ANIM_Properties(bpy.types.PropertyGroup):
    def update_node_list(self, context):
        if self.anim_option == 'MANUAL' or (self.anim_option == 'BULK' and self.bulk_anim_option == 'VIEWS'):
            space = context.space_data
            if space and space.type == 'NODE_EDITOR':
                node_tree = space.edit_tree
                if node_tree:
                    bpy.ops.nodetree_anim.refresh_nodelist()

    anim_option: EnumProperty(
        name="Anim Option",
        description="Type of animation to build",
        items=[
            ('BULK', "Bulk Build", "Automatically build animation based on node tree structure"),
            ('MANUAL', "Manual Build", "Manually specify animation parameters"),
            ('DRAW', "Annotate", "Build annotation animation"),
        ],
        default='BULK',
        update=update_node_list,
    )
    bulk_anim_option: EnumProperty(
        name="Bulk Anim Option",
        description="Which to build their anims",
        items=[
            ('NODES', "Nodes", "build nodes' animation based on node tree structure"),
            ('LINKS', "Links", "build links' animation based on node tree structure"),
            ('VIEWS', "Views", "build views' animation based on node tree structure"),
        ],
        default='NODES',
        update=update_node_list,
    )
    def update_start_frame(self, context):
        if self.bulk_anim_option == "NODES":
            if len(self.nodes) > 0:
                self.nodes[0].start_frame = self.start_frame
                self.nodes[0].end_frame = self.nodes[0].end_frame
        elif self.bulk_anim_option == "LINKS":
            if len(self.links) > 0:
                self.links[0].start_frame = self.start_frame
                self.links[0].end_frame = self.links[0].end_frame
        elif self.bulk_anim_option == "VIEWS":
            if len(self.views) > 0:
                self.views[0].start_frame = self.start_frame
                self.views[0].end_frame = self.views[0].end_frame
    start_frame: IntProperty(default=1, update=update_start_frame)
    def update_node_anim_length(self, context):
        for node in self.nodes:
            node.end_frame = node.start_frame + self.node_anim_length
    node_anim_length: IntProperty(default=12, update=update_node_anim_length)
    def update_node_anim_stagger(self, context):
        for node in self.nodes:
            node.stagger_time = self.node_anim_stagger
    node_anim_stagger: IntProperty(default=12, update=update_node_anim_stagger)
    def update_node_anim_type(self, context):
        for node in self.nodes:
            node.anim_type = self.node_anim_type
    node_anim_type: EnumProperty(
        name="Node Anim Type",
        description="Type of animation to choose",
        items=[
            ('FLY_IN', "Fly In", "flying in animation"),
            ("SHRINK", "Shrink", "Shrink animation"),
        ],
        default='FLY_IN',
        update=update_node_anim_type,
    )
    def update_link_anim_length(self, context):
        for link in self.links:
            link.end_frame = link.start_frame + self.link_anim_length
    link_anim_length: IntProperty(default=12, update=update_link_anim_length)
    def update_link_anim_stagger(self, context):
        for link in self.links:
            link.stagger_time = self.link_anim_stagger
    link_anim_stagger: IntProperty(default=12, update=update_link_anim_stagger)
    def update_link_anim_type(self, context):
        for link in self.links:
            link.anim_type = self.link_anim_type
    link_anim_type: EnumProperty(
        name="Noodle Anim Type",
        description="Type of animation to choose",
        items=[ ("GROW", "Grow", "Grow animation"),
                ("REVERSE_GROW", "Reverse Grow", "Reverse Grow animation"),
              ],
        default='GROW',
        update=update_link_anim_type,
    )
    def update_view_anim_length(self, context):
        for view in self.views:
            view.end_frame = view.start_frame + self.view_anim_length
    view_anim_length: IntProperty(default=12, update=update_view_anim_length)
    def update_view_anim_stagger(self, context):
        for view in self.views:
            view.stagger_time = self.view_anim_stagger
    view_anim_stagger: IntProperty(default=12, update=update_view_anim_stagger)
    def update_view_anim_type(self, context):
        for view in self.views:
            view.anim_type = self.view_anim_type
    view_anim_type: EnumProperty(
        name="View Anim Type",
        description="Type of animation to choose",
        items=[ ("FOLLOW", "Follow", "Follow view animation", "CON_FOLLOWPATH", 0),
                ("ZOOM", "Zoom", "zoom in or zoom out view animation", "VIEWZOOM", 1),
              ],
        default='FOLLOW',
        update=update_view_anim_type,
    )
    node_tree: PointerProperty(type=bpy.types.NodeTree)
    nodes: CollectionProperty(type=NODETREE_ANIM_NodeSelItem)
    node_index: IntProperty(default=0)
    links: CollectionProperty(type=NODETREE_ANIM_LinkSelItem)
    link_index: IntProperty(default=0)
    views: CollectionProperty(type=NODETREE_ANIM_ViewSelItem)
    view_index: IntProperty(default=0)
    def update_sync(self, context):
        for node in self.nodes:
            node.sync = self.sync_node
    sync_node: BoolProperty(default=True, update=update_sync)
    is_updating: BoolProperty(default=False)

    def update_pos(self, context):
        for node in self.nodes:
            node.start_pos = self.start_pos
    start_pos: FloatVectorProperty(size=2, update=update_pos)
    def update_multiplier(self, context):
        for node in self.nodes:
            node.path_multiplier = self.path_multiplier
    path_multiplier: FloatVectorProperty(size = 2, default=(1000.0, 1000.0),
                                         description="The 'Fly In' animation path is normalized based on the this multiplier to use curve to control the path anim. This value should be larger than the path start and end position",
                                         update=update_multiplier,
                                         )
    def update_start_offset(self, context):
        for link in self.links:
            link.start_offset = self.start_offset
    start_offset: FloatVectorProperty(size=2, update=update_start_offset)
    def update_end_offset(self, context):
        for link in self.links:
            link.end_offset = self.end_offset
    end_offset: FloatVectorProperty(size=2, update=update_end_offset)
    def update_size(self, context):
        for node in self.nodes:
            node.init_size = self.init_size
    init_size: FloatProperty(default=1.0, min=0.0, max=5.0, update=update_size)
    def update_view_offset(self, context):
        for view in self.views:
            view.view_offset = self.view_offset
    view_offset: IntVectorProperty(size=2, default=(1000, 0), update=update_view_offset)
    def update_view_zoom(self, context):
        for view in self.views:
            view.view_zoom = self.view_zoom
    view_zoom: FloatVectorProperty(size=2, default=(1000.0, 1000.0), update=update_view_zoom)
    view_sync: BoolProperty(default=True)

class NODETREE_ANIM_ViewTracking(bpy.types.PropertyGroup):
    prev_xy: FloatVectorProperty(size=2, default=(0.0, 0.0))
    prev_zoom: FloatVectorProperty(size=2, default=(0.0, 0.0))
    view_offset: IntVectorProperty(size=2)
    view_zoom: FloatVectorProperty(size=2)
    start_frame: IntProperty()
    end_frame: IntProperty()
    anim_type: StringProperty(default="")
    hide: BoolProperty(default=False)
    sync: BoolProperty(default=False)

class NODETREE_ANIM_NodeTracking(bpy.types.PropertyGroup):
    org_pos: FloatVectorProperty(size=2)
    org_size: FloatVectorProperty(size=2)
    start_pos: FloatVectorProperty(size=2)
    node_name: StringProperty()
    start_frame: IntProperty()
    end_frame: IntProperty()
    anim_type: StringProperty(default="")
    pathx_multiplier: FloatProperty(default=1000.0)
    pathy_multiplier: FloatProperty(default=1000.0)
    hide: BoolProperty(default=False)
    sync: BoolProperty(default=False)

class NODETREE_ANIM_LinkTracking(bpy.types.PropertyGroup):
    from_node: StringProperty()
    to_node: StringProperty()
    from_socket: StringProperty()
    to_socket: StringProperty(default="")
    start_frame: IntProperty()
    end_frame: IntProperty()
    anim_type: StringProperty(default="")
    start_offset: FloatVectorProperty(size=2)
    end_offset: FloatVectorProperty(size=2)
    hide: BoolProperty(default=False)

class NODETREE_ANIM_ValueTracking(bpy.types.PropertyGroup):
    socket_name: StringProperty()
    is_output: BoolProperty()
    start_frame: IntProperty()
    end_frame: IntProperty()
    hide: BoolProperty(default=False)
    sync: BoolProperty(default=False)

class NODETREE_ANIM_NodeLinkTracking(bpy.types.PropertyGroup):
    node_links: CollectionProperty(name="from_socket.to_socket", type=NODETREE_ANIM_LinkTracking)
    node_name: StringProperty()

class NODETREE_ANIM_NodeValueTracking(bpy.types.PropertyGroup):
    node_values: CollectionProperty(name="node.socket", type=NODETREE_ANIM_ValueTracking)
    node_name: StringProperty()

class NODETREE_ANIM_AnimViewTracking(bpy.types.PropertyGroup):
    anim_views: CollectionProperty(name="node_name", type=NODETREE_ANIM_ViewTracking)

class NODETREE_ANIM_AnimNodeTracking(bpy.types.PropertyGroup):
    anim_nodes: CollectionProperty(name="node_name", type=NODETREE_ANIM_NodeTracking)

class NODETREE_ANIM_AnimLinkTracking(bpy.types.PropertyGroup):
    anim_links: CollectionProperty(name="node_name", type=NODETREE_ANIM_NodeLinkTracking)

class NODETREE_ANIM_AnimValueTracking(bpy.types.PropertyGroup):
    anim_values: CollectionProperty(name="node_name", type=NODETREE_ANIM_NodeValueTracking)

class NODETREE_ANIM_NodeItem(bpy.types.PropertyGroup):
    name: StringProperty()
    type: StringProperty(default="node")

class NODETREE_ANIM_ValueItem(bpy.types.PropertyGroup):
    name: StringProperty()
    type: StringProperty(default="value")
    subtype: StringProperty()
    is_output: BoolProperty()

class NODETREE_ANIM_LinkItem(bpy.types.PropertyGroup):
    from_node: StringProperty()
    to_node: StringProperty()
    from_socket: StringProperty()
    to_socket: StringProperty()
    type: StringProperty(default="link")

class NODETREE_ANIM_NodeProps(bpy.types.PropertyGroup):
    def on_node_select(self, context):
        node_tree = None
        space = context.space_data
        if space and space.type == 'NODE_EDITOR':
            node_tree = space.edit_tree
        if node_tree is None:
            self.report("WARNING", "no node tree found!")
            return None
        if self.node_index >= len(self.nodes):
            return

        node_name = self.nodes[self.node_index].name
        node = node_tree.nodes.get(node_name)
        if not node:
            return

        # update links list based on the selected node
        self.links.clear()
        for socket in node.outputs:
            for link in socket.links:
                item = self.links.add()
                item.from_node = node.name
                item.to_node = link.to_node.name
                item.from_socket = socket.name
                item.to_socket = link.to_socket.name
        # update values list based on the selected node
        self.values.clear()
        anim_types = ['INT', 'VALUE', 'VECTOR', 'ROTATION', 'BOOLEAN', 'STRING', 'RGBA']
        for socket in node.inputs:
            if not socket.is_linked and socket.type in anim_types:
                item = self.values.add()
                item.name = socket.name
                item.type = socket.type
                item.subtype = socket.bl_subtype_label.upper()
                item.is_output = False
        for socket in node.outputs:
            if not socket.is_linked and socket.type in anim_types:
                item = self.values.add()
                item.name = socket.name
                item.type = socket.type
                item.subtype = socket.bl_subtype_label.upper()
                item.is_output = True

        # update anim curve tree
        anim_curve_tree = None
        if bpy.data.node_groups.get(f"{node_tree.name}_AnimCurves") is None:
            anim_curve_tree = bpy.data.node_groups.new(f"{node_tree.name}_AnimCurves", 'GeometryNodeTree')
            anim_curve_tree.use_fake_user = True
        else:
            anim_curve_tree = bpy.data.node_groups[f"{node_tree.name}_AnimCurves"]
        if self.add_anim == 'LINKANIM':
            if anim_curve_tree.nodes.get('node.link_anim_curve') is None:
                anim_curve_tree.nodes.new('ShaderNodeFloatCurve').name = 'node.link_anim_curve'
        elif self.add_anim == 'NODEANIM':
            if anim_curve_tree.nodes.get("node_anim_curve") is None:
                anim_curve_tree.nodes.new('ShaderNodeFloatCurve').name = "node_anim_curve"
            if self.node_anim_type == 'FLY_IN':
                for idx, path in enumerate(["pathx", "pathy"]):
                    path_multiplier = self.pathx_multiplier if idx == 0 else self.pathy_multiplier
                    if anim_curve_tree.nodes.get(f'node_{path}_curve') is None:
                        anim_curve_tree.nodes.new('ShaderNodeFloatCurve').name = f'node_{path}_curve'
                    fly_curve = anim_curve_tree.nodes[f'node_{path}_curve']
                    max_y = max(abs(self.start_pos[idx]), abs(node.location[idx]))
                    mini_range = 0.1
                    fly_curve.mapping.clip_min_y = -max(max_y*2/path_multiplier, mini_range)
                    fly_curve.mapping.clip_max_y = max(max_y*2/path_multiplier, mini_range)
                    fly_curve.mapping.curves[0].points[0].location[1] = self.start_pos[idx]/path_multiplier
                    fly_curve.mapping.curves[0].points[-1].location[1] = node.location[idx]/path_multiplier
                    fly_curve.mapping.update()
                    fly_curve.mapping.reset_view()
            if self.node_anim_type == 'SHRINK':
                if anim_curve_tree.nodes.get(f'node_shrink_curve') is None:
                    anim_curve_tree.nodes.new('ShaderNodeFloatCurve').name = 'node_shrink_curve'
                shrink_node = anim_curve_tree.nodes['node_shrink_curve']
                shrink_node.mapping.clip_min_y = 0.5
                shrink_node.mapping.clip_max_y = 5.0
                shrink_node.mapping.curves[0].points[0].location[1] = 2.0
                shrink_node.mapping.curves[0].points[-1].location[1] = 1.0
                shrink_node.mapping.update()
                shrink_node.mapping.reset_view()
        elif self.add_anim == 'VALUEANIM':
            if anim_curve_tree.nodes.get('node.value_anim_curve') is None:
                anim_curve_tree.nodes.new('ShaderNodeFloatCurve').name = 'node.value_anim_curve'
            if len(self.values) > 0 and self.value_index < len(self.values):
                if self.values[self.value_index].is_output:
                    socket = node.outputs[f"{self.values[self.value_index].name}"]
                    subtype = socket.bl_rna.properties["default_value"].subtype
                    node[f"output_{self.values[self.value_index].name}_start"] = socket.default_value
                    node[f"output_{self.values[self.value_index].name}_end"] = socket.default_value
                    ui = node.id_properties_ui(f"output_{self.values[self.value_index].name}_start")
                    ui.update(subtype=subtype)
                    ui = node.id_properties_ui(f"output_{self.values[self.value_index].name}_end")
                    ui.update(subtype=subtype)
                else:
                    socket = node.inputs[f"{self.values[self.value_index].name}"]
                    subtype = socket.bl_rna.properties["default_value"].subtype
                    node[f"input_{self.values[self.value_index].name}_start"] = socket.default_value
                    node[f"input_{self.values[self.value_index].name}_end"] = socket.default_value
                    ui = node.id_properties_ui(f"input_{self.values[self.value_index].name}_start")
                    ui.update(subtype=subtype)
                    ui = node.id_properties_ui(f"input_{self.values[self.value_index].name}_end")
                    ui.update(subtype=subtype)

        if self.locate:
            # deselect all nodes
            for n in node_tree.nodes:
                n.select = False
            # select the chosen node
            node.select = True
            node_tree.nodes.active = node
            # frame it in the node editor
            frame_node_in_editor(context, node)
            self["locate"] = False

    nodes: CollectionProperty( type=NODETREE_ANIM_NodeItem)
    node_index: IntProperty(
        description="Index of the currently selected node in the nodes collection",
        default=0,
        update=on_node_select,
    )
    locate: BoolProperty(
        default=False,
        description="Locate and zoom in the selected node in the node editor",
        update=on_node_select,
    )
    links: CollectionProperty( type=NODETREE_ANIM_LinkItem)
    link_index: IntProperty(
        description="Index of the currently selected link in the links collection",
        default=0,
        update=on_node_select,
    )
    values: CollectionProperty( type=NODETREE_ANIM_ValueItem)
    value_index: IntProperty(
        description="Index of the currently selected value in the values collection",
        default=0,
        update=on_node_select,
    )

    add_anim: EnumProperty(
        name="Add Anim",
        description="Add animation for the selected node or its output links",
        items=[ ("NODEANIM", "Add Node Anim", "add anim for a node", "ANIM", 0),
                ("LINKANIM", "Add Link Anim", "add anim for a link", "ANIM", 1),
                ("VALUEANIM", "Add Value Anim", "add anim for a value", "ANIM", 2),
              ],
        update = on_node_select,
    )
    build_link_type: EnumProperty(
        name="Link Type",
        description="add a new link or select a existing link",
        items=[("SELECTLINK", "Select Link", "Select a exisiting link"),
               ("NEWLINK", "New Link", "add a new link"),
              ],
    )
    def get_from_node(self, context):
        vb._from_node = [('None', 'None', 'None', "", 0)]
        if len(self.nodes) > 0:
            vb._from_node = [(node.name, node.name, "node in the node tree", "NODE", idx) for idx, node in enumerate(self.nodes)]
        return vb._from_node
    def from_node_setter(self, value):
        self['from_node'] = value
    def from_node_getter(self):
        value = self.get('from_node')
        valid_values = [item[4] for item in self.get_from_node(bpy.context)]
        return value if value in valid_values else valid_values[0]
    from_node: EnumProperty(
        name="From Node",
        items=get_from_node,
        set=from_node_setter,
        get=from_node_getter,
    )
    def get_to_node(self, context):
        vb._to_node = []
        idx = 0
        for node in self.nodes:
            if node.name != self.from_node:
                vb._to_node.append((node.name, node.name, "node in the node tree", "NODE", idx))
                idx += 1
        return vb._to_node if vb._to_node else [('None', 'None', 'None', "", 0)]
    def to_node_setter(self, value):
        self['to_node'] = value
    def to_node_getter(self):
        value = self.get('to_node')
        valid_values = [item[4] for item in self.get_to_node(bpy.context)]
        return value if value in valid_values else valid_values[0]
    to_node: EnumProperty(
        name="To Node",
        items=get_to_node,
        set=to_node_setter,
        get=to_node_getter,
    )
    def get_from_socket(self, context):
        vb._from_socket = [('None', 'None', 'None', "", 0)]
        node_tree = None
        space = context.space_data
        if space and space.type == 'NODE_EDITOR':
            node_tree = space.edit_tree
        if node_tree is None:
            self.report("WARNING", "no node tree found!")
            return vb._from_socket
        node = node_tree.nodes.get(self.from_node)
        if node and len(node.outputs) > 0:
            vb._from_socket = []
            idx = 0
            for socket in node.outputs:
                icon = f"NODE_SOCKET_{socket.type}"
                if socket.type == 'VALUE' or socket.type == 'CUSTOM':
                    icon = "NODE_SOCKET_FLOAT"
                vb._from_socket.append((socket.identifier, f"Output {socket.identifier}", "output socket in the node", icon, idx))
                idx += 1
        return vb._from_socket
    def from_socket_setter(self, value):
        self['from_socket'] = value
    def from_socket_getter(self):
        value = self.get('from_socket')
        valid_values = [item[4] for item in self.get_from_socket(bpy.context)]
        return value if value in valid_values else valid_values[0]
    from_socket: EnumProperty(
        name="From Socket",
        items=get_from_socket,
        set=from_socket_setter,
        get=from_socket_getter,
    )
    def get_to_socket(self, context):
        vb._to_socket = [('None', 'None', 'None', "", 0)]
        node_tree = None
        space = context.space_data
        if space and space.type == 'NODE_EDITOR':
            node_tree = space.edit_tree
        if node_tree is None:
            self.report("WARNING", "no node tree found!")
            return vb._to_socket
        node = node_tree.nodes.get(self.to_node)
        if node and len(node.inputs) > 0:
            vb._to_socket = []
            idx = 0
            for socket in node.inputs:
                icon = f"NODE_SOCKET_{socket.type}"
                if socket.type == 'VALUE' or socket.type == 'CUSTOM':
                    icon = "NODE_SOCKET_FLOAT"
                vb._to_socket.append((socket.identifier, f"Input {socket.identifier}", "input socket in the node", icon, idx))
                idx += 1
        return vb._to_socket
    def to_socket_setter(self, value):
        self['to_socket'] = value
    def to_socket_getter(self):
        value = self.get('to_socket')
        valid_values = [item[4] for item in self.get_to_socket(bpy.context)]
        return value if value in valid_values else valid_values[0]
    to_socket: EnumProperty(
        name="To Socket",
        items=get_to_socket,
        set=to_socket_setter,
        get=to_socket_getter,
    )
    node_anim_type: EnumProperty(
        name="Node Anim Type",
        description="Type of animation to choose for the selected node",
        items=[ ("FLY_IN", "Fly In", "Fly in animation"),
                ("SHRINK", "Shrink", "Shrink animation"),
              ],
        update=on_node_select,
    )
    link_anim_type: EnumProperty(
        name="Link Anim Type",
        description="Type of animation to choose for the selected link",
        items=[ ("GROW", "Grow", "Grow animation"),
                ("REVERSE_GROW", "Reverse Grow", "Reverse Grow animation"),
              ],
    )
    anim_start_frame: IntProperty()
    anim_end_frame: IntProperty()
    def reset_path_curve_view(self, context):
        node_tree = None
        space = context.space_data
        if space and space.type == 'NODE_EDITOR':
            node_tree = space.edit_tree
        if node_tree is None:
            self.report("WARNING", "no node tree found!")
            return None
        anim_curve_tree = bpy.data.node_groups[f"{node_tree.name}_AnimCurves"]
        node = node_tree.nodes[self.nodes[self.node_index].name]
        for idx, path in enumerate(["pathx", "pathy"]):
            path_curve = anim_curve_tree.nodes.get(f"node_{path}_curve")
            max_y = max(abs(self.start_pos[idx]), abs(node.location[idx]))
            mini_range = 0.1
            path_multiplier = self.pathx_multiplier if idx == 0 else self.pathy_multiplier
            path_curve.mapping.clip_min_y = -max(max_y*2/path_multiplier, mini_range)
            path_curve.mapping.clip_max_y = max(max_y*2/path_multiplier, mini_range)
            path_curve.mapping.curves[0].points[0].location[1] = self.start_pos[idx]/path_multiplier
            path_curve.mapping.curves[0].points[-1].location[1] = node.location[idx]/path_multiplier
            path_curve.mapping.update()
            path_curve.mapping.reset_view()
    start_pos: FloatVectorProperty(size=2, update=reset_path_curve_view)
    pathx_multiplier: FloatProperty(default=1000.0, update=reset_path_curve_view)
    pathy_multiplier: FloatProperty(default=1000.0, update=reset_path_curve_view)
    sync_node_path: BoolProperty(default=False)
    sync_node_shrink: BoolProperty(default=False)
    sync_value: BoolProperty(default=False)

class NODETREE_ANIM_Annotation_LayerItem(bpy.types.PropertyGroup):
    def update_time(self, context):
        note_props = context.scene.nodetree_note_props
        pre_end, pre_stagger = self.end_frame, self.stagger_time
        if note_props.is_updating:
            return
        note_props.is_updating = True
        for idx in range(self.index+1, len(note_props.layers)):
            item = note_props.layers[idx]
            anim_length = item.end_frame - item.start_frame
            item.start_frame = pre_end + pre_stagger
            item.end_frame = item.start_frame + anim_length
            pre_end, pre_stagger = item.end_frame, item.stagger_time
            if idx == len(note_props.layers) - 1:
                note_props.is_updating = False

    layer: StringProperty(description="Annotation Layer")
    index: IntProperty()
    start_frame: IntProperty(default=1, description="Start Frame")
    end_frame: IntProperty(default=24, description="End Frame", update=update_time)
    stagger_time: IntProperty(default=12, description="Stagger Time", update=update_time)
    select: BoolProperty(default=True, description="Select to build animation")
    anim_type: EnumProperty(
        name="Anim Type",
        description="Anim Type",
        items=[
            ('WRITE_ON', "Write On", "Write on animation"),
            ("WRITE_OFF", "Write Off", "Write off animation"),
            ("MORPH", "Morph", "Morph shapes animation, to be implemented"),
        ],
        default='WRITE_ON',
    )
    write_symbol: EnumProperty(
        name="Write Symbol",
        description="Add Write Symbol",
        items=[
            ('NONE', "None", "No write symbol"),
            ("WRITING_HAND", "✍", "Add a writing hand ✍write symbol"),
            ("PENCIL", "🖉", "Add a pencil 🖉 write symbol"),
            ("PEN", "🖊", "Add a pen 🖊 write symbol"),
            ("FOUNTAIN_PEN", "🖋", "Add a fountain pen 🖋 write symbol"),
        ],
        default='NONE',
    )
    symbol_scale: FloatProperty(default=1.0)
    symbol_shift: FloatVectorProperty(default=(0.0, 0.0), size=2)

class NODETREE_ANIM_Annotation_FrameItem(bpy.types.PropertyGroup):
    def update_time(self, context):
        note_props = context.scene.nodetree_note_props
        pre_end, pre_stagger = self.end_frame, self.stagger_time
        if note_props.is_updating:
            return
        note_props.is_updating = True
        for idx in range(self.index+1, len(note_props.frames)):
            item = note_props.frames[idx]
            anim_length = item.end_frame - item.start_frame
            item.start_frame = pre_end + pre_stagger
            item.end_frame = item.start_frame + anim_length
            pre_end, pre_stagger = item.end_frame, item.stagger_time
            if idx == len(note_props.frames) - 1:
                note_props.is_updating = False

    layer: StringProperty(description="Annotation Layer")
    frame: IntProperty(description="Annotation Frame of a layer")
    index: IntProperty()
    start_frame: IntProperty(default=1, description="Start Frame")
    end_frame: IntProperty(default=24, description="End Frame", update=update_time)
    stagger_time: IntProperty(default=12, description="Stagger Time", update=update_time)
    select: BoolProperty(default=True, description="Select to build animation")
    anim_type: EnumProperty(
        name="Anim Type",
        description="Anim Type",
        items=[
            ('WRITE_ON', "Write On", "Write on animation"),
            ("WRITE_OFF", "Write Off", "Write off animation"),
            ("MORPH", "Morph", "Morph shapes animation, to be implemented"),
        ],
        default='WRITE_ON',
    )
    write_symbol: EnumProperty(
        name="Write Symbol",
        description="Add Write Symbol",
        items=[
            ('NONE', "None", "No write symbol"),
            ("WRITING_HAND", "✍", "Add a writing hand ✍write symbol"),
            ("PENCIL", "🖉", "Add a pencil 🖉 write symbol"),
            ("PEN", "🖊", "Add a pen 🖊 write symbol"),
            ("FOUNTAIN_PEN", "🖋", "Add a fountain pen 🖋 write symbol"),
        ],
        default='NONE',
    )
    symbol_scale: FloatProperty(default=1.0)
    symbol_shift: FloatVectorProperty(default=(0.0, 0.0), size=2)

class NODETREE_ANIM_Annotation_StrokeItem(bpy.types.PropertyGroup):
    def update_time(self, context):
        note_props = context.scene.nodetree_note_props
        pre_end, pre_stagger = self.end_frame, self.stagger_time
        if note_props.is_updating:
            return
        note_props.is_updating = True
        for idx in range(self.index+1, len(note_props.strokes)):
            item = note_props.strokes[idx]
            anim_length = item.end_frame - item.start_frame
            item.start_frame = pre_end + pre_stagger
            item.end_frame = item.start_frame + anim_length
            pre_end, pre_stagger = item.end_frame, item.stagger_time
            if idx == len(note_props.strokes) - 1:
                note_props.is_updating = False

    layer: StringProperty(description="Annotation Layer")
    frame: IntProperty(description="Annotation Frame of a layer")
    stroke: IntProperty(description="Annotation Stroke of a frame of a layer")
    index: IntProperty()
    start_frame: IntProperty(default=1, description="Start Frame")
    end_frame: IntProperty(default=24, description="End Frame", update=update_time)
    stagger_time: IntProperty(default=12, description="Stagger Time", update=update_time)
    select: BoolProperty(default=True, description="Select to build animation")
    anim_type: EnumProperty(
        name="Anim Type",
        description="Anim Type",
        items=[
            ('WRITE_ON', "Write On", "Write on animation"),
            ("WRITE_OFF", "Write Off", "Write off animation"),
            ("MORPH", "Morph", "Morph shapes animation, to be implemented"),
        ],
        default='WRITE_ON',
    )
    write_symbol: EnumProperty(
        name="Write Symbol",
        description="Add Write Symbol",
        items=[
            ('NONE', "None", "No write symbol"),
            ("WRITING_HAND", "✍", "Add a writing hand ✍write symbol"),
            ("PENCIL", "🖉", "Add a pencil 🖉 write symbol"),
            ("PEN", "🖊", "Add a pen 🖊 write symbol"),
            ("FOUNTAIN_PEN", "🖋", "Add a fountain pen 🖋 write symbol"),
        ],
        default='NONE',
    )
    symbol_scale: FloatProperty(default=1.0)
    symbol_shift: FloatVectorProperty(default=(0.0, 0.0), size=2)

class NODETREE_ANIM_AnnotationProperties(bpy.types.PropertyGroup):
    def update_level(self, context):
        note = context.annotation_data
        if note is not None:
            if self.anim_level == 'LAYER':
                for layer in note.layers:
                    if self.layers.get(layer.info) is not None:
                        continue
                    item = self.layers.add()
                    item.name = layer.info
                    item.layer = layer.info
                    item.index = len(self.layers) - 1
                    item.stagger_time = self.anim_stagger
                    item.anim_type = self.anim_type
                    item.write_symbol = self.write_symbol
                for idx, layer in enumerate(self.layers):
                    if note.layers.get(layer.layer) is None:
                        self.layers.remove(idx)
                self.anim_start = self.anim_start
                self.anim_length = self.anim_length
            elif self.anim_level == 'FRAME':
                anim_mode = {}
                for layer in note.layers:
                    anim_mode[layer.info] = 1 if layer.lock else 0
                    for f_idx in range(len(layer.frames)-anim_mode[layer.info]):
                        if self.frames.get(f'{layer.info}.{f_idx}') is not None:
                            continue
                        item = self.frames.add()
                        item.name = f'{layer.info}.{f_idx}'
                        item.layer = layer.info
                        item.frame =  f_idx
                        item.index = len(self.frames) - 1
                        item.stagger_time = self.anim_stagger
                        item.anim_type = self.anim_type
                        item.write_symbol = self.write_symbol
                for idx, frame in enumerate(self.frames):
                    if note.layers.get(frame.layer) is None or frame.frame >= len(note.layers[frame.layer].frames) - anim_mode[frame.layer]:
                        self.frames.remove(idx)
                self.anim_start = self.anim_start
                self.anim_length = self.anim_length
            elif self.anim_level == 'STROKE':
                anim_mode = {}
                for layer in note.layers:
                    anim_mode[layer.info] = 1 if layer.lock else 0
                    for f_idx in range(len(layer.frames)-anim_mode[layer.info]):
                        for s_idx, stroke in enumerate(layer.frames[f_idx].strokes):
                            if self.strokes.get(f'{layer.info}.{f_idx}.{s_idx}') is not None:
                                continue
                            item = self.strokes.add()
                            item.name = f'{layer.info}.{f_idx}.{s_idx}'
                            item.layer = layer.info
                            item.frame = f_idx
                            item.stroke = s_idx
                            item.index = len(self.strokes) - 1
                            item.stagger_time = self.anim_stagger
                            item.anim_type = self.anim_type
                            item.write_symbol = self.write_symbol
                for idx, stroke in enumerate(self.strokes):
                    if note.layers.get(stroke.layer) is None or stroke.frame >= len(note.layers[stroke.layer].frames) - anim_mode[stroke.layer] or stroke.stroke >= len(note.layers[stroke.layer].frames[stroke.frame].strokes):
                        self.strokes.remove(idx)
                self.anim_start = self.anim_start
                self.anim_length = self.anim_length

            node_tree = context.space_data.edit_tree
            if bpy.data.node_groups.get(f"{node_tree.name}_AnimCurves") is None:
                anim_curve_tree = bpy.data.node_groups.new(f"{node_tree.name}_AnimCurves", 'GeometryNodeTree')
                anim_curve_tree.use_fake_user = True
            anim_curve_tree = bpy.data.node_groups[f"{node_tree.name}_AnimCurves"]
            if anim_curve_tree.nodes.get(f"annotation_anim_curve") is None:
               anim_curve_tree.nodes.new('ShaderNodeFloatCurve').name = f"annotation_anim_curve"

    anim_level: EnumProperty(
        name="Anim Level",
        description="Level of annnotation animation to build",
        items=[
            ('LAYER', "Layer", "Build the annotation anim for strokes of the layer", "RENDERLAYERS", 0),
            ("FRAME", "Frame", "Build annotation anim for strokes of the frame", "GP_MULTIFRAME_EDITING", 1),
            ("STROKE", "Stroke", "Build annotation anim for the stroke", "GP_DRAW_STROKE", 2),
        ],
        default='LAYER',
        update=update_level,
    )

    def update_type(self, context):
        if self.anim_level == 'LAYER':
            for layer in self.layers:
                layer.anim_type = self.anim_type
        elif self.anim_level == 'FRAME':
            for frame in self.frames:
                frame.anim_type = self.anim_type
        elif self.anim_level == 'STROKE':
            for stroke in self.strokes:
                stroke.anim_type = self.anim_type
    anim_type: EnumProperty(
        name="Anim Type",
        description="Anim Type",
        items=[
            ('WRITE_ON', "Write On", "Write on animation"),
            ("WRITE_OFF", "Write Off", "Write off animation"),
            ("MORPH", "Morph", "Morph shapes animation, to be implemented"),
        ],
        default='WRITE_ON',
        update=update_type,
    )

    def update_symbol(self, context):
        if self.anim_level == 'LAYER':
            for layer in self.layers:
                layer.write_symbol = self.write_symbol
        elif self.anim_level == 'FRAME':
            for frame in self.frames:
                frame.write_symbol = self.write_symbol
        elif self.anim_level == 'STROKE':
            for stroke in self.strokes:
                stroke.write_symbol = self.write_symbol
    write_symbol: EnumProperty(
        name="Write Symbol",
        description="Add Write Symbol",
        items=[
            ('NONE', "None", "No write symbol"),
            ("WRITING_HAND", "✍", "Add a writing hand ✍write symbol"),
            ("PENCIL", "🖉", "Add a pencil 🖉 write symbol"),
            ("PEN", "🖊", "Add a pen 🖊 write symbol"),
            ("FOUNTAIN_PEN", "🖋", "Add a fountain pen 🖋 write symbol"),
        ],
        default='NONE',
        update=update_symbol,
    )

    def update_symbol_scale(self, context):
        if self.anim_level == 'LAYER':
            for layer in self.layers:
                layer.symbol_scale = self.symbol_scale
        elif self.anim_level == 'FRAME':
            for frame in self.frames:
                frame.symbol_scale = self.symbol_scale
        elif self.anim_level == 'STROKE':
            for stroke in self.strokes:
                stroke.symbol_scale = self.symbol_scale
    symbol_scale: FloatProperty(default=1.0, update=update_symbol_scale)

    def update_symbol_shift(self, context):
        if self.anim_level == 'LAYER':
            for layer in self.layers:
                layer.symbol_shift = self.symbol_shift
        elif self.anim_level == 'FRAME':
            for frame in self.frames:
                frame.symbol_shift = self.symbol_shift
        elif self.anim_level == 'STROKE':
            for stroke in self.strokes:
                stroke.symbol_shift = self.symbol_shift
    symbol_shift: FloatVectorProperty(default=(0.0, 0.0), size=2, update=update_symbol_shift)

    def update_anim_start(self, context):
        items = {'LAYER': self.layers, 'FRAME': self.frames, 'STROKE': self.strokes}
        pre_end, pre_stagger = self.anim_start, 0
        for idx, item in enumerate(items[self.anim_level]):
            anim_length = item.end_frame - item.start_frame
            item.start_frame = pre_end + pre_stagger
            item.end_frame = item.start_frame + anim_length
            pre_end, pre_stagger = item.end_frame, item.stagger_time
    anim_start: IntProperty(default=1, description="Anim Start", update=update_anim_start)

    def update_anim_length(self, context):
        items = {'LAYER': self.layers, 'FRAME': self.frames, 'STROKE': self.strokes}
        pre_end, pre_stagger = 0, 0
        for idx, item in enumerate(items[self.anim_level]):
            item.start_frame = item.start_frame if idx == 0 else pre_end + pre_stagger
            item.end_frame = item.start_frame + self.anim_length
            pre_end, pre_stagger = item.end_frame, item.stagger_time
    anim_length: IntProperty(default=24, description="Anim Length", update=update_anim_length)

    def update_anim_stagger(self, context):
        items = {'LAYER': self.layers, 'FRAME': self.frames, 'STROKE': self.strokes}
        pre_end, pre_stagger = 0, 0
        for idx, item in enumerate(items[self.anim_level]):
            if idx == 0:
                item.stagger_time = self.anim_stagger
                pre_end, pre_stagger = item.end_frame, item.stagger_time
            else:
                anim_length = item.end_frame - item.start_frame
                item.stagger_time = self.anim_stagger
                item.start_frame = pre_end + pre_stagger
                item.end_frame = item.start_frame + anim_length
                pre_end, pre_stagger = item.end_frame, item.stagger_time
    anim_stagger: IntProperty(default=12, description="Anim Stagger Time", update=update_anim_stagger)

    layers: CollectionProperty(name="layer_name", type=NODETREE_ANIM_Annotation_LayerItem)
    frames: CollectionProperty(name="frame_name", type=NODETREE_ANIM_Annotation_FrameItem)
    strokes: CollectionProperty(name="stroke_name", type=NODETREE_ANIM_Annotation_StrokeItem)
    is_updating: BoolProperty(default=False)
    note_source: EnumProperty(
        name="Note Source",
        description="Build annotation from drawing or input text",
        items=[
            ('FREEDRAW', "Free Draw", "Free drawing"),
            ("INPUTTEXT", "Input Text", "From input text"),
        ],
        default='FREEDRAW',
    )

    def update_text(self, context):
        if self.text_body:
            curve_points = text_to_curves(self.text_body, self.text_font, self.text_step)
            if curve_points:
                if context.annotation_data is None:
                    bpy.ops.gpencil.annotation_add()
                note = context.annotation_data
                if not note.layers.active_note:
                    note.layers.new("Note")
                layer = note.layers[note.layers.active_note]
                if layer.lock:
                    layer = note.layers.new("Note")
                current_frame = context.scene.frame_current
                note_frame = None
                for frame in layer.frames:
                    if frame.frame_number == current_frame:
                        note_frame = frame
                        break
                if note_frame is None:
                    note_frame = layer.frames.new(current_frame)
                # clear the frame's strokes
                while note_frame.strokes:
                    note_frame.strokes.remove(note_frame.strokes[0])
                for curve, points in curve_points.items():
                    stroke = note_frame.strokes.new()
                    stroke.display_mode = '2DSPACE'
                    for pt in points:
                        stroke.points.add(count=1)
                        stroke.points[-1].co = (pt[0]*100*self.text_size + self.text_position[0], pt[1]*100*self.text_size + self.text_position[1], 0.0)
    text_body: StringProperty(default="", update=update_text, description="Input text to annotation on current layer and current frame. If no current layer or current layer is in animated mode, it will create a new layer.")
    text_font: PointerProperty(type=bpy.types.VectorFont, update=update_text)
    text_size: FloatProperty(default=1.0, update=update_text, description="Text Size")
    text_step: FloatProperty(default=0.04, subtype='DISTANCE', description="String curve to points' length, it determines the annotation strokes' precision", update=update_text)
    text_position: FloatVectorProperty(default=(0.0, 0.0), size=2, description="Location for the text annotation", update=update_text)

class NODETREE_ANIM_AnnotationStrokeAnim(bpy.types.PropertyGroup):
    idx : IntProperty()
    start_frame: IntProperty(default=1, description="Start Frame")
    end_frame: IntProperty(default=24, description="End Frame")
    anim_type: StringProperty(description="Anim Type")
    write_symbol: StringProperty(default="WRITING_HAND", description="Write symbol for the stroke animation")
    symbol_scale: FloatVectorProperty(default=(1.0, 1.0), size=2)
    symbol_shift: FloatVectorProperty(default=(0.0, 0.0), size=2)
    symbol_idx: IntProperty(default=-1, description="Index of the write symbol in the symbol frame of the symbol layer")

class NODETREE_ANIM_AnnotationStrokeAnims(bpy.types.PropertyGroup):
    def update_active_anim(self, context):
        current_frame = context.scene.frame_current
        for idx, anim in enumerate(self.stroke_anims):
            next_start = self.stroke_anims[idx].end_frame if idx == len(self.stroke_anims)-1 else self.stroke_anims[idx+1].start_frame
            if current_frame <= anim.end_frame or current_frame <= next_start:
                self.active_anim = idx
                break
    # stroke_anims should be sorted by start frame
    stroke_anims: CollectionProperty(name="start_frame.end_frame", type=NODETREE_ANIM_AnnotationStrokeAnim)
    active_anim: IntProperty(default=-1)
    layer: StringProperty(description="Annotation layer")
    frame: IntProperty(description="Annotation frame of a layer")
    stroke: IntProperty(description="Annotation stroke of a frame of a layer")
    idx : IntProperty()
    anim_idx: IntProperty(default=-1, description="Index of the stroke in the anim frame of a layer")

class NODETREE_ANIM_AnnotationStrokeTracking(bpy.types.PropertyGroup):
    anim_strokes: CollectionProperty(type=NODETREE_ANIM_AnnotationStrokeAnims)

class NODETREE_ANIM_AnimAnnotationTracking(bpy.types.PropertyGroup):
    anim_annotations: CollectionProperty(name="annotation_name", type=NODETREE_ANIM_AnnotationStrokeTracking)

classes = (
    NODETREE_ANIM_ViewSelItem,
    NODETREE_ANIM_NodeSelItem,
    NODETREE_ANIM_LinkSelItem,
    NODETREE_ANIM_Properties,
    NODETREE_ANIM_ViewTracking,
    NODETREE_ANIM_NodeTracking,
    NODETREE_ANIM_LinkTracking,
    NODETREE_ANIM_ValueTracking,
    NODETREE_ANIM_NodeLinkTracking,
    NODETREE_ANIM_NodeValueTracking,
    NODETREE_ANIM_AnimViewTracking,
    NODETREE_ANIM_AnimNodeTracking,
    NODETREE_ANIM_AnimLinkTracking,
    NODETREE_ANIM_AnimValueTracking,
    NODETREE_ANIM_NodeItem,
    NODETREE_ANIM_LinkItem,
    NODETREE_ANIM_ValueItem,
    NODETREE_ANIM_NodeProps,
    NODETREE_ANIM_Annotation_StrokeItem,
    NODETREE_ANIM_Annotation_FrameItem,
    NODETREE_ANIM_Annotation_LayerItem,
    NODETREE_ANIM_AnnotationProperties,
    NODETREE_ANIM_AnnotationStrokeAnim,
    NODETREE_ANIM_AnnotationStrokeAnims,
    NODETREE_ANIM_AnnotationStrokeTracking,
    NODETREE_ANIM_AnimAnnotationTracking,
)
register, unregister = bpy.utils.register_classes_factory(classes)
