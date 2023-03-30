import bpy
import bmesh
from bpy.types import Operator
from mathutils.bvhtree import BVHTree
from . import utils, viewport


class STRA_OT_Select_Collection(Operator):
    bl_idname = "stra.collection_select_objects"
    bl_label = "Select all objects in collection"

    def execute(self, context):
        for ob in context.collection.objects:
            ob.select_set(True)
        return {'FINISHED'}


class STRA_OT_Generate_Colliders(Operator):
    bl_idname = "stra.collider_generate"
    bl_label = "Generate colliders"

    def execute(self, context):
        context.scene.frame_current = 0

        props = context.scene.stra_props_collider
        cmpnd = props.shape == 'COMPOUND'

        bpy.ops.outliner.orphans_purge(do_local_ids=True)

        if cmpnd:
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
            ob.rigid_body.collision_shape = props.shape
            ob.rigid_body.collision_margin = 0

            if cmpnd:
                bm = mesh_data[ob]
                target_map = bmesh.ops.find_doubles(bm, verts=bm.verts, dist=0.01)["targetmap"]
                bmesh.ops.weld_verts(bm, targetmap=target_map)
                bmesh.ops.holes_fill(bm, edges=bm.edges, sides=4)

                bmesh.ops.scale(
                    bm,
                    vec=props.scale,
                    verts=bm.verts
                )

                new_me = bpy.data.meshes.new(ob.name + "_STRA_COLLIDER")
                bm.to_mesh(new_me)

                bmesh.ops.transform(bm, matrix=ob.matrix_world, verts=bm.verts)
                trees.append((ob, BVHTree.FromBMesh(bm)))
                bm.free()

                new_ob = bpy.data.objects.new(
                    ob.name + "_STRA_COLLIDER", new_me)
                if 'joint' in context.collection.name:
                    utils.get_parent_collection(context.collection).objects.link(new_ob)
                else:
                    context.collection.objects.link(new_ob)

                new_ob.parent = ob
                bpy.context.view_layer.objects.active = new_ob

                modifier = new_ob.modifiers.new(name="Remesh", type="REMESH")
                modifier.mode = "VOXEL"
                modifier.voxel_size = props.voxel_size
                bpy.ops.object.modifier_apply(modifier=modifier.name)

                bpy.ops.rigidbody.object_add()
                new_ob.rigid_body.collision_shape = 'MESH'
                new_ob.rigid_body.collision_margin = 0

                index += 1
                props.progress = index / len(mesh_data)

            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

        if bpy.context.view_layer.objects.active == None:
            if len(context.selectable_objects) > 0:
                bpy.context.view_layer.objects.active = context.selectable_objects[0]

        if cmpnd:
            for i in range(len(trees)):
                for j in range(i + 1, len(trees)):
                    obj1, tree1 = trees[i]
                    obj2, tree2 = trees[j]
                    overlap_pairs = tree1.overlap(tree2)
                    if overlap_pairs:
                        print(f'--------WARNING: {obj1.name} collides with {obj2.name}')

        viewport.refresh('STRA_COLLIDER')

        return {'FINISHED'}