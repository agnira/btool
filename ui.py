# context.area: VIEW_3D

from bpy import types, context
from bpy.utils import register_class, unregister_class

class UI_PT_BT(types.Panel):
    bl_idname = "UI_PT_BT"
    bl_label = "Banaspateam"
    bl_category = "Tool"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context: context):
        layout = self.layout
        row = layout.row(align=True)
        row.operator("btool.compile", text="Compile")
        row = layout.row(align=True)
        row.operator("btool.rename_data", text="Rename Data")


classes = (
    UI_PT_BT,
)


def register():
    for c in classes:
        register_class(c)


def unregister():
    for c in classes:
        unregister_class(c)
