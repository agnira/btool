import bpy, os
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
        for o in context.selectable_objects:
            o.data.name = o.name
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
        marked_edges = [edge for edge in cloth_mesh.data.edges if edge.use_edge_sharp]
        for edge in marked_edges:
            vertex_1 = cloth_mesh.data.vertices[edge.vertices[0]].co
            vertex_2 = cloth_mesh.data.vertices[edge.vertices[1]].co
            if vertex_1 not in points:
                points.append(vertex_1)
            if vertex_2 not in points:
                points.append(vertex_2)
        ops.object.armature_add(enter_editmode=True, align='WORLD', location=(0, 0, 0))
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
                    mixamoTarget.animation_data.action.name = file.name.split(".")[0]
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

classes = (
    Btool_compile,
    Btool_rename_data,
    Btool_metarig_to_applied,
    Btool_create_cloth_bones,
    Btool_import_mixamo_animations,
)


def register():
    for c in classes:
        register_class(c)


def unregister():
    for c in classes:
        unregister_class(c)
