# context.area: VIEW_3D

from bpy import types, context
from bpy.utils import register_class, unregister_class

class BanaspateamPanel:
    bl_space_type = 'VIEW_3D'
    bl_category = "Tool"
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    
    

class UI_PT_BT(types.Panel, BanaspateamPanel):
    bl_label = "Banaspateam"

    def draw(self, context: context):
        layout = self.layout
        row = layout.row(align=True)
        row.operator("btool.compile", text="Compile")
        row = layout.row(align=True)
        row.operator("btool.rename_data", text="Rename Data")
        row = layout.row(align=True)
        row.operator("btool.metarig_to_applied", text="Metarig To Applyed Rig")
        row = layout.row(align=True)
        row.operator("btool.create_cloth_bones", text="Cloth Bones Form Mesh")
        row = layout.row(align=True)
        row.operator("btool.import_mixamo_animations")

class UI_PT_MIXAMO(types.Panel, BanaspateamPanel):
    bl_label = "Mixamo"
    bl_parent_id = "UI_PT_BT"
    
    def draw(self, context: context):
        layout = self.layout
        row = layout.row(align=True)
        row.operator("btool.import_mixamo_animations")
        
classes = (
    UI_PT_BT,
    UI_PT_MIXAMO,
)


def register():
    for c in classes:
        register_class(c)


def unregister():
    for c in classes:
        unregister_class(c)