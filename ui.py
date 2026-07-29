import bpy
from bpy import types
from bpy.utils import register_class, unregister_class
from bpy.types import KeyConfig
from .operators.cleanup_op import CleanupItem


class BanaspateamPanel:
    bl_space_type = "VIEW_3D"
    bl_category = "Tool"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}


class UI_PT_BT(types.Panel, BanaspateamPanel):
    bl_label = "BNSPT"

    def draw(self, context: types.Context):
        layout = self.layout
        main_menu(layout)


class UI_PT_OPT(types.Panel, BanaspateamPanel):
    bl_label = "Options"
    bl_parent_id = "UI_PT_BT"

    def draw(self, context: types.Context):
        scene = context.scene
        layout = self.layout
        layout.prop(data=scene, property='b_e_export_path', text="export path") 
        layout.prop(data=scene, property='b_e_vcol', text="export use vcol")
        layout.prop(data=scene, property='b_e_flatten_h', text="export flatten hierarchy")
        layout.prop(data=scene, property='b_e_stepping_interpolation', text="stepping interpolation on animation")
        layout.prop(data=scene, property='b_e_only_active', text="export only active")

class UI_PT_COMPRESS(types.Panel, BanaspateamPanel):
    bl_label = "Compress Images"
    bl_parent_id = "UI_PT_BT"

    def draw(self, context: types.Context):
        scene = context.scene
        layout = self.layout

        row = layout.row(align=True)
        row.prop(scene, "b_comp_format", expand=True)

        layout.prop(scene, "b_comp_quality", slider=True)

        row = layout.row()
        row.prop(scene, "b_comp_lossless")
        row.enabled = scene.b_comp_format != 'JPEG'

        layout.separator()
        layout.label(text="Set options, then press D in Outliner", icon="INFO")


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
        if context.active_object:
            if context.active_object.type == "ARMATURE":
                if context.active_object.mode == "POSE":
                    for bone in context.selected_pose_bones:
                        layout.label(text=bone.name)
                        layout.prop(
                            data=scene, property="a_curve_strength", text="strength"
                        )
                        layout.prop(data=scene, property="a_curve_rot_w", text="rot w")
                        layout.prop(data=scene, property="a_curve_rot_x", text="rot x")
                        layout.prop(data=scene, property="a_curve_rot_y", text="rot y")
                        layout.prop(data=scene, property="a_curve_rot_z", text="rot z")
                        layout.prop(data=scene, property="a_curve_pos_x", text="pos x")
                        layout.prop(data=scene, property="a_curve_pos_y", text="pos y")
                        layout.prop(data=scene, property="a_curve_pos_z", text="pos z")


class UI_PT_CLEANUP(types.Panel, BanaspateamPanel):
    bl_label = "Data Cleanup"
    bl_parent_id = "UI_PT_BT"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: types.Context):
        layout = self.layout
        scene = context.scene

        row = layout.row()
        row.operator("btool.scan_datablocks", text="Refresh List")

        row = layout.row()
        row.prop(scene, "cleanup_search", text="", icon="VIEWZOOM")
        row.prop(scene, "cleanup_filter", text="")

        if len(scene.cleanup_items) == 0:
            layout.label(text="No items — click Refresh")
        else:
            layout.template_list(
                "DATA_UL_cleanup_items",
                "",
                scene,
                "cleanup_items",
                scene,
                "cleanup_active_index",
                rows=8,
            )

            row = layout.row(align=True)
            row.operator("btool.select_datablock", text="Select")
            row.operator("btool.remove_selected_datablock", text="Remove")
            row.operator("btool.purge_unused_datablocks", text="Purge Unused")


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
        layout.operator('btool.rename_active_collection_to_filename',
                        text="(3) Rename Active Collection to Filename")


class UI_PT_BTOutlinerMenu(types.Menu):
    bl_label = "BNSPT Outliner"
    bl_idname = "BT_MT_outliner_menu"

    def draw(self, context):
        layout = self.layout
        layout.operator("btool.rename_images")
        layout.operator("btool.compress_images")


class UI_PT_BTExportMenu(types.Menu):
    bl_label = "BNSPT Export"
    bl_idname = "BT_MT_export_menu"

    def draw(self, context: types.Context):
        layout = self.layout
        fbx_op = layout.operator("btool.export", text="fbx")
        fbx_op.export_type = "fbx"
        fbx_op_2 = layout.operator("btool.export", text="fbx combine")
        fbx_op_2.export_type = "fbx_2"
        gltf_op = layout.operator("btool.export", text="gltf")
        gltf_op.export_type = "gltf"
        gltf_op_2 = layout.operator("btool.export", text="gltf batch")
        gltf_op_2.export_type = "gltf_2"


def main_menu(layout):
    layout.menu(UI_PT_BTExportMenu.bl_idname, text="export")
    layout.menu(UI_PT_BTRenameDataMenu.bl_idname, text="Rename Data")
    layout.separator()
    layout.operator("btool.render_preview")
    layout.operator("btool.metarig_to_applied", text="Metarig To Applyed Rig")
    layout.operator("btool.bones_from_vertices", text="Bones From Vertices")
    layout.operator("btool.reparent_separated_bone_rigify")
    layout.separator()
    layout.operator("btool.import_fbx_animations")
    layout.operator("btool.import_mixamo_animations")
    layout.operator("btool.set_rigify_type")
    layout.separator()
    # layout.operator("btool.change_zero_scale_keyframe")


classes = (
    UI_PT_BT,
    UI_PT_COMPRESS,
    UI_PT_MIXAMO,
    UI_PT_BTMenu,
    UI_PT_BTRenameDataMenu,
    UI_PT_BTOutlinerMenu,
    UI_PT_BTExportMenu,
    UI_PT_ANIMATION,
    UI_PT_OPT,
    UI_PT_CLEANUP,
)

bt_keymaps = []


def seamless_menu_draw(self, context):
    self.layout.separator()
    self.layout.operator("btool.make_seamless")
    self.layout.operator("btool.mirror_image")


def register():
    for c in classes:
        register_class(c)

    bpy.types.Scene.b_e_export_path = bpy.props.StringProperty("b_e_export_path")
    bpy.types.Scene.b_e_vcol = bpy.props.BoolProperty("b_e_vcol")
    bpy.types.Scene.b_e_flatten_h = bpy.props.BoolProperty("b_e_flatten_h")
    bpy.types.Scene.b_e_stepping_interpolation = bpy.props.BoolProperty('b_e_stepping_interpolation')
    bpy.types.Scene.b_e_only_active = bpy.props.BoolProperty('b_e_only_active')

    bpy.types.Scene.b_comp_format = bpy.props.EnumProperty(
        name="Format",
        items=[
            ('WEBP', "WebP", "WebP format (supports alpha)"),
            ('JPEG', "JPEG", "JPEG format (no alpha, smaller for photos)"),
            ('SMART', "Smart", "Auto: JPEG if no alpha, WebP if alpha present"),
        ],
        default='SMART',
    )
    bpy.types.Scene.b_comp_quality = bpy.props.IntProperty(
        name="Quality", default=80, min=0, max=100, subtype='PERCENTAGE',
    )
    bpy.types.Scene.b_comp_lossless = bpy.props.BoolProperty(
        name="Lossless", default=False,
    )

    bpy.types.Scene.a_curve_strength = bpy.props.FloatProperty("a_curve_strength")
    bpy.types.Scene.a_curve_rot_w =  bpy.props.FloatProperty("a_curve_rot_w", override={'LIBRARY_OVERRIDABLE'})
    bpy.types.Scene.a_curve_rot_x =  bpy.props.FloatProperty("a_curve_rot_x")
    bpy.types.Scene.a_curve_rot_y =  bpy.props.FloatProperty("a_curve_rot_y")
    bpy.types.Scene.a_curve_rot_z =  bpy.props.FloatProperty("a_curve_rot_z")
    bpy.types.Scene.a_curve_pos_x =  bpy.props.FloatProperty("a_curve_pos_x")
    bpy.types.Scene.a_curve_pos_y =  bpy.props.FloatProperty("a_curve_pos_y")
    bpy.types.Scene.a_curve_pos_z = bpy.props.FloatProperty("a_curve_pos_z")

    bpy.types.Scene.cleanup_items = bpy.props.CollectionProperty(type=CleanupItem)
    bpy.types.Scene.cleanup_active_index = bpy.props.IntProperty(default=0)
    bpy.types.Scene.cleanup_search = bpy.props.StringProperty(
        name="Search",
        description="Filter items by name",
        default="",
    )
    bpy.types.Scene.cleanup_filter = bpy.props.EnumProperty(
        name="Filter",
        description="Filter by datablock type",
        items=[
            ('ALL', 'All', 'Show all datablocks'),
            ('IMAGE', 'Images', 'Images only'),
            ('MESH', 'Meshes', 'Meshes only'),
            ('MATERIAL', 'Materials', 'Materials only'),
            ('ARMATURE', 'Armatures', 'Armatures only'),
            ('ACTION', 'Actions', 'Actions only'),
        ],
        default='ALL',
    )

    bpy.types.IMAGE_MT_image.append(seamless_menu_draw)

    key_config: KeyConfig = bpy.context.window_manager.keyconfigs.addon

    if key_config:
        km = key_config.keymaps.new(name="3D View", space_type="VIEW_3D")
        keymap_item = km.keymap_items.new(
            "wm.call_menu", type="D", value="PRESS"
        )
        keymap_item.properties.name = UI_PT_BTMenu.bl_idname
        bt_keymaps.append((km, keymap_item))

        km_outliner = key_config.keymaps.new(
            name="Outliner", space_type="OUTLINER"
        )
        kmi_outliner = km_outliner.keymap_items.new(
            "wm.call_menu", type="D", value="PRESS"
        )
        kmi_outliner.properties.name = UI_PT_BTOutlinerMenu.bl_idname
        bt_keymaps.append((km_outliner, kmi_outliner))


def unregister():
    for c in classes:
        unregister_class(c)

    del bpy.types.Scene.cleanup_items
    del bpy.types.Scene.cleanup_active_index
    del bpy.types.Scene.cleanup_search
    del bpy.types.Scene.cleanup_filter

    del bpy.types.Scene.b_comp_format
    del bpy.types.Scene.b_comp_quality
    del bpy.types.Scene.b_comp_lossless

    bpy.types.IMAGE_MT_image.remove(seamless_menu_draw)

    for km, keymap_item in bt_keymaps:
        km.keymap_items.remove(keymap_item)
    bt_keymaps.clear()
