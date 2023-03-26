import bpy
import bmesh
from mathutils.bvhtree import BVHTree
from bpy.types import Operator


class STRA_OT_Viewport_collider_hide(Operator):
    bl_idname = "stra.viewport_collider_hide"
    bl_label = "Visible"

    def execute(self, context):
        props = context.scene.stra_props_viewport
        props.hide = not props.hide
        for ob in bpy.data.objects:
            if 'collider' in ob.name:
                ob.hide_viewport = props.hide
                ob.hide_render = props.hide

        return {'FINISHED'}


class STRA_OT_Viewport_collider_selectabe(Operator):
    bl_idname = "stra.viewport_collider_selectable"
    bl_label = "Selectable"

    def execute(self, context):
        props = context.scene.stra_props_viewport
        props.selectable = not props.selectable
        for ob in bpy.data.objects:
            if 'collider' in ob.name:
                ob.hide_select = not props.selectable

        return {'FINISHED'}


class STRA_OT_Viewport_collider_in_front(Operator):
    bl_idname = "stra.viewport_collider_show_in_front"
    bl_label = "In front"

    def execute(self, context):
        props = context.scene.stra_props_viewport
        props.show_in_front = not props.show_in_front
        for ob in bpy.data.objects:
            if 'collider' in ob.name:
                ob.show_in_front = props.show_in_front

        return {'FINISHED'}


class STRA_OT_Viewport_collider_detect(Operator):
    bl_idname = "stra.viewport_collider_detect"
    bl_label = "Print collider overlaps"

    def execute(self, context):
        trees = []
        for ob in bpy.data.objects:
            if ob.rigid_body is None:
                continue
            if 'collider' in ob.name or ob.rigid_body.collision_shape == 'CONVEX_HULL':
                bm = bmesh.new()
                bm.from_mesh(ob.data)
                if len(bm.verts) == 0:
                    continue
                bmesh.ops.transform(bm, matrix=ob.matrix_world, verts=bm.verts)
                bm.verts.ensure_lookup_table()
                bm.edges.ensure_lookup_table()
                bm.faces.ensure_lookup_table()

                tree = BVHTree.FromBMesh(bm)

                ret = bmesh.ops.convex_hull(bm, input=bm.verts)
                bmesh.ops.delete(bm, geom=ret['geom_interior'])
                bmesh.ops.delete(bm, geom=ret['geom_unused'])

                tree_convex = BVHTree.FromBMesh(bm)
                bm.free()

                trees.append((ob, tree, tree_convex))

        not_found = True
        for i in range(len(trees)):
            for j in range(i + 1, len(trees)):
                ob1, tree1, tree1_convex = trees[i]
                ob2, tree2, tree2_convex = trees[j]
                overlap_pairs = tree1.overlap(tree2)
                if not overlap_pairs:
                    tree1.overlap(tree2_convex)
                if overlap_pairs:
                    not_found = False
                    print(f'--------WARNING: {ob1.name} collides with {ob2.name}')

        if not_found:
            print('No collider overlaps found')
        return {'FINISHED'}
