import bpy
from bpy.types import Operator
import bmesh
from . import utils

class STRA_OT_Generate_Wireframe(Operator):
    bl_idname = "stra.wireframe_generate"
    bl_label = "Generate wireframe"

    def execute(self, context):
        objs = context.selected_objects

        for ob in objs:
            if ob.type != 'MESH':
                continue

            new_col = utils.reset_collection(context.collection, f'{ob.name}_wireframe')

            bm = bmesh.new()
            bm.from_mesh(ob.data)
            bm.edges.ensure_lookup_table()

            for edge in bm.edges:
                new_mesh = bpy.data.meshes.new(f'{ob.name}_STRA_EDGE_MESH')
                new_bm = bmesh.new()
                v1 = new_bm.verts.new(edge.verts[0].co)
                v2 = new_bm.verts.new(edge.verts[1].co)
                new_bm.edges.new([v1, v2])
                new_bm.transform(ob.matrix_world)
                new_bm.to_mesh(new_mesh)
                new_obj = bpy.data.objects.new(f'{ob.name}_STRA_EDGE', new_mesh)
                new_col.objects.link(new_obj)


        return {'FINISHED'}