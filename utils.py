import bpy

OBJNAME_COLLIDER = 'STRA_COLLIDER'
OBJNAME_JOINT = 'STRA_JOINT'


def get_collection(parent_col, name, create=True):
    col = parent_col.children.get(name)

    if col is None and create:
        col = bpy.data.collections.new(name)
        parent_col.children.link(col)

        col.color_tag = 'COLOR_04'

    return col


def get_collection_temp(create=True):
    col_parent = get_collection(bpy.context.scene.collection, 'STRUCTURA', create=create)
    col = get_collection(col_parent, 'STRUCTURA_TEMP', create=create)
    return col


def clear_temp_collection():
    col = get_collection_temp()
    for obj in col.objects:
        bpy.data.objects.remove(obj)


def get_collection_joints(create=True):
    col_parent = get_collection(bpy.context.scene.collection, 'STRUCTURA', create=create)
    if col_parent is None:
        return None
    col = get_collection(col_parent, 'STRUCTURA_JOINTS', create=create)
    if col is None:
        return None

    return col


def get_collection_colliders(create=True):
    col_parent = get_collection(bpy.context.scene.collection, 'STRUCTURA', create=create)
    if col_parent is None:
        return None
    col = get_collection(col_parent, 'STRUCTURA_COLLIDERS', create=create)
    if col is None:
        return None

    for ob in col.objects:
        if ob.parent is None:
            for cl in ob.users_collection:
                cl.objects.unlink(ob)

    if create:
        col.hide_select = True
        col.hide_render = True

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