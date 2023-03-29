from gc import collect
import bpy


def reset_collection(parent_collection, name):
    col_reset = None
    for col in bpy.data.collections:
        if col.name == name:
            col_reset = col
        if 'RigidBodyWorld' in col.name:
            colrbw = col
        if 'RigidBodyConstraints' in col.name:
            colrbc = col
    if col_reset is None:
        col_reset = bpy.data.collections.new(name)
        parent_collection.children.link(col_reset)
    else:
        for ob in col_reset.objects:
            if colrbw.objects.get(ob.name) is not None:
                colrbw.objects.unlink(ob)
            if colrbc.objects.get(ob.name) is not None:
                colrbc.objects.unlink(ob)
            col_reset.objects.unlink(ob)

    bpy.ops.outliner.orphans_purge(do_local_ids=True)

    return col_reset


def get_parent_collection(collection):
    for parent in bpy.data.collections:
        for child in parent.children_recursive:
            if child == collection:
                return parent

def draw_list_entry(b, left, right):
    r = b.row()
    r.scale_y = 0.7
    c1 = r.column()
    c1.alignment = 'LEFT'
    c1.label(text=f'{left}')

    c2 = r.column()
    c2.alignment = 'RIGHT'
    c2.label(text=f'{right}')
