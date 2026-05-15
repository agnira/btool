import bpy
import os
from bpy import types
from bpy.props import CollectionProperty, StringProperty


class Btool_import_mixamo_animations(bpy.types.Operator):
    bl_idname = "btool.import_mixamo_animations"
    bl_label = "Import mixamo Animations"

    files: CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={"HIDDEN", "SKIP_SAVE"},
    )
    directory: StringProperty(subtype="DIR_PATH")

    @classmethod
    def poll(cls, context: types.Context):
        return context.object and context.object.type in {"ARMATURE"}

    def execute(self, context: types.Context):
        mixamoTarget = bpy.context.object
        for file in self.files:
            filepath = os.path.join(self.directory, file.name)
            if filepath.endswith(".fbx"):
                bpy.ops.import_scene.fbx(filepath=filepath, use_anim=True)
                if hasattr(bpy.context.object.animation_data, "action"):
                    bpy.ops.object.select_all(action="DESELECT")
                    bpy.context.object.select_set(True)
                    bpy.context.object.animation_data.action.use_fake_user = False
                    bpy.context.scene.mix_source_armature = bpy.context.object
                    context.view_layer.objects.active = mixamoTarget
                    bpy.ops.mr.import_anim_to_rig()
                    bpy.ops.object.select_all(action="DESELECT")
                    mixamoTarget.animation_data.action.name = file.name.split(".")[0]
                    mixamoTarget.animation_data.action.use_fake_user = True
                    context.view_layer.objects.active = (
                        bpy.context.scene.mix_source_armature
                    )
                    bpy.context.scene.mix_source_armature.select_set(True)
                for child in bpy.context.object.children_recursive:
                    bpy.data.objects[child.name].select_set(True)
                bpy.ops.object.delete()

        bpy.ops.outliner.orphans_purge()
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


class Btool_import_fbx_animations(bpy.types.Operator):
    bl_idname = "btool.import_fbx_animations"
    bl_label = "Import fbx Animations"

    files: CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={"HIDDEN", "SKIP_SAVE"},
    )
    directory: StringProperty(subtype="DIR_PATH")

    @classmethod
    def poll(cls, context: types.Context):
        return context.active_object and context.active_object.type in {"ARMATURE"}

    def execute(self, context: types.Context):
        target = context.active_object
        for file in self.files:
            filepath = os.path.join(self.directory, file.name)
            if filepath.endswith(".fbx"):
                bpy.ops.import_scene.fbx(filepath=filepath, use_anim=True)
                context.active_object.animation_data.action.name = file.name.split(".")[
                    0
                ]
                bpy.ops.object.delete()

        bpy.ops.outliner.orphans_purge()
        context.view_layer.objects.active = target
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}
