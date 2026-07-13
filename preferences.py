import bpy
import sys
import os
import subprocess

class Preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    panel_category: bpy.props.StringProperty(
        name="Panel Category",
        default="Nodetree Anim",
        description="Category to show up the addon in the viewport N Panel, restart to take effect",
    )
    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.label(text="Fancy Node Tree animation builder")

        # give option to set category of the Addon in the N Panel
        col.separator()
        col.separator()
        col.prop(self, "panel_category", text='N Panel Location')
        col.separator()
        col.separator()

classes = (
    Preferences,
)
register, unregister = bpy.utils.register_classes_factory(classes)
