import bpy
from bpy.types import Panel, Operator, PropertyGroup
from . import utils


class STRA_PT_Panel(Panel):
    bl_idname = "OBJECT_PT_structura_panel"
    bl_label = "Structura"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Structura"

    def draw(self, context):
        layout = self.layout
        props_structure = context.scene.stra_props_structure
        props_collider = context.scene.stra_props_collider
        props_joint = context.scene.stra_props_joint
        props_viewport = context.scene.stra_props_viewport

        col_selected = context.collection
        if 'joints' in col_selected.name:
            col_selected = utils.get_parent_collection(col_selected)

        col_joints = col_selected.children.get(col_selected.name + '_joints')
        generated = col_joints is not None and len(col_joints.objects) > 0

        r = layout.row()
        r.operator("stra.viewport_collider_hide",
                   icon='HIDE_ON' if props_viewport.hide else 'HIDE_OFF', text='')
        r.operator("stra.viewport_collider_selectable",
                   icon='RESTRICT_SELECT_OFF' if props_viewport.selectable else 'RESTRICT_SELECT_ON', text='')
        r.operator("stra.viewport_collider_show_in_front",
                   icon='XRAY' if props_viewport.show_in_front else 'CUBE', text='')
        r.operator("stra.viewport_collider_detect", icon='ALIGN_LEFT', text='')

        layout.separator(factor=2)

        if col_selected == context.scene.collection:
            layout.label(text='Scene collection selected')
            return

        if generated:
            layout.label(text=f'{len(col_joints.objects)} generated joint constraints')
        layout.prop(props_joint, "type", text="Constraint type")
        if props_joint.type == 'GENERIC':
            r = layout.row()
            r.prop(props_joint, "leeway_linear")
            r.prop(props_joint, "leeway_angular")
        layout.prop(props_joint, "use_local_collisions")
        layout.prop(props_joint, "break_threshold")

        layout.separator(factor=2)

        mesh_amount = 0
        for ob in col_selected.objects:
            if ob.type != 'MESH':
                continue
            if 'collider' in ob.name:
                continue
            mesh_amount += 1

        layout.label(text=f'{mesh_amount} mesh objects in [{col_selected.name}]')

        layout.prop(props_structure, "use_overlap_margin")
        if props_structure.use_overlap_margin:
            layout.prop(props_structure, "overlap_margin")
        layout.prop(props_structure, "subd")

        if props_structure.progress > 0.0 and props_structure.progress < 1.0:
            layout.label(text=f"Progress: {props_structure.progress*100:.2f}%")
        else:
            layout.operator("stra.structure_generate", icon='MOD_MESHDEFORM')

        if len(context.selected_objects) == 0:
            return

        layout.separator(factor=2)

        mesh_amount = 0
        rb_amount = 0
        rb_shapes = bpy.types.RigidBodyObject.bl_rna.properties["collision_shape"].enum_items
        sh_amount = dict.fromkeys(rb_shapes, 0)
        for ob in context.selected_objects:
            if ob.type == 'MESH':
                if 'collider' in ob.name:
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

        if mesh_amount == 0:
            return

        layout.label(text=f'{mesh_amount} mesh selected ({rb_amount} RB)')

        b = layout.box()
        for sh in sh_amount:
            if sh_amount[sh] == 0:
                continue
            r = b.row()
            r.scale_y = 0.7
            c1 = r.column()
            c1.alignment = 'LEFT'
            c1.label(text=f'{sh.name}')

            c2 = r.column()
            c2.alignment = 'RIGHT'
            c2.label(text=f'{sh_amount[sh]}')

        layout.prop(props_collider, property="shape", text="Collider shape")
        if props_collider.shape == 'COMPOUND':
            layout.prop(props_collider, "scale")
            layout.prop(props_collider, "voxel_size")

        if props_collider.progress > 0.0 and props_collider.progress < 1.0:
            layout.label(text=f"Progress: {props_collider.progress*100:.2f}%")
        else:
            layout.operator("stra.collider_generate", icon='RIGID_BODY')
