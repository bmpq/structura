import bpy
from bpy.types import Operator

import bmesh
import math
from mathutils.bvhtree import BVHTree
from mathutils import Vector
from . import utils
import time

def modify_const(ob, props):
    rbc = ob.rigid_body_constraint
    rbc.type = props.type
    rbc.disable_collisions = not props.use_local_collisions
    rbc.use_breaking = True
    rbc.breaking_threshold = props.break_threshold

    if props.use_overlap_volume:
        rbc.breaking_threshold *= ob['intersection_volume']

    ang_max = math.radians(props.leeway_angular)
    lin_max = props.leeway_linear

    rbc.use_limit_ang_x = True
    rbc.limit_ang_x_lower = -ang_max
    rbc.limit_ang_x_upper = ang_max
    rbc.use_limit_ang_y = True
    rbc.limit_ang_y_lower = -ang_max
    rbc.limit_ang_y_upper = ang_max
    rbc.use_limit_ang_z = True
    rbc.limit_ang_z_lower = -ang_max
    rbc.limit_ang_z_upper = ang_max

    rbc.use_limit_lin_x = True
    rbc.limit_lin_x_lower = -lin_max
    rbc.limit_lin_x_upper = lin_max
    rbc.use_limit_lin_y = True
    rbc.limit_lin_y_lower = -lin_max
    rbc.limit_lin_y_upper = lin_max
    rbc.use_limit_lin_z = True
    rbc.limit_lin_z_lower = -lin_max
    rbc.limit_lin_z_upper = lin_max


def get_bvh(objects, overlap_margin):
    trees = []
    for obj in objects:
        if obj.type != 'MESH':
            continue
        if utils.OBJNAME_COLLIDER in obj.name:
            continue

        bm = bmesh.new()
        bm.from_mesh(obj.data)

        if len(bm.verts) == 0:
            print('todo remove empty mesh objects')
            continue

        bmesh.ops.transform(bm, matrix=obj.matrix_world, verts=bm.verts)

        if overlap_margin != 0.0:
            bmesh.ops.solidify(bm, geom=bm.faces, thickness=-overlap_margin / 4)

        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        tree = BVHTree.FromBMesh(bm)
        trees.append((tree, (obj, bm)))

        bm.free()

    return trees


def get_joints_by_rb(obj_rb, col_joints):
    joint_objs = []

    if "joints" not in obj_rb:
        return joint_objs

    for name in obj_rb["joints"]:
        joint_obj = col_joints.objects.get(name)
        if joint_obj is not None:
            joint_objs.append(joint_obj)

    return joint_objs


def store_joint_reference(obj1, joint):
    if "joints" in obj1:
        joints = obj1["joints"]
        if isinstance(joints, list):
            if joint.name not in joints:
                joints.append(joint.name)
        else:
            joints = [joint.name]
    else:
        joints = [joint.name]
    obj1["joints"] = joints


def create_joint(col_joints, obj1, obj2, loc, volume):
    if len(col_joints.objects) == 0:
        empty = bpy.data.objects.new(utils.OBJNAME_JOINT, None)
        col_joints.objects.link(empty)
        bpy.context.view_layer.objects.active = empty
        bpy.ops.rigidbody.constraint_add()
    else:
        original = col_joints.objects[0]
        empty = original.copy()
        col_joints.objects.link(empty)

    empty.location = loc

    empty.rigid_body_constraint.object1 = obj1
    empty.rigid_body_constraint.object2 = obj2

    empty.empty_display_size = 0.05

    empty['intersection_volume'] = volume

    store_joint_reference(obj1, empty)
    store_joint_reference(obj2, empty)

    return empty


def remove_existing_joints(col_joints, obj1, obj2):
    num_existing_joints = 0
    existing_joints = get_joints_by_rb(obj1, col_joints)
    for ex_joint in existing_joints:
        rbc = ex_joint.rigid_body_constraint
        if rbc.object1 == obj2 or rbc.object2 == obj2:
            print(f'removing joint between {rbc.object1.name} and {rbc.object2.name}')

            utils.remove_joint_from_property(rbc.object1, ex_joint.name)
            utils.remove_joint_from_property(rbc.object2, ex_joint.name)

            for col in ex_joint.users_collection:
                col.objects.unlink(ex_joint)
            num_existing_joints += 1

    return num_existing_joints


def joint_exists(col_joints, obj1, obj2):
    existing_joints = get_joints_by_rb(obj1, col_joints)
    for ex_joint in existing_joints:
        rbc = ex_joint.rigid_body_constraint
        if rbc.object1 == obj2 or rbc.object2 == obj2:
            return True

    return False


class STRA_OT_Modify_Structure(Operator):
    bl_idname = "stra.structure_modify"
    bl_label = "Modify structure"
    bl_options = {"UNDO_GROUPED"}

    def execute(self, context):
        props = context.scene.stra_props_joint

        bpy.context.scene.frame_current = 0
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

        col_joints = utils.get_collection_joints()

        already_applied = []
        for ob in context.selected_objects:
            if ob.rigid_body is None:
                continue
            joints = get_joints_by_rb(ob, col_joints)
            for ob in joints:
                if ob in already_applied:
                    continue
                already_applied.append(ob)
                modify_const(ob, props)

        self.report({'INFO'}, f'Applied for {len(already_applied)} joint(s)')
        return {'FINISHED'}


def create_intersection_mesh(obj1, obj2, solidify_thickness):
    bm = bmesh.new()
    bm.from_mesh(obj1.data)
    bmesh.ops.transform(bm, matrix=obj1.matrix_world, verts=bm.verts)
    bmesh.ops.solidify(bm, geom=bm.faces, thickness=-solidify_thickness)

    solidified_mesh = bpy.data.meshes.new("Solidified_Mesh")
    bm.to_mesh(solidified_mesh)
    bm.free()
    temp_obj = bpy.data.objects.new("Solidified_Object", solidified_mesh)

    col_temp = utils.get_collection_temp()
    col_temp.objects.link(temp_obj)

    bpy.context.view_layer.objects.active = temp_obj

    bool_mod = temp_obj.modifiers.new(type="BOOLEAN", name="bool")
    bool_mod.solver = 'EXACT' # FAST causes bad volumes
    bool_mod.operation = 'INTERSECT'
    bool_mod.object = obj2
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)

    return temp_obj


class STRA_OT_Generate_Structure(Operator):
    bl_idname = "stra.structure_generate"
    bl_label = "Generate structure"
    bl_options = {"UNDO_GROUPED"}

    def execute(self, context):
        bpy.context.scene.frame_current = 0

        if context.scene.rigidbody_world is None:
            bpy.ops.rigidbody.world_add()

        props = context.scene.stra_props_structure
        props_const = context.scene.stra_props_joint

        col_joints = utils.get_collection_joints()

        bpy.context.scene.frame_current = 0
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

        print('creating bvh trees...')
        trees = get_bvh(context.selected_objects, props.overlap_margin)

        num_existing_joints = 0

        if props.existing_joint_behaviour == 'OVERWRITE':
            print(f'overwrite on, removing existing joints...')
            for obj1 in context.selected_objects:
                for obj2 in context.selected_objects:
                    if obj1 == obj2:
                        continue
                    num_existing_joints += remove_existing_joints(col_joints, obj1, obj2)
            print(f'done removing {num_existing_joints} joints')

        joints_generated_amount = 0
        joints_already_exist = 0

        start_time = time.time()

        for i in range(len(trees)):
            for j in range(i + 1, len(trees)):
                tree1, (obj1, bm1) = trees[i]
                tree2, (obj2, bm2) = trees[j]

                overlap_pairs = tree1.overlap(tree2)
                if not overlap_pairs:
                    continue

                if props.existing_joint_behaviour == 'NEWONLY':
                    if (joint_exists(col_joints, obj1, obj2)):
                        joints_already_exist += 1
                        print(f'(skip) joint already exists!')
                        continue

                print(f' ')
                print(f'overlap found: ({obj1.name} x {obj2.name})')

                loc = Vector((0, 0, 0))
                volume = props.overlap_margin

                if props.mode == "EXACT":
                    intersect_obj = create_intersection_mesh(
                        obj1, obj2, props.overlap_margin)

                    if len(intersect_obj.data.vertices) == 0:
                        print(f'(skip) created intersection has no volume')
                        bpy.data.objects.remove(intersect_obj)
                        continue

                    bm = bmesh.new()
                    bm.from_mesh(intersect_obj.data)
                    volume = bm.calc_volume()
                    bm.free()

                    if volume < props.min_overlap_threshold:
                        print('(skip) intersection volume too small')
                        bpy.data.objects.remove(intersect_obj)
                        continue

                    for v in intersect_obj.data.vertices:
                        loc += v.co
                    loc /= len(intersect_obj.data.vertices)

                    loc = intersect_obj.matrix_world @ loc

                    bpy.data.objects.remove(intersect_obj)
                else:
                    # midpoint between two objects
                    loc = (obj1.location + obj2.location) / 2

                joint = create_joint(col_joints, obj1, obj2, loc, volume)
                modify_const(joint, props_const)

                joint.show_in_front = True

                joints_generated_amount += 1
                print(f'(ok) joint created with volume {volume:.2f}')

            props.progress = (i + 1) / (len(trees))
            print(f"One iteration done")
            print(f"Progress: {props.progress*100:.2f}%")

            if props.mode == "EXACT":
                bpy.ops.outliner.orphans_purge(do_local_ids=True)

        result = f"{joints_generated_amount} joint(s) generated"
        result += f", ({joints_generated_amount - num_existing_joints} new, {joints_already_exist} already exist)"
        self.report({'INFO'}, result)

        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f'FINISHED! Overlap calculations took {elapsed_time:.2f} seconds')

        return {'FINISHED'}
