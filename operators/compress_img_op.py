import bpy
import os


def _has_alpha(img):
    if img.channels < 4:
        return False
    pixels = img.pixels
    total = len(pixels) // 4
    sample = min(total, 1000)
    step = max(1, total // sample)
    for i in range(0, total, step):
        if abs(pixels[i * 4 + 3] - 1.0) > 0.001:
            return True
    return False


class Btool_compress_images(bpy.types.Operator):
    bl_idname = "btool.compress_images"
    bl_label = "Compress Packed Images"
    bl_description = "Compress selected packed images to WebP or JPEG"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return any(isinstance(id, bpy.types.Image) for id in context.selected_ids)

    def execute(self, context):
        images = [
            id for id in context.selected_ids
            if isinstance(id, bpy.types.Image) and id.source != 'VIEWER'
        ]
        if not images:
            self.report({"WARNING"}, "No compressible images selected")
            return {"CANCELLED"}

        blend_path = bpy.data.filepath
        if not blend_path:
            self.report({"ERROR"}, "Save the blend file first")
            return {"CANCELLED"}

        blend_dir = os.path.dirname(blend_path)
        output_dir = os.path.join(blend_dir, "compressed_images")
        os.makedirs(output_dir, exist_ok=True)

        scene = context.scene

        orig_file_format = scene.render.image_settings.file_format
        orig_quality = scene.render.image_settings.quality
        orig_color_mode = scene.render.image_settings.color_mode
        orig_view_transform = scene.view_settings.view_transform
        orig_use_nodes = scene.use_nodes

        scene.view_settings.view_transform = 'Standard'
        scene.use_nodes = False

        img_format = scene.b_comp_format
        quality = scene.b_comp_quality
        lossless = scene.b_comp_lossless

        total_original = 0
        total_compressed = 0
        compressed_count = 0
        skipped = []

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

            has_alpha = _has_alpha(img)

            if img_format == 'JPEG' and has_alpha:
                skipped.append(f"{img.name} (has alpha, JPEG not supported)")
                continue

            if img_format == 'SMART':
                use_jpeg = not has_alpha
            else:
                use_jpeg = img_format == 'JPEG'

            if use_jpeg:
                fmt = 'JPEG'
                color_mode = 'RGB'
                ext = 'jpg'
            else:
                fmt = 'WEBP'
                color_mode = 'RGBA'
                ext = 'webp'

            safe_name = "".join(c if c.isalnum() or c in '-_' else '_' for c in img.name)
            output_path = os.path.join(output_dir, f"{safe_name}_compressed.{ext}")

            try:
                scene.render.image_settings.file_format = fmt
                scene.render.image_settings.quality = quality
                scene.render.image_settings.color_mode = color_mode

                if fmt == 'WEBP' and hasattr(scene.render.image_settings, 'webp_lossless'):
                    scene.render.image_settings.webp_lossless = lossless

                if os.path.exists(output_path):
                    os.remove(output_path)

                img.save_render(output_path, scene=scene)

                file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
                if file_size == 0:
                    skipped.append(f"{img.name} (save failed)")
                    continue

                if file_size >= orig_size:
                    skipped.append(f"{img.name} ({fmt}: {file_size/1024:.1f}KB >= {orig_size/1024:.1f}KB)")
                    continue

                rel_path = os.path.relpath(output_path, blend_dir)
                img.filepath_raw = f"//{rel_path}"

                with open(output_path, 'rb') as f:
                    data = f.read()
                img.pack(data=data, data_len=len(data))

                clean_name = safe_name.replace("_compressed", "")
                for old_ext in ("_png", "_PNG", "_jpg", "_JPG", "_jpeg", "_JPEG", "_webp", "_WEBP", "_tga", "_TGA", "_bmp", "_BMP"):
                    if clean_name.endswith(old_ext):
                        clean_name = clean_name[:-len(old_ext)]
                        break
                img.name = f"{clean_name}.{ext}"
                img.update_tag()

                total_original += orig_size
                total_compressed += len(img.packed_file.data)
                compressed_count += 1

            except Exception:
                skipped.append(img.name)

        scene.render.image_settings.file_format = orig_file_format
        scene.render.image_settings.quality = orig_quality
        scene.render.image_settings.color_mode = orig_color_mode
        scene.view_settings.view_transform = orig_view_transform
        scene.use_nodes = orig_use_nodes

        for img in list(bpy.data.images):
            if img.users == 0:
                bpy.data.images.remove(img)

        if compressed_count:
            saved = total_original - total_compressed
            orig_mb = total_original / (1024 * 1024)
            comp_mb = total_compressed / (1024 * 1024)
            saved_mb = saved / (1024 * 1024)
            self.report(
                {"INFO"},
                f"Compressed {compressed_count} images: {orig_mb:.2f}MB \u2192 {comp_mb:.2f}MB ({saved_mb:.2f}MB saved)",
            )
        if skipped:
            self.report({"WARNING"}, f"Skipped {len(skipped)} images (not compressible)")

        return {"FINISHED"}
