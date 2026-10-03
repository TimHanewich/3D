"""Honor environment — aerial-inspired companion to house and pool.

RUN: honor_exterior.py, then honor_pool.py, then this file in Blender's Text Editor.
No add-ons, external textures, downloads, cameras or lights.
Lit materials use the Solid swatch base colors without procedural color mixing.
Bump detail is retained in Blender; appearance varies with lighting.
Sets scene-wide Standard/sRGB color management; no companion script required.
All generated surface materials use lit Principled shaders.
Rerunning replaces ONLY owned HONOR_ENVIRONMENT data. Existing house/pool objects
and materials are read, never changed. Intended for Blender 3.6+.

REFERENCE: user-supplied backyard.jpeg; the black truck identifies the home lot.
Curved residential street, open rear lawn, an irregular palmetto/brush edge,
a deep mixed preserve, a narrow utility clearing and a long retention pond.
The pond is offset left when looking out the back (+Y), with clipped corners,
muted green water, pale lower lining, dark upper lining and a grassy berm.
Species, distances, pond dimensions and lot boundaries are visual estimates,
NOT surveyed measurements. No distant roads, vehicles or neighboring houses.
Open neighboring lots remain continuous grass, without invented fences or
painted boundary lines. Rear-only ground extensions contain the full pond;
residential street width, frontage and opposite lots are unchanged.
User opposite-lot revision: grass extends 38 meters from the far road edge,
following the street curve, with flat potential home sites and subtle rear-lawn
relief. The existing opposite sidewalk is retained with a grass cutout below it.
Opposite lot depth and grading are inferred and adjustable below.

Coordinates: meters, +Y rear, front faces -Y, matching honor_exterior.py.
Reads the house foundation transform; follows its placement when regenerated.
Pool ground cutout is read in that same coordinate system. Keep house and pool
in registration before running. Fallback dimensions match the supplied scripts.

The useful scale/layout controls are below. Tree/brush meshes are shared among
instances. All vegetation is simple opaque geometry, not individual leaves.
Progress is printed to Blender's console. This file does not save the .blend.
"""

import math
import random
import bpy
import bmesh
from mathutils import Matrix, Vector


# ------------------------------- user controls -------------------------------
COLLECTION_NAME = 'HONOR_ENVIRONMENT'
OWNER = 'honor_environment_generated'
SEED = 1047
NEIGHBOR_LOTS_EACH_SIDE = 4
LOT_WIDTH = 16.0                 # estimated frontage; not a legal boundary
FRONT_SETBACK = 7.0              # garage face to lot-side road edge
ROAD_WIDTH = 7.2
ROAD_RADIUS = 185.0              # larger = straighter; bends away at each end
REAR_LAWN_AFTER_POOL = 9.0        # open lawn before irregular preserve edge
PRESERVE_DEPTH = 175.0          # minimum rear extent, including pond and far trees
BUILD_RETENTION_POND = True
POND_LENGTH = 210.0             # water dimensions; estimated from oblique photo
POND_WIDTH = 65.0
POND_CENTER_LEFT = 28.0         # left of house center when looking toward +Y
POND_CENTER_AFTER_CLEARING = 112.0
POND_ANGLE_DEGREES = 10.0        # long axis rises away from house toward the right
POND_CORNER_CUT = 8.0           # clipped corners, not an ornamental oval
POND_WATER_BELOW_GRADE = 1.65
POND_BERM_HEIGHT = 0.80
POND_BANK_WIDTH = 6.0           # horizontal waterline-to-crest distance
POND_OUTER_SLOPE = 6.0          # crest-to-natural-ground distance
POND_FAR_TREE_BUFFER = 26.0
BUILD_PRESERVE_CORRIDOR = True
BUILD_PRESERVE_UTILITY_POLES = True  # simple photo-inspired silhouettes, no lights
CORRIDOR_AFTER_CLEARING = 48.0
CORRIDOR_WIDTH = 9.0
TREE_DENSITY = 0.033             # approximate trees per square meter
BRUSH_DENSITY = 0.060
VEGETATION_MULTIPLIER = 1.0       # 0.5 for a lighter scene; 1.5 for denser woods
BUILD_DRIVEWAY = True            # inferred connection, not a supplied paving plan
BUILD_ENTRY_WALK = True
BUILD_OPPOSITE_SIDEWALK = True   # sidewalk visible in aerial, but no houses
OPPOSITE_LOT_DEPTH = 38.0        # far road edge to back of grassy lots; inferred
OPPOSITE_LAWN_RELIEF = 0.10      # subtle rear-lawn undulation; frontage stays flat
BUILD_SMALL_STREET_DETAILS = True
GROUND_GRID = 2.5


def progress(message):
    print('[Honor environment] ' + message, flush=True)


# ------------------------- read-only scene alignment -------------------------
def bounds_in_frame(obj, inverse):
    points = [inverse @ (obj.matrix_world @ Vector(c)) for c in obj.bound_box]
    return (min(p.x for p in points), min(p.y for p in points), min(p.z for p in points),
            max(p.x for p in points), max(p.y for p in points), max(p.z for p in points))


def find_mesh(collection, prefix):
    if collection is None:
        return None
    return next((o for o in collection.all_objects
                 if o.type == 'MESH' and o.name.startswith(prefix)), None)


bpy.context.view_layer.update()
HOUSE = bpy.data.collections.get('HONOR_FH1')
FOUNDATION = find_mesh(HOUSE, 'Main foundation')
ANCHOR = FOUNDATION.matrix_world.copy() if FOUNDATION else Matrix.Identity(4)
if abs(ANCHOR.determinant()) < 1e-9:
    raise RuntimeError('House transform is singular; restore nonzero scale first.')
INVERSE = ANCHOR.inverted()
HX0, HX1, FRONT, BACK, BASE_Z = 0.0, 10.06, 0.0, 17.04, 0.0
if FOUNDATION:
    a = bounds_in_frame(FOUNDATION, INVERSE)
    HX0, HX1, BACK, BASE_Z = a[0], a[3], a[4], a[2]
CX = (HX0 + HX1) / 2
GARAGE = find_mesh(HOUSE, 'Projecting garage foundation')
RIGHT_GARAGE = HOUSE.get('garage_side_from_street', 'right') == 'right' if HOUSE else True
GX0, GX1 = (HX1 - 5.97, HX1) if RIGHT_GARAGE else (HX0, HX0 + 5.97)
if GARAGE:
    a = bounds_in_frame(GARAGE, INVERSE)
    GX0, GX1, FRONT = a[0], a[3], a[1]
GARAGE_TOP = bounds_in_frame(GARAGE, INVERSE)[5] if GARAGE else BASE_Z + 0.18
STEP = find_mesh(HOUSE, 'Entry threshold step')
POOL = bpy.data.collections.get('HONOR_POOL')
POOL_REAR = BACK + 30 * 0.3048
POOL_CUTOUT = (CX - 33 * 0.3048 / 2 + 5.5 * 0.3048,
               BACK + 11 * 0.3048,
               CX - 33 * 0.3048 / 2 + 30.5 * 0.3048,
               BACK + 27.5 * 0.3048)
SHELL = find_mesh(POOL, 'Pool | six inch perimeter shell')
if SHELL:
    a = bounds_in_frame(SHELL, INVERSE)
    POOL_CUTOUT = (a[0] - 0.025, a[1] - 0.025, a[3] + 0.025, a[4] + 0.025)
    POOL_REAR = max(POOL_REAR, a[4] + 0.9)
DECK = find_mesh(POOL, 'Pool | deck bed with open basin')
if DECK:
    POOL_REAR = max(POOL_REAR, bounds_in_frame(DECK, INVERSE)[4])

HALF_WIDTH = LOT_WIDTH * (NEIGHBOR_LOTS_EACH_SIDE + 0.5) + 9.0
XMIN, XMAX = CX - HALF_WIDTH, CX + HALF_WIDTH
CLEAR_REAR = POOL_REAR + REAR_LAWN_AFTER_POOL
YMAX = CLEAR_REAR + PRESERVE_DEPTH
GROUND_Z = BASE_Z - 0.035
ROAD_Z = BASE_Z - 0.12
CURB_WIDTH = 0.22
assert min(LOT_WIDTH, ROAD_WIDTH, ROAD_RADIUS, GROUND_GRID, PRESERVE_DEPTH) > 0
assert min(TREE_DENSITY, BRUSH_DENSITY, VEGETATION_MULTIPLIER) >= 0
assert OPPOSITE_LOT_DEPTH > 7.0
assert OPPOSITE_LAWN_RELIEF >= 0
assert min(POND_LENGTH, POND_WIDTH, POND_WATER_BELOW_GRADE,
           POND_BANK_WIDTH, POND_OUTER_SLOPE, POND_FAR_TREE_BUFFER) > 0
assert 0 < POND_CORNER_CUT < min(POND_LENGTH, POND_WIDTH) / 2
assert POND_BERM_HEIGHT >= 0 and CORRIDOR_WIDTH > 0
assert POND_CENTER_AFTER_CLEARING > 0 and CORRIDOR_AFTER_CLEARING > 0

POND_ANGLE = math.radians(POND_ANGLE_DEGREES)
POND_COS, POND_SIN = math.cos(POND_ANGLE), math.sin(POND_ANGLE)
POND_CX = CX - POND_CENTER_LEFT
POND_CY = CLEAR_REAR + POND_CENTER_AFTER_CLEARING
POND_OUTER_OFFSET = POND_BANK_WIDTH + POND_OUTER_SLOPE


def pond_outline(offset=0.0):
    # Counterclockwise convex rings with matching vertices for clean bank strips.
    a, b = POND_LENGTH / 2 + offset, POND_WIDTH / 2 + offset
    c = POND_CORNER_CUT + offset * (2.0 - math.sqrt(2.0))
    local = [(-a + c, -b), (a - c, -b), (a, -b + c), (a, b - c),
             (a - c, b), (-a + c, b), (-a, b - c), (-a, -b + c)]
    return [(POND_CX + u * POND_COS - v * POND_SIN,
             POND_CY + u * POND_SIN + v * POND_COS) for u, v in local]


POND_OUTLINE = pond_outline(POND_OUTER_OFFSET)
PRESERVE_XMIN, PRESERVE_XMAX = XMIN, XMAX
REAR_EXTENSION_Y = CLEAR_REAR - 8.0
if BUILD_RETENTION_POND:
    PRESERVE_XMIN = min(XMIN, min(p[0] for p in POND_OUTLINE) - POND_FAR_TREE_BUFFER)
    PRESERVE_XMAX = max(XMAX, max(p[0] for p in POND_OUTLINE) + POND_FAR_TREE_BUFFER)
    YMAX = max(YMAX, max(p[1] for p in POND_OUTLINE) + POND_FAR_TREE_BUFFER)
    if min(p[1] for p in POND_OUTLINE) < CLEAR_REAR + 16.0:
        raise ValueError('Move the pond farther back to retain woods behind the lawn.')


def inside_pond(x, y, margin=0.0):
    if not BUILD_RETENTION_POND:
        return False
    u = (x - POND_CX) * POND_COS + (y - POND_CY) * POND_SIN
    v = -(x - POND_CX) * POND_SIN + (y - POND_CY) * POND_COS
    a = POND_LENGTH / 2 + POND_OUTER_OFFSET
    b = POND_WIDTH / 2 + POND_OUTER_OFFSET
    c = POND_CORNER_CUT + POND_OUTER_OFFSET * (2.0 - math.sqrt(2.0))
    # Offset all supporting edges, including the diagonal corner cuts.
    return (abs(u) <= a + margin and abs(v) <= b + margin and
            abs(u) + abs(v) <= a + b - c + margin * math.sqrt(2.0))


def corridor_distance(x, y):
    # Same direction as the pond, crossing the wooded buffer, not the home lot.
    return (-(x - CX) * POND_SIN +
            (y - CLEAR_REAR - CORRIDOR_AFTER_CLEARING) * POND_COS)


def in_corridor(x, y, margin=0.0):
    return (BUILD_PRESERVE_CORRIDOR and
            abs(corridor_distance(x, y)) < CORRIDOR_WIDTH / 2 + margin)


def road_edge(x):
    # Smooth parabolic approximation to the shallow curve in the aerial.
    return FRONT - FRONT_SETBACK - (x - CX) ** 2 / (2 * ROAD_RADIUS)


def preserve_edge(x):
    d = x - CX
    return CLEAR_REAR + 2.5 * math.sin(d * 0.072) + 1.2 * math.sin(d * 0.19 + 0.5)


def terrain_z(x, y):
    # Flat near house/pool; small undulations beyond, not a fabricated hillside.
    t = max(0.0, min(1.0, (y - POOL_REAR - 2.0) / 12.0))
    return GROUND_Z + t * (0.12 * math.sin(x * 0.12) * math.sin(y * 0.15))


# ----------------------------- isolated cleanup ------------------------------
def descendants(collection):
    result = [collection]
    for child in collection.children:
        result.extend(descendants(child))
    return result


progress('1/5: checking ownership and preparing scene alignment.')
old = bpy.data.collections.get(COLLECTION_NAME)
if old:
    groups = descendants(old)
    if any(not c.get(OWNER) for c in groups) or any(not o.get(OWNER) for o in old.all_objects):
        raise RuntimeError('HONOR_ENVIRONMENT contains unowned data; rename it first.')
    for obj in list(old.all_objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for group in reversed(groups):
        bpy.data.collections.remove(group)
for mesh in list(bpy.data.meshes):
    if mesh.get(OWNER) and mesh.users == 0:
        bpy.data.meshes.remove(mesh)
for mat in list(bpy.data.materials):
    if mat.get(OWNER) and mat.users == 0:
        bpy.data.materials.remove(mat)

ROOT = bpy.data.collections.new(COLLECTION_NAME)
ROOT[OWNER] = True
ROOT['reference'] = 'User backyard.jpeg; home lot identified by black truck'
ROOT['pond_layout_note'] = 'Photo-inspired estimates; left-offset elongated lined retention basin'
ROOT['pond_water_length_m'] = POND_LENGTH
ROOT['pond_water_width_m'] = POND_WIDTH
ROOT['pond_center_after_clearing_m'] = POND_CENTER_AFTER_CLEARING
ROOT['pond_angle_degrees'] = POND_ANGLE_DEGREES
ROOT['preserve_depth_m'] = YMAX - CLEAR_REAR
ROOT['pond_enabled'] = BUILD_RETENTION_POND
ROOT['utility_clearing_enabled'] = BUILD_PRESERVE_CORRIDOR
ROOT['accuracy'] = 'Aerial-inspired visual setting, NOT a survey or landscape design'
ROOT['coordinates'] = 'Meters in house frame; front -Y, preserve +Y'
ROOT['estimated_frontage_m'] = LOT_WIDTH
ROOT['estimated_rear_clearing_y'] = CLEAR_REAR
ROOT['seed'] = SEED
bpy.context.scene.collection.children.link(ROOT)
GROUPS = {}
for name in ('Ground and open lots', 'Street and access', 'Preserve trees',
             'Preserve brush', 'Retention pond', 'Preserve corridor'):
    col = bpy.data.collections.new('Environment | ' + name)
    col[OWNER] = True
    ROOT.children.link(col)
    GROUPS[name] = col


# ------------------------ procedural earthy materials ------------------------
# Always use lit Principled materials with the Solid swatch base colors.
CONFIGURE_COLOR_MANAGEMENT = True

if CONFIGURE_COLOR_MANAGEMENT:
    scene = bpy.context.scene
    scene.display_settings.display_device = 'sRGB'
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0
    scene.view_settings.use_curve_mapping = False
    if hasattr(scene.view_settings, 'use_white_balance'):
        scene.view_settings.use_white_balance = False


def linear(v):
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def rgba(rgb):
    return tuple(linear(v) for v in rgb) + (1.0,)


def material(name, rgb, second=None, scale=1.0, bump=0.0):
    # Keep the Solid swatch as the actual base color. Retain bump detail,
    # but do not mix in lighter/tan procedural colors in Material Preview.
    second = None
    mat = bpy.data.materials.new('Environment | ' + name)
    mat[OWNER] = True
    mat.use_nodes = True
    mat.diffuse_color = rgba(rgb)
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = rgba(rgb)
    bsdf.inputs['Roughness'].default_value = 0.88
    if second is not None or bump:
        coords = nodes.new('ShaderNodeTexCoord')
        noise = nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = scale
        noise.inputs['Detail'].default_value = 3.0
        links.new(coords.outputs['Object'], noise.inputs['Vector'])
        if second is not None:
            ramp = nodes.new('ShaderNodeValToRGB')
            ramp.color_ramp.elements[0].position = 0.25
            ramp.color_ramp.elements[0].color = rgba(rgb)
            ramp.color_ramp.elements[1].position = 0.75
            ramp.color_ramp.elements[1].color = rgba(second)
            links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
            links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
        if bump:
            fine = nodes.new('ShaderNodeTexNoise')
            fine.inputs['Scale'].default_value = 95.0
            fine.inputs['Detail'].default_value = 2.0
            links.new(coords.outputs['Object'], fine.inputs['Vector'])
            relief = nodes.new('ShaderNodeBump')
            relief.inputs['Strength'].default_value = 0.24
            relief.inputs['Distance'].default_value = bump
            links.new(fine.outputs['Fac'], relief.inputs['Height'])
            links.new(relief.outputs['Normal'], bsdf.inputs['Normal'])
    return mat


M = {
    'grass': material('patchy cleared grass', (0.30, 0.37, 0.19), (0.59, 0.56, 0.38), 0.26, 0.018),
    'edge': material('dry grass and sandy scrub margin', (0.35, 0.38, 0.23), (0.59, 0.55, 0.43), 0.7, 0.025),
    'floor': material('dark preserve floor', (0.20, 0.25, 0.13), (0.34, 0.32, 0.21), 0.45, 0.02),
    'asphalt': material('weathered gray asphalt', (0.38, 0.39, 0.40), (0.47, 0.47, 0.47), 0.8, 0.003),
    'concrete': material('warm pale concrete', (0.70, 0.69, 0.64), (0.82, 0.81, 0.76), 2.0, 0.001),
    'metal': material('dark roadside metal', (0.17, 0.18, 0.17)),
    'bark': material('gray brown trunks', (0.29, 0.28, 0.23), (0.43, 0.41, 0.33), 4.0, 0.009),
    'dry': material('dry palm skirts', (0.39, 0.34, 0.22), (0.52, 0.46, 0.30), 3.0),
}
LEAVES = [material('foliage tone %02d' % i, a, b, 1.4, 0.015)
          for i, (a, b) in enumerate((
              ((0.19, 0.28, 0.12), (0.31, 0.40, 0.19)),
              ((0.25, 0.33, 0.15), (0.41, 0.45, 0.23)),
              ((0.15, 0.25, 0.16), (0.27, 0.37, 0.20)),
              ((0.32, 0.38, 0.17), (0.48, 0.49, 0.25)),
              ((0.23, 0.31, 0.22), (0.38, 0.43, 0.30)),
              ((0.29, 0.31, 0.19), (0.40, 0.40, 0.25))))]
PLANT_MATS = [M['bark'], M['dry']] + LEAVES
M.update({
    'pond_water': material('muted olive green retention water', (0.34, 0.46, 0.39)),
    'pond_dark': material('charcoal upper pond lining', (0.115, 0.135, 0.18)),
    'pond_pale': material('pale exposed lower pond lining', (0.84, 0.85, 0.80)),
    'berm': material('mown olive pond berm', (0.39, 0.43, 0.27), bump=0.008),
    'track': material('sandy utility maintenance track', (0.56, 0.53, 0.42), bump=0.008),
    'pole': material('weathered pale utility poles', (0.58, 0.59, 0.55)),
    'wire': material('muted utility cables', (0.22, 0.24, 0.22)),
})
# Opaque water reads well even in Solid mode and cannot reveal a false flat floor.
# Low roughness provides reflections when preview/render lighting supports them.
water_bsdf = M['pond_water'].node_tree.nodes.get('Principled BSDF')
water_bsdf.inputs['Roughness'].default_value = 0.21
water_bsdf.inputs['IOR'].default_value = 1.333
water_nodes = M['pond_water'].node_tree.nodes
water_links = M['pond_water'].node_tree.links
water_coords = water_nodes.new('ShaderNodeTexCoord')
water_noise = water_nodes.new('ShaderNodeTexNoise')
water_noise.inputs['Scale'].default_value = 1.8
water_noise.inputs['Detail'].default_value = 2.0
water_bump = water_nodes.new('ShaderNodeBump')
water_bump.inputs['Strength'].default_value = 0.14
water_bump.inputs['Distance'].default_value = 0.018
water_links.new(water_coords.outputs['Object'], water_noise.inputs['Vector'])
water_links.new(water_noise.outputs['Fac'], water_bump.inputs['Height'])
water_links.new(water_bump.outputs['Normal'], water_bsdf.inputs['Normal'])
M['pond_dark'].node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value = 0.66


# -------------------------- direct mesh construction -------------------------
class Geo:
    def __init__(self):
        self.v, self.f, self.mi = [], [], []

    def face(self, points, index=0):
        k = len(self.v)
        self.v.extend(tuple(p) for p in points)
        self.f.append(tuple(range(k, k + len(points))))
        self.mi.append(index)

    def loft(self, first, second, index=0):
        k, n = len(self.v), len(first)
        self.v.extend(tuple(p) for p in list(first) + list(second))
        self.f.extend([tuple(k + i for i in reversed(range(n))),
                       tuple(k + n + i for i in range(n))])
        self.mi.extend([index, index])
        for i in range(n):
            j = (i + 1) % n
            self.f.append((k + i, k + j, k + n + j, k + n + i))
            self.mi.append(index)

    def box(self, lo, hi, index=0):
        x0, y0, z0 = lo
        x1, y1, z1 = hi
        a = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)]
        self.loft(a, [(x, y, z1) for x, y, z in a], index)

    def paving(self, top, index=0):
        # Solid infill to below grade, rather than a floating paper-thin surface.
        bottom = [(x, y, min(GROUND_Z - 0.08, z - 0.10)) for x, y, z in top]
        self.loft(bottom, top, index)

    def branch(self, a, b, radius, tip=None, index=0, sides=7):
        a, b = Vector(a), Vector(b)
        direction = b - a
        if direction.length < 1e-8:
            return
        axis = direction.normalized()
        ref = Vector((1, 0, 0)) if abs(axis.z) > 0.9 else Vector((0, 0, 1))
        u = axis.cross(ref).normalized()
        v = axis.cross(u).normalized()
        radial = [u * math.cos(i * math.tau / sides) + v * math.sin(i * math.tau / sides)
                  for i in range(sides)]
        tip = radius if tip is None else tip
        self.loft([a + d * radius for d in radial], [b + d * tip for d in radial], index)

    def blob(self, center, size, rng, index=2):
        # Reuse one icosphere topology; distort each crown lobe independently.
        start = len(self.v)
        center = Vector(center)
        for p in ICO_V:
            f = rng.uniform(0.86, 1.14)
            self.v.append(tuple(center + Vector((p[0] * size[0] * f,
                                                  p[1] * size[1] * f,
                                                  p[2] * size[2] * f))))
        self.f.extend(tuple(start + i for i in face) for face in ICO_F)
        self.mi.extend([index] * len(ICO_F))

    def mesh(self, name, materials, smooth=False):
        mesh = bpy.data.meshes.new('Environment | ' + name)
        mesh[OWNER] = True
        mesh.from_pydata(self.v, [], self.f)
        for mat in materials:
            mesh.materials.append(mat)
        for face, index in zip(mesh.polygons, self.mi):
            face.material_index = index
            face.use_smooth = smooth
        mesh.update()
        return mesh

    def finish(self, name, materials, group, smooth=False):
        if not self.f:
            return None
        mesh = self.mesh(name, materials, smooth)
        return place(name, mesh, group)


def place(name, mesh, group, position=(0, 0, 0), rotation=0.0, scale=(1, 1, 1)):
    obj = bpy.data.objects.new('Environment | ' + name, mesh)
    obj[OWNER] = True
    local = (Matrix.Translation(Vector(position)) @ Matrix.Rotation(rotation, 4, 'Z') @
             Matrix.Diagonal(Vector((*scale, 1.0))))
    obj.matrix_world = ANCHOR @ local
    GROUPS[group].objects.link(obj)
    return obj


bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
bm.verts.ensure_lookup_table()
bm.verts.index_update()
ICO_V = [tuple(v.co) for v in bm.verts]
ICO_F = [tuple(v.index for v in f.verts) for f in bm.faces]
bm.free()


def subtract_rect(rect, hole):
    x0, y0, x1, y1 = rect
    a, b, c, d = hole
    a, b, c, d = max(x0, a), max(y0, b), min(x1, c), min(y1, d)
    if a >= c or b >= d:
        return [rect]
    return [r for r in ((x0, y0, a, y1), (c, y0, x1, y1),
                        (a, y0, c, b), (a, d, c, y1))
            if r[2] - r[0] > 1e-7 and r[3] - r[1] > 1e-7]


def subtract_pond(polygon):
    # Partition a convex terrain cell against the pond's CCW outer boundary.
    # Emit only outside pieces: no terrain sheet remains over the recessed water.
    if not BUILD_RETENTION_POND:
        return [polygon]
    if (max(p[0] for p in polygon) < min(p[0] for p in POND_OUTLINE) or
            min(p[0] for p in polygon) > max(p[0] for p in POND_OUTLINE) or
            max(p[1] for p in polygon) < min(p[1] for p in POND_OUTLINE) or
            min(p[1] for p in polygon) > max(p[1] for p in POND_OUTLINE)):
        return [polygon]
    remainder, pieces = polygon, []
    for i, a in enumerate(POND_OUTLINE):
        b = POND_OUTLINE[(i + 1) % len(POND_OUTLINE)]
        inside, outside = [], []
        if len(remainder) < 3:
            break
        prev = remainder[-1]
        dp = (b[0] - a[0]) * (prev[1] - a[1]) - (b[1] - a[1]) * (prev[0] - a[0])
        for curr in remainder:
            dc = (b[0] - a[0]) * (curr[1] - a[1]) - (b[1] - a[1]) * (curr[0] - a[0])
            if (dp >= 0.0) != (dc >= 0.0):
                t = dp / (dp - dc)
                hit = (prev[0] + t * (curr[0] - prev[0]),
                       prev[1] + t * (curr[1] - prev[1]))
                inside.append(hit)
                outside.append(hit)
            (inside if dc >= 0.0 else outside).append(curr)
            prev, dp = curr, dc
        if len(outside) >= 3:
            pieces.append(outside)
        remainder = inside
    return pieces


def ground_faces(geo, polygon, index=0, lift=0.0):
    # Convex pieces can be triangulated as a fan; discard boundary slivers.
    for i in range(1, len(polygon) - 1):
        a, b, c = polygon[0], polygon[i], polygon[i + 1]
        area = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        if abs(area) > 1e-9:
            geo.face([(x, y, terrain_z(x, y) + lift) for x, y in (a, b, c)], index)


# ---------------- ground with actual pool and pond openings ------------------
progress('2/5: building lots, preserve ground, recessed pond and curved street.')
# The original frontage is retained. Only the wooded rear expands sideways.
YJOIN = FRONT - FRONT_SETBACK + 0.7
geo = Geo()
regions = [(XMIN, YJOIN, XMAX, YMAX)]
if PRESERVE_XMIN < XMIN:
    regions.append((PRESERVE_XMIN, REAR_EXTENSION_Y, XMIN, YMAX))
if PRESERVE_XMAX > XMAX:
    regions.append((XMAX, REAR_EXTENSION_Y, PRESERVE_XMAX, YMAX))
for x0, y0, x1, y1 in regions:
    x = x0
    while x < x1 - 1e-7:
        nx = min(x + GROUND_GRID, x1)
        y = y0
        while y < y1 - 1e-7:
            ny = min(y + GROUND_GRID, y1)
            for a, b, c, d in subtract_rect((x, y, nx, ny), POOL_CUTOUT):
                cell = [(a, b), (c, b), (c, d), (a, d)]
                for polygon in subtract_pond(cell):
                    midx = sum(p[0] for p in polygon) / len(polygon)
                    midy = sum(p[1] for p in polygon) / len(polygon)
                    dist = midy - preserve_edge(midx)
                    index = 0 if dist < -2.0 else (1 if dist < 2.0 else 2)
                    if dist > 3.0 and in_corridor(midx, midy):
                        index = 1
                    ground_faces(geo, polygon, index)
            y = ny
        x = nx
geo.finish('continuous lots and expanded preserve - pool and pond cutouts',
           [M['grass'], M['edge'], M['floor']], 'Ground and open lots')


# ------------------------ engineered retention basin -------------------------
if BUILD_RETENTION_POND:
    water_z = GROUND_Z - POND_WATER_BELOW_GRADE
    crest_z = GROUND_Z + POND_BERM_HEIGHT
    # Densify matching rings to seat the outer grassy toe on the terrain.
    def pond_ring(offset, height=None):
        corners = pond_outline(offset)
        result = []
        for i, a in enumerate(corners):
            b = corners[(i + 1) % len(corners)]
            for j in range(48):
                t = j / 48
                x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
                result.append((x, y, terrain_z(x, y) if height is None else height))
        return result

    rings = [pond_ring(0.0, water_z),
             pond_ring(POND_BANK_WIDTH * 0.42, water_z + (crest_z - water_z) * 0.42),
             pond_ring(POND_BANK_WIDTH, crest_z),
             pond_ring(POND_BANK_WIDTH + min(1.6, POND_OUTER_SLOPE * 0.3), crest_z),
             pond_ring(POND_OUTER_OFFSET)]
    banks = Geo()
    for band, (inner, outer) in enumerate(zip(rings, rings[1:])):
        index = 0 if band == 0 else (1 if band == 1 else 2)
        for i in range(len(inner)):
            j = (i + 1) % len(inner)
            banks.face([inner[i], outer[i], outer[j]], index)
            banks.face([inner[i], outer[j], inner[j]], index)
    banks.finish('retention pond - pale lower liner dark upper liner and grassy berm',
                 [M['pond_pale'], M['pond_dark'], M['berm']], 'Retention pond')
    water = Geo()
    water.face([(x, y, water_z) for x, y in pond_outline()])
    water_obj = water.finish('retention pond - recessed green water',
                             [M['pond_water']], 'Retention pond')
    water_obj['estimated_dimensions_m'] = [POND_LENGTH, POND_WIDTH]
    water_obj['water_depth_below_surrounding_grade_m'] = POND_WATER_BELOW_GRADE


# Narrow, lightly wandering maintenance tracks through the utility clearing.
# Ground underneath remains dry scrub; tracks stop rather than crossing a berm.
if BUILD_PRESERVE_CORRIDOR and abs(POND_COS) > 0.1:
    tracks = Geo()
    x = PRESERVE_XMIN
    while x < PRESERVE_XMAX - 1e-7:
        nx = min(x + 1.5, PRESERVE_XMAX)
        for offset in (-0.95, 0.95):
            def track_y(px):
                center = CLEAR_REAR + CORRIDOR_AFTER_CLEARING + (px - CX) * POND_SIN / POND_COS
                return center + offset + 0.30 * math.sin((px - CX) * 0.065)
            a, b = track_y(x), track_y(nx)
            if min(a - preserve_edge(x), b - preserve_edge(nx)) > 5.0 and max(a, b) < YMAX - 1.0:
                cell = [(x, a - 0.36), (nx, b - 0.36), (nx, b + 0.36), (x, a + 0.36)]
                for polygon in subtract_pond(cell):
                    ground_faces(tracks, polygon, lift=0.018)
        x = nx
    tracks.finish('paired sandy tracks in preserve clearing', [M['track']], 'Preserve corridor')


def ribbon(name, y0, y1, z0, z1, mat, group='Street and access', segments=200):
    geo = Geo()
    for i in range(segments):
        a = XMIN + (XMAX - XMIN) * i / segments
        b = XMIN + (XMAX - XMIN) * (i + 1) / segments
        geo.face([(a, y0(a), z0), (b, y0(b), z0),
                  (b, y1(b), z1), (a, y1(a), z1)])
    return geo.finish(name, [mat], group)


ribbon('lot frontage grass to curb', lambda x: road_edge(x) + CURB_WIDTH,
       lambda x: YJOIN, GROUND_Z, GROUND_Z, M['grass'], 'Ground and open lots')
ribbon('gently curved unmarked residential road', lambda x: road_edge(x) - ROAD_WIDTH,
       road_edge, ROAD_Z, ROAD_Z, M['asphalt'])
# Low, sloping concrete curb; driveway apron covers this where needed.
ribbon('lot-side low rolled curb', road_edge, lambda x: road_edge(x) + CURB_WIDTH,
       ROAD_Z, GROUND_Z + 0.005, M['concrete'])
ribbon('opposite low rolled curb', lambda x: road_edge(x) - ROAD_WIDTH - CURB_WIDTH,
       lambda x: road_edge(x) - ROAD_WIDTH, GROUND_Z + 0.005, ROAD_Z, M['concrete'])
# Broad opposite-side grassy home lots follow the road, without houses/fences.
def opposite_terrain_point(x, distance):
    y = road_edge(x) - ROAD_WIDTH - distance
    # Keep frontage and potential home sites flat; shape only the rear lawn.
    t = max(0.0, min(1.0, (distance - 24.0) / 10.0))
    t = t * t * (3.0 - 2.0 * t)
    relief = OPPOSITE_LAWN_RELIEF * t * (
        0.65 * math.sin((x - CX) * 0.10) * math.sin(distance * 0.19)
        + 0.35 * math.sin((x - CX) * 0.045 + distance * 0.13))
    return (x, y, GROUND_Z + relief)


opposite = Geo()
grass_bands = ([(CURB_WIDTH, 1.65), (3.0, OPPOSITE_LOT_DEPTH)]
               if BUILD_OPPOSITE_SIDEWALK else [(CURB_WIDTH, OPPOSITE_LOT_DEPTH)])
# Match the road and sidewalk's 200 segments so curved seams align exactly.
for i in range(200):
    a = XMIN + (XMAX - XMIN) * i / 200
    b = XMIN + (XMAX - XMIN) * (i + 1) / 200
    for near, far in grass_bands:
        distance = near
        while distance < far - 1e-7:
            next_distance = min(distance + GROUND_GRID, far)
            p = [opposite_terrain_point(a, next_distance),
                 opposite_terrain_point(b, next_distance),
                 opposite_terrain_point(b, distance),
                 opposite_terrain_point(a, distance)]
            opposite.face([p[0], p[1], p[2]])
            opposite.face([p[0], p[2], p[3]])
            distance = next_distance
opposite_obj = opposite.finish('opposite residential grassy lots and verge - curved frontage',
                               [M['grass']], 'Ground and open lots')
opposite_obj['lot_depth_from_far_road_edge_m'] = OPPOSITE_LOT_DEPTH
opposite_obj['layout_note'] = 'Open grass; flat frontage/home sites and gently shaped rear lawn'
ROOT['opposite_grassy_lot_depth_m'] = OPPOSITE_LOT_DEPTH
ROOT['opposite_lots_note'] = 'Expanded grass across street; depth/ground shaping inferred; no houses or fences'
if BUILD_OPPOSITE_SIDEWALK:
    ribbon('opposite sidewalk only - no houses', lambda x: road_edge(x) - ROAD_WIDTH - 3.0,
           lambda x: road_edge(x) - ROAD_WIDTH - 1.65,
           GROUND_Z + 0.018, GROUND_Z + 0.018, M['concrete'])

if BUILD_DRIVEWAY:
    # Mild flare at road; driveway top joins the actual garage slab level.
    gc = (GX0 + GX1) / 2
    dw = min(5.25, GX1 - GX0 - 0.30)
    drive = Geo()
    for i in range(16):
        t0, t1 = i / 16, (i + 1) / 16
        rows = []
        for t in (t0, t1):
            half = dw / 2 + 0.45 * (1 - t) ** 2
            row = []
            for x in (gc - half, gc + half):
                y = (road_edge(x) - 0.08) * (1 - t) + FRONT * t
                # Rise above curb by row 1, then gently slope to garage.
                z = ((ROAD_Z + 0.012) * (1 - t / 0.07) + (BASE_Z + 0.015) * (t / 0.07)
                     if t < 0.07 else
                     (BASE_Z + 0.015) + (GARAGE_TOP - 0.008 - BASE_Z - 0.015) * (t - 0.07) / 0.93)
                row.append((x, y, z))
            rows.append(row)
        drive.paving([rows[0][0], rows[0][1], rows[1][1], rows[1][0]])
    drive.finish('inferred concrete driveway - garage aligned', [M['concrete']], 'Street and access')
    if BUILD_ENTRY_WALK:
        if STEP:
            a = bounds_in_frame(STEP, INVERSE)
            ex, ey, ez = (a[0] + a[3]) / 2, a[1], a[2]
        else:
            ex = HX0 + 1.475 if RIGHT_GARAGE else HX1 - 1.475
            ey, ez = FRONT + 4.62, BASE_Z + 0.015
        # Low L-shaped walk joins driveway alongside garage, then entry step.
        join_y = FRONT - 0.85
        join_t = (join_y - road_edge(gc)) / (FRONT - road_edge(gc))
        join_z = BASE_Z + 0.015 + (GARAGE_TOP - 0.008 - BASE_Z - 0.015) * max(0, (join_t - 0.07) / 0.93)
        side_x = gc - dw / 2 + 0.04 if ex < gc else gc + dw / 2 - 0.04
        g = Geo()
        left, right = min(ex - 0.55, side_x), max(ex + 0.55, side_x)
        g.paving([(left, join_y - 0.55, join_z), (right, join_y - 0.55, join_z),
                  (right, join_y + 0.55, join_z), (left, join_y + 0.55, join_z)])
        g.paving([(ex - 0.55, join_y + 0.55, join_z), (ex + 0.55, join_y + 0.55, join_z),
                  (ex + 0.55, ey, max(ez, BASE_Z + 0.025)),
                  (ex - 0.55, ey, max(ez, BASE_Z + 0.025))])
        g.finish('inferred entry walk', [M['concrete']], 'Street and access')


# -------------------------- shared vegetation assets -------------------------
progress('3/5: creating reusable broadleaf, pine and palm silhouettes.')

def broadleaf(seed):
    rng, g = random.Random(seed), Geo()
    height = rng.uniform(7.0, 10.5)
    lean = (rng.uniform(-0.5, 0.5), rng.uniform(-0.4, 0.4))
    g.branch((0, 0, -0.08), (*lean, height * 0.64), 0.19, 0.09)
    tone = rng.randrange(len(LEAVES))
    for i in range(9):
        angle = i * 2.399 + rng.uniform(-0.3, 0.3)
        reach = rng.uniform(0.8, 2.5)
        center = (lean[0] + math.cos(angle) * reach,
                  lean[1] + math.sin(angle) * reach, height * rng.uniform(0.66, 0.94))
        g.branch((lean[0], lean[1], height * 0.46), center, 0.09, 0.025)
        g.blob(center, (rng.uniform(1.4, 2.3), rng.uniform(1.3, 2.1), rng.uniform(1.2, 2.0)),
               rng, 2 + ((tone + (i % 3 == 0)) % len(LEAVES)))
    return g.mesh('shared broadleaf %d' % seed, PLANT_MATS, True)


def pine(seed):
    rng, g = random.Random(seed), Geo()
    height = rng.uniform(10.5, 14.0)
    g.branch((0, 0, -0.08), (0.30, 0.12, height), 0.17, 0.045)
    for i in range(11):
        angle = i * 2.399
        z = height * rng.uniform(0.66, 0.95)
        reach = rng.uniform(1.0, 2.6)
        p = (math.cos(angle) * reach, math.sin(angle) * reach, z)
        g.branch((0.2, 0.1, z - 1.0), p, 0.055, 0.018)
        g.blob(p, (rng.uniform(1.0, 1.7), rng.uniform(1.0, 1.6), rng.uniform(0.65, 1.0)), rng, 3)
    return g.mesh('shared open pine crown %d' % seed, PLANT_MATS, True)


def palm_fan(g, root, angle, length, rng, index):
    # Folded radial blades form a low-detail fan, not a flat billboard.
    root = Vector(root)
    outward = Vector((math.cos(angle), math.sin(angle), 0))
    hinge = root + outward * length * 0.43 + Vector((0, 0, length * 0.27))
    g.branch(root, hinge, 0.019, 0.008, index=index, sides=5)
    for j in range(9):
        theta = angle + (j - 4) * 0.16
        direction = Vector((math.cos(theta), math.sin(theta), 0))
        sideways = Vector((-direction.y, direction.x, 0))
        tip = hinge + direction * length * rng.uniform(0.47, 0.68)
        tip.z += length * (0.03 - 0.15 * abs(j - 4) / 4)
        mid = hinge.lerp(tip, 0.5) + Vector((0, 0, length * 0.06))
        width = length * 0.055
        g.face([hinge, mid - sideways * width, tip], index)
        g.face([hinge, tip, mid + sideways * width], index)


def palm(seed, low=False):
    rng, g = random.Random(seed), Geo()
    height = rng.uniform(0.3, 0.75) if low else rng.uniform(3.3, 6.0)
    g.branch((0, 0, -0.06), (0.08, 0.04, height), 0.15 if low else 0.20, 0.13)
    if not low:
        for i in range(12):
            a = i * math.tau / 12
            g.branch((0.08, 0.04, height - 0.15),
                     (math.cos(a) * 0.55, math.sin(a) * 0.55, height - 1.05),
                     0.10, 0.025, index=1, sides=5)
    for i in range(13):
        palm_fan(g, (0.08, 0.04, height + rng.uniform(-0.08, 0.10)),
                 i * 2.399, rng.uniform(1.0, 1.5) if low else rng.uniform(1.8, 2.5),
                 rng, 2 + rng.choice((0, 1, 3)))
    return g.mesh('shared %s %d' % ('palmetto scrub' if low else 'fan palm', seed), PLANT_MATS)


def shrub(seed):
    rng, g = random.Random(seed), Geo()
    for i in range(6):
        a = i * 2.399
        p = (math.cos(a) * 0.55, math.sin(a) * 0.55, rng.uniform(0.45, 1.0))
        g.blob(p, (rng.uniform(0.55, 0.95), rng.uniform(0.5, 0.95), rng.uniform(0.5, 0.95)),
               rng, 2 + (seed % len(LEAVES)))
    return g.mesh('shared scrub thicket %d' % seed, PLANT_MATS, True)


BROAD = [broadleaf(SEED + i) for i in range(7)]
PINES = [pine(SEED + 30 + i) for i in range(3)]
PALMS = [palm(SEED + 40 + i) for i in range(3)]
LOW_PALMS = [palm(SEED + 50 + i, True) for i in range(4)]
SHRUBS = [shrub(SEED + 60 + i) for i in range(6)]


# ------------------------ irregular layered preserve -------------------------
progress('4/5: planting layered woods around the pond and utility clearing.')
rng = random.Random(SEED + 100)
counts = {'trees': 0, 'brush': 0}


def planting_allowed(px, py, canopy):
    # Exclude the full OUTER berm, not just the waterline, with canopy clearance.
    return (PRESERVE_XMIN + canopy < px < PRESERVE_XMAX - canopy and
            preserve_edge(px) + (5.5 if canopy > 4.0 else 0.5) < py < YMAX - canopy and
            not inside_pond(px, py, canopy) and not in_corridor(px, py, canopy))


# Jittered spacing and broad density patches break up rows. Far trees are sparser;
# shared meshes keep the expanded aerial setting modest.
if TREE_DENSITY * VEGETATION_MULTIPLIER > 0:
    spacing = 1.0 / math.sqrt(TREE_DENSITY * VEGETATION_MULTIPLIER)
    x = PRESERVE_XMIN + 7.5
    while x < PRESERVE_XMAX - 7.5:
        y = CLEAR_REAR - 4.0 + rng.uniform(0.0, spacing)
        while y < YMAX - 7.5:
            px = x + rng.uniform(-0.38, 0.38) * spacing
            py = y + rng.uniform(-0.38, 0.38) * spacing
            if planting_allowed(px, py, 7.5):
                density = 0.84 + 0.13 * math.sin(px * 0.065 + py * 0.035)
                if py > POND_CY + POND_WIDTH / 2:
                    density *= 0.72
                if rng.random() < density:
                    chance = rng.random()
                    library = BROAD if chance < 0.55 else (PINES if chance < 0.85 else PALMS)
                    asset = rng.choice(library)
                    s = rng.uniform(0.72, 1.20)
                    height_scale = rng.uniform(0.88, 1.15)
                    place('preserve tree %04d' % counts['trees'], asset, 'Preserve trees',
                          (px, py, terrain_z(px, py)), rng.random() * math.tau,
                          (s, s * rng.uniform(0.90, 1.08), s * height_scale))
                    counts['trees'] += 1
            y += spacing
        x += spacing


def plant_brush(px, py, edge=False):
    if not planting_allowed(px, py, 3.2):
        return
    asset = rng.choice(LOW_PALMS if rng.random() < 0.52 else SHRUBS)
    s = rng.uniform(0.65, 1.15) if edge else rng.uniform(0.8, 1.55)
    place('brush clump %04d' % counts['brush'], asset, 'Preserve brush',
          (px, py, terrain_z(px, py)), rng.random() * math.tau,
          (s, s * rng.uniform(0.85, 1.15), s * rng.uniform(0.8, 1.1)))
    counts['brush'] += 1


if VEGETATION_MULTIPLIER > 0:
    # Two ragged near-edge bands give patio views a believable palmetto fringe.
    for band in (1.6, 4.0):
        x = PRESERVE_XMIN + 3.2
        while x < PRESERVE_XMAX - 3.2:
            px = x + rng.uniform(-0.35, 0.35)
            plant_brush(px, preserve_edge(px) + band + rng.uniform(-0.45, 0.45), True)
            x += rng.uniform(1.3, 2.4) / math.sqrt(VEGETATION_MULTIPLIER)
    # Understory excludes the entire basin and maintenance corridor.
    area = (PRESERVE_XMAX - PRESERVE_XMIN) * (YMAX - CLEAR_REAR)
    amount = int(area * BRUSH_DENSITY * VEGETATION_MULTIPLIER)
    for i in range(amount):
        px = rng.uniform(PRESERVE_XMIN + 3.2, PRESERVE_XMAX - 3.2)
        py = rng.uniform(CLEAR_REAR - 4, YMAX - 3.2)
        density = 0.66 + 0.25 * math.sin(px * 0.17) * math.cos(py * 0.13)
        if py > POND_CY:
            density *= 0.60
        if rng.random() < density:
            plant_brush(px, py)
    # Scrub along clearing margins prevents a ruler-straight forest wall.
    if BUILD_PRESERVE_CORRIDOR and abs(POND_COS) > 0.1:
        x = PRESERVE_XMIN + 4.0
        while x < PRESERVE_XMAX - 4.0:
            center = CLEAR_REAR + CORRIDOR_AFTER_CLEARING + (x - CX) * POND_SIN / POND_COS
            for side in (-1, 1):
                py = center + side * (CORRIDOR_WIDTH / 2 + rng.uniform(3.3, 5.0)) / abs(POND_COS)
                plant_brush(x, py, True)
            x += rng.uniform(2.0, 3.8) / math.sqrt(VEGETATION_MULTIPLIER)


# ----------------------- photo-inspired utility corridor ----------------------
if BUILD_PRESERVE_CORRIDOR and BUILD_PRESERVE_UTILITY_POLES and abs(POND_COS) > 0.1:
    poles, wires = Geo(), Geo()
    previous = None
    x = PRESERVE_XMIN + 15.0
    while x < PRESERVE_XMAX - 12.0:
        y = (CLEAR_REAR + CORRIDOR_AFTER_CLEARING + (x - CX) * POND_SIN / POND_COS
             + (CORRIDOR_WIDTH / 2 - 1.1) / abs(POND_COS))
        if (preserve_edge(x) + 8.0 < y < YMAX - 4.0 and not inside_pond(x, y, 2.0)):
            z = terrain_z(x, y)
            top = Vector((x, y, z + 11.5))
            cross = Vector((-POND_SIN, POND_COS, 0))
            poles.branch((x, y, z - 0.15), top + Vector((0, 0, 0.5)), 0.14, 0.085, sides=8)
            poles.branch(top - cross * 1.25, top + cross * 1.25, 0.065, sides=6)
            if previous is not None:
                # Skip a span if an adjusted layout would take it over the pond.
                span_points = [previous.lerp(top, i / 12) for i in range(13)]
                if not any(inside_pond(p.x, p.y, 2.0) for p in span_points):
                    for offset in (-1.0, 0.0, 1.0):
                        for i in range(12):
                            a, b = span_points[i].copy(), span_points[i + 1].copy()
                            a += cross * offset
                            b += cross * offset
                            ta, tb = i / 12, (i + 1) / 12
                            a.z -= 4.0 * 0.65 * ta * (1.0 - ta)
                            b.z -= 4.0 * 0.65 * tb * (1.0 - tb)
                            wires.branch(a, b, 0.012, sides=4)
            previous = top
        else:
            previous = None
        x += 38.0
    poles.finish('simple pale poles along preserve clearing', [M['pole']], 'Preserve corridor')
    wires.finish('three lightly sagging utility lines', [M['wire']], 'Preserve corridor')


# -------------------------- restrained roadside detail -----------------------
progress('5/5: adding restrained street details and finishing.')
if BUILD_SMALL_STREET_DETAILS:
    # Sparse simple lamps like those visible along the cleared frontage.
    # Geometry only; no new light objects or frontage utility networks.
    g = Geo()
    for offset in (-2.5, 0.5, 3.5):
        x = CX + offset * LOT_WIDTH
        y = road_edge(x) + 1.15
        z = terrain_z(x, y)
        g.branch((x, y, z), (x, y, z + 3.2), 0.045, 0.033, sides=8)
        g.box((x - 0.13, y - 0.13, z + 3.18), (x + 0.13, y + 0.13, z + 3.44))
        g.box((x - 0.17, y - 0.17, z + 3.44), (x + 0.17, y + 0.17, z + 3.48))
    g.finish('approximate frontage lamp silhouettes - unlit', [M['metal']], 'Street and access')
    # Small dark drain grates in the roadway, away from the driveway apron.
    g = Geo()
    for offset in (-1.4, 1.8):
        x = CX + offset * LOT_WIDTH
        y = road_edge(x) - 0.30
        for i in range(6):
            g.box((x - 0.33 + i * 0.12, y - 0.15, ROAD_Z + 0.003),
                  (x - 0.29 + i * 0.12, y + 0.15, ROAD_Z + 0.009))
    g.finish('small curbside drain grates', [M['metal']], 'Street and access')

# Drop unused prototype meshes (e.g. if vegetation was disabled).
for mesh in list(bpy.data.meshes):
    if mesh.get(OWNER) and mesh.users == 0:
        bpy.data.meshes.remove(mesh)
ROOT['tree_instances'] = counts['trees']
ROOT['brush_instances'] = counts['brush']
bpy.context.view_layer.update()
progress('Done: %d trees, %d brush clumps. House/pool data untouched.' %
         (counts['trees'], counts['brush']))
if BUILD_RETENTION_POND:
    progress('Retention pond: %.0f x %.0f m water; pale/dark liner, grassy berm and actual ground opening.' %
             (POND_LENGTH, POND_WIDTH))
progress('All layout dimensions are estimates; adjust controls at the top as needed.')
progress('No camera, lighting, world, unit or selection changes.')
progress('All surface materials are lit; procedural color mixing disabled.')
