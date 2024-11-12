bl_info = {
    "name": "Structura",
    "author": "bmpq",
    "version": (0, 4, 2),
    "location": "View3D > Sidebar > Tools",
    "blender": (3, 0, 0),
    "category": "3D View"
}

import bpy

from . import (
    properties,
    ops_structure,
    ops_utilities,
    ui,
    utils
)

classes = [
    properties.STRA_PGT_Structure,
    properties.STRA_PGT_Joint,

    ops_structure.STRA_OT_Generate_Structure,
    ops_structure.STRA_OT_Modify_Structure,

    ops_utilities.STRA_OT_Select_Joints,

    ui.STRA_PT_Joint,
    ui.STRA_PT_Utilities
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.stra_props_structure = bpy.props.PointerProperty(type=properties.STRA_PGT_Structure)
    bpy.types.Scene.stra_props_joint = bpy.props.PointerProperty(type=properties.STRA_PGT_Joint)


def unregister():
   for cls in reversed(classes):
       bpy.utils.unregister_class(cls)

   del bpy.types.Scene.stra_props_structure
   del bpy.types.Scene.stra_props_joint


if __name__ == "__main__":
   register()
