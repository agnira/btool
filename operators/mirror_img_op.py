import bpy
from bpy import types
from bpy.props import EnumProperty
import numpy as np


class Btool_mirror_image(types.Operator):
    bl_idname = "btool.mirror_image"
    bl_label = "Mirror Image"
    bl_description = "Mirror one half of the active image onto the other"
    bl_options = {'REGISTER', 'UNDO'}

    mode: EnumProperty(
        name="Direction",
        items=[
            ("LEFT_TO_RIGHT", "Left to Right", "Mirror left half onto right half"),
            ("RIGHT_TO_LEFT", "Right to Left", "Mirror right half onto left half"),
        ],
        default="LEFT_TO_RIGHT",
    )

    @classmethod
    def poll(cls, context):
        return (
            context.space_data
            and context.space_data.type == "IMAGE_EDITOR"
            and context.space_data.image
        )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, "mode")

    def execute(self, context):
        image = context.space_data.image

        if not image.has_data:
            self.report({"ERROR"}, "Image has no data")
            return {"CANCELLED"}

        w, h = image.size
        if w < 2:
            self.report({"ERROR"}, "Image width too small to mirror")
            return {"CANCELLED"}

        src = image.source
        if src in {"VIEWER", "COMPOSITOR", "SCENE"}:
            self.report({"ERROR"}, f"Cannot modify {src.lower()} images")
            return {"CANCELLED"}

        buf = np.array(image.pixels, dtype=np.float64).reshape((h, w, 4))
        half = w // 2

        if self.mode == "LEFT_TO_RIGHT":
            buf[:, half:, :] = buf[:, :half, :][:, ::-1, :]
            if w % 2:
                buf[:, half, :] = buf[:, half - 1, :]
        else:
            buf[:, :half, :] = buf[:, half:, :][:, ::-1, :]
            if w % 2:
                buf[:, half - 1, :] = buf[:, half, :]

        image.pixels[:] = buf.ravel().tolist()
        image.update_tag()

        if context.screen:
            for a in context.screen.areas:
                if a.type == 'IMAGE_EDITOR':
                    a.tag_redraw()

        self.report({"INFO"}, f"'{image.name}' mirrored ({self.mode.replace('_', ' ').title()})")
        return {"FINISHED"}
