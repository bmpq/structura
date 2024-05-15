import bpy
from bpy.types import Panel, Operator, PropertyGroup
from . import utils, ops_structure
import bmesh


class STRA_PT_Joint(Panel):
    bl_idname = "STRA_PT_Joint"
    bl_label = "Joints"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Structura"
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout
        props_structure = context.scene.stra_props_structure
        props_joint = context.scene.stra_props_joint

        col_joints = utils.get_collection_joints(False)
        generated = col_joints is not None and len(col_joints.objects) > 0

        all_objects_have_rigidbody = True
        mesh_amount = 0
        for ob in context.selected_objects:
            if ob.rigid_body is None:
                all_objects_have_rigidbody = False
            if ob.type != 'MESH':
                continue
            if utils.OBJNAME_COLLIDER in ob.name:
                continue
            mesh_amount += 1

        layout.label(text=f'{mesh_amount} mesh object(s) selected')

        if mesh_amount < 2:
            layout.label(text=f'(Select at least 2 mesh objects)')
            return

        if not all_objects_have_rigidbody:
            layout.label(text=f'(Not all selected objects have rigid body)')
            return

        layout.prop(props_structure, "skip_volume")
        r = layout.row()
        c1 = r.column()
        c2 = r.column()
        c1.label(text='Joint type')
        c2.prop(props_joint, "type", text="")
        if props_joint.type == 'GENERIC':
            r = layout.row()
            r.prop(props_joint, "leeway_linear")
            r.prop(props_joint, "leeway_angular")
        layout.prop(props_joint, "use_local_collisions")

        if not props_structure.skip_volume:
            layout.prop(props_joint, "use_overlap_volume")
        layout.prop(props_joint, "break_threshold")

        joint_amount = 0
        if generated:
            for ob1 in context.selected_objects:
                if ob1.rigid_body is None:
                    continue
                joints = ops_structure.get_joints_by_rb(ob1, col_joints)
                if len(joints) == 0:
                    continue
                joint_amount += 1
                break

        if joint_amount > 0:
            r = layout.row()
            r.scale_y = 2
            r.operator("stra.structure_modify", icon='MOD_NORMALEDIT', text=f'Apply to joints of selected objects')

        layout.separator(factor=1)

        layout.prop(props_structure, "use_overlap_margin", text='Use overlap margin')
        if props_structure.use_overlap_margin:
            layout.prop(props_structure, "overlap_margin")

        if not props_structure.skip_volume:
            layout.prop(props_structure, "min_overlap_threshold")

        if props_structure.progress > 0.0 and props_structure.progress < 1.0:
            r = layout.row()
            r.label(text=f"Progress: {props_structure.progress*100:.2f}%")

        layout.prop(props_structure, "overwrite")

        if not props_structure.overwrite:
            layout.prop(props_structure, "skip_check_existing_joints")

        if mesh_amount > 1:
            r = layout.row()
            r.scale_y = 2
            txt_button = f'Generate between {mesh_amount} objects'
            r.operator("stra.structure_generate", icon='MOD_MESHDEFORM', text=txt_button)


class STRA_PT_Collider(Panel):
    bl_idname = "STRA_PT_Collider"
    bl_label = "Custom colliders"
    bl_category = "Structura"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props_collider = context.scene.stra_props_collider

        mesh_amount = 0
        rb_amount = 0
        rb_shapes = bpy.types.RigidBodyObject.bl_rna.properties["collision_shape"].enum_items
        sh_amount = dict.fromkeys(rb_shapes, 0)
        for ob in context.selected_objects:
            if ob.type == 'MESH':
                if utils.OBJNAME_COLLIDER in ob.name:
                    ob = ob.parent
                mesh_amount += 1
                rb = ob.rigid_body
                if rb is None:
                    continue
                rb_amount += 1
                for sh in rb_shapes:
                    if sh.identifier == ob.rigid_body.collision_shape:
                        sh_amount[sh] += 1
                        break

        col_colliders = utils.get_collection_colliders(False)
        if col_colliders is not None and len(col_colliders.objects) > 1:
            layout.operator("stra.collider_detect", icon='SELECT_DIFFERENCE')

        r = layout.row()
        r.label(text=f'{mesh_amount} selected object(s)')

        if mesh_amount == 0:
            return

        layout.prop(props_collider, property="shape", text="Collider shape")
        layout.prop(props_collider, "scale_global")
        layout.prop(props_collider, "scale_custom")
        if props_collider.shape == 'VOXEL':
            layout.prop(props_collider, "voxel_size")

        r = layout.row()
        r.scale_y = 2
        if props_collider.progress > 0.0 and props_collider.progress < 1.0:
            r.label(text=f"Progress: {props_collider.progress*100:.2f}%")
        else:
            txt = f'Generate colliders for {mesh_amount} object(s)'
            r.operator("stra.collider_generate", icon='MESH_ICOSPHERE', text=txt)

        layout.separator(factor=1)

        layout.prop(props_collider, "density")

        r = layout.row()
        r.scale_y = 2
        txt = f'Calculate mass for {mesh_amount} object(s)'
        r.operator("stra.calculate_mass", icon='PHYSICS', text=txt)
