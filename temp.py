import bpy

C = bpy.context

def move_uv_up(obj):
    _, active_uv = get_active_render(obj)
    
    uvs = obj.data.uv_layers
    uvs.active = active_uv
    up_index = uvs.active_index - 1

    uvs.active = uvs[up_index]
    zero_name = uvs[up_index].name

    uvs.new(name=zero_name)
    uvs.remove(uvs[up_index])
    uvs[len(uvs)-1].name = zero_name

    idx, _ = get_active_render(obj)

    uvs.active = uvs[idx]
    
    return idx    

def get_active_render(obj):
    uvs = obj.data.uv_layers
    idx = 0
    for uv in uvs:
        if (uv.active_render):
            return idx, uv
        idx += 1

def make_first(obj):
    idx, _ = get_active_render(obj)
    print("processing ", obj.name, " ", idx)
    while idx > 0:
        idx = move_uv_up(obj)
        print(idx)

for obj in C.selected_objects:
    make_first(obj)

def set_rigify_type_selected_bones():
    pose_bones = C.selected_pose_bones

    for bone in pose_bones:
        bone.rigify_type = 'basic.super_copy'
        bone.rigify_parameters.super_copy_widget_type = 'bone'
