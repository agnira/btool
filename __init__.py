bl_info = {
    "name" : "Btool",
    "author" : "Agni Rakai Sahakarya",
    "description" : "",
    "blender" : (3, 3, 0),
    "version" : (0, 0, 1),
    "location" : "",
    "warning" : "",
    "category" : "Object"
}

if "bpy" in locals():
    import imp
    imp.reload(ui_operator)
    imp.reload(ui)
else:
    from . import ui, ui_operator

import bpy

def register():
    ui_operator.register()
    ui.register()
    pass

def unregister():
    ui_operator.unregister()
    ui.unregister()
    pass

if __name__ == "__main__":
    register()