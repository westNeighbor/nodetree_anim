'''
Copyright (C) 2025-2026 Minghui Zhao
zhaominghui2011@gmail.com

Created by Minghui Zhao

This is a blender addon to build node tree animate
'''

import bpy

from .preferences  import *
from .ui import *
from .properties import *
from .operations import *
from .handlers import *


def register():

    # preperties
    properties.register()

    # preferences
    preferences.register()

    # operators
    operations.register()

    # ui
    ui.register()

    bpy.types.Scene.nodetree_anim_props  = bpy.props.PointerProperty(type=NODETREE_ANIM_Properties)
    bpy.types.Scene.nodetree_node_props  = bpy.props.PointerProperty(type=NODETREE_ANIM_NodeProps)
    bpy.types.Scene.nodetree_note_props  = bpy.props.PointerProperty(type=NODETREE_ANIM_AnnotationProperties)
    bpy.types.Scene.nodetree_anim_view_tracking  = bpy.props.CollectionProperty(name="nodetree",type=NODETREE_ANIM_AnimViewTracking)
    bpy.types.Scene.nodetree_anim_node_tracking  = bpy.props.CollectionProperty(name="nodetree",type=NODETREE_ANIM_AnimNodeTracking)
    bpy.types.Scene.nodetree_anim_link_tracking  = bpy.props.CollectionProperty(name="nodetree",type=NODETREE_ANIM_AnimLinkTracking)
    bpy.types.Scene.nodetree_anim_value_tracking  = bpy.props.CollectionProperty(name="nodetree",type=NODETREE_ANIM_AnimValueTracking)
    bpy.types.Scene.nodetree_anim_note_tracking  = bpy.props.PointerProperty(name="annotations",type=NODETREE_ANIM_AnimAnnotationTracking)

    # handlers
    register_handlers("register")

    update_panel_category(None, None)

def unregister():
    # handlers
    register_handlers("unregister")

    # preferences
    preferences.unregister()

    # ui
    ui.unregister()

    # operators
    operations.unregister()

    # preperties
    properties.unregister()

    del bpy.types.Scene.nodetree_anim_props
    del bpy.types.Scene.nodetree_node_props
    del bpy.types.Scene.nodetree_note_props
    del bpy.types.Scene.nodetree_anim_value_tracking
    del bpy.types.Scene.nodetree_anim_node_tracking
    del bpy.types.Scene.nodetree_anim_link_tracking
    del bpy.types.Scene.nodetree_anim_view_tracking
    del bpy.types.Scene.nodetree_anim_note_tracking

if __name__ == "__main__":
    try:
        unregister()
    except:
        pass

    register()
