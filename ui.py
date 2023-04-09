import bpy
from bpy.types import Panel, Operator, PropertyGroup
from . import utils, ops_structure
import bmesh


class STRA_PT_Wireframe(Panel):
    bl_idname = "STRA_PT_Wireframe"
    bl_label = "Wireframe generator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Structura"
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout
        props = context.scene.stra_props_wireframe

        edges = 0

        for ob in context.selected_objects:
            if 'STRA_EDGE' in ob.name:
                layout.label(text='Generated edge selected')
                return
            if ob.type == 'MESH':
                if 'STRA_COLLIDER' in ob.name:
                    ob = ob.parent
                bm = bmesh.new()
                bm.from_mesh(ob.data)
                bm.edges.ensure_lookup_table()
                for edge in bm.edges:
                    edges += 1

        layout.label(text=f'Selected edges: {edges}')

        if edges == 0:
            return

        layout.prop(props, "prune")
        layout.prop(props, "thickness")

        txt_gen = f'Generate {edges} edge objects'

        if len(context.selected_objects) == 1:
            ob = context.selected_objects[0]
            for col in bpy.data.collections:
                if (ob.name + '_STRA_WIREFRAME') in col.name:
                    txt_gen = f'Regenerate {edges} edge objects'
                    break

        r = layout.row()
        r.scale_y = 2
        r.operator("stra.wireframe_generate", icon="MOD_WIREFRAME", text=txt_gen)


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


        col_joints = utils.get_collection_joints(context)
        generated = len(col_joints.objects) > 0

        mesh_amount = 0
        for ob in context.selected_objects:
            if ob.type != 'MESH':
                continue
            if 'STRA_COLLIDER' in ob.name:
                continue
            mesh_amount += 1

        layout.label(text=f'{mesh_amount} mesh object(s) selected')

        if mesh_amount < 2:
            return

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
        layout.prop(props_structure, "subd", text='Overlap detection accuracy')

        if mesh_amount > 1:
            r = layout.row()
            r.scale_y = 2
            if props_structure.progress > 0.0 and props_structure.progress < 1.0:
                r.label(text=f"Progress: {props_structure.progress*100:.2f}%")
            txt_button = f'Regenerate between {mesh_amount} objects' if joint_amount > 0 else f'Generate between {mesh_amount} objects'
            r.operator("stra.structure_generate", icon='MOD_MESHDEFORM', text=txt_button)


class STRA_PT_Collider(Panel):
    bl_idname = "STRA_PT_Collider"
    bl_label = "Colliders"
    bl_category = "Structura"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout
        props_collider = context.scene.stra_props_collider

        mesh_amount = 0
        rb_amount = 0
        rb_shapes = bpy.types.RigidBodyObject.bl_rna.properties["collision_shape"].enum_items
        sh_amount = dict.fromkeys(rb_shapes, 0)
        for ob in context.selected_objects:
            if ob.type == 'MESH':
                if 'STRA_COLLIDER' in ob.name:
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

        layout.operator("stra.collection_select_objects", icon='RESTRICT_SELECT_OFF')
        r = layout.row()
        r.label(text=f'Collider shapes in')
        r = layout.row()
        r.scale_y = 0.5
        r.label(text=f'{mesh_amount} selected object(s):')

        if mesh_amount == 0:
            return

        b = layout.box()
        b.active = False
        for sh in sh_amount:
            if sh_amount[sh] == 0:
                continue
            utils.draw_list_entry(b, sh.name, sh_amount[sh])
        if mesh_amount > rb_amount:
            utils.draw_list_entry(b, '[No rigid body]', str(mesh_amount - rb_amount))

        layout.separator(factor=1)

        layout.prop(props_collider, property="shape", text="Collider shape")
        if props_collider.shape == 'COMPOUND':
            layout.prop(props_collider, "scale")
            layout.prop(props_collider, "voxel_size")

        r = layout.row()
        r.scale_y = 2
        if props_collider.progress > 0.0 and props_collider.progress < 1.0:
            r.label(text=f"Progress: {props_collider.progress*100:.2f}%")
        else:
            txt = f'Generate colliders for {mesh_amount} object(s)' if props_collider.shape == 'COMPOUND' else f'Set to {props_collider.shape} for {mesh_amount} object(s)'
            if rb_amount < mesh_amount:
                txt = f'Add rigid body to {mesh_amount - rb_amount} object(s)'
            r.operator("stra.collider_generate", icon='MESH_ICOSPHERE', text=txt)