import bpy
import os
from bpy import types, context, ops
from bpy.types import Collection
from bpy.utils import register_class, unregister_class
from bpy.props import *

from bpy.props import CollectionProperty, StringProperty


def unselect_object():
    # D = bpy.data
    # for o in D.objects:
    #     o.select_set(False)
    ops.object.select_all(action='DESELECT')


class Btool_compile(types.Operator):
    bl_idname = "btool.compile"
    bl_label = "Compile"
    bl_description = "Compile finished project (please hide render unnecesary collection)"

    remove_vertex_group: BoolProperty(
        name="Remove vertex group", description="remove vertex group")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, ctx: context):
        self.layout.prop(self, "remove_vertex_group",
                         text="Remove Vertex Group")

    def execute(self, context: context):
        D = bpy.data
        found: Collection = None
        for c in context.scene.collection.children_recursive:
            if (c.name == "COMPILED"):
                found = c

        if (found == None):
            found = D.collections.new("COMPILED")
            context.scene.collection.children.link(found)

        for c in context.scene.collection.children_recursive:
            if (c.hide_render == False):
                if (c.name != "COMPILED"):
                    dup_name_list = []
                    o: types.Object
                    for o in c.objects:
                        if (o.hide_render == False):
                            dup_obj = o.copy()
                            dup_obj.data = o.data.copy()
                            found.objects.link(dup_obj)
                            dup_name_list.append(dup_obj.name)
                    unselect_object()
                    for n in dup_name_list:
                        D.objects[n].select_set(True)
                    if (len(dup_name_list) > 0):
                        context.view_layer.objects.active = D.objects[dup_name_list[0]]
                        ops.object.convert(target='MESH')
                        ops.object.join()
                        context.active_object.name = c.name
                        context.active_object.data.name = c.name
                        for m in context.active_object.material_slots:
                            context.active_object.active_material = m.material
                            ops.node.y_duplicate_yp_nodes(
                                duplicate_material=True)
                            ops.node.y_rename_ypaint_tree(
                                name=c.name+"-compiled")
                            m.material.name = c.name+"-compiled"
                            ops.node.y_bake_channels(
                                width=2048, height=2048, uv_map="UVMap", samples=5, margin=50, fxaa=True, aa_level=1)
                            ops.node.y_remove_yp_node()
                        uv_i = 0
                        uv_l = context.active_object.data.uv_layers
                        while len(uv_l) > uv_i:
                            if (uv_l[uv_i].name != "UVMap"):
                                uv_l.remove(uv_l[uv_i])
                            else:
                                uv_i += 1
                        ca_l = context.active_object.data.color_attributes
                        while ca_l:
                            ca_l.active_color_index = 0
                            ops.geometry.color_attribute_remove()
                        if (len(context.active_object.vertex_groups) > 0):
                            if (self.remove_vertex_group):
                                ops.object.vertex_group_remove(all=True)
                        c.hide_viewport = True

        return {'FINISHED'}


class Btool_rename_data(types.Operator):
    bl_idname = "btool.rename_data"
    bl_label = "Rename Data (Batch)"
    bl_description = "Batch rename selected data to object name"

    def execute(self, context: context):
        o: types.Object
        for o in context.selected_objects:
            o.data.name = o.name
        return {'FINISHED'}


class Btool_rename_data_with_ucupaint(types.Operator):
    bl_idname = "btool.rename_data_with_ucupaint"
    bl_label = "Rename Data w/ ucupaint_node)"
    bl_description = "Batch rename selected data w/ ucupaint_node (only active) to object name"

    def execute(self, context: context):
        o: types.Object
        for o in context.selected_objects:
            o.data.name = o.name
            if hasattr(o.active_material, "name"):
                o.active_material.name = o.name
            bpy.ops.node.y_rename_ypaint_tree(name=o.name)
        return {'FINISHED'}


class Btool_metarig_to_applied(types.Operator):
    bl_idname = "btool.metarig_to_applied"
    bl_label = "Metarig to applied"
    bl_description = "Move every bone position to applyed bone position"

    metarig_object: StringProperty(
        name="Metarig", description="Select metarig target")

    @classmethod
    def poll(cls, context: context):
        return context.object and context.object.type in {'ARMATURE'}

    def invoke(self, context, event):
        if (context.object.name.find("APPLIED") == -1):
            self.report({'ERROR'}, "Please select applied armature")
            return {'CANCELLED'}
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context: context):
        self.layout.prop_search(self, 'metarig_object', bpy.data, "armatures")

    def execute(self, context: context):
        ops.object.mode_set(mode="OBJECT")
        unselect_object()
        metarig = context.scene.objects[self.metarig_object]
        metarig.select_set(True)
        applied = context.scene.objects[context.active_object.name]
        applied.select_set(True)
        applied_armature = bpy.data.armatures[applied.data.name]
        ops.object.mode_set(mode="EDIT")
        bone: types.EditBone
        for bone in bpy.data.armatures[self.metarig_object].edit_bones:
            if (bone.name.find("heel") == -1):
                bone.length = applied_armature.edit_bones["DEF-" +
                                                          bone.name].length
                bone.matrix = applied_armature.edit_bones["DEF-" +
                                                          bone.name].matrix.copy()
            if (bone.name.find("heel") == -1):
                bone.head = applied_armature.edit_bones["DEF-"+bone.name].head
        return {'FINISHED'}


class Btool_create_cloth_bones(types.Operator):
    bl_idname = "btool.create_cloth_bones"
    bl_label = "Cloth Bones Form Mesh"
    bl_description = "mark seam for bones line, mark sharp for the root mark"

    def execute(self, context: context):
        cloth_mesh = context.object
        if not cloth_mesh:
            self.report({'WARNING'}, "Please select mesh guide.")
            return {"CANCELLED"}
        if cloth_mesh and cloth_mesh.type != 'MESH':
            self.report({'WARNING'}, "Please select mesh guide.")
            return {"CANCELLED"}

        points = []
        marked_edges = [
            edge for edge in cloth_mesh.data.edges if edge.use_edge_sharp]
        for edge in marked_edges:
            vertex_1 = cloth_mesh.data.vertices[edge.vertices[0]].co
            vertex_2 = cloth_mesh.data.vertices[edge.vertices[1]].co
            if vertex_1 not in points:
                points.append(vertex_1)
            if vertex_2 not in points:
                points.append(vertex_2)
        ops.object.armature_add(enter_editmode=True,
                                align='WORLD', location=(0, 0, 0))
        armature = context.object

        ops.armature.select_all(action='DESELECT')
        ops.armature.select_all(action='SELECT')
        ops.armature.delete()

        ops.object.mode_set(mode='EDIT')

        bones = []  # Store bones to check for parent relationships

        for row_index, edge in enumerate(cloth_mesh.data.edges):
            if edge.use_seam:
                bone_name = f'Row_{row_index}_Bone'
                ops.armature.bone_primitive_add(name=bone_name)
                new_bone = armature.data.edit_bones[bone_name]
                new_bone.head = cloth_mesh.matrix_world @ cloth_mesh.data.vertices[edge.vertices[0]].co
                new_bone.tail = cloth_mesh.matrix_world @ cloth_mesh.data.vertices[edge.vertices[1]].co
                bones.append(new_bone)

        # Set up parent-child relationships based on bone head positions
        for child_bone in bones:
            for parent_bone in bones:
                if parent_bone != child_bone and (parent_bone.tail - child_bone.head).length < 0.001:
                    child_bone.parent = parent_bone
                    child_bone.use_connect = True
            child_bone.select = False
        for point in points:
            for bone in bones:
                if (bone.tail - point).length < 0.001:
                    bone.select = True
                    for parent in bone.parent_recursive:
                        parent.select = True

        ops.armature.switch_direction()

        ops.object.mode_set(mode='OBJECT')
        ops.object.select_all(action='DESELECT')
        armature.select_set(True)
        context.view_layer.objects.active = armature
        return {'FINISHED'}


class Btool_import_mixamo_animations(bpy.types.Operator):
    bl_idname = "btool.import_mixamo_animations"
    bl_label = "Import mixamo Animations"

    files: CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={'HIDDEN', 'SKIP_SAVE'},
    )
    directory: StringProperty(
        subtype='DIR_PATH',
    )

    @classmethod
    def poll(cls, context: context):
        return context.object and context.object.type in {'ARMATURE'}

    def execute(self, context: context):
        mixamoTarget = bpy.context.object
        for file in self.files:
            filepath = os.path.join(self.directory, file.name)
            if filepath.endswith(".fbx"):
                bpy.ops.import_scene.fbx(filepath=filepath, use_anim=True)
                if hasattr(bpy.context.object.animation_data, "action"):
                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.context.object.select_set(True)
                    bpy.context.object.animation_data.action.use_fake_user = False
                    bpy.context.scene.mix_source_armature = bpy.context.object
                    context.view_layer.objects.active = mixamoTarget
                    bpy.ops.mr.import_anim_to_rig()
                    bpy.ops.object.select_all(action='DESELECT')
                    mixamoTarget.animation_data.action.name = file.name.split(".")[
                        0]
                    mixamoTarget.animation_data.action.use_fake_user = True
                    context.view_layer.objects.active = bpy.context.scene.mix_source_armature
                    bpy.context.scene.mix_source_armature.select_set(True)
                for child in bpy.context.object.children_recursive:
                    bpy.data.objects[child.name].select_set(True)
                print(context.selected_objects)
                bpy.ops.object.delete()

        bpy.ops.outliner.orphans_purge()
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class Btool_export(bpy.types.Operator):
    bl_idname = "btool.export"
    bl_label = "Export File"

    type: StringProperty(name="type", default="fbx")

    def execute(self, context: context):
        gltf_options = dict(
            check_existing=True,
            use_selection=True,
            export_format="GLB",
            export_image_format='AUTO',
            export_image_add_webp=False,
            export_image_webp_fallback=False,
            export_texture_dir="",
            export_jpeg_quality=90,
            export_image_quality=90,
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
            export_materials='EXPORT',
            export_colors=False,
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
            export_apply=False,
            export_animations=True,
            export_frame_range=False,
            export_frame_step=1,
            export_force_sampling=True,
            export_animation_mode='NLA_TRACKS',
            export_nla_strips_merged_animation_name="Animation",
            export_def_bones=False,
            export_hierarchy_flatten_bones=True,
            export_optimize_animation_size=True,
            export_optimize_animation_keep_anim_armature=True,
            export_optimize_animation_keep_anim_object=False,
            export_negative_frame='SLIDE',
            export_anim_slide_to_zero=False,
            export_bake_animation=False,
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
            export_copyright=""
        )
        if (self.type == "fbx"):
            dir = os.path.join(os.path.dirname(bpy.data.filepath), "fbx")
            filename = bpy.path.basename(
                bpy.data.filepath).split('.')[0]+".fbx"
            try:
                os.mkdir(dir)
            except OSError as error:
                print("fbx folder exist, skipped")

            bpy.ops.export_scene.fbx(
                filepath=os.path.join(dir, filename),
                check_existing=False,
                use_selection=True,
                use_triangles=True,
                bake_anim=True,
                bake_anim_use_all_bones=True,
                bake_anim_use_nla_strips=True,
                bake_anim_use_all_actions=False,
                path_mode='COPY',
                use_armature_deform_only=True
            )
        elif (self.type == "fbx_2"):
            dir = os.path.join(os.path.dirname(bpy.data.filepath), "fbx")
            filename = bpy.path.basename(
                bpy.data.filepath).split('.')[0]+".fbx"
            try:
                os.mkdir(dir)
            except OSError as error:
                print("fbx folder exist, skipped")

            bpy.ops.export_scene.fbx(
                filepath=os.path.join(dir, filename),
                check_existing=False,
                use_selection=True,
                use_triangles=True,
                bake_anim=True,
                bake_anim_use_all_bones=True,
                bake_anim_use_nla_strips=False,
                bake_anim_use_all_actions=False,
                path_mode='COPY',
                use_armature_deform_only=True
            )
        elif (self.type == "gltf"):
            directory = os.path.join(os.path.dirname(bpy.data.filepath), "gltf")
            # filename = bpy.path.basename(
            # bpy.data.filepath).split('.')[0]+".gltf"
            filename = context.active_object.users_collection[0].name
            try:
                os.mkdir(directory)
            except OSError as error:
                print("fbx folder exist, skipped")

            
            gltf_options['filepath'] = os.path.join(directory, filename)
            bpy.ops.export_scene.gltf(**gltf_options)
        elif (self.type == "gltf_2"):
            filename = bpy.path.basename(bpy.data.filepath).split('.')[0]
            collection_name = context.active_object.users_collection[0].name
            # object_name = context.active_object.name
            dir_1 = os.path.join(os.path.dirname(bpy.data.filepath), "gltf", filename)
            directory = os.path.join(os.path.dirname(bpy.data.filepath), "gltf", filename, collection_name)
            try:
                os.mkdir(dir_1)
            except OSError as error:
                print("gltf folder exist, skipped")
            gltf_options['filepath'] = directory
            gltf_options['export_colors'] = True
            bpy.ops.export_scene.gltf(**gltf_options)
            
        return {'FINISHED'}

class Btool_render_preview(bpy.types.Operator):
    bl_idname = "btool.render_preview"
    bl_label = "Render preview"

    def execute(self, context: context):
        selected_objects = context.selected_objects
        objects = bpy.data.objects
        hidden = []
        for selected in selected_objects:
            for object in objects:
                if object.type == "MESH" and object.name != selected.name and object.hide_render == False:
                    object.hide_render = True
                    hidden.append(object)
            
            locx = selected.location[0]
            locy = selected.location[1]
            locz = selected.location[2]
            
            selected.location[0] = 0
            selected.location[1] = 0
            selected.location[2] = 0
            
            file_name = selected.name.replace(".", "_")
            
            context.scene.render.filepath = "//preview/"+file_name+".png"
            bpy.ops.render.render(use_viewport=True, write_still=True)
            
            selected.location[0] = locx
            selected.location[1] = locy
            selected.location[2] = locz
            
            for object in hidden:
                object.hide_render = False
            
            hidden = []
        return {'FINISHED'}

classes = (
    Btool_compile,
    Btool_rename_data,
    Btool_rename_data_with_ucupaint,
    Btool_metarig_to_applied,
    Btool_create_cloth_bones,
    Btool_import_mixamo_animations,
    Btool_export,
    Btool_render_preview,
)


def register():
    for c in classes:
        register_class(c)


def unregister():
    for c in classes:
        unregister_class(c)
