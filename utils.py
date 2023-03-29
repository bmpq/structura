from gc import collect
import bpy


def clear_collection(col_clear):
    for child_col in col_clear.children:
        clear_collection(child_col)
    for ob in col_clear.objects:
        for col in ob.users_collection:
            col.objects.unlink(ob)


def reset_collection(parent_collection, name):
    col_reset = bpy.data.collections.get(name)
    if col_reset is None:
        col_reset = bpy.data.collections.new(name)
        parent_collection.children.link(col_reset)
    else:
        clear_collection(col_reset)

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
