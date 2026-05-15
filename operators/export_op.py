import bpy
import os
from bpy import types, ops
from bpy.props import StringProperty


class Btool_export(bpy.types.Operator):
    bl_idname = "btool.export"
    bl_label = "Export File"

    export_type: StringProperty(name="export_type", default="fbx")

    def execute(self, context: types.Context):
        from ..utils import duplicate_rig, restore_rig, fbx_options, gltf_options

        scene = context.scene
        objects = context.selected_objects
        material_names = []
        armatures = []
        for o in objects:
            if o.type == "ARMATURE":
                armatures.append(o)
            for mat in o.material_slots:
                try:
                    material_names.remove(mat.name)
                except ValueError:
                    pass
                material_names.append(mat.name)

        emissionMaterials = {}

        for matname in material_names:
            outputnodename = ""
            material: types.Material = bpy.data.materials[matname]
            node_tree = material.node_tree
            nodes = node_tree.nodes
            unusedoutputs = []
            for node in nodes:
                if node.type == "OUTPUT_MATERIAL":
                    if node.is_active_output is True:
                        outputnodename = node.name
                    else:
                        unusedoutputs.append(node.name)

            for unusedoutput in unusedoutputs:
                try:
                    nodes.remove(nodes[unusedoutput])
                except KeyError:
                    pass

            outputnode = nodes[outputnodename]
            fromnode: types.Node = outputnode.inputs["Surface"].links[0].from_node
            if fromnode.type == "EMISSION":
                nodeprincipled = nodes.new("ShaderNodeBsdfPrincipled")
                nodeprincipled.location = fromnode.location

                colorsource = fromnode.inputs["Color"].links[0].from_socket
                node_tree.links.new(
                    nodeprincipled.inputs["Base Color"], colorsource
                )

                node_tree.links.new(
                    outputnode.inputs["Surface"], nodeprincipled.outputs["BSDF"]
                )
                emissionMaterials[matname] = [
                    outputnodename,
                    fromnode.name,
                    nodeprincipled.name,
                ]

        activeobject = context.active_object
        context.view_layer.objects.active = activeobject

        active_object = duplicate_rig(context)

        if self.export_type == "fbx":
            dir_fbx = os.path.join(
                os.path.dirname(bpy.data.filepath), "fbx"
            )
            try:
                os.mkdir(dir_fbx)
            except OSError:
                pass
            dir = os.path.join(
                dir_fbx,
                context.active_object.users_collection[0].name,
            )
            filename = (
                context.active_object.users_collection[0].name + ".fbx"
            )
            try:
                os.mkdir(dir)
            except OSError:
                pass

            for matname in material_names:
                material: types.Material = bpy.data.materials[matname]
                for node in material.node_tree.nodes:
                    if node.type == "TEX_IMAGE":
                        try:
                            node.image.unpack()
                        except RuntimeError:
                            pass

            fbx_options["filepath"] = os.path.join(dir, filename)
            bpy.ops.export_scene.fbx(**fbx_options)

            for matname in material_names:
                material: types.Material = bpy.data.materials[matname]
                for node in material.node_tree.nodes:
                    if node.type == "TEX_IMAGE":
                        try:
                            node.image.pack()
                        except RuntimeError:
                            pass

        elif self.export_type == "fbx_2":
            dir = os.path.join(os.path.dirname(bpy.data.filepath), "fbx")
            filename = bpy.path.basename(bpy.data.filepath).split(".")[0] + ".fbx"
            try:
                os.mkdir(dir)
            except OSError:
                pass

            bpy.ops.export_scene.fbx(
                filepath=os.path.join(dir, filename),
                check_existing=False,
                use_selection=True,
                use_triangles=True,
                bake_anim=True,
                bake_anim_use_all_bones=True,
                bake_anim_use_nla_strips=False,
                bake_anim_use_all_actions=False,
                path_mode="COPY",
                use_armature_deform_only=True,
            )
        elif self.export_type == "gltf":
            directory = os.path.join(
                os.path.dirname(bpy.data.filepath), "gltf"
            )
            if scene.b_e_export_path != "":
                directory = scene.b_e_export_path
            if scene.b_e_stepping_interpolation is True:
                gltf_options["export_sampling_interpolation_fallback"] = "STEP"
            filename = context.active_object.users_collection[0].name
            try:
                os.mkdir(directory)
            except OSError:
                pass

            gltf_options["filepath"] = os.path.join(directory, filename)
            gltf_options["export_hierarchy_flatten_bones"] = scene.b_e_flatten_h
            bpy.ops.export_scene.gltf(**gltf_options)
        elif self.export_type == "gltf_2":
            filename = bpy.path.basename(bpy.data.filepath).split(".")[0]
            collection_name = context.active_object.users_collection[0].name
            dir_1 = os.path.join(
                os.path.dirname(bpy.data.filepath), "gltf", filename
            )
            directory = os.path.join(
                os.path.dirname(bpy.data.filepath),
                "gltf",
                filename,
                collection_name,
            )
            try:
                os.mkdir(dir_1)
            except OSError:
                pass
            gltf_options["filepath"] = directory
            bpy.ops.export_scene.gltf(**gltf_options)

        for key in emissionMaterials.keys():
            materials = bpy.data.materials
            node_tree: types.NodeTree = materials[key].node_tree
            nodes = node_tree.nodes
            outputnode: types.Node = nodes[emissionMaterials[key][0]]
            emissionnode: types.Node = nodes[emissionMaterials[key][1]]
            principlednode: types.Node = nodes[emissionMaterials[key][2]]

            node_tree.links.new(
                outputnode.inputs["Surface"], emissionnode.outputs["Emission"]
            )
            nodes.remove(principlednode)

        restore_rig(context)
        context.view_layer.objects.active = active_object

        return {"FINISHED"}
