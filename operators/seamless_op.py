import bpy
from bpy import types
import numpy as np


class Btool_make_seamless(types.Operator):
    bl_idname = "btool.make_seamless"
    bl_label = "Make Seamless"
    bl_description = "Convert the active image in Image Editor to seamless (tileable)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (
            context.space_data
            and context.space_data.type == "IMAGE_EDITOR"
            and context.space_data.image
        )

    def execute(self, context):
        image = context.space_data.image

        if not image.has_data:
            self.report({"ERROR"}, "Image has no data")
            return {"CANCELLED"}

        w, h = image.size
        if w < 2 or h < 2:
            self.report({"ERROR"}, "Image too small")
            return {"CANCELLED"}

        src = image.source
        if src in {"VIEWER", "COMPOSITOR", "SCENE"}:
            self.report({"ERROR"}, f"Cannot modify {src.lower()} images")
            return {"CANCELLED"}

        buf = np.array(list(image.pixels), dtype=np.float64).reshape((h, w, 4))
        alpha = buf[:, :, 3:]
        result = buf[:, :, :3].copy()

        fw = max(2, min(w, h) // 8)

        # ── Horizontal feather (left ↔ right edge pairs) ──
        if fw < w // 2:
            x_left = np.arange(fw)
            x_right = np.arange(w - fw, w)

            t_left = (x_left / fw)[None, :, None]
            t_right = ((w - 1 - x_right) / fw)[None, :, None]

            # Compute all averages from ORIGINAL data before any modification
            avg_l = (result[:, x_left, :] + result[:, w - 1 - x_left, :]) * 0.5
            avg_r = (result[:, x_right, :] + result[:, w - 1 - x_right, :]) * 0.5

            result[:, x_left, :] = result[:, x_left, :] * t_left + avg_l * (1.0 - t_left)
            result[:, x_right, :] = result[:, x_right, :] * t_right + avg_r * (1.0 - t_right)

        # ── Vertical feather (top ↔ bottom edge pairs) ──
        if fw < h // 2:
            y_top = np.arange(fw)
            y_bottom = np.arange(h - fw, h)

            t_top = (y_top / fw)[:, None, None]
            t_bottom = ((h - 1 - y_bottom) / fw)[:, None, None]

            # Averages from result (already horizontally feathered)
            avg_t = (result[y_top, :, :] + result[h - 1 - y_top, :, :]) * 0.5
            avg_b = (result[y_bottom, :, :] + result[h - 1 - y_bottom, :, :]) * 0.5

            result[y_top, :, :] = result[y_top, :, :] * t_top + avg_t * (1.0 - t_top)
            result[y_bottom, :, :] = result[y_bottom, :, :] * t_bottom + avg_b * (1.0 - t_bottom)

        out = np.concatenate([result, alpha], axis=2)

        image.pixels[:] = out.ravel().tolist()
        image.update_tag()

        if context.screen:
            for a in context.screen.areas:
                if a.type == 'IMAGE_EDITOR':
                    a.tag_redraw()

        print(f"[btool] edge-feather: {w}x{h} fw={fw}")

        self.report({"INFO"}, f"'{image.name}' made seamless ({w}x{h})")
        return {"FINISHED"}
