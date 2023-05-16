bl_info = {
    "name": "Structura",
    "author": "bmpq",
    "version": (0, 3),
    "location": "View3D > Sidebar > Tools",
    "blender": (3, 0, 0),
    "category": "3D View"
}

import bpy

from . import (
    properties,
    ops_structure,
    ops_collider,
    ui,
)

classes = [
    properties.STRA_PGT_Structure,
    properties.STRA_PGT_Joint,
    properties.STRA_PGT_Collider,

    ops_structure.STRA_OT_Generate_Structure,
    ops_structure.STRA_OT_Modify_Structure,
    ops_collider.STRA_OT_Generate_Colliders,
    ops_collider.STRA_OT_Select_Collection,
    ops_collider.STRA_OT_Detect_Collisions,
    ops_collider.STRA_OT_Calculate_Mass,

    ui.STRA_PT_Joint,
    ui.STRA_PT_Collider
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.stra_props_structure = bpy.props.PointerProperty(type=properties.STRA_PGT_Structure)
    bpy.types.Scene.stra_props_joint = bpy.props.PointerProperty(type=properties.STRA_PGT_Joint)
    bpy.types.Scene.stra_props_collider = bpy.props.PointerProperty(type=properties.STRA_PGT_Collider)


def unregister():
   for cls in reversed(classes):
       bpy.utils.unregister_class(cls)

   del bpy.types.Scene.stra_props_structure
   del bpy.types.Scene.stra_props_joint
   del bpy.types.Scene.stra_props_collider


if __name__ == "__main__":
   register()
