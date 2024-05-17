import bpy
from bpy.types import PropertyGroup
from . import utils


class STRA_PGT_Structure(PropertyGroup):
    existing_joint_behaviour_choice = []
    existing_joint_behaviour_choice.append(('OVERWRITE', 'Overwrite', 'If there is already a joint between objects, delete it and calculate again'))
    existing_joint_behaviour_choice.append(('NEWONLY', 'New only', 'If there is already a joint between objects, don\'t create a new one'))
    existing_joint_behaviour_choice.append(('NOCHECK', 'Skip checking completely', 'Allow the possibility of duplicate joints between objects. Improves performance when there is a high amount of joints on the scene'))

    skip_volume: bpy.props.BoolProperty(
        name="Skip overlap volume calculation",
        description="Faster but approximates the joint location by just putting it at the midpoint between objects",
        default=False
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
        step=1,
        description="Don't create joint if the overlap between 2 objects is smaller than this value."
    )
    existing_joint_behaviour: bpy.props.EnumProperty(
        name="Existing joint behaviour",
        items=existing_joint_behaviour_choice
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
        name="Joint type",
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
        default=500
    )
    leeway_linear: bpy.props.FloatProperty(
        name="Linear range",
        min=0.0,
        soft_max=1.0,
        default=0.0,
    )
    leeway_angular: bpy.props.FloatProperty(
        name="Angular range",
        min=0.0,
        soft_max=180.0,
        default=0.1
    )