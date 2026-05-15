from bpy import types


class Btool_move_uv_to_front(types.Operator):
    bl_idname = "btool.move_uv_to_front"
    bl_label = "Move Active UV to Front"
    bl_description = "Move the active UV layer to the first slot"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == "MESH" and obj.data.uv_layers

    def execute(self, context):
        from ..utils import move_active_uv_to_front
        move_active_uv_to_front(context.active_object)
        return {"FINISHED"}
