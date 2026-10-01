"""Honor backyard pool — additive companion to honor_exterior.py.

RUN: Run the house script first, then run this file in Blender's Text Editor.
This file NEVER imports, executes, edits, deletes or recolors the house. It only
replaces its own HONOR_POOL collection when rerun. No cameras, lights, ground
plane, landscaping, simulations, external textures or render settings are added.

REFERENCE: supplied pool_specs.jpg, pool1.jpeg and pool2.jpeg.
Plan dimensions govern geometry; renders govern approximate finishes.
  Basin 24 x 12 ft plus 7 x 3.5 ft entry bay: 312.5 sf, perimeter 79 ft.
  Depth 3 to 5 ft, 6-inch shell/beam, 6 x 6-inch waterline tiles.
  Three entry treads, far shallow-corner bench, full deep-end bench.
  Rear feature: 4.5 / 8 / 4.5 ft tiers, +6 / +12 / +6 inches,
  3-ft-deep caps/platforms, centered 36-inch sheer-descent waterfall.
  Deck envelope 33 x 30 ft, 6 / 3 ft left/right pool margins, 3 ft behind pool.
  House wall to main pool edge 15 ft, to step-bay edge 11.5 ft.
  One drain, one skimmer, four returns, modeled nicheless light fitting.
  Bronze mansard enclosure, two doors and removable child barrier per specs.

INFERRED: floor transition, seat/tread heights, coping width, paver module/color,
exact feature centering, cage member sections/roof height, barrier/gate routing,
equipment shapes and pipe routes. These are VISUAL models, not engineering.
The specified 571 sf deck is not used to distort the dimensioned footprint;
quoted takeoffs and small access aprons may use different inclusion conventions.
No spa, heater, landscape beds or optional extra features are invented.

Coordinates are built in plan feet, then converted to meters. +Y is backyard.
The plan ALREADY specifies garage R: do not mirror the pool again.
If the original main foundation exists, its rear edge/top and object transform
anchor the new model. Otherwise use the known house coordinates as a fallback.
Existing lanai geometry and slab remain untouched; deck paving stops at its edge.
"""

import math
import random
import bpy
import bmesh
from mathutils import Vector, Matrix


# ------------------------------- user switches -------------------------------
BUILD_SCREEN_ENCLOSURE = True     # False gives the unobstructed supplied render view
BUILD_CHILD_BARRIER = False       # Child barrier omitted at user's request
BUILD_EQUIPMENT = True
BUILD_WATER = True
BUILD_WATERFALL = True

COLLECTION_NAME = 'HONOR_POOL'
OWNER = 'honor_pool_generated'
FT = 0.3048
SEED = 395
DECK_W, DECK_D = 33.0, 30.0
WATER_Z = -0.45                   # feet below coping, estimated freeboard
SHALLOW_DEPTH, DEEP_DEPTH = 3.0, 5.0
SHELL_T = 0.5
COPING_W = 0.9
CAGE_EAVE, CAGE_RISE, CAGE_INSET = 9.85, 3.0, 3.0
BARRIER_H = 4.0                  # visual assumption, not a safety certification
# CCW outline, including the outward entry-step bay on the house side.
OUTLINE = [(6.0, 11.5), (13.0, 11.5), (13.0, 15.0),
           (30.0, 15.0), (30.0, 27.0), (6.0, 27.0)]
FEATURES = [(9.5, 14.0, 0.5), (14.0, 22.0, 1.0), (22.0, 26.5, 0.5)]


def polygon_area(poly):
    return sum(a[0] * b[1] - b[0] * a[1]
               for a, b in zip(poly, poly[1:] + poly[:1])) * 0.5


AREA = polygon_area(OUTLINE)
PERIMETER = sum(math.hypot(b[0] - a[0], b[1] - a[1])
                for a, b in zip(OUTLINE, OUTLINE[1:] + OUTLINE[:1]))
assert abs(AREA - 312.5) < 1e-8
assert abs(PERIMETER - 79.0) < 1e-8


# ------------------------------ house: READ ONLY -----------------------------
def house_anchor():
    house = bpy.data.collections.get('HONOR_FH1')
    fallback = Matrix.Translation(((10.06 - DECK_W * FT) / 2, 17.04, 0.18))
    lanai_x = DECK_W - 4.98 / FT
    lanai_y = 8.0
    if house is None:
        return fallback, lanai_x, lanai_y
    if house.get('garage_side_from_street', 'right') != 'right':
        raise RuntimeError('This pool plan is for the right-hand-garage house.')
    foundation = next((o for o in house.all_objects
                       if o.type == 'MESH' and o.name.startswith('Main foundation')), None)
    if foundation is None:
        return fallback, lanai_x, lanai_y
    points = [v.co for v in foundation.data.vertices]
    x0, x1 = min(p.x for p in points), max(p.x for p in points)
    rear, top = max(p.y for p in points), max(p.z for p in points)
    origin = Vector(((x0 + x1 - DECK_W * FT) / 2, rear, top))
    anchor = foundation.matrix_world @ Matrix.Translation(origin)
    # Locate the existing slab without modifying it or putting new pavers on it.
    slab = next((o for o in house.all_objects
                 if o.type == 'MESH' and o.name.startswith('Rear lanai slab')), None)
    if slab is not None:
        inverse = anchor.inverted()
        local = [inverse @ (slab.matrix_world @ v.co) / FT for v in slab.data.vertices]
        lanai_x = min(p.x for p in local)
        lanai_y = max(p.y for p in local)
    return anchor, lanai_x, lanai_y


ANCHOR, LANAI_X, LANAI_Y = house_anchor()


# ------------------------ strictly isolated rerun cleanup ---------------------
def descendants(collection):
    result = [collection]
    for child in collection.children:
        result.extend(descendants(child))
    return result


old = bpy.data.collections.get(COLLECTION_NAME)
if old is not None:
    groups = descendants(old)
    if any(not c.get(OWNER) for c in groups) or any(not o.get(OWNER) for o in old.all_objects):
        raise RuntimeError('HONOR_POOL contains unowned data; rename that collection first.')
    for obj in list(old.all_objects):
        data = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if isinstance(data, bpy.types.Mesh) and data.users == 0:
            bpy.data.meshes.remove(data)
    for group in reversed(groups):
        bpy.data.collections.remove(group)
for mat in list(bpy.data.materials):
    if mat.get(OWNER) and mat.users == 0:
        bpy.data.materials.remove(mat)

ROOT = bpy.data.collections.new(COLLECTION_NAME)
ROOT[OWNER] = True
ROOT['reference'] = 'User pool_specs.jpg / pool1.jpeg / pool2.jpeg; garage R'
ROOT['water_outline_sqft'] = AREA
ROOT['water_outline_perimeter_ft'] = PERIMETER
ROOT['dimensions_ft'] = '24 x 12 plus 7 x 3.5 step bay; depth 3 to 5'
ROOT['visual_model_only'] = 'Not a construction, electrical or barrier-compliance design'
bpy.context.scene.collection.children.link(ROOT)
GROUPS = {}
for name in ('Basin', 'Deck and coping', 'Water', 'Waterfall feature',
             'Screen enclosure', 'Child barrier', 'Equipment and fittings'):
    group = bpy.data.collections.new('Pool | ' + name)
    group[OWNER] = True
    ROOT.children.link(group)
    GROUPS[name] = group


# -------------------------------- materials ----------------------------------
def linear(v):
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def color(rgb):
    return tuple(linear(v) for v in rgb) + (1.0,)


def material(name, rgb, roughness=0.6, noise=0.0, metallic=0.0):
    mat = bpy.data.materials.new('Pool | ' + name)
    mat[OWNER] = True
    mat.use_nodes = True
    mat.diffuse_color = color(rgb)
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = color(rgb)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    if noise:
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        coords = nodes.new('ShaderNodeTexCoord')
        texture = nodes.new('ShaderNodeTexNoise')
        texture.inputs['Scale'].default_value = 150.0
        texture.inputs['Detail'].default_value = 2.0
        links.new(coords.outputs['Object'], texture.inputs['Vector'])
        bump = nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = 0.22
        bump.inputs['Distance'].default_value = noise
        links.new(texture.outputs['Fac'], bump.inputs['Height'])
        links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    return mat


M = {
    'pebble': material('pale blue StoneScapes-style pebble - shade inferred', (0.67, 0.82, 0.85), 0.48, 0.0018),
    'concrete': material('structural concrete', (0.57, 0.57, 0.53), 0.9, 0.002),
    'grout': material('blue gray tile grout', (0.29, 0.39, 0.43), 0.75),
    'joint': material('warm gray paver joints', (0.57, 0.55, 0.51), 0.9),
    'coping': material('light ivory limestone-style coping', (0.89, 0.875, 0.835), 0.65, 0.0007),
    'bronze': material('dark bronze coated aluminum', (0.20, 0.175, 0.15), 0.42, metallic=0.35),
    'black': material('dark openings and rubber', (0.075, 0.085, 0.09), 0.7),
    'pvc': material('ivory fittings and PVC', (0.83, 0.85, 0.83), 0.4),
    'steel': material('stainless fitting rims', (0.67, 0.70, 0.71), 0.24, metallic=0.8),
    'lens': material('unlit pool fixture lens', (0.50, 0.70, 0.76), 0.15),
    'equipment': material('graphite pool equipment', (0.29, 0.31, 0.31), 0.56),
    'filter': material('cartridge filter housing', (0.69, 0.68, 0.60), 0.55),
    'foam': material('subtle waterfall aeration', (0.81, 0.93, 0.95), 0.33),
}
PAVERS = [material('ivory paver tone %02d' % i, (0.875 * f, 0.86 * f, 0.825 * f), 0.72, 0.0008)
          for i, f in enumerate((0.96, 0.978, 0.99, 1.0, 1.014, 1.025))]
TILES = [material('blue waterline ceramic %02d' % i, (0.16 * f, 0.30 * f, 0.405 * f), 0.28, 0.00025)
         for i, f in enumerate((0.85, 0.94, 1.0, 1.06, 1.13))]


def water_material(name, volume=False):
    mat = material(name, (0.94, 0.985, 1.0), 0.10)
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes.get('Principled BSDF')
    socket = bsdf.inputs.get('Transmission Weight')
    if socket is None:
        socket = bsdf.inputs.get('Transmission')
    if socket is not None:
        socket.default_value = 1.0
    bsdf.inputs['IOR'].default_value = 1.333
    coords = nodes.new('ShaderNodeTexCoord')
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 8.0 if volume else 26.0
    noise.inputs['Detail'].default_value = 2.5
    links.new(coords.outputs['Object'], noise.inputs['Vector'])
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.13
    bump.inputs['Distance'].default_value = 0.006 if volume else 0.002
    links.new(noise.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    if volume:
        absorption = nodes.new('ShaderNodeVolumeAbsorption')
        absorption.inputs['Color'].default_value = (0.55, 0.90, 1.0, 1.0)
        absorption.inputs['Density'].default_value = 0.065
        links.new(absorption.outputs['Volume'], nodes.get('Material Output').inputs['Volume'])
    # Enable only material-local compatibility flags; leave render engine alone.
    if hasattr(mat, 'use_screen_refraction'):
        mat.use_screen_refraction = True
    return mat


M['water'] = water_material('clear blue pool water - closed refractive volume', True)
M['sheet'] = water_material('clear falling water sheet')


def screen_material():
    mat = material('fine dark insect/barrier screen - procedural open weave', (0.16, 0.15, 0.14), 0.8)
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    coords = nodes.new('ShaderNodeTexCoord')
    separate = nodes.new('ShaderNodeSeparateXYZ')
    links.new(coords.outputs['UV'], separate.inputs[0])
    masks = []
    # Visually estimated weave; the sheet does not specify exact standard pitch.
    for output, pitch in (('X', 0.0014), ('Y', 0.0018)):
        scale = nodes.new('ShaderNodeMath')
        scale.operation = 'MULTIPLY'
        scale.inputs[1].default_value = 1.0 / pitch
        links.new(separate.outputs[output], scale.inputs[0])
        fract = nodes.new('ShaderNodeMath')
        fract.operation = 'FRACT'
        links.new(scale.outputs[0], fract.inputs[0])
        strand = nodes.new('ShaderNodeMath')
        strand.operation = 'LESS_THAN'
        strand.inputs[1].default_value = 0.075
        links.new(fract.outputs[0], strand.inputs[0])
        masks.append(strand)
    combine = nodes.new('ShaderNodeMath')
    combine.operation = 'MAXIMUM'
    links.new(masks[0].outputs[0], combine.inputs[0])
    links.new(masks[1].outputs[0], combine.inputs[1])
    transparent = nodes.new('ShaderNodeBsdfTransparent')
    mix = nodes.new('ShaderNodeMixShader')
    links.new(combine.outputs[0], mix.inputs[0])
    links.new(transparent.outputs[0], mix.inputs[1])
    links.new(nodes.get('Principled BSDF').outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], nodes.get('Material Output').inputs['Surface'])
    if hasattr(mat, 'surface_render_method'):
        mat.surface_render_method = 'DITHERED'
    elif hasattr(mat, 'blend_method'):
        mat.blend_method = 'HASHED'
    mat.diffuse_color = (0.04, 0.035, 0.03, 0.12)
    return mat


M['screen'] = screen_material()


# ---------------------------- direct mesh utilities ---------------------------
class Geo:
    def __init__(self):
        self.v, self.f, self.mi = [], [], []

    def face(self, points, index=0):
        start = len(self.v)
        self.v.extend(tuple(p) for p in points)
        self.f.append(tuple(range(start, start + len(points))))
        self.mi.append(index)

    def prism(self, ring, offset, index=0):
        start, count = len(self.v), len(ring)
        ring = [Vector(p) for p in ring]
        off = Vector(offset)
        self.v.extend(tuple(p) for p in ring + [p + off for p in ring])
        self.f.extend([tuple(start + i for i in reversed(range(count))),
                       tuple(start + count + i for i in range(count))])
        self.mi.extend([index, index])
        for i in range(count):
            j = (i + 1) % count
            self.f.append((start + i, start + j, start + count + j, start + count + i))
            self.mi.append(index)

    def loft(self, first, second, index=0):
        # Connected end rings let normal correction identify a solid's outside.
        count, start = len(first), len(self.v)
        assert count == len(second)
        self.v.extend(tuple(p) for p in list(first) + list(second))
        self.f.extend([tuple(start + i for i in reversed(range(count))),
                       tuple(start + count + i for i in range(count))])
        self.mi.extend([index, index])
        for i in range(count):
            j = (i + 1) % count
            self.f.append((start + i, start + j, start + count + j, start + count + i))
            self.mi.append(index)

    def box(self, x0, y0, z0, x1, y1, z1, index=0):
        if min(x1 - x0, y1 - y0, z1 - z0) <= 1e-7:
            return
        self.prism([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)],
                   (0, 0, z1 - z0), index)

    def finish(self, name, materials, group, bevel=0.0, uv=False, smooth=False):
        if not self.f:
            return None
        if not isinstance(materials, (list, tuple)):
            materials = [materials]
        mesh = bpy.data.meshes.new('Pool | ' + name)
        mesh.from_pydata([(x * FT, y * FT, z * FT) for x, y, z in self.v], [], self.f)
        for mat in materials:
            mesh.materials.append(mat)
        for poly, index in zip(mesh.polygons, self.mi):
            poly.material_index = index
        mesh.update()
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(mesh)
        bm.free()
        mesh.update()
        if uv:
            layer = mesh.uv_layers.new(name='Screen meters')
            for poly in mesh.polygons:
                vertices = [mesh.vertices[i].co for i in poly.vertices]
                origin = vertices[0]
                u = (vertices[1] - origin).normalized()
                v = poly.normal.cross(u).normalized()
                for loop_index in poly.loop_indices:
                    point = mesh.vertices[mesh.loops[loop_index].vertex_index].co - origin
                    layer.data[loop_index].uv = (point.dot(u), point.dot(v))
        if smooth:
            for poly in mesh.polygons:
                poly.use_smooth = True
        obj = bpy.data.objects.new('Pool | ' + name, mesh)
        obj[OWNER] = True
        obj.matrix_world = ANCHOR.copy()
        GROUPS[group].objects.link(obj)
        if bevel:
            modifier = obj.modifiers.new('soft manufactured edges', 'BEVEL')
            modifier.width = bevel * FT
            modifier.segments = 2
        return obj


def box(name, lo, hi, mat, group='Equipment and fittings', bevel=0.0):
    geo = Geo()
    geo.box(*lo, *hi)
    return geo.finish(name, mat, group, bevel)


def bar(geo, a, b, width, depth=None):
    a, b = Vector(a), Vector(b)
    axis = (b - a).normalized()
    up = Vector((0, 0, 1))
    u = up - axis * axis.dot(up)
    if u.length < 1e-6:
        u = Vector((1, 0, 0))
    u.normalize()
    v = axis.cross(u).normalized()
    u *= width / 2
    v *= (depth if depth is not None else width) / 2
    geo.prism([a - u - v, a + u - v, a + u + v, a - u + v], b - a)


def cylinder(geo, a, b, radius, segments=24, index=0):
    a, b = Vector(a), Vector(b)
    axis = (b - a).normalized()
    ref = Vector((0, 0, 1)) if abs(axis.z) < 0.9 else Vector((1, 0, 0))
    u = axis.cross(ref).normalized()
    v = axis.cross(u).normalized()
    ring = [a + radius * (u * math.cos(i * 2 * math.pi / segments) +
                         v * math.sin(i * 2 * math.pi / segments)) for i in range(segments)]
    geo.prism(ring, b - a, index)


def offset_polygon(poly, distance):
    # Mitered offset of a CCW orthogonal polygon, also valid at its concave corner.
    result = []
    for i, p in enumerate(poly):
        prev, nxt = poly[i - 1], poly[(i + 1) % len(poly)]
        d0 = Vector((p[0] - prev[0], p[1] - prev[1])).normalized()
        d1 = Vector((nxt[0] - p[0], nxt[1] - p[1])).normalized()
        n0, n1 = Vector((d0.y, -d0.x)), Vector((d1.y, -d1.x))
        bisector = n0 + n1
        scale = distance / bisector.dot(n0)
        result.append(tuple(Vector(p) + bisector * scale))
    return result


def floor_z(x):
    t = max(0.0, min(1.0, (x - 13.0) / 14.0))
    return WATER_Z - (SHALLOW_DEPTH + (DEEP_DEPTH - SHALLOW_DEPTH) * t)


def subtract_rect(rect, hole):
    x0, y0, x1, y1 = rect
    a, b, c, d = hole
    a, b, c, d = max(x0, a), max(y0, b), min(x1, c), min(y1, d)
    if a >= c or b >= d:
        return [rect]
    candidates = [(x0, y0, a, y1), (c, y0, x1, y1),
                  (a, y0, c, b), (a, d, c, y1)]
    return [r for r in candidates if r[2] - r[0] > 1e-6 and r[3] - r[1] > 1e-6]


# ------------------------- basin / slope / benches ----------------------------
outer = offset_polygon(OUTLINE, SHELL_T)
geo = Geo()
for x0, x1, y0, y1 in ((6, 13, 15, 27), (13, 27, 15, 27),
                       (27, 30, 15, 27), (6, 13, 11.5, 15)):
    geo.prism([(x0, y0, floor_z(x0)), (x1, y0, floor_z(x1)),
               (x1, y1, floor_z(x1)), (x0, y1, floor_z(x0))], (0, 0, -SHELL_T))
geo.finish('continuous sloping pebble floor - 3 to 5 feet', M['pebble'], 'Basin')
geo = Geo()
for i, a in enumerate(OUTLINE):
    b, oa, ob = OUTLINE[(i + 1) % len(OUTLINE)], outer[i], outer[(i + 1) % len(outer)]
    ring = [(a[0], a[1], -0.17), (b[0], b[1], -0.17),
            (ob[0], ob[1], -0.17), (oa[0], oa[1], -0.17)]
    bottom = [(p[0], p[1], floor_z(p[0]) - SHELL_T) for p in ring]
    geo.loft(bottom, ring)
geo.finish('six inch perimeter shell', M['pebble'], 'Basin')

# Entry treads occupy only the 7 x 3.5 ft projecting bay.
for i, (ya, yb, top) in enumerate(((11.5, 12.5, -0.85),
                                  (12.5, 13.5, -1.70), (13.5, 15.0, -2.55))):
    box('entry tread %d - 7 ft wide' % (i + 1), (6, ya, floor_z(6)),
        (13, yb, top), M['pebble'], 'Basin', 0.018)
    box('blue step nosing %d' % (i + 1), (6.025, yb - 0.08, top + 0.003),
        (12.975, yb - 0.01, top + 0.012), TILES[2], 'Basin')
seat_z = WATER_Z - 1.45
box('full width deep end bench', (28.5, 15, floor_z(30)), (30, 27, seat_z),
    M['pebble'], 'Basin', 0.025)
geo = Geo()
geo.prism([(6, 24, seat_z), (9, 27, seat_z), (6, 27, seat_z)],
          (0, 0, floor_z(6) - seat_z))
geo.finish('triangular shallow corner bench', M['pebble'], 'Basin', 0.018)


def tile_strip(name, a, b, low, high, group='Basin'):
    a, b = Vector((a[0], a[1], 0)), Vector((b[0], b[1], 0))
    axis = (b - a).normalized()
    inside = Vector((-axis.y, axis.x, 0))
    length = (b - a).length
    g = Geo()
    rng = random.Random(SEED + sum(map(ord, name)))
    u = 0.0
    while u < length - 1e-6:
        end = min(u + 0.5, length)
        z = low
        while z < high - 1e-6:
            top = min(z + 0.5, high)
            p = a + axis * (u + 0.005) + inside * 0.012
            q = a + axis * (end - 0.005) + inside * 0.012
            if end - u > 0.01 and top - z > 0.01:
                g.prism([(p.x, p.y, z + 0.005), (q.x, q.y, z + 0.005),
                         (q.x, q.y, top - 0.005), (p.x, p.y, top - 0.005)],
                        -inside * 0.018, rng.randrange(len(TILES)))
            z = top
        u = end
    return g.finish(name, TILES, group)


for i, a in enumerate(OUTLINE):
    b = OUTLINE[(i + 1) % len(OUTLINE)]
    tile_strip('six inch waterline tiles %d' % (i + 1), a, b, -0.67, -0.17)


# -------------------- continuous segmented bullnose coping --------------------
# Profile distances measured outward from water outline; rounded inner nose.
profile = [(-0.055, -0.10), (-0.045, -0.055), (-0.020, -0.025),
           (0.020, -0.006), (0.055, 0.0), (COPING_W, 0.0),
           (COPING_W, -0.17), (0.01, -0.17), (-0.035, -0.145)]
rings = [offset_polygon(OUTLINE, d) for d, z in profile]
geo = Geo()
for i, a in enumerate(OUTLINE):
    j = (i + 1) % len(OUTLINE)
    b = OUTLINE[j]
    length = math.hypot(b[0] - a[0], b[1] - a[1])
    count = max(1, math.ceil(length / 2.0))
    for k in range(count):
        t0 = k / count + 0.002 / length
        t1 = (k + 1) / count - 0.002 / length
        ends = []
        for t in (t0, t1):
            ends.append([(ring[i][0] * (1 - t) + ring[j][0] * t,
                          ring[i][1] * (1 - t) + ring[j][1] * t, z)
                         for ring, (d, z) in zip(rings, profile)])
        geo.loft(ends[0], ends[1])
geo.finish('mitered single bullnose coping stones', M['coping'], 'Deck and coping')


# ------------------------------- paver terrace --------------------------------
# Rectangular subtraction creates the stepped hole without boolean modifiers.
# The existing lanai is excluded, so the house slab is neither covered nor edited.
HOLES = [(6 - COPING_W, 15 - COPING_W, 30 + COPING_W, 27 + COPING_W),
         (6 - COPING_W, 11.5 - COPING_W, 13 + COPING_W, 15),
         (LANAI_X, 0, DECK_W + 0.01, LANAI_Y)]
HOLES += [(a, 27, b, 30) for a, b, height in FEATURES]


def deck_regions(rect):
    parts = [rect]
    for hole in HOLES:
        parts = [piece for r in parts for piece in subtract_rect(r, hole)]
    return parts


geo = Geo()
for x0, y0, x1, y1 in deck_regions((0, 0, DECK_W, DECK_D)):
    geo.box(x0, y0, -0.34, x1, y1, -0.14)
geo.finish('deck bed with open basin and lanai cutouts', M['joint'], 'Deck and coping')
geo = Geo()
rng = random.Random(SEED)
for row in range(int(DECK_D)):
    x = -1.0 if row % 2 else 0.0
    while x < DECK_W:
        rect = (max(0, x), float(row), min(DECK_W, x + 2), float(row + 1))
        for x0, y0, x1, y1 in deck_regions(rect):
            geo.box(x0 + 0.005, y0 + 0.005, -0.14,
                    x1 - 0.005, y1 - 0.005, -0.006, rng.randrange(len(PAVERS)))
        x += 2
geo.finish('individual staggered ivory deck pavers', PAVERS, 'Deck and coping', 0.004)
# Small access landings at the two enclosure doors, as indicated by plan tabs.
for side, x0, x1, y0 in (('left', -3, 0, 0.8), ('right', 33, 36, 8.8)):
    box(side + ' screen door landing', (x0, y0, -0.30), (x1, y0 + 4, -0.01),
        M['coping'], 'Deck and coping', 0.025)


# ---------------------- raised blue waterfall feature -------------------------
for index, (a, b, height) in enumerate(FEATURES):
    box('raised feature tier %d' % (index + 1), (a, 27, -0.18), (b, 30, height - 0.13),
        M['grout'], 'Waterfall feature')
    # Front, ends and outside face are ceramic faced. Caps overhang slightly.
    tile_strip('feature front ceramic %d' % index, (b, 27), (a, 27),
               -0.17, height - 0.13, 'Waterfall feature')
    tile_strip('feature rear ceramic %d' % index, (a, 30), (b, 30),
               -0.17, height - 0.13, 'Waterfall feature')
    tile_strip('feature left ceramic %d' % index, (a, 27), (a, 30),
               -0.17, height - 0.13, 'Waterfall feature')
    tile_strip('feature right ceramic %d' % index, (b, 30), (b, 27),
               -0.17, height - 0.13, 'Waterfall feature')
    g = Geo()
    n = math.ceil((b - a) / 2.0)
    for k in range(n):
        x0, x1 = a + (b - a) * k / n, a + (b - a) * (k + 1) / n
        g.box(x0 + 0.003, 26.94, height - 0.13,
              x1 - 0.003, 30.045, height)
    g.finish('light stone cap at +%d inches' % round(height * 12), M['coping'],
             'Waterfall feature', 0.028)
box('36 inch sheer descent dark outlet', (16.5, 26.975, 0.72), (19.5, 27.035, 0.79),
    M['black'], 'Waterfall feature')
box('36 inch spillway lip', (16.5, 26.90, 0.715), (19.5, 27.04, 0.733),
    M['steel'], 'Waterfall feature')


# ----------------------- fittings (no Blender lights) -------------------------
for i, (x, y, nx, ny) in enumerate(((17, 15, 0, 1), (26, 15, 0, 1),
                                   (10, 27, 0, -1), (26, 27, 0, -1))):
    z = WATER_Z - 1.2
    g = Geo()
    cylinder(g, (x, y, z), (x + nx * 0.065, y + ny * 0.065, z), 0.10)
    g.finish('return fitting %d of 4' % (i + 1), M['pvc'], 'Equipment and fittings')
    g = Geo()
    cylinder(g, (x + nx * 0.066, y + ny * 0.066, z),
             (x + nx * 0.076, y + ny * 0.076, z), 0.038)
    g.finish('return nozzle %d' % (i + 1), M['black'], 'Equipment and fittings')
# Deep-end light above the bench. Geometry only, not an illumination object.
g = Geo()
cylinder(g, (30, 21, WATER_Z - 0.9), (29.94, 21, WATER_Z - 0.9), 0.105)
g.finish('24W nicheless fixture rim - unlit', M['steel'], 'Equipment and fittings')
g = Geo()
cylinder(g, (29.939, 21, WATER_Z - 0.9), (29.931, 21, WATER_Z - 0.9), 0.082)
g.finish('nicheless color light lens - unlit', M['lens'], 'Equipment and fittings')
# One main drain, following the sloped floor rather than floating above it.
g = Geo()
x0, y0, size = 25.6, 20.3, 0.68
g.prism([(x0, y0, floor_z(x0) + 0.035), (x0 + size, y0, floor_z(x0 + size) + 0.035),
         (x0 + size, y0 + size, floor_z(x0 + size) + 0.035),
         (x0, y0 + size, floor_z(x0) + 0.035)], (0, 0, -0.025))
g.finish('single main drain cover', M['pvc'], 'Equipment and fittings')
g = Geo()
for i in range(8):
    y = y0 + 0.06 + i * 0.073
    g.face([(x0 + 0.06, y, floor_z(x0 + 0.06) + 0.038),
            (x0 + size - 0.06, y, floor_z(x0 + size - 0.06) + 0.038),
            (x0 + size - 0.06, y + 0.022, floor_z(x0 + size - 0.06) + 0.038),
            (x0 + 0.06, y + 0.022, floor_z(x0 + 0.06) + 0.038)])
g.finish('drain cover slots', M['black'], 'Equipment and fittings')
box('skimmer dark throat', (23.5, 15.014, -0.60), (24.5, 15.03, -0.23), M['black'])
box('skimmer lower weir', (23.54, 15.031, -0.60), (24.46, 15.055, -0.48), M['pvc'])
box('skimmer deck access lid', (23.64, 13.92, -0.005), (24.36, 14.62, 0.008), M['coping'], bevel=0.015)

# 43 linear feet of deck channel; exact routing is an appearance assumption.
DRAIN_PATH = [(0.4, 0.2), (0.4, 10.2), (32.6, 10.2), (32.6, 11.0)]
assert abs(sum(math.dist(a, b) for a, b in zip(DRAIN_PATH[:-1], DRAIN_PATH[1:])) - 43) < 1e-6
g, slots = Geo(), Geo()
for a, b in zip(DRAIN_PATH[:-1], DRAIN_PATH[1:]):
    bar(g, (*a, -0.025), (*b, -0.025), 0.08, 0.20)
    av, bv = Vector(a), Vector(b)
    axis = (bv - av).normalized()
    normal = Vector((-axis.y, axis.x))
    count = max(1, int((bv - av).length / 0.10))
    for i in range(count):
        p = av + (bv - av) * (i + 0.5) / count
        ends = (p - normal * 0.07, p + normal * 0.07)
        bar(slots, (*ends[0], 0.018), (*ends[1], 0.018), 0.008, 0.023)
g.finish('43 ft deck drainage grate', M['pvc'], 'Deck and coping')
slots.finish('deck drainage grate slots', M['black'], 'Deck and coping')


# ---------------------- closed, gently rippled water --------------------------
def ripple_z(x, y):
    z = WATER_Z + 0.004 * math.sin(x * 3.2 + y * 1.9) + 0.003 * math.cos(y * 4.5 - x)
    if BUILD_WATERFALL:
        r = math.hypot(x - 18, (y - 26.42) * 1.25)
        z += 0.014 * math.sin(r * 15) * math.exp(-r * 1.4)
    return z


def closed_grid_volume():
    g = Geo()
    keys = {}
    def vertex(x, y):
        key = (round(x, 6), round(y, 6))
        if key not in keys:
            keys[key] = len(g.v)
            g.v.append((x, y, ripple_z(x, y)))
        return keys[key]
    for x0, x1, y0, y1 in ((6, 30, 15, 27), (6, 13, 11.5, 15)):
        nx, ny = round((x1 - x0) * 4), round((y1 - y0) * 4)
        for j in range(ny):
            for i in range(nx):
                x, y = x0 + i * 0.25, y0 + j * 0.25
                g.f.append((vertex(x, y), vertex(x + 0.25, y),
                            vertex(x + 0.25, y + 0.25), vertex(x, y + 0.25)))
    top_faces = list(g.f)
    n = len(g.v)
    g.v.extend((x, y, floor_z(x) + 0.012) for x, y, z in list(g.v))
    edges = {}
    for face in top_faces:
        for a, b in zip(face, face[1:] + face[:1]):
            key = tuple(sorted((a, b)))
            if key in edges:
                edges[key] = None
            else:
                edges[key] = (a, b)
        g.f.append(tuple(i + n for i in reversed(face)))
    for edge in edges.values():
        if edge is not None:
            a, b = edge
            g.f.append((b, a, a + n, b + n))
    g.mi = [0] * len(g.f)
    return g.finish('continuous water volume with entry bay and local ripples', M['water'], 'Water', smooth=True)


if BUILD_WATER:
    closed_grid_volume()

if BUILD_WATERFALL:
    g = Geo()
    nx, ny = 28, 24
    for j in range(ny + 1):
        t = j / ny
        for i in range(nx + 1):
            u = i / nx
            x = 18 + (u - 0.5) * (3.0 - 0.16 * t)
            y = 26.90 - 0.49 * t + 0.008 * math.sin(u * 36) * t
            z = 0.735 - (0.735 - WATER_Z) * t * t
            g.v.append((x, y, z))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            g.f.append((a, a + 1, a + nx + 2, a + nx + 1))
    faces = list(g.f)
    n = len(g.v)
    g.v.extend((x, y + 0.012, z) for x, y, z in list(g.v))
    edges = {}
    for face in faces:
        for a, b in zip(face, face[1:] + face[:1]):
            key = tuple(sorted((a, b)))
            edges[key] = None if key in edges else (a, b)
        g.f.append(tuple(i + n for i in reversed(face)))
    for edge in edges.values():
        if edge is not None:
            a, b = edge
            g.f.append((b, a, a + n, b + n))
    g.mi = [0] * len(g.f)
    g.finish('36 inch static sheer descent water sheet', M['sheet'], 'Water', smooth=True)
    # Small restrained impact flecks, not an opaque painted splash disk.
    g = Geo()
    rng = random.Random(SEED + 1)
    for i in range(45):
        x = 16.63 + rng.random() * 2.74
        y = 26.30 + rng.random() * 0.20
        length = rng.uniform(0.025, 0.075)
        cylinder(g, (x, y, WATER_Z + 0.018), (x + length, y + 0.025, WATER_Z + 0.022), 0.009, 8)
    g.finish('fine waterfall impact aeration', M['foam'], 'Water')


# ------------------------- bronze mansard screen cage -------------------------
def screen_quad(geo, points):
    geo.face(points)


def screened_wall(name, a, b, door=None):
    a, b = Vector(a), Vector(b)
    axis = (b - a).normalized()
    length = (b - a).length
    cuts = {0.0, length}
    for i in range(1, math.ceil(length / 5.5)):
        cuts.add(length * i / math.ceil(length / 5.5))
    if door:
        d0, d1 = door
        cuts = {v for v in cuts if not d0 < v < d1}
        cuts.update((d0, d1))
    cuts = sorted(cuts)
    frame, mesh = Geo(), Geo()
    def p(u, z):
        q = a + axis * u
        return (q.x, q.y, z)
    for u in cuts:
        bar(frame, p(u, 0), p(u, CAGE_EAVE), 0.14, 0.14)
    bar(frame, p(0, CAGE_EAVE), p(length, CAGE_EAVE), 0.16, 0.16)
    for u0, u1 in zip(cuts[:-1], cuts[1:]):
        is_door = door and abs(u0 - door[0]) < 1e-6 and abs(u1 - door[1]) < 1e-6
        levels = [0.10, 3.2, CAGE_EAVE - 0.08] if not is_door else [7.0, CAGE_EAVE - 0.08]
        for low, high in zip(levels[:-1], levels[1:]):
            screen_quad(mesh, [p(u0 + 0.065, low), p(u1 - 0.065, low),
                               p(u1 - 0.065, high), p(u0 + 0.065, high)])
        for z in ([0.08, 3.2] if not is_door else [7.0]):
            bar(frame, p(u0, z), p(u1, z), 0.085, 0.085)
        if is_door:
            # Closed physical screen door with latch and lower kick plate.
            for u in (u0 + 0.08, u1 - 0.08):
                bar(frame, p(u, 0.10), p(u, 6.93), 0.08, 0.08)
            for z in (0.13, 1.0, 3.35, 6.90):
                bar(frame, p(u0 + 0.08, z), p(u1 - 0.08, z), 0.08, 0.08)
            screen_quad(mesh, [p(u0 + 0.12, 1.05), p(u1 - 0.12, 1.05),
                               p(u1 - 0.12, 6.86), p(u0 + 0.12, 6.86)])
            screen_quad(frame, [p(u0 + 0.12, 0.16), p(u1 - 0.12, 0.16),
                                p(u1 - 0.12, 0.96), p(u0 + 0.12, 0.96)])
            bar(frame, p(u1 - 0.24, 3.3), p(u1 - 0.24, 3.65), 0.09, 0.14)
    frame.finish(name + ' bronze frame and door', M['bronze'], 'Screen enclosure')
    mesh.finish(name + ' open weave', M['screen'], 'Screen enclosure', uv=True)


if BUILD_SCREEN_ENCLOSURE:
    screened_wall('left side', (0, 0), (0, 30), (1.0, 4.0))
    screened_wall('right side', (33, LANAI_Y), (33, 30), (1.0, 4.0))
    screened_wall('rear wall', (0, 30), (33, 30))
    # Close the existing open lanai flank with added screen infill only.
    # No house column, slab, soffit or roof is edited or duplicated.
    flank_frame, flank_mesh = Geo(), Geo()
    flank_top = (3.025 - 0.18) / FT
    for ya, yb in ((0.0, LANAI_Y / 2), (LANAI_Y / 2, LANAI_Y)):
        for y in (ya, yb):
            bar(flank_frame, (33, y, 0), (33, y, flank_top), 0.10, 0.10)
        for z in (0.08, 3.2, flank_top - 0.04):
            bar(flank_frame, (33, ya, z), (33, yb, z), 0.075, 0.075)
        screen_quad(flank_mesh, [(33, ya + 0.05, 0.10), (33, yb - 0.05, 0.10),
                                 (33, yb - 0.05, flank_top - 0.05),
                                 (33, ya + 0.05, flank_top - 0.05)])
    flank_frame.finish('added lanai flank screen frame', M['bronze'], 'Screen enclosure')
    flank_mesh.finish('added lanai flank screen mesh', M['screen'], 'Screen enclosure', uv=True)
    # L-shaped roof avoids the existing lanai roof: no duplicate roof over it.
    edge = [(0, 0), (LANAI_X, 0), (LANAI_X, LANAI_Y),
            (33, LANAI_Y), (33, 30), (0, 30)]
    inner = offset_polygon(edge, -CAGE_INSET)
    frame, mesh = Geo(), Geo()
    for i, a in enumerate(edge):
        j = (i + 1) % len(edge)
        b, ia, ib = edge[j], inner[i], inner[j]
        bar(frame, (*a, CAGE_EAVE), (*b, CAGE_EAVE), 0.16, 0.16)
        bar(frame, (*ia, CAGE_EAVE + CAGE_RISE), (*ib, CAGE_EAVE + CAGE_RISE), 0.15, 0.15)
        n = max(1, math.ceil(math.dist(a, b) / 5.5))
        for k in range(n + 1):
            t = k / n
            p = (a[0] * (1 - t) + b[0] * t, a[1] * (1 - t) + b[1] * t, CAGE_EAVE)
            q = (ia[0] * (1 - t) + ib[0] * t, ia[1] * (1 - t) + ib[1] * t, CAGE_EAVE + CAGE_RISE)
            bar(frame, p, q, 0.12, 0.12)
            if k:
                screen_quad(mesh, [previous_p, p, q, previous_q])
            previous_p, previous_q = p, q
    # Horizontal L-shaped crown, divided into framed screen panels.
    for x0, y0, x1, y1 in ((3, 3, LANAI_X - 3, 27),
                           (LANAI_X - 3, LANAI_Y + 3, 30, 27)):
        nx, ny = math.ceil((x1 - x0) / 5.5), math.ceil((y1 - y0) / 5.5)
        z = CAGE_EAVE + CAGE_RISE
        for i in range(nx + 1):
            x = x0 + (x1 - x0) * i / nx
            bar(frame, (x, y0, z), (x, y1, z), 0.12, 0.12)
        for j in range(ny + 1):
            y = y0 + (y1 - y0) * j / ny
            bar(frame, (x0, y, z), (x1, y, z), 0.12, 0.12)
        for j in range(ny):
            for i in range(nx):
                a, b = x0 + (x1 - x0) * i / nx, x0 + (x1 - x0) * (i + 1) / nx
                c, d = y0 + (y1 - y0) * j / ny, y0 + (y1 - y0) * (j + 1) / ny
                screen_quad(mesh, [(a, c, z), (b, c, z), (b, d, z), (a, d, z)])
    frame.finish('L shaped mansard roof framing', M['bronze'], 'Screen enclosure')
    mesh.finish('mansard roof open screen panels', M['screen'], 'Screen enclosure', uv=True)


# ----------------------- removable child barrier / gate ----------------------
if BUILD_CHILD_BARRIER:
    # Follows the jog shown between the steps and lanai; gate location inferred.
    path = [(0, 11.5), (2, 9.5), (15.3, 9.5), (15.3, 12.2), (31, 12.2), (33, 13.7)]
    frame, mesh = Geo(), Geo()
    for segment, (a, b) in enumerate(zip(path[:-1], path[1:])):
        av, bv = Vector(a), Vector(b)
        length = (bv - av).length
        n = max(1, math.ceil(length / 3))
        cuts = [i / n for i in range(n + 1)]
        if segment == 1:
            cuts = sorted(set([t for t in cuts if not 0.35 < t < 0.35 + 3 / length] +
                              [0.35, 0.35 + 3 / length]))
        for t in cuts:
            p = av + (bv - av) * t
            cylinder(frame, (p.x, p.y, 0.01), (p.x, p.y, BARRIER_H), 0.038, 12)
        for ta, tb in zip(cuts[:-1], cuts[1:]):
            a0, b0 = av + (bv - av) * ta, av + (bv - av) * tb
            for z in (0.08, BARRIER_H - 0.04):
                bar(frame, (*a0, z), (*b0, z), 0.035, 0.035)
            screen_quad(mesh, [(*a0, 0.10), (*b0, 0.10),
                               (*b0, BARRIER_H - 0.05), (*a0, BARRIER_H - 0.05)])
            if segment == 1 and abs(ta - 0.35) < 1e-6:
                bar(frame, (*a0, 0.05), (*a0, BARRIER_H), 0.07, 0.07)
                bar(frame, (*b0, 0.05), (*b0, BARRIER_H + 0.35), 0.07, 0.07)
    frame.finish('removable barrier posts and 3 ft gate', M['bronze'], 'Child barrier')
    mesh.finish('removable barrier open mesh', M['screen'], 'Child barrier', uv=True)


# --------------------- equipment: appearance-only assembly --------------------
if BUILD_EQUIPMENT:
    # Outside the house side wall, as on the sheet. No heater or spa equipment.
    box('3 x 8 ft equipment pad', (33.35, -10.0, -0.43), (36.35, -2.0, -0.10),
        M['concrete'], bevel=0.02)
    box('variable speed pump mounting foot', (33.65, -4.9, -0.10), (35.1, -3.0, 0.10), M['black'])
    g = Geo()
    cylinder(g, (34.35, -4.85, 0.57), (34.35, -3.65, 0.57), 0.41)
    cylinder(g, (34.35, -3.4, 0.12), (34.35, -3.4, 1.0), 0.39)
    g.finish('Jandy FloPro style pump - approximate casing', M['equipment'], 'Equipment and fittings')
    box('pump controller', (33.96, -4.65, 0.84), (34.74, -3.96, 1.15), M['equipment'], bevel=0.05)
    box('pump display', (34.04, -4.55, 1.15), (34.66, -4.07, 1.17), M['black'])
    g = Geo()
    cylinder(g, (34.65, -7.4, -0.1), (34.65, -7.4, 2.55), 0.70, 40)
    cylinder(g, (34.65, -7.4, 2.55), (34.65, -7.4, 2.77), 0.61, 40)
    g.finish('cartridge filter tank - approximate', M['filter'], 'Equipment and fittings', 0.04)
    g = Geo()
    cylinder(g, (34.65, -7.4, 1.31), (34.65, -7.4, 1.40), 0.724, 40)
    g.finish('filter tank clamp band', M['black'], 'Equipment and fittings')
    pipes = Geo()
    for points in (((34.35, -3.4, 1.0), (34.35, -2.8, 1.0), (35.6, -2.8, 1.0), (35.6, -2.8, -0.1)),
                   ((34.35, -4.9, 0.55), (35.6, -4.9, 0.55), (35.6, -6.5, 0.55), (34.65, -6.5, 0.55)),
                   ((34.65, -8.1, 0.55), (34.65, -8.9, 0.55), (35.6, -8.9, 0.55), (35.6, -8.9, -0.1))):
        for a, b in zip(points[:-1], points[1:]):
            cylinder(pipes, a, b, 0.087, 16)
    pipes.finish('illustrative equipment pipework - not a plumbing design', M['pvc'], 'Equipment and fittings')
    g = Geo()
    cylinder(g, (34.78, -8.9, 0.55), (35.42, -8.9, 0.55), 0.145, 24)
    g.finish('Jandy salt cell style housing - approximate', M['equipment'], 'Equipment and fittings')
    box('salt controller and mechanical timer cabinet', (33.16, -6.25, 1.55),
        (33.35, -5.15, 2.65), M['equipment'], bevel=0.025)

bpy.context.view_layer.update()
print('Honor pool added. House objects and materials were not modified.')
print('Pool outline: %.1f sf / %.1f ft perimeter. Plan orientation: garage R.' % (AREA, PERIMETER))
print('Screen cage and child barrier switches are at the top of honor_pool.py.')
