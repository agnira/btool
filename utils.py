import bpy
from bpy import types
from bpy_extras import anim_utils


SKIPPED_REPARENT_BONES = {
    "ORG-spine.003", "ORG-pelvis.L", "ORG-pelvis.R",
    "ORG-thigh.L", "ORG-toe.L", "ORG-thigh.R", "ORG-toe.R",
    "ORG-spine.009", "ORG-hair", "ORG-ear.L", "ORG-eye.L",
    "ORG-ear.R", "ORG-eye.R", "ORG-shoulder.L",
    "ORG-front_thigh.L", "ORG-front_toe.L", "ORG-shoulder.R",
    "ORG-front_thigh.R", "ORG-front_toe.R",
}

gltf_options = dict(
    check_existing=False,
    use_selection=True,
    export_format="GLB",
    export_image_format="AUTO",
    export_image_add_webp=False,
    export_image_webp_fallback=False,
    export_texture_dir="",
    export_jpeg_quality=75,
    export_image_quality=75,
    export_keep_originals=False,
    export_texcoords=True,
    export_normals=True,
    export_draco_mesh_compression_enable=False,
    export_draco_mesh_compression_level=6,
    export_draco_position_quantization=14,
    export_draco_normal_quantization=10,
    export_draco_texcoord_quantization=12,
    export_draco_color_quantization=10,
    export_draco_generic_quantization=12,
    export_tangents=False,
    export_materials="EXPORT",
    export_vertex_color="MATERIAL",
    export_active_vertex_color_when_no_material=True,
    export_all_vertex_colors=False,
    export_attributes=False,
    use_mesh_edges=False,
    use_mesh_vertices=False,
    export_cameras=False,
    use_visible=False,
    use_renderable=False,
    use_active_collection_with_nested=False,
    use_active_collection=False,
    use_active_scene=False,
    export_extras=False,
    export_yup=True,
    export_apply=True,
    export_animations=True,
    export_frame_range=False,
    export_frame_step=1,
    export_force_sampling=True,
    export_animation_mode="NLA_TRACKS",
    export_nla_strips_merged_animation_name="Animation",
    export_def_bones=True,
    export_hierarchy_flatten_bones=True,
    export_optimize_animation_size=True,
    export_optimize_animation_keep_anim_armature=True,
    export_optimize_animation_keep_anim_object=False,
    export_negative_frame="SLIDE",
    export_anim_slide_to_zero=False,
    export_bake_animation=True,
    export_anim_single_armature=True,
    export_reset_pose_bones=True,
    export_current_frame=False,
    export_rest_position_armature=True,
    export_anim_scene_split_object=True,
    export_skins=True,
    export_influence_nb=4,
    export_all_influences=False,
    export_morph=True,
    export_morph_normal=True,
    export_morph_tangent=False,
    export_morph_animation=True,
    export_morph_reset_sk_data=True,
    export_lights=False,
    export_try_sparse_sk=True,
    export_try_omit_sparse_sk=False,
    export_gpu_instances=False,
    export_nla_strips=True,
    export_original_specular=False,
    will_save_settings=False,
    export_copyright="",
)

fbx_options = dict(
    check_existing=False,
    use_selection=True,
    use_triangles=True,
    embed_textures=False,
    bake_anim=True,
    bake_anim_use_all_bones=True,
    bake_anim_use_nla_strips=True,
    bake_anim_use_all_actions=False,
    path_mode="COPY",
    use_armature_deform_only=True,
    add_leaf_bones=False,
)


def is_rigify(object: types.Object):
    return "rig_id" in object.data


def unselect_object():
    bpy.ops.object.select_all(action="DESELECT")


def duplicate_rig(context: types.Context):
    active_object = context.active_object
    mode = context.object.mode
    objects = context.selected_objects
    game_rig = None
    for obj in objects:
        if obj.type == "ARMATURE" and is_rigify(obj):
            game_rig = obj.copy()
            obj.users_collection[0].objects.link(game_rig)
            game_rig["original_rig"] = obj
            game_rig.data = obj.data.copy()
    if game_rig is not None:
        original_rig: types.Object = game_rig["original_rig"]
        bpy.ops.object.mode_set(mode="OBJECT")
        context.view_layer.objects.active = game_rig
        bpy.ops.object.mode_set(mode="EDIT")
        edit_bones = game_rig.data.edit_bones
        for bone in edit_bones:
            if bone.use_deform is False:
                edit_bones.remove(bone)
            else:
                bone.use_connect = False
                bone.parent = None
        bpy.ops.object.mode_set(mode="POSE")
        pose_bones = game_rig.pose.bones

        for bone in pose_bones:
            for constraint in bone.constraints:
                bone.constraints.remove(constraint)
            ct: types.CopyTransformsConstraint = bone.constraints.new("COPY_TRANSFORMS")
            ct.target = original_rig
            ct.subtarget = bone.name
            ct.target_space = "WORLD"
            ct.owner_space = "WORLD"

        for track in original_rig.animation_data.nla_tracks:
            game_rig.animation_data.nla_tracks.remove(
                game_rig.animation_data.nla_tracks[track.name]
            )
            track.is_solo = True
            frame_start = int(track.strips[0].frame_start)
            frame_end = int(track.strips[0].frame_end)

            bake_action = anim_utils.bake_action_objects(
                object_action_pairs=[[game_rig, None]],
                frames=[i for i in range(frame_start, frame_end)],
                bake_options=anim_utils.BakeOptions(
                    only_selected=False,
                    do_pose=True,
                    do_object=False,
                    do_visual_keying=True,
                    do_constraint_clear=False,
                    do_parents_clear=False,
                    do_clean=False,
                    do_location=True,
                    do_rotation=True,
                    do_scale=True,
                    do_bbone=True,
                    do_custom_props=True,
                ),
            )
            bake_action[0].name = track.name + "_b"
            if context.scene.b_e_stepping_interpolation is True:
                for fcurve in bake_action[0].fcurves:
                    for keyframe in fcurve.keyframe_points:
                        keyframe.interpolation = "CONSTANT"
            new_track = game_rig.animation_data.nla_tracks.new()
            new_track.name = track.name
            new_track.strips.new(bake_action[0].name, 0, bake_action[0])
            track.is_solo = False

        for bone in pose_bones:
            for constraint in bone.constraints:
                bone.constraints.remove(constraint)

        bpy.ops.object.mode_set(mode=mode)
        original_rig.select_set(False)

    for obj in objects:
        for modifier in obj.modifiers:
            if modifier.type == "ARMATURE" and game_rig is not None:
                modifier.object = game_rig
                obj.parent = game_rig

    return active_object


def restore_rig(context: types.Context):
    objects = context.selected_objects
    game_rig: types.Object = None
    for obj in objects:
        for modifier in obj.modifiers:
            if modifier.type == "ARMATURE":
                if "original_rig" in modifier.object:
                    game_rig = modifier.object
                    game_rig["original_rig"].select_set(True)
                    obj.parent = modifier.object["original_rig"]
                    modifier.object = modifier.object["original_rig"]
    if game_rig:
        for track in game_rig.animation_data.nla_tracks:
            bpy.data.actions.remove(track.strips[0].action)
        bpy.data.objects.remove(game_rig)


def reparent_rigify_bone(context: types.Context):
    mode = context.object.mode
    if context.active_object.type == "ARMATURE":
        bpy.ops.object.mode_set(mode="EDIT")
        rig = bpy.data.armatures[context.active_object.data.name]
        edit_bones = rig.edit_bones
        pose_bones = context.active_object.pose.bones
        for edit_bone in edit_bones:
            if "ORG" in edit_bone.name and edit_bone.use_connect is False:
                if "tweak" not in edit_bone.parent.name:
                    if edit_bone.name not in SKIPPED_REPARENT_BONES:
                        def_name = edit_bone.name.replace("ORG", "DEF")
                        def_parent = edit_bone.parent.name.replace("ORG", "DEF")
                        if (
                            edit_bones.get(def_name) is not None
                            and edit_bones.get(def_parent) is not None
                        ):
                            edit_bones[def_name].parent = edit_bones[def_parent]
        bpy.ops.object.mode_set(mode="POSE")
        for pose_bone in pose_bones:
            bpy.ops.object.mode_set(mode="EDIT")
            if "ORG" in pose_bone.name:
                if pose_bone.name not in SKIPPED_REPARENT_BONES:
                    def_name = pose_bone.name.replace("ORG", "DEF")
                    def_parent = pose_bone.parent.name.replace("ORG", "DEF")
                    if (
                        pose_bones.get(def_name) is not None
                        and pose_bones.get(def_parent) is not None
                    ):
                        if not pose_bones[def_name].constraints.get("Copy Transforms"):
                            ct = pose_bones[def_name].constraints.new("COPY_TRANSFORMS")
                            ct.target = context.active_object
                            ct.subtarget = def_name.replace("DEF", "ORG")
                            ct.target_space = "WORLD"
                            ct.owner_space = "WORLD"
        bpy.ops.object.mode_set(mode=mode)


def move_active_uv_to_front(obj):
    mesh = obj.data
    uvs = mesh.uv_layers
    active = uvs.active
    if not active:
        return
    if uvs[0].name == active.name:
        return

    saved = []
    for uv in uvs:
        data = [0.0] * (len(uv.data) * 2)
        uv.data.foreach_get("uv", data)
        saved.append((uv.name, data))

    active_name = active.name

    while uvs:
        uvs.remove(uvs[0])

    new_uv = uvs.new(name=active_name)
    active_data = next(d for n, d in saved if n == active_name)
    new_uv.data.foreach_set("uv", active_data)
    new_uv.data.update()
    uvs.active = new_uv

    for name, data in saved:
        if name == active_name:
            continue
        new_uv = uvs.new(name=name)
        new_uv.data.foreach_set("uv", data)
        new_uv.data.update()
