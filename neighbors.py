"""Rough exterior neighbors from across_the_street.jpeg.

Run honor.py, honor_pool.py and honor_environment.py first, then this script
in Blender's Text Editor. No add-ons, textures, cameras, lights or interiors.
Rerunning replaces ONLY this script's owned HONOR_NEIGHBORS collection.
House, pool and environment objects/materials are read, never modified.

PHOTO INTERPRETATION
Only the immediate row on the opposite side of the truck's street is modeled.
The truck marks the Honor lot, NOT a neighboring driveway. The pale one-story
hip-roof home near the green van is the approximate opposite-lot reference.
The two blue-gray two-story homes lie toward photo-left; another blue-gray
home and the partly cropped end home lie toward photo-right. The roof-overlap
sequence toward the distant bend is represented by manually listed masses.
Fifteen approximate exterior masses are listed below, including the cropped
end home; the tightly overlapping far-end roof count and hidden elevations
are interpretations, not measured/confirmed house identities.
No other rows beyond the ponds, cross-street houses, construction sites,
ponds, vehicles or property fences are generated. Hidden backs are generic.
Colors, sizes, setbacks and spacing are inferred, not surveyed specifications.
Roof course strips suggest tile roofing without individual tile geometry.
Windows are opaque exterior panels over solid masses, not interior openings.

ALIGNMENT
Uses the existing environment road mesh in the Honor foundation frame.
Actual road vertices are interpolated; a fitted parabola continues the curve
only where the photographed row exceeds the current environment's extent.
That extra street/verge/sidewalk/grass belongs to HONOR_NEIGHBORS and never
covers the existing road/grass. Turn EXTEND_SETTING off to omit extensions.
Photo-left maps to +X when looking outward from Honor toward -Y.
ROW_SHIFT_LOTS adjusts the uncertain truck-to-opposite-house registration.
Rerun after moving/rebuilding the house or environment; re-export afterward.
Source reviewed only: execute and inspect in Blender before final export.
"""

import math
import bpy
import bmesh
from mathutils import Matrix, Vector


COLLECTION_NAME = 'HONOR_NEIGHBORS'
OWNER = 'honor_neighbors_generated'
REFERENCE_IMAGE = r'C:\Users\timh\Downloads\across_the_street.jpeg'
ROW_SHIFT_LOTS = 0.0             # +1 shifts the row one frontage toward photo-right
FRONT_SETBACK = 7.0              # approximate garage face to far road edge
EXTEND_SETTING = True           # support the visible row beyond existing road ends
BUILD_DRIVEWAYS = True
BUILD_ROOF_COURSES = True
BUILD_LANAI_FRAMES = True        # a few visible rear enclosure silhouettes
LOT_DEPTH = 38.0                 # matches the expanded opposite grassy lots
LAWN_RELIEF = 0.10

# Explicit photo-order list, NOT random houses or a generated distant estate.
# slot, label, width, depth, stories, body tone, roof tone, garage side, lanai
# Negative slots run toward photo-left/the distant bend. Slot 0 is the
# approximate home opposite the truck-marked Honor lot. Far-end details are
# especially uncertain because the roofs obscure the facades.
HOUSES = [
    (-12, 'bend end pale low home',         11.2, 14.8, 1, 'ivory', 'gray',  'left', False),
    (-11, 'bend pale warm-roof home',      11.0, 15.2, 1, 'pale',  'warm',  'left', False),
    (-10, 'bend light warm-roof home',     11.4, 15.5, 1, 'ivory', 'warm',  'left', False),
    (-9,  'bend gray warm-roof home',      11.1, 15.3, 1, 'gray',  'warm',  'left', True),
    (-8,  'white two-story landmark',      11.2, 15.8, 2, 'ivory', 'gray',  'left', True),
    (-7,  'middle pale low home',          11.5, 16.0, 1, 'pale',  'warm',  'left', True),
    (-6,  'middle light-gray low home',    11.5, 16.2, 1, 'gray',  'gray',  'left', False),
    (-5,  'middle blue-gray low home',     11.6, 16.0, 1, 'blue',  'gray',  'left', True),
    (-4,  'middle warm-roof low home',     11.8, 16.0, 1, 'pale',  'warm',  'left', False),
    (-3,  'near pale broad single-story',  12.0, 16.3, 1, 'pale',  'warm',  'left', False),
    (-2,  'near blue two-story stepped',   11.0, 15.4, 2, 'blue',  'warm',  'left', False),
    (-1,  'blue-gray two-story by SUV',    10.8, 15.2, 2, 'blue',  'gray',  'left', False),
    (0,   'pale hip-roof opposite truck',  11.2, 17.0, 1, 'ivory', 'gray',  'right', False),
    (1,   'blue two-story photo-right',    11.0, 15.6, 2, 'blue',  'warm',  'left', True),
    (2,   'partly cropped right-end home', 11.3, 15.4, 2, 'gray',  'gray',  'left', False),
]


def find_mesh(collection, prefix):
    return next((o for o in collection.all_objects
                 if o.type == 'MESH' and o.name.startswith(prefix)), None) if collection else None


def frame_points(obj, inverse):
    return [inverse @ (obj.matrix_world @ v.co) for v in obj.data.vertices]


# Read and validate dependencies BEFORE removing the previous neighbors.
bpy.context.view_layer.update()
house = bpy.data.collections.get('HONOR_FH1')
environment = bpy.data.collections.get('HONOR_ENVIRONMENT')
foundation = find_mesh(house, 'Main foundation')
road_obj = find_mesh(environment, 'Environment | gently curved unmarked residential road')
if foundation is None or road_obj is None:
    raise RuntimeError('Run honor.py and honor_environment.py before neighbors.py.')
anchor = foundation.matrix_world.copy()
if abs(anchor.determinant()) < 1e-9:
    raise RuntimeError('Honor foundation has a singular transform.')
inverse = anchor.inverted()
fp = frame_points(foundation, inverse)
CX = (min(p.x for p in fp) + max(p.x for p in fp)) / 2
BASE_Z = min(p.z for p in fp)
GROUND_Z = BASE_Z - 0.035
LOT_WIDTH = float(environment.get('estimated_frontage_m', 16.0))
LOT_DEPTH = float(environment.get('opposite_grassy_lot_depth_m', LOT_DEPTH))
assert LOT_WIDTH > 13.5 and LOT_DEPTH > FRONT_SETBACK + 22.0

# Read both edges at each road column. Rounded keys merge duplicate vertices.
columns = {}
road_points = frame_points(road_obj, inverse)
for p in road_points:
    columns.setdefault(round(p.x, 6), []).append(p.y)
XS = sorted(columns)
if len(XS) < 3:
    raise RuntimeError('Environment road has too few columns for alignment.')
NEAR = [max(columns[x]) for x in XS]
FAR = [min(columns[x]) for x in XS]
ROAD_Z = sum(p.z for p in road_points) / len(road_points)
ROAD_WIDTH = sum(n - f for n, f in zip(NEAR, FAR)) / len(XS)
XMIN, XMAX = XS[0], XS[-1]
assert ROAD_WIDTH > 1.0
SIDEWALK = find_mesh(environment, 'Environment | opposite sidewalk only - no houses') is not None

# Fit y = A*x*x + B*x + C to three road columns, using centered coordinates.
k = len(XS) // 2
u0, u1, u2 = XS[0] - CX, XS[k] - CX, XS[-1] - CX
y0, y1, y2 = NEAR[0], NEAR[k], NEAR[-1]
A = ((y2 - y1) / (u2 - u1) - (y1 - y0) / (u1 - u0)) / (u2 - u0)
B = (y1 - y0) / (u1 - u0) - A * (u1 + u0)
C = y0 - A * u0 * u0 - B * u0


def road_near(x):
    if x <= XMIN or x >= XMAX:
        u = x - CX
        return A * u * u + B * u + C
    # Match the actual polygonal road, not just the analytic approximation.
    import bisect
    i = min(len(XS) - 2, max(0, bisect.bisect_right(XS, x) - 1))
    t = (x - XS[i]) / (XS[i + 1] - XS[i])
    return NEAR[i] * (1 - t) + NEAR[i + 1] * t


def road_far(x):
    return road_near(x) - ROAD_WIDTH


def arc_length(x):
    # Signed distance along the fitted curve from the Honor centerline.
    if abs(A) < 1e-10:
        return (x - CX) * math.sqrt(1 + B * B)
    def primitive(u):
        return 0.5 * (u * math.sqrt(1 + u * u) + math.asinh(u))
    return (primitive(2 * A * (x - CX) + B) - primitive(B)) / (2 * A)


def x_at_arc(distance):
    lo, hi = CX - abs(distance) - 1, CX + abs(distance) + 1
    for _ in range(60):
        mid = (lo + hi) / 2
        if arc_length(mid) < distance:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


placements = []
for spec in HOUSES:
    slot, label, width, depth, stories, body, roof, garage, lanai = spec
    x = x_at_arc(-(slot + ROW_SHIFT_LOTS) * LOT_WIDTH)
    slope = 2 * A * (x - CX) + B
    # Local +Y is away from the road, local front faces -Y. Rotation only:
    # no negative scales, so window/roof normals remain consistent.
    angle = math.pi + math.atan(slope)
    rotation = Matrix.Rotation(angle, 4, 'Z')
    inward = rotation @ Vector((0, 1, 0))
    across = rotation @ Vector((1, 0, 0))
    center = Vector((x, road_far(x), GROUND_Z)) + inward * FRONT_SETBACK
    origin = center - across * width / 2
    transform = Matrix.Translation(origin) @ rotation
    placements.append((spec, transform))


def descendants(col):
    result = [col]
    for child in col.children:
        result.extend(descendants(child))
    return result


old = bpy.data.collections.get(COLLECTION_NAME)
if old:
    groups = descendants(old)
    if any(not c.get(OWNER) for c in groups) or any(not o.get(OWNER) for o in old.all_objects):
        raise RuntimeError('HONOR_NEIGHBORS contains unowned data; rename it first.')
    for obj in list(old.all_objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for col in reversed(groups):
        bpy.data.collections.remove(col)
for mesh in list(bpy.data.meshes):
    if mesh.get(OWNER) and mesh.users == 0:
        bpy.data.meshes.remove(mesh)
for mat in list(bpy.data.materials):
    if mat.get(OWNER) and mat.users == 0:
        bpy.data.materials.remove(mat)
ROOT = bpy.data.collections.new(COLLECTION_NAME)
ROOT[OWNER] = True
ROOT['reference_image'] = REFERENCE_IMAGE
ROOT['registration'] = 'Truck = Honor lot; pale single-story near green van approximately opposite'
ROOT['accuracy'] = 'Photo-inspired rough exteriors; far roof overlaps and hidden elevations interpreted'
ROOT['row_shift_lots'] = ROW_SHIFT_LOTS
ROOT['house_count'] = len(HOUSES)
bpy.context.scene.collection.children.link(ROOT)


def material(name, rgb, roughness=0.8):
    mat = bpy.data.materials.new('Neighbors | ' + name)
    mat[OWNER] = True
    mat.use_nodes = True
    color = tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb) + (1,)
    mat.diffuse_color = color
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = color
    shader.inputs['Roughness'].default_value = roughness
    return mat


MATERIALS = []
INDEX = {}
for name, color, rough in (
        ('ivory', (0.83, 0.84, 0.81), 0.88),
        ('pale', (0.72, 0.74, 0.71), 0.88),
        ('gray', (0.58, 0.63, 0.64), 0.88),
        ('blue', (0.47, 0.56, 0.61), 0.88),
        ('trim', (0.90, 0.90, 0.86), 0.60),
        ('roof_gray', (0.53, 0.55, 0.56), 0.90),
        ('roof_warm', (0.58, 0.54, 0.52), 0.90),
        ('glass', (0.16, 0.23, 0.27), 0.25),
        ('dark', (0.14, 0.16, 0.17), 0.75),
        ('concrete', (0.70, 0.69, 0.64), 0.88),
        ('grass', (0.30, 0.37, 0.19), 0.98),
        ('asphalt', (0.38, 0.39, 0.40), 0.92),
        ('shrub', (0.20, 0.29, 0.13), 0.95)):
    INDEX[name] = len(MATERIALS)
    MATERIALS.append(material(name, color, rough))
# Reuse existing swatches for seamless extensions; never change these materials.
for key, prefix in (('grass', 'Environment | patchy cleared grass'),
                    ('asphalt', 'Environment | weathered gray asphalt'),
                    ('concrete', 'Environment | warm pale concrete')):
    existing = next((m for m in bpy.data.materials if m.name.startswith(prefix)), None)
    if existing:
        MATERIALS[INDEX[key]] = existing


class Geo:
    def __init__(self):
        self.v, self.f, self.mi = [], [], []

    def prism(self, ring, offset, mat):
        k, n = len(self.v), len(ring)
        off = Vector(offset)
        self.v.extend(tuple(p) for p in ring)
        self.v.extend(tuple(Vector(p) + off) for p in ring)
        faces = [tuple(k + i for i in reversed(range(n))), tuple(k + n + i for i in range(n))]
        faces.extend((k + i, k + (i + 1) % n, k + n + (i + 1) % n, k + n + i) for i in range(n))
        self.f.extend(faces)
        self.mi.extend([INDEX[mat]] * len(faces))

    def box(self, lo, hi, mat):
        a, b, c = lo
        d, e, f = hi
        if min(d - a, e - b, f - c) <= 1e-7:
            return
        self.prism([(a, b, c), (d, b, c), (d, e, c), (a, e, c)], (0, 0, f - c), mat)

    def face(self, points, mat):
        k = len(self.v)
        self.v.extend(tuple(p) for p in points)
        self.f.append(tuple(range(k, k + len(points))))
        self.mi.append(INDEX[mat])

    def beam(self, a, b, width, mat):
        a, b = Vector(a), Vector(b)
        axis = (b - a).normalized()
        ref = Vector((0, 0, 1)) if abs(axis.z) < 0.95 else Vector((1, 0, 0))
        u = axis.cross(ref).normalized() * width / 2
        v = axis.cross(u).normalized() * width / 2
        self.prism([a - u - v, a + u - v, a + u + v, a - u + v], b - a, mat)

    def finish(self, name, transform=None):
        if not self.f:
            return None
        mesh = bpy.data.meshes.new('Neighbors | ' + name)
        mesh[OWNER] = True
        mesh.from_pydata(self.v, [], self.f)
        for mat in MATERIALS:
            mesh.materials.append(mat)
        for poly, index in zip(mesh.polygons, self.mi):
            poly.material_index = index
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(mesh)
        bm.free()
        mesh.update()
        obj = bpy.data.objects.new('Neighbors | ' + name, mesh)
        obj[OWNER] = True
        obj.matrix_world = anchor @ (transform if transform is not None else Matrix.Identity(4))
        ROOT.objects.link(obj)
        return obj


def hip(g, rect, eave, pitch, tone):
    x0, y0, x1, y1 = rect
    w, d = x1 - x0, y1 - y0
    run = min(w, d) / 2
    top = eave + run * pitch
    a, b, c, dpt = (x0, y0, eave), (x1, y0, eave), (x1, y1, eave), (x0, y1, eave)
    if w <= d:
        p, q = ((x0 + x1) / 2, y0 + run, top), ((x0 + x1) / 2, y1 - run, top)
        faces = ([a, b, p], [b, c, q, p], [c, dpt, q], [dpt, a, p, q])
    else:
        p, q = (x0 + run, (y0 + y1) / 2, top), (x1 - run, (y0 + y1) / 2, top)
        faces = ([a, b, q, p], [b, c, q], [c, dpt, p, q], [dpt, a, p])
    for face in faces:
        # Square hips have one peak; discard repeated ridge endpoints.
        unique = []
        for point in face:
            if point not in unique:
                unique.append(point)
        g.prism(unique, (0, 0, -0.09), 'roof_' + tone)
    for start, end in ((a, b), (b, c), (c, dpt), (dpt, a)):
        g.beam(tuple(Vector(start) - Vector((0, 0, 0.07))),
               tuple(Vector(end) - Vector((0, 0, 0.07))), 0.14, 'trim')
    if (Vector(q) - Vector(p)).length > 0.001:
        g.beam(tuple(Vector(p) + Vector((0, 0, 0.025))),
               tuple(Vector(q) + Vector((0, 0, 0.025))), 0.075, 'roof_' + tone)
    if BUILD_ROOF_COURSES:
        # Shallow real geometry remains visible in GLB without external textures.
        inset = 0.18
        while inset < run - 0.12:
            z = eave + inset * pitch + 0.012
            l, r, f, back = x0 + inset, x1 - inset, y0 + inset, y1 - inset
            for start, end in (((l, f, z), (r, f, z)), ((r, f, z), (r, back, z)),
                               ((r, back, z), (l, back, z)), ((l, back, z), (l, f, z))):
                g.beam(start, end, 0.025, 'roof_' + tone)
            inset += 0.32


def window(g, center, axis='front', width=0.90, height=1.35):
    x, y, z = center
    # Local panel coordinates: horizontal, outward thickness, vertical.
    def panel(a, b, low, high, depth, mat):
        if axis == 'front':
            g.box((x + a, y - depth, z + low), (x + b, y - 0.003, z + high), mat)
        elif axis == 'back':
            g.box((x + a, y + 0.003, z + low), (x + b, y + depth, z + high), mat)
        elif axis == 'left':
            g.box((x - depth, y + a, z + low), (x - 0.003, y + b, z + high), mat)
        else:
            g.box((x + 0.003, y + a, z + low), (x + depth, y + b, z + high), mat)
    h = width / 2
    panel(-h, h, 0, height, 0.035, 'glass')
    for a, b in ((-h - 0.065, -h), (h, h + 0.065)):
        panel(a, b, -0.055, height + 0.055, 0.07, 'trim')
    for lo, hi in ((-0.055, 0), (height, height + 0.055), (height * 0.47, height * 0.47 + 0.035)):
        panel(-h, h, lo, hi, 0.07, 'trim')


def build_house(spec, transform):
    slot, label, w, d, stories, body, roof, garage_side, lanai = spec
    g = Geo()
    floor = 0.18
    garage_w = 5.45
    # Build the standard facade, then mirror its local X geometry for the
    # right-garage variant. Winding is reversed together with the reflection.
    g.box((0, 3.0, -0.08), (w, d, floor), 'concrete')
    g.box((0, 3.0, floor), (w, d, 3.20), body)
    g.box((0, 0, -0.08), (garage_w, 5.0, floor), 'concrete')
    g.box((0, 0, floor), (garage_w, 5.0, 3.00), body)
    g.box((7.3, 1.7, floor), (w, 4.0, 3.20), body)
    g.box((5.45, 1.65, 0.08), (7.3, 3.0, floor), 'concrete')
    if stories == 2:
        upper_x = 0.0 if slot in (-8, -1, 2) else 2.0
        g.box((upper_x, 3.0, 3.20), (w, d - 1.0, 6.02), body)
        g.box((upper_x - 0.025, 2.97, 3.18), (w + 0.025, 3.04, 3.32), 'trim')
        hip(g, (upper_x - 0.35, 2.65, w + 0.35, d - 0.65), 6.06, 0.40, roof)
        # Lower rear wing closes the step below the upper mass.
        hip(g, (-0.3, d - 3.0, w + 0.3, d + 0.35), 3.23, 0.34, roof)
        if upper_x > 0:
            hip(g, (-0.3, 4.8, upper_x + 0.12, d - 2.9), 3.24, 0.35, roof)
        for x in (upper_x + 1.25, (upper_x + w) / 2, w - 1.25):
            window(g, (x, 3.0, 4.05), width=0.92, height=1.42)
        for y in (6.0, 10.0, d - 2.5):
            window(g, (w, y, 4.12), 'right', 0.82, 1.25)
            window(g, (upper_x, y, 4.12), 'left', 0.82, 1.25)
    else:
        hip(g, (-0.35, 2.65, w + 0.35, d + 0.35), 3.24, 0.40, roof)
    hip(g, (-0.33, -0.35, garage_w + 0.30, 3.9), 3.04, 0.40, roof)
    hip(g, (7.0, 1.35, w + 0.30, 4.15), 3.24, 0.36, roof)
    # Recessed front entry, two porch posts and a simple low canopy.
    g.box((5.92, 2.95, floor), (6.84, 2.985, floor + 2.15), 'dark')
    g.box((5.84, 2.90, floor + 2.15), (6.92, 2.97, floor + 2.23), 'trim')
    for x in (5.55, 7.12):
        g.box((x, 1.73, floor), (x + 0.14, 1.87, 2.77), 'trim')
    hip(g, (5.3, 1.4, 7.5, 3.1), 2.82, 0.25, roof)
    # Closed sectional garage: panel fields and thin horizontal joints.
    g.box((0.27, -0.035, floor), (garage_w - 0.27, -0.006, floor + 2.30), 'trim')
    for row in range(4):
        z = floor + row * 0.565
        for col in range(4):
            x = 0.36 + col * (garage_w - 0.72) / 4
            g.box((x, -0.052, z + 0.055), (x + (garage_w - 0.72) / 4 - 0.05, -0.036, z + 0.48), 'pale')
    for x in (0.16, garage_w - 0.23):
        g.box((x, -0.06, floor), (x + 0.07, -0.005, floor + 2.4), 'trim')
    g.box((0.16, -0.06, floor + 2.30), (garage_w - 0.16, -0.005, floor + 2.4), 'trim')
    for x in (8.1, w - 0.85):
        window(g, (x, 1.7, 0.86), width=0.86, height=1.48)
    for y in (6.8, 10.7, d - 1.6):
        window(g, (0, y, 1.0), 'left', 0.76, 1.24)
        window(g, (w, y, 1.0), 'right', 0.88, 1.35)
    for x in (2.0, w - 2.0):
        window(g, (x, d, 0.90), 'back', 1.30, 1.40)
    g.box((w / 2 - 1.25, d + 0.006, floor), (w / 2 + 1.25, d + 0.04, floor + 2.20), 'glass')
    if BUILD_LANAI_FRAMES and lanai:
        # Frame-only screen enclosure silhouette, no opaque box or interior.
        l, r, f, back, top = 0.7, w - 0.7, d + 0.05, d + 3.0, 2.65
        g.box((l, f, 0.025), (r, back, 0.075), 'concrete')
        for x in (l, (l + r) / 2, r):
            for y in (f, back):
                g.beam((x, y, 0.075), (x, y, top), 0.045, 'dark')
            g.beam((x, f, top), (x, back, top), 0.045, 'dark')
        for y in (f, back):
            for z in (0.25, 1.10, top):
                g.beam((l, y, z), (r, y, z), 0.04, 'dark')
        for x in (l, r):
            g.beam((x, f, 1.10), (x, back, 1.10), 0.035, 'dark')
    if garage_side == 'right':
        g.v = [(w - x, y, z) for x, y, z in g.v]
        g.f = [tuple(reversed(face)) for face in g.f]
    obj = g.finish('%+03d | %s | rough exterior' % (slot, label), transform)
    obj['photo_order_slot'] = slot
    obj['stories'] = stories
    obj['reference_image'] = REFERENCE_IMAGE
    obj['detail_note'] = 'Approximate exterior only; hidden elevations inferred; opaque windows'
    if BUILD_DRIVEWAYS:
        build_driveway(slot, w, garage_w, garage_side, transform)


def build_driveway(slot, w, garage_w, side, transform):
    g = Geo()
    left, right = (0.18, garage_w - 0.18) if side == 'left' else (w - garage_w + 0.18, w - 0.18)
    garage = [transform @ Vector((x, -0.055, 0.174)) for x in (left, right)]
    # Garage edge to sampled far road edge, following the rotated home.
    for i in range(24):
        rows = []
        for t in (i / 24, (i + 1) / 24):
            row = []
            for j, end in enumerate(garage):
                x = end.x + (-0.28 if j == 0 else 0.28) * (1 - t)
                y = (road_far(x) + 0.04) * (1 - t) + end.y * t
                distance = road_far(x) - y
                if distance < 0.24:
                    z = ROAD_Z + 0.012 + (GROUND_Z + 0.028 - ROAD_Z - 0.012) * max(0, distance / 0.24)
                else:
                    full = max(3.1, road_far(end.x) - end.y)
                    rise = max(0.0, min(1.0, (distance - 3.0) / (full - 3.0)))
                    z = GROUND_Z + 0.028 + rise * (end.z - GROUND_Z - 0.028)
                row.append((x, y, z))
            rows.append(row)
        # Solid apron overlays the curb/sidewalk only at each actual driveway.
        g.prism([rows[0][0], rows[0][1], rows[1][1], rows[1][0]], (0, 0, -0.14), 'concrete')
    g.finish('%+03d | driveway and curb apron' % slot)
    walk = Geo()
    entry = 6.4 if side == 'left' else w - 6.4
    garage_edge = garage_w - 0.3 if side == 'left' else w - garage_w + 0.3
    walk.box((min(entry - 0.50, garage_edge), -0.65, 0.02),
             (max(entry + 0.50, garage_edge), 0.35, 0.12), 'concrete')
    walk.box((entry - 0.50, 0.35, 0.02), (entry + 0.50, 1.80, 0.12), 'concrete')
    walk.finish('%+03d | simple entry walk' % slot, transform)


def lawn_z(x, distance):
    t = max(0.0, min(1.0, (distance - 24.0) / 10.0))
    t = t * t * (3 - 2 * t)
    return GROUND_Z + LAWN_RELIEF * t * (
        0.65 * math.sin((x - CX) * 0.10) * math.sin(distance * 0.19)
        + 0.35 * math.sin((x - CX) * 0.045 + distance * 0.13))


def extend_setting(left, right):
    if right - left < 0.001:
        return
    g = Geo()
    n = math.ceil((right - left) / 0.8)
    for i in range(n):
        a, b = left + (right - left) * i / n, left + (right - left) * (i + 1) / n
        def strip(d0, d1, z0, z1, mat):
            g.face([(a, road_far(a) - d1, z1), (b, road_far(b) - d1, z1),
                    (b, road_far(b) - d0, z0), (a, road_far(a) - d0, z0)], mat)
        strip(-ROAD_WIDTH, 0, ROAD_Z, ROAD_Z, 'asphalt')
        strip(-ROAD_WIDTH - 0.22, -ROAD_WIDTH, GROUND_Z + 0.005, ROAD_Z, 'concrete')
        strip(0, 0.22, ROAD_Z, GROUND_Z + 0.005, 'concrete')
        if SIDEWALK:
            strip(1.65, 3.0, GROUND_Z + 0.018, GROUND_Z + 0.018, 'concrete')
        for near, far in ([(0.22, 1.65), (3.0, LOT_DEPTH)] if SIDEWALK else [(0.22, LOT_DEPTH)]):
            distance = near
            while distance < far - 1e-7:
                end = min(distance + 2.5, far)
                p = [(a, road_far(a) - end, lawn_z(a, end)),
                     (b, road_far(b) - end, lawn_z(b, end)),
                     (b, road_far(b) - distance, lawn_z(b, distance)),
                     (a, road_far(a) - distance, lawn_z(a, distance))]
                g.face([p[0], p[1], p[2]], 'grass')
                g.face([p[0], p[2], p[3]], 'grass')
                distance = end
    g.finish('photo-row supporting street and grass extension %.1f to %.1f' % (left, right))


if EXTEND_SETTING:
    extents = []
    for spec, transform in placements:
        w, d = spec[2], spec[3]
        extents.extend((transform @ Vector((x, y, 0))).x
                       for x in (-0.5, w + 0.5) for y in (-1.0, d + 3.5))
    extend_setting(min(XMIN, min(extents) - 5), XMIN)
    extend_setting(XMAX, max(XMAX, max(extents) + 5))
for spec, transform in placements:
    build_house(spec, transform)
# Remove unused owned swatches, but never touch shared environment materials.
for mat in list(bpy.data.materials):
    if mat.get(OWNER) and mat.users == 0:
        bpy.data.materials.remove(mat)
bpy.context.view_layer.update()
print('[Neighbors] Created %d rough exterior homes in %s.' % (len(HOUSES), COLLECTION_NAME))
print('[Neighbors] Immediate opposite row only; truck-to-house alignment and obscured roofs are approximate.')
print('[Neighbors] House, pool and environment untouched. No interiors, ponds, vehicles, cameras or lights.')
print('[Neighbors] Inspect the row in Blender; adjust HOUSES / ROW_SHIFT_LOTS if needed, then re-export.')
