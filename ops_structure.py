import bpy
from bpy.types import Operator

import bmesh
import math
from mathutils.bvhtree import BVHTree
from . import utils


def modify_active_const(props):
    bpy.context.object.rigid_body_constraint.type = props.type
    bpy.context.object.rigid_body_constraint.disable_collisions = not props.use_local_collisions
    bpy.context.object.rigid_body_constraint.use_breaking = True
    bpy.context.object.rigid_body_constraint.breaking_threshold = props.break_threshold

    ang_max = math.radians(props.leeway_angular)
    lin_max = props.leeway_linear

    bpy.context.object.rigid_body_constraint.use_limit_ang_x = True
    bpy.context.object.rigid_body_constraint.limit_ang_x_lower = 0
    bpy.context.object.rigid_body_constraint.limit_ang_x_upper = ang_max
    bpy.context.object.rigid_body_constraint.use_limit_ang_y = True
    bpy.context.object.rigid_body_constraint.limit_ang_y_lower = 0
    bpy.context.object.rigid_body_constraint.limit_ang_y_upper = ang_max
    bpy.context.object.rigid_body_constraint.use_limit_ang_z = True
    bpy.context.object.rigid_body_constraint.limit_ang_z_lower = 0
    bpy.context.object.rigid_body_constraint.limit_ang_z_upper = ang_max

    bpy.context.object.rigid_body_constraint.use_limit_lin_x = True
    bpy.context.object.rigid_body_constraint.limit_lin_x_lower = 0
    bpy.context.object.rigid_body_constraint.limit_lin_x_upper = lin_max
    bpy.context.object.rigid_body_constraint.use_limit_lin_y = True
    bpy.context.object.rigid_body_constraint.limit_lin_y_lower = 0
    bpy.context.object.rigid_body_constraint.limit_lin_y_upper = lin_max
    bpy.context.object.rigid_body_constraint.use_limit_lin_z = True
    bpy.context.object.rigid_body_constraint.limit_lin_z_lower = 0
    bpy.context.object.rigid_body_constraint.limit_lin_z_upper = lin_max


def get_bvh(collection, use_overlap_margin, overlap_margin, subd):
    trees = []
    for obj in collection.objects:
        if obj.type != 'MESH':
            continue
        if 'collider' in obj.name:
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


class STRA_OT_Generate_Structure(Operator):
    bl_idname = "stra.structure_generate"
    bl_label = "Generate structure"

    def execute(self, context):
        props = context.scene.stra_props_structure
        props_const = context.scene.stra_props_joint
        collection = context.collection
        if 'joint' in collection.name:
            collection = utils.get_parent_collection(collection)

        bpy.context.scene.frame_current = 0
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

        trees = get_bvh(collection, props.overlap_margin, props.overlap_margin, props.subd)
        col_empties = utils.reset_collection(collection, collection.name + '_joints')

        for i in range(len(trees)):
            for j in range(i + 1, len(trees)):
                tree1, (obj1, bm1) = trees[i]
                tree2, (obj2, bm2) = trees[j]
                overlap_pairs = tree1.overlap(tree2)
                if overlap_pairs:
                    face1 = bm1.faces[overlap_pairs[0][0]]
                    face2 = bm2.faces[overlap_pairs[0][1]]
                    loc = (face1.verts[0].co + face2.verts[0].co) / 2
                    min_dist = (face1.verts[0].co - face2.verts[0].co).length

                    for p1, p2 in overlap_pairs:
                        face1 = bm1.faces[p1]
                        face2 = bm2.faces[p2]

                        for v1 in face1.verts:
                            for v2 in face2.verts:
                                if (v1.co - v2.co).length < min_dist:
                                    min_dist = (v1.co - v2.co).length
                                    loc = (v1.co + v2.co) / 2

                    empty_name = f'{obj1.name}_{obj2.name}_joint'
                    empty = bpy.data.objects.new(empty_name, None)
                    empty.empty_display_size = 0.2

                    empty.location = loc
                    col_empties.objects.link(empty)

                    bpy.context.view_layer.objects.active = empty
                    bpy.ops.rigidbody.constraint_add(type=props_const.type)

                    modify_active_const(props_const)

                    bpy.context.object.rigid_body_constraint.object1 = obj1
                    bpy.context.object.rigid_body_constraint.object2 = obj2

            props.progress = (i + 1) / (len(trees))
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
            print(f"Progress: {props.progress*100:.2f}%")

        return {'FINISHED'}
