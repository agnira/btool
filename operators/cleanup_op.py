import bpy
from bpy.props import IntProperty, StringProperty
from bpy.types import PropertyGroup, UIList, Operator


def _fmt_bytes(b):
    if b < 1024:
        return f"{b}B"
    elif b < 1024 ** 2:
        return f"{b / 1024:.1f}KB"
    elif b < 1024 ** 3:
        return f"{b / 1024 ** 2:.1f}MB"
    return f"{b / 1024 ** 3:.1f}GB"


class CleanupItem(PropertyGroup):
    name: StringProperty()
    size_bytes: IntProperty(default=0)
    size_str: StringProperty()
    users: IntProperty(default=0)
    type: StringProperty()
    extra_info: StringProperty()
    is_packed: IntProperty(default=0)


class DATA_UL_cleanup_items(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.label(text=item.name, translate=False)
            row.label(text=item.size_str)
            row.label(text=str(item.users))

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        flt = self.bitflag_filter_item
        filter_type = context.scene.cleanup_filter

        helper_funcs = bpy.types.UI_UL_list
        filter_result = helper_funcs.filter_items_by_name(
            context.scene.cleanup_search, flt, items, "name",
            reverse=False
        )

        for i, item in enumerate(items):
            if filter_type != 'ALL' and item.type != filter_type:
                filter_result[i] = 0

        return filter_result, []


class Btool_scan_datablocks(Operator):
    bl_idname = "btool.scan_datablocks"
    bl_label = "Scan Datablocks"
    bl_description = "Scan all datablocks and compute storage sizes"

    def execute(self, context):
        scene = context.scene
        scene.cleanup_items.clear()

        for img in bpy.data.images:
            if img.source == 'VIEWER':
                continue
            item = scene.cleanup_items.add()
            item.name = img.name
            item.users = img.users
            item.type = 'IMAGE'
            item.extra_info = f"{img.size[0]}x{img.size[1]}"

            if img.packed_file:
                item.size_bytes = len(img.packed_file.data)
                item.is_packed = 1
            else:
                item.size_bytes = img.size[0] * img.size[1] * 4

            item.size_str = _fmt_bytes(item.size_bytes)

        for mesh in bpy.data.meshes:
            item = scene.cleanup_items.add()
            item.name = mesh.name
            item.users = mesh.users
            item.type = 'MESH'
            verts = len(mesh.vertices)
            faces = len(mesh.polygons)
            item.size_bytes = verts
            item.extra_info = f"{verts:,} verts, {faces:,} faces"
            item.size_str = _fmt_bytes(verts * 48)

        for mat in bpy.data.materials:
            item = scene.cleanup_items.add()
            item.name = mat.name
            item.users = mat.users
            item.type = 'MATERIAL'
            item.size_str = "-"

        for arm in bpy.data.armatures:
            item = scene.cleanup_items.add()
            item.name = arm.name
            item.users = arm.users
            item.type = 'ARMATURE'
            bones = len(arm.bones) if arm.bones else 0
            item.size_bytes = bones
            item.extra_info = f"{bones} bones"
            item.size_str = str(bones)

        for action in bpy.data.actions:
            item = scene.cleanup_items.add()
            item.name = action.name
            item.users = action.users
            item.type = 'ACTION'
            fcurves = len(action.fcurves)
            item.size_bytes = fcurves
            item.extra_info = f"{fcurves} fcurves"
            item.size_str = str(fcurves)

        total = len(scene.cleanup_items)
        self.report({'INFO'}, f"Found {total} datablocks")
        return {'FINISHED'}


class Btool_select_datablock(Operator):
    bl_idname = "btool.select_datablock"
    bl_label = "Select Datablock"
    bl_description = "Select or reveal the active datablock in the viewport"

    @classmethod
    def poll(cls, context):
        idx = context.scene.cleanup_active_index
        return 0 <= idx < len(context.scene.cleanup_items)

    def execute(self, context):
        scene = context.scene
        item = scene.cleanup_items[scene.cleanup_active_index]
        dtype = item.type
        dname = item.name

        if dtype == 'IMAGE':
            img = bpy.data.images.get(dname)
            if img:
                for area in context.screen.areas:
                    if area.type == 'IMAGE_EDITOR':
                        area.spaces.active.image = img
                        self.report({'INFO'}, f"Opened image: {dname}")
                        return {'FINISHED'}
                self.report({'INFO'}, f"Image: {dname} (open Image Editor to view)")
                return {'FINISHED'}
            self.report({'WARNING'}, f"Image '{dname}' not found")
            return {'CANCELLED'}

        for obj in bpy.data.objects:
            if dtype == 'MESH' and obj.type == 'MESH' and obj.data and obj.data.name == dname:
                context.view_layer.objects.active = obj
                obj.select_set(True)
                self.report({'INFO'}, f"Selected {obj.name}")
                return {'FINISHED'}
            if dtype == 'ARMATURE' and obj.type == 'ARMATURE' and obj.data and obj.data.name == dname:
                context.view_layer.objects.active = obj
                obj.select_set(True)
                self.report({'INFO'}, f"Selected {obj.name}")
                return {'FINISHED'}
            if dtype == 'MATERIAL':
                for slot in obj.material_slots:
                    if slot.material and slot.material.name == dname:
                        context.view_layer.objects.active = obj
                        obj.select_set(True)
                        self.report({'INFO'}, f"Selected {obj.name} (using mat)")
                        return {'FINISHED'}

        if dtype == 'ACTION':
            self.report({'INFO'}, f"Action: {dname}")

        return {'FINISHED'}


class Btool_remove_selected(Operator):
    bl_idname = "btool.remove_selected_datablock"
    bl_label = "Remove Datablock"
    bl_description = "Remove the selected datablock (only if unused)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        idx = context.scene.cleanup_active_index
        items = context.scene.cleanup_items
        return 0 <= idx < len(items) and items[idx].users == 0

    def execute(self, context):
        scene = context.scene
        idx = scene.cleanup_active_index
        item = scene.cleanup_items[idx]

        if item.users > 0:
            self.report({'WARNING'}, f"'{item.name}' has {item.users} user(s), skipping")
            return {'CANCELLED'}

        dtype = item.type
        dname = item.name

        remove_map = {
            'IMAGE': (bpy.data.images, 'images'),
            'MESH': (bpy.data.meshes, 'meshes'),
            'MATERIAL': (bpy.data.materials, 'materials'),
            'ARMATURE': (bpy.data.armatures, 'armatures'),
            'ACTION': (bpy.data.actions, 'actions'),
        }

        collection, label = remove_map.get(dtype, (None, None))
        if collection is None:
            return {'CANCELLED'}

        datablock = collection.get(dname)
        if datablock is None:
            scene.cleanup_items.remove(idx)
            self.report({'WARNING'}, f"'{dname}' already removed")
            return {'FINISHED'}

        try:
            collection.remove(datablock)
            scene.cleanup_items.remove(idx)
            new_idx = min(idx, len(scene.cleanup_items) - 1)
            scene.cleanup_active_index = max(new_idx, 0)
            self.report({'INFO'}, f"Removed {label[:-1]}: {dname}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to remove {dname}: {e}")
            return {'CANCELLED'}


class Btool_purge_unused(Operator):
    bl_idname = "btool.purge_unused_datablocks"
    bl_label = "Purge Unused"
    bl_description = "Remove all orphan (zero-user) datablocks"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.outliner.orphans_purge()
        self.report({'INFO'}, "Purged unused datablocks")
        return {'FINISHED'}


classes = (
    CleanupItem,
    DATA_UL_cleanup_items,
    Btool_scan_datablocks,
    Btool_select_datablock,
    Btool_remove_selected,
    Btool_purge_unused,
)
