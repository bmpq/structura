import bpy
from bpy.types import Operator
import bmesh
from . import utils
import math
import numpy as np


def move_coords(coord1, coord2, dist_delta):
    if dist_delta == 0:
      return coord1, coord2

    x1, y1, z1 = coord1
    x2, y2, z2 = coord2

    orig_dist = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)

    ux = (x2 - x1) / orig_dist
    uy = (y2 - y1) / orig_dist
    uz = (z2 - z1) / orig_dist

    new_dist = orig_dist + dist_delta

    if new_dist < 0:
        print('Warning: pruning resulted in negative distance')

    new_x1 = x1 + (ux * dist_delta / 2)
    new_y1 = y1 + (uy * dist_delta / 2)
    new_z1 = z1 + (uz * dist_delta / 2)
    new_x2 = x2 - (ux * dist_delta / 2)
    new_y2 = y2 - (uy * dist_delta / 2)
    new_z2 = z2 - (uz * dist_delta / 2)

    return (new_x1, new_y1, new_z1), (new_x2, new_y2, new_z2)


class STRA_OT_Generate_Wireframe(Operator):
    bl_idname = "stra.wireframe_generate"
    bl_label = "Generate wireframe"

    def execute(self, context):
        props = context.scene.stra_props_wireframe
        objs = context.selected_objects

        for ob in objs:
            ob.select_set(False)
            if ob.type != 'MESH':
                continue

            new_col = utils.reset_collection(context.collection, f'{ob.name}_STRA_WIREFRAME')

            bm = bmesh.new()
            bm.from_mesh(ob.data)
            bm.edges.ensure_lookup_table()

            for edge in bm.edges:
                new_mesh = bpy.data.meshes.new(f'{ob.name}_STRA_EDGE_MESH')
                new_bm = bmesh.new()
                coord1 = edge.verts[0].co
                coord2 = edge.verts[1].co
                coord1, coord2 = move_coords(coord1, coord2, props.prune)
                v1 = new_bm.verts.new(coord1)
                v2 = new_bm.verts.new(coord2)
                new_bm.edges.new([v1, v2])
                new_bm.transform(ob.matrix_world)
                new_bm.to_mesh(new_mesh)
                new_bm.free()
                new_obj = bpy.data.objects.new(f'{ob.name}_STRA_EDGE', new_mesh)
                new_col.objects.link(new_obj)

                bpy.context.view_layer.objects.active = new_obj

                modifier = new_obj.modifiers.new(name="Skin", type="SKIN")
                new_mesh.update()
                new_mesh.skin_vertices[0].data[0].radius = (props.thickness, props.thickness)
                new_mesh.skin_vertices[0].data[1].radius = (props.thickness, props.thickness)
                bpy.ops.object.modifier_apply(modifier=modifier.name)

                new_obj.select_set(True)
                bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME')
                new_obj.select_set(False)

                bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

        return {'FINISHED'}