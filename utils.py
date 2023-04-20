import bpy


def get_collection(parent_col, name):
    col = parent_col.children.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        parent_col.children.link(col)
    return col


def get_collection_joints():
    col_parent = get_collection(bpy.context.scene.collection, 'STRUCTURA')
    col = get_collection(col_parent, 'STRUCTURA_JOINTS')
    return col


def get_collection_colliders():
    col_parent = get_collection(bpy.context.scene.collection, 'STRUCTURA')
    col = get_collection(col_parent, 'STRUCTURA_COLLIDERS')
    return col


def draw_list_entry(b, left, right):
    r = b.row()
    r.scale_y = 0.7
    c1 = r.column()
    c1.alignment = 'LEFT'
    c1.label(text=f'{left}')

    c2 = r.column()
    c2.alignment = 'RIGHT'
    c2.label(text=f'{right}')
