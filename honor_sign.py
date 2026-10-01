"""A little front-lawn sign for the future Honor home.

Run this file in Blender's Text Editor after the house and environment scripts.
Creates a white, dark-trimmed two-post sign facing the street (-Y):
    6278 Dry Tortugas
    Our future home!

Only this script's HONOR_SIGN collection is replaced on rerun. No existing
house, pool, environment, camera, lighting or render settings are changed.
Text stays editable and uses Blender's built-in font; no external assets.
Coordinates are meters in the house's frame. Position/size controls are below.
Source reviewed; not executed or rendered in Blender in the assistant session.
"""

import math
import bpy
from mathutils import Matrix, Vector


# ------------------------------ user controls -------------------------------
COLLECTION_NAME = 'HONOR_SIGN'
OWNER = 'honor_sign_generated'
LINE_1 = '6278 Dry Tortugas'
LINE_2 = 'Our future home!'
SIGN_WIDTH = 1.90
SIGN_HEIGHT = 0.85
PANEL_BOTTOM = 0.80              # above the lawn
SIGN_X = None                   # None = front lawn, opposite the garage
SIGN_Y = None                   # None = 2 meters behind the road edge
SIGN_Z = None                   # None = default environment lawn elevation
ANGLE_DEGREES = 0.0             # rotation about house-frame Z
ROAD_CLEARANCE = 2.0

assert SIGN_WIDTH > 0.5 and SIGN_HEIGHT > 0.35 and PANEL_BOTTOM >= 0.0


# --------------------------- read-only placement ----------------------------
def find_mesh(collection, prefix):
    if collection is None:
        return None
    return next((o for o in collection.all_objects
                 if o.type == 'MESH' and o.name.startswith(prefix)), None)


def points_in_frame(obj, inverse):
    transform = inverse @ obj.matrix_world
    return [transform @ v.co for v in obj.data.vertices]


bpy.context.view_layer.update()
house = bpy.data.collections.get('HONOR_FH1')
foundation = find_mesh(house, 'Main foundation')
anchor = foundation.matrix_world.copy() if foundation else Matrix.Identity(4)
if abs(anchor.determinant()) < 1e-9:
    raise RuntimeError('House has zero scale; restore its scale before adding the sign.')
inverse = anchor.inverted()
x0, x1, front, base = 0.0, 10.06, 0.0, 0.0
if foundation:
    points = points_in_frame(foundation, inverse)
    x0, x1, base = min(p.x for p in points), max(p.x for p in points), min(p.z for p in points)
right_garage = house.get('garage_side_from_street', 'right') == 'right' if house else True
garage = find_mesh(house, 'Projecting garage foundation')
gx0, gx1 = (x1 - 5.97, x1) if right_garage else (x0, x0 + 5.97)
if garage:
    points = points_in_frame(garage, inverse)
    gx0, gx1 = min(p.x for p in points), max(p.x for p in points)
    front = min(p.y for p in points)
sx = ((x0 + gx0) / 2 if right_garage else (gx1 + x1) / 2) if SIGN_X is None else SIGN_X
road_y = front - 7.0 - (sx - (x0 + x1) / 2) ** 2 / (2 * 185.0)

# Read the actual road ribbon when available rather than importing/executing
# the environment generator. The larger Y at each X is the lot-side edge.
environment = bpy.data.collections.get('HONOR_ENVIRONMENT')
road = find_mesh(environment, 'Environment | gently curved unmarked residential road')
if road:
    columns = {}
    for p in points_in_frame(road, inverse):
        key = round(p.x, 6)
        columns[key] = max(columns.get(key, -float('inf')), p.y)
    xs = sorted(columns)
    if xs and xs[0] <= sx <= xs[-1]:
        for a, b in zip(xs[:-1], xs[1:]):
            if a <= sx <= b:
                t = (sx - a) / (b - a)
                road_y = columns[a] * (1 - t) + columns[b] * t
                break
sy = road_y + ROAD_CLEARANCE if SIGN_Y is None else SIGN_Y
sz = base - 0.035 if SIGN_Z is None else SIGN_Z
SIGN_FRAME = (anchor @ Matrix.Translation((sx, sy, sz)) @
              Matrix.Rotation(math.radians(ANGLE_DEGREES), 4, 'Z'))


# -------------------------- isolated rerun cleanup --------------------------
def descendants(collection):
    result = [collection]
    for child in collection.children:
        result.extend(descendants(child))
    return result


old = bpy.data.collections.get(COLLECTION_NAME)
if old is not None:
    groups = descendants(old)
    if any(not c.get(OWNER) for c in groups) or any(not o.get(OWNER) for o in old.all_objects):
        raise RuntimeError('HONOR_SIGN contains unowned data; rename the collection first.')
    for obj in list(old.all_objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for group in reversed(groups):
        bpy.data.collections.remove(group)
for library in (bpy.data.meshes, bpy.data.curves, bpy.data.materials):
    for item in list(library):
        if item.get(OWNER) and item.users == 0:
            library.remove(item)

COL = bpy.data.collections.new(COLLECTION_NAME)
COL[OWNER] = True
COL['wording'] = LINE_1 + '\n' + LINE_2
COL['placement'] = 'Front lawn, street-facing; visual placement only'
bpy.context.scene.collection.children.link(COL)


def linear(v):
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def material(name, rgb):
    mat = bpy.data.materials.new('Sign | ' + name)
    mat[OWNER] = True
    mat.use_nodes = True
    color = tuple(linear(v) for v in rgb) + (1.0,)
    mat.diffuse_color = color
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = color
    shader.inputs['Roughness'].default_value = 0.57
    return mat


WHITE = material('warm white board and posts', (0.945, 0.949, 0.933))
DARK = material('charcoal lettering and trim', (0.16, 0.19, 0.20))
ACCENT = material('muted coastal blue lettering', (0.25, 0.43, 0.48))


def box(name, lo, hi, mat, bevel=0.006):
    a, b, c = lo
    d, e, f = hi
    vertices = [(a, b, c), (d, b, c), (d, e, c), (a, e, c),
                (a, b, f), (d, b, f), (d, e, f), (a, e, f)]
    faces = [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    mesh = bpy.data.meshes.new('Sign | ' + name)
    mesh[OWNER] = True
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(mat)
    mesh.update()
    obj = bpy.data.objects.new('Sign | ' + name, mesh)
    obj[OWNER] = True
    COL.objects.link(obj)
    obj.matrix_world = SIGN_FRAME.copy()
    if bevel:
        modifier = obj.modifiers.new('soft painted edges', 'BEVEL')
        modifier.width = bevel
        modifier.segments = 3
    return obj


# Front is negative Y. Posts are behind the board; trim surrounds a white inset.
w, h, bottom = SIGN_WIDTH, SIGN_HEIGHT, PANEL_BOTTOM
top = bottom + h
box('charcoal outer frame', (-w / 2, -0.035, bottom), (w / 2, 0.035, top), DARK, 0.012)
box('white inset face', (-w / 2 + 0.035, -0.047, bottom + 0.035),
    (w / 2 - 0.035, -0.030, top - 0.035), WHITE)
for side in (-1, 1):
    x = side * (w / 2 - 0.18)
    box('white support post %s' % side, (x - 0.045, 0.035, -0.20),
        (x + 0.045, 0.125, top + 0.08), WHITE)
    box('post cap %s' % side, (x - 0.057, 0.023, top + 0.075),
        (x + 0.057, 0.137, top + 0.11), DARK)
box('small blue divider', (-w * 0.32, -0.052, bottom + h * 0.46),
    (w * 0.32, -0.046, bottom + h * 0.46 + 0.008), ACCENT, 0.002)


def lettering(name, body, center_z, max_width, max_height, mat):
    curve = bpy.data.curves.new('Sign | ' + name, type='FONT')
    curve[OWNER] = True
    curve.body = body
    curve.align_x = 'CENTER'
    curve.align_y = 'CENTER'
    curve.size = 1.0
    curve.extrude = 0.002
    curve.resolution_u = 8
    curve.materials.append(mat)
    obj = bpy.data.objects.new('Sign | ' + name, curve)
    obj[OWNER] = True
    COL.objects.link(obj)
    bpy.context.view_layer.update()
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    temporary = evaluated.to_mesh()
    try:
        if temporary is None or not temporary.vertices:
            raise RuntimeError('Could not generate sign lettering: ' + body)
        xs = [v.co.x for v in temporary.vertices]
        ys = [v.co.y for v in temporary.vertices]
        width, height = max(xs) - min(xs), max(ys) - min(ys)
        center = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, 0))
        scale = min(max_width / max(width, 1e-6), max_height / max(height, 1e-6))
    finally:
        evaluated.to_mesh_clear()
    # Text's local +Y becomes up (+Z); its front normal becomes street-facing -Y.
    # Center from actual glyph bounds, then uniformly fit without stretching.
    obj.matrix_world = (SIGN_FRAME @ Matrix.Translation((0, -0.053, center_z)) @
                        Matrix.Rotation(math.pi / 2, 4, 'X') @
                        Matrix.Diagonal((scale, scale, scale, 1.0)) @
                        Matrix.Translation(-center))
    return obj


lettering('address', LINE_1, bottom + h * 0.69, w - 0.20, h * 0.23, DARK)
lettering('future home message', LINE_2, bottom + h * 0.27, w - 0.28, h * 0.19, ACCENT)
bpy.context.view_layer.update()
print('Honor front-lawn sign added: ' + LINE_1 + ' / ' + LINE_2)
print('Existing models and scene settings were not changed. Rerun to replace only this sign.')
