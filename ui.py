import bpy
from bpy.types import Panel, Operator, PropertyGroup
from . import utils
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
        props_viewport = context.scene.stra_props_viewport_joint

        generated_joints_on_scene = False
        for ob in context.scene.objects:
            if 'STRA_JOINT' in ob.name:
                generated_joints_on_scene = True
                break

        if generated_joints_on_scene:
            b = layout.box()
            r = b.row()
            args = r.operator("stra.viewport_toggle", icon='HIDE_ON' if props_viewport.hide else 'HIDE_OFF', text='')
            args.obname = 'STRA_JOINT'
            args.propname = 'VISIBLE'
            args.state = not props_viewport.hide

            args = r.operator("stra.viewport_toggle", icon='RESTRICT_SELECT_OFF' if props_viewport.selectable else 'RESTRICT_SELECT_ON', text='')
            args.obname = 'STRA_JOINT'
            args.propname = 'SELECTABLE'
            args.state = not props_viewport.selectable

            args = r.operator("stra.viewport_toggle", icon='XRAY' if props_viewport.show_in_front else 'MATCUBE', text='')
            args.obname = 'STRA_JOINT'
            args.propname = 'INFRONT'
            args.state = not props_viewport.show_in_front

        col_selected = context.collection
        if 'STRA_JOINTS' in col_selected.name:
            col_selected = utils.get_parent_collection(col_selected)

        col_joints = col_selected.children.get(col_selected.name + '_STRA_JOINTS')
        generated = col_joints is not None and len(col_joints.objects) > 0

        if col_selected == context.scene.collection:
            r = layout.row()
            r.alert = True
            r.label(text='Scene collection selected')
            return

        mesh_amount = 0
        for ob in col_selected.objects:
            if ob.type != 'MESH':
                continue
            if 'STRA_COLLIDER' in ob.name:
                continue
            mesh_amount += 1

        layout.label(text=f'{mesh_amount} mesh object(s) in [{col_selected.name}]')

        if mesh_amount < 2:
            return

        if generated:
            layout.label(text=f'{len(col_joints.objects)} generated joint constraints')

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

        if generated:
            r = layout.row()
            r.scale_y = 2
            r.operator("stra.structure_modify", icon='MOD_NORMALEDIT', text=f'Apply to {len(col_joints.objects)} joint(s)')

        layout.separator(factor=1)

        layout.prop(props_structure, "use_overlap_margin", text='Use overlap margin (slower)')
        if props_structure.use_overlap_margin:
            layout.prop(props_structure, "overlap_margin")
        layout.prop(props_structure, "subd", text='Overlap detection accuracy')

        r = layout.row()
        r.scale_y = 2
        if props_structure.progress > 0.0 and props_structure.progress < 1.0:
            r.label(text=f"Progress: {props_structure.progress*100:.2f}%")
        txt_button = 'Regenerate joints and apply' if generated else f'Generate between {mesh_amount} objects'
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
        props_viewport = context.scene.stra_props_viewport_collider

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

        using_custom_colliders = False
        for ob in context.scene.objects:
            if ob.rigid_body:
                if ob.rigid_body.collision_shape == 'COMPOUND':
                    using_custom_colliders = True
                    break

        if using_custom_colliders:
            b = layout.box()
            r = b.row()
            args = r.operator("stra.viewport_toggle", icon='HIDE_ON' if props_viewport.hide else 'HIDE_OFF', text='')
            args.obname = 'STRA_COLLIDER'
            args.propname = 'VISIBLE'
            args.state = not props_viewport.hide

            args = r.operator("stra.viewport_toggle", icon='RESTRICT_SELECT_OFF' if props_viewport.selectable else 'RESTRICT_SELECT_ON', text='')
            args.obname = 'STRA_COLLIDER'
            args.propname = 'SELECTABLE'
            args.state = not props_viewport.selectable

            args = r.operator("stra.viewport_toggle", icon='XRAY' if props_viewport.show_in_front else 'MATCUBE', text='')
            args.obname = 'STRA_COLLIDER'
            args.propname = 'INFRONT'
            args.state = not props_viewport.show_in_front

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