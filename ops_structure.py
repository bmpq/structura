import bpy
from bpy.types import Operator

import bmesh
import math
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
from . import utils


def modify_const(ob, props):
    rbc = ob.rigid_body_constraint
    rbc.type = props.type
    rbc.disable_collisions = not props.use_local_collisions
    rbc.use_breaking = True
    rbc.breaking_threshold = props.break_threshold

    if props.use_mass_threshold and rbc.object1 is not None and rbc.object2 is not None:
        mass_min = rbc.object1.rigid_body.mass
        if rbc.object2.rigid_body.mass < mass_min:
            mass_min = rbc.object2.rigid_body.mass
        rbc.breaking_threshold *= mass_min

    ang_max = math.radians(props.leeway_angular)
    lin_max = props.leeway_linear

    rbc.use_limit_ang_x = True
    rbc.limit_ang_x_lower = 0
    rbc.limit_ang_x_upper = ang_max
    rbc.use_limit_ang_y = True
    rbc.limit_ang_y_lower = 0
    rbc.limit_ang_y_upper = ang_max
    rbc.use_limit_ang_z = True
    rbc.limit_ang_z_lower = 0
    rbc.limit_ang_z_upper = ang_max

    rbc.use_limit_lin_x = True
    rbc.limit_lin_x_lower = 0
    rbc.limit_lin_x_upper = lin_max
    rbc.use_limit_lin_y = True
    rbc.limit_lin_y_lower = 0
    rbc.limit_lin_y_upper = lin_max
    rbc.use_limit_lin_z = True
    rbc.limit_lin_z_lower = 0
    rbc.limit_lin_z_upper = lin_max


def get_bvh(objects, use_overlap_margin, overlap_margin, subd):
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

        bmesh.ops.transform(bm, matrix=obj.matrix_world, verts=bm.verts)

        if use_overlap_margin:
            bmesh.ops.solidify(bm, geom=bm.faces, thickness=-overlap_margin)

        if subd > 0:
            bmesh.ops.subdivide_edges(bm, edges=bm.edges, cuts=subd)

        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        tree = BVHTree.FromBMesh(bm)
        trees.append((tree, (obj, bm)))

    return trees


def get_joints_by_rb(obj_rb, col_joints):
    joint_objs = []

    for ob in col_joints.objects:
        const = ob.rigid_body_constraint
        if const is None:
            continue
        if const.object1 == obj_rb or const.object2 == obj_rb:
            joint_objs.append(ob)
            continue

    return joint_objs


def create_joint(col_joints, obj1, obj2, loc):
    empty_name = utils.OBJNAME_JOINT
    empty = bpy.data.objects.new(empty_name, None)
    col_joints.objects.link(empty)

    bpy.context.view_layer.objects.active = empty
    bpy.ops.rigidbody.constraint_add()

    empty.location = loc

    bpy.context.object.rigid_body_constraint.object1 = obj1
    bpy.context.object.rigid_body_constraint.object2 = obj2

    empty.empty_display_size = 0.2

    return empty


def remove_existing_joints(col_joints, obj1, obj2):
    existing_joints = get_joints_by_rb(obj1, col_joints)
    for ex_joint in existing_joints:
        rbc = ex_joint.rigid_body_constraint
        if rbc.object1 == obj2 or rbc.object2 == obj2:
            for col in ex_joint.users_collection:
                col.objects.unlink(ex_joint)


class STRA_OT_Modify_Structure(Operator):
    bl_idname = "stra.structure_modify"
    bl_label = "Modify structure"
    bl_options = {"UNDO_GROUPED"}

    def execute(self, context):
        props = context.scene.stra_props_joint

        bpy.context.scene.frame_current = 0
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

        col_joints = utils.get_collection_joints()

        for ob in context.selected_objects:
            if ob.rigid_body is None:
                continue
            joints = get_joints_by_rb(ob, col_joints)
            for ob in joints:
                modify_const(ob, props)

        return {'FINISHED'}


def get_closest_pair(list1, list2):
    if not list1 or not list2:
        return None

    kd = KDTree(len(list2))
    for i, p2 in enumerate(list2):
        kd.insert(p2, i)
    kd.balance()

    min_dist = math.inf
    pair = None

    for p1 in list1:
        co, index, dist = kd.find(p1)
        if dist < min_dist:
            min_dist = dist
            pair = (p1, co)

    return pair


class STRA_OT_Generate_Structure(Operator):
    bl_idname = "stra.structure_generate"
    bl_label = "Generate structure"
    bl_options = {"UNDO_GROUPED"}

    def execute(self, context):
        if context.scene.rigidbody_world is None:
            bpy.ops.rigidbody.world_add()

        props = context.scene.stra_props_structure
        props_const = context.scene.stra_props_joint

        col_joints = utils.get_collection_joints()

        bpy.context.scene.frame_current = 0
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

        trees = get_bvh(context.selected_objects, props.use_overlap_margin, props.overlap_margin, props.subd)

        for obj1 in context.selected_objects:
            for obj2 in context.selected_objects:
                if obj1 == obj2:
                    continue
                remove_existing_joints(col_joints, obj1, obj2)

        joints_generated_amount = 0
        for i in range(len(trees)):
            for j in range(i + 1, len(trees)):
                tree1, (obj1, bm1) = trees[i]
                tree2, (obj2, bm2) = trees[j]
                overlap_pairs = tree1.overlap(tree2)
                if overlap_pairs:
                    coords_list1 = []
                    coords_list2 = []
                    for p1, p2 in overlap_pairs:
                        face1 = bm1.faces[p1]
                        face2 = bm2.faces[p2]

                        if props.select_mode == 'VERTEX' or props.select_mode == 'AND':
                            print('vertex')
                            for v1 in face1.verts:
                                coords_list1.append(v1.co)
                            for v2 in face2.verts:
                                coords_list2.append(v2.co)

                        if props.select_mode == 'FACE' or props.select_mode == 'AND':
                            print('face')
                            coords_list1.append(face1.calc_center_median_weighted())
                            coords_list2.append(face2.calc_center_median_weighted())

                    closest_pair = get_closest_pair(coords_list1, coords_list2)

                    loc = (closest_pair[0] + closest_pair[1]) / 2

                    joint = create_joint(col_joints, obj1, obj2, loc)
                    modify_const(joint, props_const)

                    joint.show_in_front = True

                    joints_generated_amount += 1

            props.progress = (i + 1) / (len(trees))
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
            print(f"Progress: {props.progress*100:.2f}%")

        print(f'RESULT: Generated {joints_generated_amount} joints')

        return {'FINISHED'}
