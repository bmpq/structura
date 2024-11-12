import bpy
from bpy.types import Panel, Operator, PropertyGroup
from . import utils, ops_structure
import bmesh


class STRA_PT_Joint(Panel):
    bl_idname = "STRA_PT_Joint"
    bl_label = "Create joints"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Structura"
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout
        props_structure = context.scene.stra_props_structure
        props_joint = context.scene.stra_props_joint

        col_joints = utils.get_collection_joints(False)

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

        layout.separator(factor=1)
        r = layout.row()
        r.scale_y = 0.5
        r.label(text='Generation mode:')
        layout.prop(props_structure, "mode", expand=True)
        layout.separator(factor=1.8)

        r = layout.row()
        c1 = r.column()
        c2 = r.column()
        c1.label(text='Joint type:')
        c2.prop(props_joint, "type", text="")
        if props_joint.type == 'GENERIC':
            r = layout.row()
            r.prop(props_joint, "leeway_linear")
            r.prop(props_joint, "leeway_angular")
        layout.prop(props_joint, "use_local_collisions")

        layout.prop(props_joint, "break_threshold", )
        if props_structure.mode == "EXACT":
            layout.prop(props_joint, "use_overlap_volume")

        if col_joints is not None and len(col_joints.objects) > 0:
            r = layout.row()
            r.scale_y = 2
            r.operator("stra.structure_modify", icon='MOD_NORMALEDIT', text=f'Apply to joints of selected objects')

        layout.separator(factor=2)

        layout.prop(props_structure, "overlap_margin")

        if props_structure.mode == "EXACT":
            layout.prop(props_structure, "min_overlap_threshold")

        layout.separator(factor=0.1)
        r = layout.row()
        r.scale_y = 0.5
        r.label(text="Existing joint behaviour:")
        layout.prop(props_structure, "existing_joint_behaviour", text="")

        if props_structure.progress > 0.0 and props_structure.progress < 1.0:
            r = layout.row()
            r.label(text=f"Progress: {props_structure.progress*100:.2f}%")

        if mesh_amount > 1:
            r = layout.row()
            r.scale_y = 2
            txt_button = f'Generate between {mesh_amount} objects'
            r.operator("stra.structure_generate", icon='MOD_MESHDEFORM', text=txt_button)



class STRA_PT_Utilities(Panel):
    bl_idname = "STRA_PT_Utilities"
    bl_label = "Utilities"
    bl_category = "Structura"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        amount_selected_meshes = 0
        joints = []
        for ob in context.selected_objects:
            if ob.type == 'MESH':
                amount_selected_meshes += 1
                if ob.get("joints"):
                    for name in ob["joints"]:
                        if name not in joints:
                            joints.append(name)
        layout.label(text=f'{amount_selected_meshes} selected meshes')
        layout.label(text=f'with {len(joints)} joints')

        r = layout.row()
        r.operator("stra.utils_select_joints", icon='ACTION_TWEAK', text="Select joints", )
        r.enabled = len(joints) > 0