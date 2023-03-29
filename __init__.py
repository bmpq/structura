bl_info = {
    "name": "Structura",
    "author": "bmpq",
    "version": (0, 2),
    "location": "View3D > Sidebar > Tools",
    "blender": (3, 0, 0),
    "category": "3D View"
}

import bpy

from . import (
    properties,
    viewport,
    ops_structure,
    ops_collider,
    ops_wireframe,
    ui,
)

classes = [
    properties.STRA_PGT_Structure,
    properties.STRA_PGT_Joint,
    properties.STRA_PGT_Collider,
    properties.STRA_PGT_Viewport,
    properties.STRA_PGT_Wireframe,

    viewport.STRA_OT_Viewport_collider_in_front,
    viewport.STRA_OT_Viewport_collider_selectabe,
    viewport.STRA_OT_Viewport_collider_hide,
    viewport.STRA_OT_Viewport_collider_detect,

    ops_structure.STRA_OT_Generate_Structure,
    ops_structure.STRA_OT_Modify_Structure,
    ops_collider.STRA_OT_Generate_Colliders,
    ops_wireframe.STRA_OT_Generate_Wireframe,

    ui.STRA_PT_Wireframe,
    ui.STRA_PT_Joint,
    ui.STRA_PT_Collider
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.stra_props_structure = bpy.props.PointerProperty(type=properties.STRA_PGT_Structure)
    bpy.types.Scene.stra_props_joint = bpy.props.PointerProperty(type=properties.STRA_PGT_Joint)
    bpy.types.Scene.stra_props_collider = bpy.props.PointerProperty(type=properties.STRA_PGT_Collider)
    bpy.types.Scene.stra_props_viewport = bpy.props.PointerProperty(type=properties.STRA_PGT_Viewport)
    bpy.types.Scene.stra_props_wireframe = bpy.props.PointerProperty(type=properties.STRA_PGT_Wireframe)


def unregister():
   for cls in reversed(classes):
       bpy.utils.unregister_class(cls)

   del bpy.types.Scene.stra_props_structure
   del bpy.types.Scene.stra_props_joint
   del bpy.types.Scene.stra_props_collider
   del bpy.types.Scene.stra_props_viewport
   del bpy.types.Scene.stra_props_wireframe


if __name__ == "__main__":
   register()
