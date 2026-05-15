bl_info = {
    "name": "Btool",
    "author": "Agni Rakai Sahakarya",
    "description": "Banaspateam internal workflow automation tools for Blender",
    "blender": (4, 2, 0),
    "version": (1, 2, 7),
    "location": "View3D > Sidebar > Tool > BNSPT",
    "warning": "",
    "category": "Object",
}

if "bpy" in locals():
    import importlib
    importlib.reload(utils)
    importlib.reload(operators)
    importlib.reload(ui)
else:
    from . import utils, operators, ui

import bpy


def register():
    operators.register()
    ui.register()


def unregister():
    operators.unregister()
    ui.unregister()


if __name__ == "__main__":
    register()
