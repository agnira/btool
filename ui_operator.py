from bpy import types, context, ops, data
from bpy.types import Collection
from bpy.utils import register_class, unregister_class


def unselect_object():
    for o in data.objects:
        o.select_set(False)


class Teamtool_compile(types.Operator):
    bl_idname = "teamtool.compiler_compile"
    bl_label = "Compile"

    def execute(self, context: context):
        found: Collection = None
        for c in context.scene.collection.children_recursive:
            if (c.name == "COMPILED"):
                found = c

        if (found == None):
            found = data.collections.new("COMPILED")
            context.collection.children.link(found)

        for c in context.scene.collection.children_recursive:
            if (c.hide_render == False):
                if (c.name != "COMPILED"):
                    dup_name_list = []
                    o:types.Object
                    for o in c.objects:
                        if (o.hide_render == False):
                            dup_obj = o.copy()
                            dup_obj.data = o.data.copy()
                            found.objects.link(dup_obj)
                            dup_name_list.append(dup_obj.name)
                    unselect_object()
                    for n in dup_name_list:
                        data.objects[n].select_set(True)
                    if (len(dup_name_list) > 0):
                        context.view_layer.objects.active = data.objects[dup_name_list[0]]
                        ops.object.convert(target='MESH')
                        ops.object.join()
                        context.active_object.name = c.name
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
                            ops.object.vertex_group_remove(all=True)
                        c.hide_viewport = True

        return {'FINISHED'}


classes = (
    Teamtool_compile,
)


def register():
    for c in classes:
        register_class(c)


def unregister():
    for c in classes:
        unregister_class(c)
