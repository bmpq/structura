import bpy
from bpy.types import Operator
from . import utils


class STRA_OT_Select_Joints(Operator):
    bl_idname = "stra.utils_select_joints"
    bl_label = "Select joints"
    bl_options = {"UNDO_GROUPED"}

    def execute(self, context):
        col_joints = utils.get_collection_joints()

        joint_objs_to_select = []

        for ob in context.selected_objects:
            if ob.type != 'MESH':
                continue
            if not ob.get("joints"):
                continue

            for name in ob["joints"][:]:
                joint_obj = col_joints.objects.get(name)
                if joint_obj is None:
                    utils.remove_joint_from_property(ob, name)
                elif joint_obj not in joint_objs_to_select:
                    joint_objs_to_select.append(joint_obj)

        bpy.ops.object.select_all(action='DESELECT')

        first_item = True
        for joint_obj in joint_objs_to_select:
            joint_obj.select_set(True)
            if first_item:
                first_item = False
                bpy.context.view_layer.objects.active = joint_obj

        return {'FINISHED'}