from .compile_op import Btool_compile
from .rename_op import Btool_rename_data
from .rigging_op import (
    Btool_metarig_to_applied,
    Btool_create_cloth_bones,
    Btool_set_rigify_type,
    Btool_reparent_separated_bone_rigify,
)
from .import_anim_op import Btool_import_mixamo_animations, Btool_import_fbx_animations
from .export_op import Btool_export
from .render_op import Btool_render_preview
# from .uv_op import Btool_move_uv_to_front
from .image_rename_op import Btool_rename_images


classes = (
    Btool_compile,
    Btool_rename_data,
    Btool_metarig_to_applied,
    Btool_create_cloth_bones,
    Btool_import_mixamo_animations,
    Btool_export,
    Btool_render_preview,
    Btool_set_rigify_type,
    Btool_reparent_separated_bone_rigify,
    Btool_import_fbx_animations,
    # Btool_move_uv_to_front,
    Btool_rename_images,
)


def register():
    for c in classes:
        from bpy.utils import register_class
        register_class(c)


def unregister():
    for c in reversed(classes):
        from bpy.utils import unregister_class
        unregister_class(c)
