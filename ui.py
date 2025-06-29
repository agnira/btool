# context.area: VIEW_3D

import bpy
from bpy import types
from bpy.utils import register_class, unregister_class
from bpy.types import KeyConfig, UILayout


class BanaspateamPanel:
    bl_space_type = 'VIEW_3D'
    bl_category = "Tool"
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}


class UI_PT_BT(types.Panel, BanaspateamPanel):
    bl_label = "BNSPT"

    def draw(self, c: types.Context):
        layout = self.layout
        main_menu(layout)

class UI_PT_OPT(types.Panel, BanaspateamPanel):
    bl_label = "Options"
    bl_parent_id = "UI_PT_BT"

    def draw(self, c: types.Context):
        scene = c.scene
        layout = self.layout
        layout.prop(data=scene, property='b_e_export_path', text="export path") 
        layout.prop(data=scene, property='b_e_vcol', text="export use vcol")
        layout.prop(data=scene, property='b_e_flatten_h', text="export flatten hierarchy")
        layout.prop(data=scene, property='b_e_stepping_interpolation', text="stepping interpolation on animation")

class UI_PT_MIXAMO(types.Panel, BanaspateamPanel):
    bl_label = "Mixamo"
    bl_parent_id = "UI_PT_BT"

    def draw(self, context: types.Context):
        layout = self.layout
        layout.operator("btool.import_mixamo_animations")

class UI_PT_ANIMATION(types.Panel, BanaspateamPanel):
    bl_label = "Animation Tool"
    bl_parent_id = "UI_PT_BT"

    def draw(self, context: types.Context):
        scene = context.scene
        layout = self.layout
        layout.label(text="Curve Offset Tool")
        layout.separator()
        if (context.active_object):
            if (context.active_object.type == 'ARMATURE'):
                if (context.active_object.mode == 'POSE'):
                    for bone in context.selected_pose_bones:
                        layout.label(text=bone.name)
                        layout.prop(data=scene, property='a_curve_strength', text="strength")
                        layout.prop(data=scene, property='a_curve_rot_w', text="rot w")
                        layout.prop(data=scene, property='a_curve_rot_x', text="rot x")
                        layout.prop(data=scene, property='a_curve_rot_y', text="rot y")
                        layout.prop(data=scene, property='a_curve_rot_z', text="rot z")
                        layout.prop(data=scene, property='a_curve_pos_x', text="pos x")
                        layout.prop(data=scene, property='a_curve_pos_y', text="pos y")
                        layout.prop(data=scene, property='a_curve_pos_z', text="pos z")     
# menu
class UI_PT_BTMenu(types.Menu):
    bl_label = "BNSPT Menu"
    bl_idname = "BT_MT_menu"

    def draw(self, context: types.Context):
        layout = self.layout
        main_menu(layout)



class UI_PT_BTRenameDataMenu(types.Menu):
    bl_label = "BNSPT Rename Data"
    bl_idname = "BT_MT_rename_data_menu"

    def draw(self, context):
        layout = self.layout
        layout.operator("btool.rename_data",
                        text="(1) Rename Data")
        layout.operator("btool.rename_data_with_ucupaint",
                        text="(2) Rename Data w/ Ucupaint Node")


class UI_PT_BTExportMenu(types.Menu):
    bl_label, bl_idname = "BNSPT Export", "BT_MT_export_menu"
    
    def draw(self, context: types.Context):
        layout = self.layout
        fbx_op = layout.operator("btool.export", text="fbx")
        fbx_op["type"]="fbx"
        fbx_op_2 = layout.operator("btool.export", text="fbx combine")
        fbx_op_2["type"]="fbx_2"
        gltf_op = layout.operator("btool.export", text="gltf")
        gltf_op["type"]="gltf"
        gltf_op_2 = layout.operator("btool.export", text="gltf batch")
        gltf_op_2["type"]="gltf_2"

def main_menu(layout: UILayout):
    # layout.operator("btool.compile", text="Compile")
    layout.menu(UI_PT_BTExportMenu.bl_idname, text="export")
    layout.menu(UI_PT_BTRenameDataMenu.bl_idname, text="Rename Data")
    layout.separator()
    layout.operator("btool.render_preview")
    layout.operator("btool.metarig_to_applied",
                    text="Metarig To Applyed Rig")
    layout.operator("btool.create_cloth_bones",
                    text="Cloth Bones Form Mesh")
    layout.operator("btool.reparent_separated_bone_rigify")
    layout.separator()
    layout.operator("btool.import_fbx_animations")
    layout.operator("btool.import_mixamo_animations")
    layout.operator("btool.set_rigify_type")


classes = (
    UI_PT_BT,
    UI_PT_MIXAMO,
    UI_PT_BTMenu,
    UI_PT_BTRenameDataMenu,
    UI_PT_BTExportMenu,
    UI_PT_ANIMATION,
    UI_PT_OPT,
)

bt_keymaps = []

def register():
    for c in classes:
        register_class(c)

    bpy.types.Scene.b_e_export_path = bpy.props.StringProperty("b_e_export_path")
    bpy.types.Scene.b_e_vcol = bpy.props.BoolProperty("b_e_vcol")
    bpy.types.Scene.b_e_flatten_h = bpy.props.BoolProperty("b_e_flatten_h")
    bpy.types.Scene.b_e_stepping_interpolation = bpy.props.BoolProperty('b_e_stepping_interpolation')
    bpy.types.Scene.a_curve_strength = bpy.props.FloatProperty("a_curve_strength")
    bpy.types.Scene.a_curve_rot_w =  bpy.props.FloatProperty("a_curve_rot_w")
    bpy.types.Scene.a_curve_rot_x =  bpy.props.FloatProperty("a_curve_rot_x")
    bpy.types.Scene.a_curve_rot_y =  bpy.props.FloatProperty("a_curve_rot_y")
    bpy.types.Scene.a_curve_rot_z =  bpy.props.FloatProperty("a_curve_rot_z")
    bpy.types.Scene.a_curve_pos_x =  bpy.props.FloatProperty("a_curve_pos_x")
    bpy.types.Scene.a_curve_pos_y =  bpy.props.FloatProperty("a_curve_pos_y")
    bpy.types.Scene.a_curve_pos_z =  bpy.props.FloatProperty("a_curve_pos_z")

    key_config: KeyConfig = bpy.context.window_manager.keyconfigs.addon

    if key_config:
        km = key_config.keymaps.new(name='3D View', space_type='VIEW_3D')
        keymap_item = km.keymap_items.new(
            'wm.call_menu', type='D', value='PRESS')
        keymap_item.properties.name = UI_PT_BTMenu.bl_idname
        bt_keymaps.append((km, keymap_item))


def unregister():
    for c in classes:
        unregister_class(c)
    
    for km, keymap_item in bt_keymaps:
        km.keymap_items.remove(keymap_item)
    bt_keymaps.clear()
