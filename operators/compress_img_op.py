import bpy
from bpy.props import IntProperty, BoolProperty
import os
import tempfile
import uuid


class Btool_compress_images(bpy.types.Operator):
    bl_idname = "btool.compress_images"
    bl_label = "Compress Packed Images"
    bl_description = "Compress selected packed images to WebP in-memory"
    bl_options = {'REGISTER', 'UNDO'}

    quality: IntProperty(
        name="Quality",
        description="WebP image quality (0=worst, 100=best)",
        default=80,
        min=0,
        max=100,
        subtype='PERCENTAGE',
    )

    lossless: BoolProperty(
        name="Lossless",
        description="Use lossless WebP compression (quality setting is ignored)",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        return any(isinstance(id, bpy.types.Image) for id in context.selected_ids)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "quality", slider=True)
        layout.prop(self, "lossless")

    def execute(self, context):
        images = [
            id for id in context.selected_ids
            if isinstance(id, bpy.types.Image) and id.source != 'VIEWER'
        ]
        if not images:
            self.report({"WARNING"}, "No compressible images selected")
            return {"CANCELLED"}

        scene = context.scene

        orig_file_format = scene.render.image_settings.file_format
        orig_quality = scene.render.image_settings.quality
        orig_color_mode = scene.render.image_settings.color_mode
        orig_view_transform = scene.view_settings.view_transform
        orig_use_nodes = scene.use_nodes

        scene.render.image_settings.file_format = 'WEBP'
        scene.render.image_settings.quality = self.quality
        scene.render.image_settings.color_mode = 'RGBA'
        scene.view_settings.view_transform = 'Raw'
        scene.use_nodes = False

        if hasattr(scene.render.image_settings, 'webp_lossless'):
            scene.render.image_settings.webp_lossless = self.lossless

        total_original = 0
        total_compressed = 0
        compressed_count = 0
        skipped = []

        temp_dir = tempfile.gettempdir()

        for img in images:
            if not img.packed_file:
                if img.source == 'GENERATED':
                    skipped.append(img.name)
                    continue
                try:
                    img.pack()
                except RuntimeError:
                    skipped.append(img.name)
                    continue

            orig_size = len(img.packed_file.data)

            temp_path = os.path.join(temp_dir, f"btool_compress_{uuid.uuid4().hex}.webp")

            try:
                img.save_render(temp_path, scene=scene)

                if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                    skipped.append(img.name)
                    continue

                with open(temp_path, 'rb') as f:
                    img.packed_file.data = f.read()

                safe_name = "".join(c if c.isalnum() or c in '-_' else '_' for c in img.name)
                img.filepath_raw = f"//{safe_name}.webp"
                img.update_tag()

                total_original += orig_size
                total_compressed += len(img.packed_file.data)
                compressed_count += 1

            except Exception:
                skipped.append(img.name)
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        scene.render.image_settings.file_format = orig_file_format
        scene.render.image_settings.quality = orig_quality
        scene.render.image_settings.color_mode = orig_color_mode
        scene.view_settings.view_transform = orig_view_transform
        scene.use_nodes = orig_use_nodes

        if compressed_count:
            saved = total_original - total_compressed
            orig_mb = total_original / (1024 * 1024)
            comp_mb = total_compressed / (1024 * 1024)
            saved_mb = saved / (1024 * 1024)
            self.report(
                {"INFO"},
                f"Compressed {compressed_count} images: {orig_mb:.2f}MB → {comp_mb:.2f}MB ({saved_mb:.2f}MB saved)",
            )
        if skipped:
            self.report({"WARNING"}, f"Skipped {len(skipped)} images (not compressible)")

        return {"FINISHED"}
