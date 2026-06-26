import bpy
import bmesh
from bpy import types, ops
from bpy.props import StringProperty, FloatProperty


class Btool_metarig_to_applied(types.Operator):
    bl_idname = "btool.metarig_to_applied"
    bl_label = "Metarig to applied"
    bl_description = "Move every bone position to applyed bone position"

    metarig_object: StringProperty(name="Metarig", description="Select metarig target")

    @classmethod
    def poll(cls, context: types.Context):
        return context.object and context.object.type in {"ARMATURE"}

    def invoke(self, context, event):
        if context.object.name.find("APPLIED") == -1:
            self.report({"ERROR"}, "Please select applied armature")
            return {"CANCELLED"}
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context: types.Context):
        self.layout.prop_search(self, "metarig_object", bpy.data, "armatures")

    def execute(self, context: types.Context):
        ops.object.mode_set(mode="OBJECT")
        from ..utils import unselect_object

        unselect_object()
        metarig = context.scene.objects[self.metarig_object]
        metarig.select_set(True)
        applied = context.scene.objects[context.active_object.name]
        applied.select_set(True)
        applied_armature = bpy.data.armatures[applied.data.name]
        ops.object.mode_set(mode="EDIT")
        for bone in bpy.data.armatures[self.metarig_object].edit_bones:
            if bone.name.find("heel") == -1:
                bone.length = applied_armature.edit_bones[
                    "DEF-" + bone.name
                ].length
                bone.matrix = applied_armature.edit_bones[
                    "DEF-" + bone.name
                ].matrix.copy()
            if bone.name.find("heel") == -1:
                bone.head = applied_armature.edit_bones["DEF-" + bone.name].head
        return {"FINISHED"}


class Btool_bones_from_vertices(types.Operator):
    bl_idname = "btool.bones_from_vertices"
    bl_label = "Bones From Vertices"
    bl_description = "Create bones from selected vertices along vertex normals"

    bone_length: FloatProperty(
        name="Bone Length",
        default=0.1,
        min=0.001,
    )

    @classmethod
    def poll(cls, context: types.Context):
        return (
            context.object
            and context.object.type == "MESH"
            and context.object.mode == "EDIT"
        )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context: types.Context):
        self.layout.prop(self, "bone_length")

    def execute(self, context: types.Context):
        mesh_obj = context.object
        mesh = mesh_obj.data
        matrix = mesh_obj.matrix_world

        bm = bmesh.from_edit_mesh(mesh)
        selected_verts = [v for v in bm.verts if v.select]

        if not selected_verts:
            self.report({"WARNING"}, "No vertices selected")
            bm.free()
            return {"CANCELLED"}

        vert_data = []
        for v in selected_verts:
            pos = matrix @ v.co
            normal = matrix.to_3x3() @ v.normal
            if normal.length_squared > 0:
                normal.normalize()
            else:
                normal = (0, 0, 1)
            vert_data.append((pos, normal))

        bm.free()

        ops.object.mode_set(mode="OBJECT")
        ops.object.armature_add(
            enter_editmode=True, align="WORLD", location=(0, 0, 0)
        )
        armature = context.object
        edit_bones = armature.data.edit_bones

        for i, (pos, normal) in enumerate(vert_data):
            bone = edit_bones.new(f"Bone_{i}")
            bone.head = pos
            bone.tail = pos + normal * self.bone_length

        ops.object.mode_set(mode="OBJECT")
        ops.object.select_all(action="DESELECT")
        armature.select_set(True)
        context.view_layer.objects.active = armature
        return {"FINISHED"}


class Btool_set_rigify_type(types.Operator):
    bl_idname = "btool.set_rigify_type"
    bl_label = "Set Rigify Bones Type"

    @classmethod
    def poll(cls, context: types.Context):
        return (
            context.object
            and context.object.type in {"ARMATURE"}
            and context.object.mode == "POSE"
        )

    def execute(self, context: types.Context):
        pose_bones = context.selected_pose_bones
        for bone in pose_bones:
            bone.rigify_type = "basic.super_copy"
            bone.rigify_parameters.super_copy_widget_type = "bone"
        return {"FINISHED"}


class Btool_reparent_separated_bone_rigify(types.Operator):
    bl_idname = "btool.reparent_separated_bone_rigify"
    bl_label = "Reparent Separated Bone(rigify)"

    @classmethod
    def poll(cls, context: types.Context):
        return context.object and context.object.type in {"ARMATURE"}

    def execute(self, context: types.Context):
        from ..utils import reparent_rigify_bone

        reparent_rigify_bone(context)
        return {"FINISHED"}
