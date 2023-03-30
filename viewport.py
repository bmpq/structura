import bpy
import bmesh
from mathutils.bvhtree import BVHTree
from bpy.types import Operator


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


class STRA_OT_Viewport_toggle(Operator):
    bl_idname = "stra.viewport_toggle"
    bl_label = "Visibility"

    obname : bpy.props.StringProperty()
    propname : bpy.props.StringProperty()
    state : bpy.props.BoolProperty()

    def execute(self, context):
        if self.obname == 'STRA_JOINT':
            props = context.scene.stra_props_viewport_joint
        else:
            props = context.scene.stra_props_viewport_collider

        if self.propname == 'VISIBLE':
            props.hide = self.state
        elif self.propname == 'SELECTABLE':
            props.selectable = self.state
        elif self.propname == 'INFRONT':
            props.show_in_front = self.state

        refresh(self.obname)

        return {'FINISHED'}


def refresh(obname):
    if obname == 'STRA_JOINT':
        props = bpy.context.scene.stra_props_viewport_joint
    else:
        props = bpy.context.scene.stra_props_viewport_collider

    for ob in bpy.data.objects:
        if obname in ob.name:
            ob.hide_viewport = props.hide
            ob.hide_render = props.hide
            ob.hide_select = not props.selectable
            ob.show_in_front = props.show_in_front