import bpy
import bmesh
from bpy.types import Operator
from mathutils.bvhtree import BVHTree
from . import utils, viewport
from mathutils import Matrix, Vector

class STRA_OT_Select_Collection(Operator):
    bl_idname = "stra.collection_select_objects"
    bl_label = "Select all objects in collection"

    def execute(self, context):
        for ob in context.collection.objects:
            ob.select_set(True)
        return {'FINISHED'}


def scale_bmesh(bm, scale):
    max_dist = 0
    v1 = v2 = None
    for vert1 in bm.verts:
        for vert2 in bm.verts:
            dist = (vert1.co - vert2.co).length
            if dist > max_dist:
                max_dist = dist
                v1 = vert1
                v2 = vert2

    # Calculate the custom local axis
    custom_local_axis = (v1.co - v2.co).normalized()

    # Calculate the other two axes relative to the custom local axis
    axis_y = Vector((0, 0, 1)).cross(custom_local_axis).normalized()
    axis_z = custom_local_axis.cross(axis_y).normalized()

    # Create a transformation matrix to scale along the custom local axis
    mat_loc = Matrix.Translation((v1.co + v2.co) / 2)
    mat_scale = Matrix.Scale(scale.x, 4, custom_local_axis) @ Matrix.Scale(scale.y, 4, axis_y) @ Matrix.Scale(scale.z, 4, axis_z)
    mat_transf = mat_loc @ mat_scale @ mat_loc.inverted()

    # Scale the bmesh along the custom local axis
    bmesh.ops.transform(bm, matrix=mat_transf, verts=bm.verts)


def get_verts_only(bm):
    new_bm = bmesh.new()
    for v in bm.verts:
        new_bm.verts.new(v.co)
    new_bm.verts.ensure_lookup_table()
    return new_bm


class STRA_OT_Generate_Colliders(Operator):
    bl_idname = "stra.collider_generate"
    bl_label = "Generate colliders"
    bl_options = {"UNDO_GROUPED"}

    def execute(self, context):
        context.scene.frame_current = 0

        props = context.scene.stra_props_collider

        bpy.ops.outliner.orphans_purge(do_local_ids=True)

        mesh_data = {}
        for ob in context.selected_objects:
            if ob.type != 'MESH':
                continue

            if 'STRA_COLLIDER' in ob.name:
                ob = ob.parent

            bm = bmesh.new()
            bm.from_mesh(ob.data)

            if len(bm.verts) == 0:
                context.collection.objects.unlink(ob)
                continue

            bm.verts.ensure_lookup_table()
            bm.edges.ensure_lookup_table()
            bm.faces.ensure_lookup_table()

            mesh_data[ob] = bm

        trees = []

        index = 0
        for ob in context.selected_objects:
            if ob is None:
                continue

            if 'STRA_COLLIDER' in ob.name:
                ob = ob.parent

            if ob.type != 'MESH':
                continue

            bpy.context.view_layer.objects.active = ob
            for ch in ob.children_recursive:
                bpy.data.objects.remove(ch, do_unlink=True)

            if ob.rigid_body is None:
                bpy.ops.rigidbody.object_add()

            ob.rigid_body.mass = 10
            ob.rigid_body.use_deactivation = True
            ob.rigid_body.collision_shape = 'COMPOUND'
            ob.rigid_body.collision_margin = 0

            bm = mesh_data[ob]
            target_map = bmesh.ops.find_doubles(bm, verts=bm.verts, dist=0.01)["targetmap"]
            bmesh.ops.weld_verts(bm, targetmap=target_map)
            bmesh.ops.holes_fill(bm, edges=bm.edges, sides=4)

            bmesh.ops.scale(
                bm,
                vec=props.scale_global,
                verts=bm.verts
            )

            scale_bmesh(bm, props.scale_custom)

            if props.shape == 'CONVEX':
                bm = get_verts_only(bm)
                bmesh.ops.convex_hull(bm, input=bm.verts)
                bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_edges], context='VERTS')

            trees.append((ob, BVHTree.FromBMesh(bm)))

            new_me = bpy.data.meshes.new(ob.name + "_STRA_COLLIDER")
            bm.to_mesh(new_me)
            bm.free()
            new_ob = bpy.data.objects.new(ob.name + "_STRA_COLLIDER", new_me)
            col_colliders = utils.get_collection_colliders()
            col_colliders.objects.link(new_ob)

            new_ob.parent = ob

            bpy.context.view_layer.objects.active = new_ob
            bpy.ops.rigidbody.object_add()
            new_ob.rigid_body.collision_margin = 0

            if props.shape == "VOXEL":
                modifier = new_ob.modifiers.new(name="Remesh", type="REMESH")
                modifier.mode = "VOXEL"
                modifier.voxel_size = props.voxel_size
                bpy.ops.object.modifier_apply(modifier=modifier.name)
                new_ob.rigid_body.collision_shape = 'MESH'
            else:
                new_ob.rigid_body.collision_shape = 'CONVEX_HULL'

            new_ob.show_in_front = True

            index += 1
            props.progress = index / len(mesh_data)

            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

        if bpy.context.view_layer.objects.active == None:
            if len(context.selectable_objects) > 0:
                bpy.context.view_layer.objects.active = context.selectable_objects[0]

        for i in range(len(trees)):
            for j in range(i + 1, len(trees)):
                obj1, tree1 = trees[i]
                obj2, tree2 = trees[j]
                overlap_pairs = tree1.overlap(tree2)
                if overlap_pairs:
                    print(f'--------WARNING: {obj1.name} collides with {obj2.name}')

        return {'FINISHED'}