import bpy
from bpy import types


class Btool_rename_data(types.Operator):
    bl_idname = "btool.rename_data"
    bl_label = "Rename Data"
    bl_description = "Rename object data, materials, and ucupaint nodes to match object names"

    def execute(self, context: types.Context):
        for o in context.selected_objects:
            if o.data:
                o.data.name = o.name

            if o.active_material:
                o.active_material.name = o.name

            if hasattr(bpy.ops.wm, "y_rename_ypaint_tree"):
                bpy.ops.wm.y_rename_ypaint_tree(name=o.name)

        return {"FINISHED"}
