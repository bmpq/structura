import bpy
from bpy.types import PropertyGroup


class STRA_PGT_Viewport(PropertyGroup):
    hide: bpy.props.BoolProperty(
        name="Toggle collider viewport and render visibility",
        default=False
    )
    selectable: bpy.props.BoolProperty(
        name="Toggle selectable in viewport",
        default=False
    )
    show_in_front: bpy.props.BoolProperty(
        name="Toggle in front",
        default=True
    )


class STRA_PGT_Structure(PropertyGroup):
    use_overlap_margin: bpy.props.BoolProperty(
        name="Overlap margin"
    )
    overlap_margin: bpy.props.FloatProperty(
        name="Overlap margin",
        min=0,
        max=10,
        default=0.0
    )
    subd: bpy.props.IntProperty(
        name="Subdivision cuts",
        description='The accuracy of finding overlap points, useful for low poly meshes',
        min=0,
        max=100,
        default=4
    )
    progress: bpy.props.FloatProperty(
        name="Progress",
        min=0.0,
        max=1.0,
        default=0.0
    )


class STRA_PGT_Joint(PropertyGroup):
    constraint_types = bpy.types.RigidBodyConstraint.bl_rna.properties["type"].enum_items
    type: bpy.props.EnumProperty(
        items=[(item.identifier, item.name, item.description) for item in constraint_types]
    )
    use_local_collisions: bpy.props.BoolProperty(
        name="Enable local collisions",
        default=False
    )
    break_threshold: bpy.props.FloatProperty(
        name="Break threshold",
        min=0.0,
        max=1000.0,
        default=40
    )
    leeway_linear: bpy.props.FloatProperty(
        name="Linear range",
        min=0.0,
        max=1.0,
        default=0.01,
    )
    leeway_angular: bpy.props.FloatProperty(
        name="Angular range",
        min=0.0,
        max=10.0,
        default=1
    )


class STRA_PGT_Collider(PropertyGroup):
    rb_shapes = bpy.types.RigidBodyObject.bl_rna.properties["collision_shape"].enum_items
    shape: bpy.props.EnumProperty(
        items=[(item.identifier, item.name, item.description) for item in rb_shapes]
    )
    scale: bpy.props.FloatVectorProperty(
        name='Scale', subtype='XYZ',
        default=(1.0, 1.0, 1.0),
        min= 0.0,
        max = 2.0
    )
    voxel_size: bpy.props.FloatProperty(
        name='Voxel size',
        min=0.01,
        default=0.04
    )
    progress: bpy.props.FloatProperty(
        name='Progress',
        default=0
    )