import bpy
from bpy import types, ops


class Btool_render_preview(bpy.types.Operator):
    bl_idname = "btool.render_preview"
    bl_label = "Render preview"

    def execute(self, context: types.Context):
        selected_objects = context.selected_objects
        objects = bpy.data.objects
        hidden = []
        for selected in selected_objects:
            for object in objects:
                if (
                    object.type == "MESH"
                    and object.name != selected.name
                    and object.hide_render is False
                ):
                    object.hide_render = True
                    hidden.append(object)

            locx = selected.location[0]
            locy = selected.location[1]
            locz = selected.location[2]

            selected.location[0] = 0
            selected.location[1] = 0
            selected.location[2] = 0

            file_name = selected.name.replace(".", "_")

            context.scene.render.filepath = "//preview/" + file_name + ".png"
            bpy.ops.render.render(use_viewport=True, write_still=True)

            selected.location[0] = locx
            selected.location[1] = locy
            selected.location[2] = locz

            for object in hidden:
                object.hide_render = False

            hidden = []
        return {"FINISHED"}
