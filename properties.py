import bpy
from bpy.types import PropertyGroup
from . import utils


class STRA_PGT_Structure(PropertyGroup):
    skip_volume: bpy.props.BoolProperty(
        name="Skip volume calculation",
        description="Faster but approximates the joint location. Not recommended",
        default=False
    )
    use_overlap_margin: bpy.props.BoolProperty(
        name="Overlap margin",
        default=True
    )
    overlap_margin: bpy.props.FloatProperty(
        name="Overlap margin",
        soft_min=0,
        soft_max=10,
        default=0.002,
        precision=3,
        step=1
    )
    min_overlap_threshold: bpy.props.FloatProperty(
        name="Min overlap volume",
        min=0,
        soft_max=10,
        default=0,
        precision=3,
        step=1
    )
    overwrite: bpy.props.BoolProperty(
        name="Overwrite",
        default=True
    )
    skip_check_existing_joints: bpy.props.BoolProperty(
        name="Skip checking existing joints",
        default=False,
        description="Helps performance when there is high amount of existing joints on the scene (>10k)"
    )
    progress: bpy.props.FloatProperty(
        name="Progress",
        min=0.0,
        max=1.0,
        default=0.0
    )


class STRA_PGT_Joint(PropertyGroup):
    constraint_types = []
    constraint_types.append(('FIXED', 'Fixed', 'Glueing objects together'))
    constraint_types.append(('POINT', 'Ball', 'Jointed objects can rotate around the joint freely'))
    constraint_types.append(('GENERIC', 'Elastic', 'Joints with elbow room'))

    type: bpy.props.EnumProperty(
        items=constraint_types
    )
    use_local_collisions: bpy.props.BoolProperty(
        name="Enable local collisions",
        default=True,
        description='Enable collisions between jointed objects'
    )
    use_overlap_volume: bpy.props.BoolProperty(
        name="Multiply break threshold by overlap volume",
        default=True
    )
    break_threshold: bpy.props.FloatProperty(
        name="Break threshold",
        min=0.0,
        soft_max=10000.0,
        default=5
    )
    leeway_linear: bpy.props.FloatProperty(
        name="Linear range",
        min=0.0,
        soft_max=1.0,
        default=0.01,
    )
    leeway_angular: bpy.props.FloatProperty(
        name="Angular range",
        min=0.0,
        soft_max=180.0,
        default=1
    )


class STRA_PGT_Collider(PropertyGroup):
    rb_shapes = []
    rb_shapes.append(('CONVEX', 'Convex Hull', ''))
    rb_shapes.append(('VOXEL', 'Remesh Voxel', ''))
    shape: bpy.props.EnumProperty(
        items=rb_shapes
    )
    scale_global: bpy.props.FloatVectorProperty(
        name='Scale (object local axis)', subtype='XYZ',
        default=(1.0, 1.0, 1.0),
        precision=4,
        step=1
    )
    scale_custom: bpy.props.FloatVectorProperty(
        name='Scale (mesh calculated axis)', subtype='XYZ',
        description='The custom axis is derived from the vertices that are the furthest apart from each other',
        default=(1.0, 1.0, 1.0),
        precision=4,
        step=1
    )
    voxel_size: bpy.props.FloatProperty(
        name='Voxel size',
        min=0.01,
        default=0.1
    )
    progress: bpy.props.FloatProperty(
        name='Progress',
        default=0
    )
    density: bpy.props.FloatProperty(
        name='Density',
        default=2600,
        step=100
    )