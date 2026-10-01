# Written by GPT-6-astra on medium reasoning on Oct 1 2026

"""Honor / Grand Park — FH-1 exterior and first-floor interior.

Run this entire file in Blender's Text Editor. No add-ons or external textures.
Creates only mesh objects and materials in the HONOR_FH1 collection; rerunning
replaces only this script's collection. Existing scene objects are untouched.

REFERENCE / LIMITATIONS
  Supplied brochure page 1: FH-1 rendering (NOT the C-1 or I-1 finishes).
  Supplied page 2: C-1 floor plan used as a dimensional/footprint reference.
  Plan-derived: projecting 18'4\" wide garage, recessed entry, nearly square
  upper floor, 16'4\" x 8' rear lanai, rear openings and upper side openings.
  Ceiling references: ground 9'4\", upper 8'8\". Exterior widths include walls.
  Heights of openings, roof pitches and trim estimated from rendering.
  Paint colors use the exact RGB values supplied in paint_codes.md:
  Delicate White: body, secondary body/gable and all painted white trim.
  SkyDiving: front entry door. Witchcraft: garage door, shutters and brackets.
  Shutter/bracket paint placement inferred from coloring.jpeg; doors per user.
  Roof, glazing, factory window frames and hardware remain photo approximations.
  LRV values stored as metadata; appearance still depends on lighting/display.
  Right-hand garage variant: the full exterior is mirrored across X = W / 2.
  Garage is on the right and entry on the left when viewed from the street.
  Dimensions, details and paint assignments are preserved; no negative scales.
  Set RIGHT_HAND_GARAGE = False to restore the brochure's left-hand layout.
  Side/rear finishes and lanai roof are inferred, not documented elevations.
  Optional lanai extension and optional ground stair window are NOT included.
  First-floor increment: leisure, foyer, powder bath, kitchen, cafe, great room,
  service vestibule/pantry, rear garage extension and straight stair flight.
  Interior traced from honor_page-0002.jpg and fitted to the existing shell;
  small partition offsets and the entry-door alignment are adjusted to fit.
  The brochure's rear 11'4\" x 13'1\" GARAGE bay remains part of the garage.
  Interior finishes, service-room labels, cabinets and stair details inferred.
  Ground-floor glazing is clear and entry/service doors are statically open
  by default. Upper-floor rooms remain deferred; upper glazing stays backed.
  First-floor ceiling has a real stairwell opening; no new roof or footprint.
  Interior switches are below. No loose furniture, optional rooms or lights.
  Source reviewed only; execute and inspect in Blender before final export.

Coordinates: meters; X left/right, +Y toward rear, +Z up. Front faces -Y.
Designed for Blender 3.6+ using direct mesh creation, not context-sensitive ops.
No cameras, lights, ground plane, landscaping or world changes.
Lit Principled materials are the default; lighting reveals siding and shingles.
Retains the selected base colors, including the #C6C6C6 house paint override.
Sets scene-wide Standard/sRGB color management; no companion script required.
Appearance varies with lighting. All generated materials use lit Principled shaders.
"""

import math
import random
import bpy
import bmesh
from mathutils import Vector


# --------------------------- adjustable dimensions ---------------------------
COLLECTION_NAME = 'HONOR_FH1'
TAG = 'honor_fh1_generated'
RIGHT_HAND_GARAGE = True         # viewed from the street; False restores brochure layout
W = 10.06
GARAGE_W = 5.97
FRONT = 6.24                     # front of two-story main block
BACK = 17.04
PORCH_FRONT = 4.92
LANAI_W = 4.98
LANAI_D = 2.4384
FF = 0.18
UPPER_FLOOR = 3.35
UPPER_EAVE = 6.18
GARAGE_EAVE = 3.04
ROOF_EAVE = 6.30
OVERHANG = 0.38
MAIN_PITCH = 0.42
LOW_EAVE = 3.18
GARAGE_PITCH = 0.49
PORCH_PITCH = 0.42
SIDING_EXPOSURE = 0.165
MODEL_SHINGLES = True            # actual clipped, overlapping shingle geometry
SHINGLE_WIDTH = 0.305
SHINGLE_EXPOSURE = 0.145
SEED = 1701

# First-floor increment. Coordinates below use the brochure's LEFT-garage frame;
# Geometry.finish() mirrors the entire house/interior together exactly once.
BUILD_FIRST_FLOOR = True
BUILD_FIRST_FLOOR_CEILINGS = True  # False opens the floor plate for inspection
BUILD_FIRST_FLOOR_FIXTURES = True  # Kitchen, pantry shelves and powder fixtures
FIRST_FLOOR_OPEN_DOORS = True     # Static open leaves for walkthrough access
FIRST_FLOOR_CLEAR_GLASS = True    # Ground-floor glazing only; upper shell retained
INTERIOR_WALL_T = 0.115
INTERIOR_FLOOR_Z = FF + 0.018
INTERIOR_CEILING_Z = INTERIOR_FLOOR_Z + (9 + 4 / 12) * 0.3048
# Traced from honor_page-0002.jpg and fitted to the existing exterior footprint.
# These partitions/finishes are visual approximations, not construction drawings.
GARAGE_EXTENSION_X = 3.70
GARAGE_REAR_Y = 10.25
SERVICE_REAR_Y = 12.05
FOYER_X = 7.45
STAIR_X0, STAIR_X1 = 8.82, W - 0.205
STAIR_Y0, STAIR_Y1 = 8.68, 12.68  # upper/front landing to lower/rear stair foot
POWDER_REAR_Y = STAIR_Y0
assert 0 < GARAGE_EXTENSION_X < GARAGE_W < FOYER_X < STAIR_X0 < STAIR_X1 < W
assert FRONT < GARAGE_REAR_Y < SERVICE_REAR_Y < BACK
assert INTERIOR_FLOOR_Z < INTERIOR_CEILING_Z < UPPER_FLOOR


# ------------------------------ safe ownership -------------------------------
def clear_owned_collection():
    old = bpy.data.collections.get(COLLECTION_NAME)
    if old is not None:
        if not old.get(TAG):
            raise RuntimeError('An unowned HONOR_FH1 collection exists; rename it first.')
        for obj in list(old.all_objects):
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if isinstance(data, bpy.types.Mesh) and data.users == 0:
                bpy.data.meshes.remove(data)
        bpy.data.collections.remove(old)
    for mat in list(bpy.data.materials):
        if mat.get(TAG) and mat.users == 0:
            bpy.data.materials.remove(mat)


clear_owned_collection()
COL = bpy.data.collections.new(COLLECTION_NAME)
COL[TAG] = True
bpy.context.scene.collection.children.link(COL)
COL['reference'] = 'Honor brochure FH-1 rendering; C-1 plan for approximate footprint'
COL['units'] = 'Geometry is in meters; scene unit settings are not modified'
COL['accuracy_note'] = 'Roof pitches and unseen elevations are inferred, not surveyed'
COL['garage_side_from_street'] = 'right' if RIGHT_HAND_GARAGE else 'left'


# Always use lit Principled materials to reveal siding and shingle geometry.
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


def linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def material(name, rgb, roughness=0.65, noise=0.0, metallic=0.0):
    mat = bpy.data.materials.new('Honor | ' + name)
    mat[TAG] = True
    mat.use_nodes = True
    rgba = tuple(linear(c) for c in rgb) + (1.0,)
    mat.diffuse_color = rgba
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = rgba
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    if noise:
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        tex = nodes.new('ShaderNodeTexNoise')
        tex.inputs['Scale'].default_value = 125.0
        tex.inputs['Detail'].default_value = 2.0
        coords = nodes.new('ShaderNodeTexCoord')
        links.new(coords.outputs['Object'], tex.inputs['Vector'])
        bump = nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = 0.22
        bump.inputs['Distance'].default_value = noise
        links.new(tex.outputs['Fac'], bump.inputs['Height'])
        links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    return mat


# Paint RGB values transcribed from paint_codes.md; no external file needed.
# Treat the supplied 8-bit RGB values as sRGB. material() converts them to linear
# exactly once. LRV is retained as reference metadata, NOT a brightness multiplier.
# SkyDiving on entry / Witchcraft on garage follow the user's recollection.
# Witchcraft on shutters and gable brackets is inferred from coloring.jpeg.
# Roofing, glazing, factory window frames and hardware retain photo-based colors.
# Preserve dimensions and roof profiles; RIGHT_HAND_GARAGE controls mirroring.
PAINT_CODES = {
    'Delicate White': {'rgb': (198, 198, 198), 'lrv': 88},  # User override: #C6C6C6; LRV is original reference only
    'SkyDiving': {'rgb': (198, 214, 215), 'lrv': 65},
    'Witchcraft': {'rgb': (71, 76, 80), 'lrv': 7},
}


def paint(name, color, roughness=0.65, noise=0.0):
    spec = PAINT_CODES[color]
    rgb = tuple(channel / 255.0 for channel in spec['rgb'])
    mat = material(color + ' | ' + name, rgb, roughness, noise)
    mat['paint_name'] = color
    mat['paint_srgb_8bit'] = list(spec['rgb'])
    mat['paint_lrv_reference'] = spec['lrv']
    mat['paint_source'] = 'User-supplied paint_codes.md'
    return mat


M = {
    'siding': paint('lap siding', 'Delicate White', noise=0.001),
    'stucco': paint('stucco body', 'Delicate White', noise=0.007),
    'gable': paint('secondary body and gable boards', 'Delicate White', noise=0.001),
    'trim': paint('trim, fascia, columns and casing', 'Delicate White', 0.52),
    'blue': paint('shutters', 'Witchcraft', 0.53),
    'blue_edge': paint('shutter battens and braces', 'Witchcraft', 0.53),
    'door': paint('front entry door', 'SkyDiving', 0.53),
    'brackets': paint('gable brackets', 'Witchcraft', 0.54),
    'wood': material('near black factory window frames', (0.14, 0.155, 0.17), 0.54),
    'garage': paint('garage door', 'Witchcraft', 0.57),
    'panel': paint('garage raised panels', 'Witchcraft', 0.54),
    'recess': material('neutral dark panel and sash recesses', (0.12, 0.135, 0.15), 0.76),
    'glass': material('opaque dark reflective exterior glazing', (0.115, 0.17, 0.18), 0.16, metallic=0.35),
    'concrete': material('foundation and porch slab', (0.61, 0.60, 0.55), noise=0.003),
    'roofbase': material('dark charcoal roof underlay', (0.18, 0.185, 0.195), 0.88),
    'metal': material('black door hardware', (0.105, 0.115, 0.125), 0.3, metallic=0.75),
}
SHINGLES = [material('charcoal gray roof shingle %02d' % i,
                    (0.335 * f, 0.34 * f, 0.35 * f), 0.9, noise=0.0015)
            for i, f in enumerate((0.83, 0.90, 0.96, 1.0, 1.045, 1.09, 1.14))]


# Interior finishes are neutral placeholders, NOT additional exterior paint codes.
if BUILD_FIRST_FLOOR:
    M.update({
        'int_wall': material('Interior | warm off-white drywall - inferred', (0.88, 0.87, 0.83), 0.83),
        'int_trim': material('Interior | white doors and millwork - inferred', (0.94, 0.935, 0.91), 0.56),
        'int_ceiling': material('Interior | matte white ceiling', (0.93, 0.93, 0.90), 0.92),
        'int_tile': material('Interior | warm light tile - inferred', (0.76, 0.74, 0.68), 0.55),
        'int_grout': material('Interior | fine warm grout', (0.57, 0.55, 0.50), 0.88),
        'int_wood': material('Interior | pale oak leisure floor - inferred', (0.64, 0.51, 0.36), 0.65),
        'int_counter': material('Interior | pale stone worktop - inferred', (0.88, 0.875, 0.84), 0.34),
        'int_ceramic': material('Interior | white sanitary ceramic', (0.94, 0.95, 0.93), 0.22),
        'int_steel': material('Interior | brushed appliance steel', (0.60, 0.62, 0.64), 0.30, metallic=0.8),
        'int_dark': material('Interior | appliance glass and recesses', (0.06, 0.075, 0.08), 0.24),
        'int_glass': material('Interior | clear ground-floor glazing', (0.98, 0.995, 1.0), 0.08),
    })
    glazing = M['int_glass'].node_tree.nodes.get('Principled BSDF')
    transmission = glazing.inputs.get('Transmission Weight')
    if transmission is None:
        transmission = glazing.inputs.get('Transmission')
    if transmission is not None:
        transmission.default_value = 1.0
    glazing.inputs['IOR'].default_value = 1.45


# ------------------------------- mesh utilities ------------------------------
class Geometry:
    """Batch disconnected solids into one named mesh; avoids thousands of objects."""
    def __init__(self):
        self.vertices = []
        self.faces = []
        self.indices = []

    def face(self, points, material_index=0):
        if len(points) < 3:
            return
        k = len(self.vertices)
        self.vertices.extend(tuple(p) for p in points)
        self.faces.append(tuple(range(k, k + len(points))))
        self.indices.append(material_index)

    def prism(self, ring, offset, material_index=0):
        ring = [Vector(p) for p in ring]
        if len(ring) < 3:
            return
        off = Vector(offset)
        upper = [p + off for p in ring]
        k, n = len(self.vertices), len(ring)
        self.vertices.extend(tuple(p) for p in ring + upper)
        self.faces.append(tuple(k + i for i in reversed(range(n))))
        self.faces.append(tuple(k + n + i for i in range(n)))
        self.indices.extend([material_index, material_index])
        for i in range(n):
            j = (i + 1) % n
            self.faces.append((k + i, k + j, k + n + j, k + n + i))
            self.indices.append(material_index)

    def box(self, lo, hi, material_index=0):
        x0, y0, z0 = lo
        x1, y1, z1 = hi
        if min(x1 - x0, y1 - y0, z1 - z0) <= 0.000001:
            return
        self.prism([(x0, y0, z0), (x1, y0, z0),
                    (x1, y1, z0), (x0, y1, z0)], (0, 0, z1 - z0), material_index)

    def finish(self, name, materials, bevel=0.0):
        if not self.faces:
            return None
        if not isinstance(materials, (list, tuple)):
            materials = [materials]
        # All builders emit world-aligned coordinates. Mirror at this one output
        # point so roofs, openings, trim, hardware and lanai stay in registration.
        # Bake X -> W - X into mesh data, not a negative object scale. Reverse
        # winding for the reflection, then run the normal correction below.
        vertices, faces = self.vertices, self.faces
        if RIGHT_HAND_GARAGE:
            vertices = [(W - x, y, z) for x, y, z in self.vertices]
            faces = [tuple(reversed(face)) for face in self.faces]
            side_names = {'left': 'right', 'right': 'left',
                          'Left': 'Right', 'Right': 'Left'}
            name = ' '.join(side_names.get(word, word) for word in name.split(' '))
        mesh = bpy.data.meshes.new(name + ' mesh')
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        for mat in materials:
            mesh.materials.append(mat)
        for poly, index in zip(mesh.polygons, self.indices):
            poly.material_index = index
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(mesh)
        bm.free()
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        obj[TAG] = True
        COL.objects.link(obj)
        if bevel:
            modifier = obj.modifiers.new('small real-world edge radii', 'BEVEL')
            modifier.width = bevel
            modifier.segments = 2
        return obj


def box(name, lo, hi, mat, bevel=0.0):
    g = Geometry()
    g.box(lo, hi)
    return g.finish(name, mat, bevel)


def beam(name, a, b, width, depth, mat):
    # Explicit basis keeps fascia height vertical and brace depth out of plane.
    a, b = Vector(a), Vector(b)
    direction = b - a
    if direction.length < 1e-7:
        return None
    axis = direction.normalized()
    up = Vector((0, 0, 1))
    wide = up - axis * up.dot(axis)
    if wide.length < 1e-7:
        wide = Vector((1, 0, 0))
    wide.normalize()
    thick = axis.cross(wide).normalized()
    w, d = wide * width / 2, thick * depth / 2
    g = Geometry()
    g.prism([a - w - d, a + w - d, a + w + d, a - w + d], direction)
    return g.finish(name, mat)


class Facade:
    def __init__(self, name, origin, tangent, normal, length):
        self.name = name
        self.origin = Vector((origin[0], origin[1], 0))
        self.u = Vector((tangent[0], tangent[1], 0))
        self.n = Vector((normal[0], normal[1], 0))
        self.length = length

    def p(self, u, depth, z):
        return self.origin + self.u * u + self.n * depth + Vector((0, 0, z))

    def solid(self, geo, u0, u1, d0, d1, z0, z1, index=0):
        if min(u1 - u0, d1 - d0, z1 - z0) <= 0.000001:
            return
        geo.prism([self.p(u0, d0, z0), self.p(u1, d0, z0),
                   self.p(u1, d1, z0), self.p(u0, d1, z0)],
                  (0, 0, z1 - z0), index)

    def part(self, name, u0, u1, d0, d1, z0, z1, mat, bevel=0.0):
        g = Geometry()
        self.solid(g, u0, u1, d0, d1, z0, z1)
        return g.finish(self.name + ' | ' + name, mat, bevel)


def opening(name, center, width, bottom, height, kind='window', shutters=False):
    return dict(name=name, u=center, w=width, z=bottom, h=height,
                kind=kind, shutters=shutters)


def intervals_without_openings(length, openings, z0, z1):
    spans = [(0.0, length)]
    for op in openings:
        if z1 <= op['z'] + 1e-7 or z0 >= op['z'] + op['h'] - 1e-7:
            continue
        a, b = op['u'] - op['w'] / 2, op['u'] + op['w'] / 2
        result = []
        for l, r in spans:
            if b <= l or a >= r:
                result.append((l, r))
            else:
                if a > l:
                    result.append((l, a))
                if b < r:
                    result.append((b, r))
        spans = result
    return spans


def wall(facade, bottom, top, openings=(), lap=False):
    # Shell subdivided at opening boundaries: genuine recesses, no wall over glass.
    levels = sorted(set([bottom, top] + [max(bottom, min(top, v))
                    for op in openings for v in (op['z'], op['z'] + op['h'])]))
    geo = Geometry()
    for low, high in zip(levels[:-1], levels[1:]):
        for l, r in intervals_without_openings(facade.length, openings, low, high):
            facade.solid(geo, l, r, -0.19, 0, low, high)
    geo.finish(facade.name + ' | closed exterior shell', M['siding'] if lap else M['stucco'])
    if BUILD_FIRST_FLOOR and bottom < UPPER_FLOOR - 0.1:
        # Thin interior skin respects precisely the same actual window/door holes.
        lining, skirting = Geometry(), Geometry()
        for low, high in zip(levels[:-1], levels[1:]):
            high = min(high, INTERIOR_CEILING_Z)
            if high <= low:
                continue
            for l, r in intervals_without_openings(facade.length, openings, low, high):
                facade.solid(lining, l, r, -0.205, -0.19, low, high)
        for l, r in intervals_without_openings(facade.length, openings,
                                               INTERIOR_FLOOR_Z, INTERIOR_FLOOR_Z + 0.10):
            facade.solid(skirting, l, r, -0.218, -0.205,
                         INTERIOR_FLOOR_Z, INTERIOR_FLOOR_Z + 0.10)
        lining.finish('Interior | ' + facade.name + ' drywall lining', M['int_wall'])
        skirting.finish('Interior | ' + facade.name + ' baseboard', M['int_trim'])
        for op in openings:
            a, b = op['u'] - op['w'] / 2, op['u'] + op['w'] / 2
            z, t = op['z'], op['z'] + op['h']
            trim = Geometry()
            facade.solid(trim, a - 0.065, a, -0.22, -0.19, z, t + 0.065)
            facade.solid(trim, b, b + 0.065, -0.22, -0.19, z, t + 0.065)
            facade.solid(trim, a, b, -0.22, -0.19, t, t + 0.065)
            if op['kind'] == 'window':
                facade.solid(trim, a - 0.065, b + 0.065, -0.245, -0.06, z - 0.035, z)
            trim.finish('Interior | ' + facade.name + ' | ' + op['name'] + ' casing', M['int_trim'])
    if lap:
        boards = Geometry()
        z = bottom
        while z < top - 1e-6:
            end = min(z + SIDING_EXPOSURE, top)
            cuts = sorted(set([z, end] + [v for v in levels if z < v < end]))
            for low, high in zip(cuts[:-1], cuts[1:]):
                dlow = 0.035 - 0.026 * (low - z) / SIDING_EXPOSURE
                dhigh = 0.035 - 0.026 * (high - z) / SIDING_EXPOSURE
                for l, r in intervals_without_openings(facade.length, openings, low, high):
                    profile = [facade.p(l, 0.003, low), facade.p(l, dlow, low),
                               facade.p(l, dhigh, high - 0.001), facade.p(l, 0.003, high - 0.001)]
                    boards.prism(profile, facade.u * (r - l))
            z = end
        boards.finish(facade.name + ' | individual beveled lap courses', M['siding'])
    for op in openings:
        if op['kind'] == 'garage':
            garage_door(facade, op)
        elif op['kind'] == 'entry':
            entry_door(facade, op)
        elif op['kind'] == 'slider':
            window(facade, op, slider=True)
        else:
            window(facade, op)


def surround(f, op, width=0.095, sill=True, head=True):
    a, b = op['u'] - op['w'] / 2, op['u'] + op['w'] / 2
    z, t = op['z'], op['z'] + op['h']
    g = Geometry()
    f.solid(g, a - width, a, -0.025, 0.084, z, t)
    f.solid(g, b, b + width, -0.025, 0.084, z, t)
    if head:
        f.solid(g, a - width, b + width, -0.025, 0.084, t, t + width)
    if sill:
        f.solid(g, a - width - 0.02, b + width + 0.02, -0.035, 0.12, z - 0.065, z)
    g.finish(f.name + ' | ' + op['name'] + ' ivory casing', M['trim'], 0.003)


def window(f, op, slider=False):
    a, b = op['u'] - op['w'] / 2, op['u'] + op['w'] / 2
    z, t, c = op['z'], op['z'] + op['h'], op['u']
    surround(f, op, width=0.07 if op['shutters'] else 0.095)
    clear = BUILD_FIRST_FLOOR and FIRST_FLOOR_CLEAR_GLASS and z < UPPER_FLOOR - 0.1
    if not clear:
        f.part(op['name'] + ' shadow reveal', a, b, -0.11, -0.078, z, t, M['recess'])
    else:
        # A perimeter reveal, not the old opaque slab across the whole opening.
        reveal = Geometry()
        for l, r in ((a, a + 0.035), (b - 0.035, b)):
            f.solid(reveal, l, r, -0.205, -0.06, z, t)
        for low, high in ((z, z + 0.035), (t - 0.035, t)):
            f.solid(reveal, a, b, -0.205, -0.06, low, high)
        reveal.finish(f.name + ' | ' + op['name'] + ' open perimeter reveal', M['trim'])
    f.part(op['name'] + (' clear glazing' if clear else ' backed glazing'),
           a + 0.04, b - 0.04, -0.075, -0.069 if clear else -0.059,
           z + 0.035, t - 0.035, M['int_glass'] if clear else M['glass'])
    g = Geometry()
    for l, r in ((a, a + 0.046), (b - 0.046, b)):
        f.solid(g, l, r, -0.085, -0.012, z, t)
    for low, high in ((z, z + 0.048), (t - 0.048, t)):
        f.solid(g, a, b, -0.085, -0.012, low, high)
    if slider:
        for i in (1, 2):
            u = a + (b - a) * i / 3
            f.solid(g, u - 0.026, u + 0.026, -0.071, -0.004, z, t)
    elif op['w'] > 2.0:
        # Great-room triple grouping.
        for i in (1, 2):
            u = a + (b - a) * i / 3
            f.solid(g, u - 0.04, u + 0.04, -0.07, 0.006, z, t)
        f.solid(g, a, b, -0.07, -0.005, z + op['h'] * 0.48, z + op['h'] * 0.48 + 0.04)
    elif op['h'] > 1.1:
        meeting = z + op['h'] * 0.48
        f.solid(g, a, b, -0.078, 0.0, meeting - 0.027, meeting + 0.027)
        # FH-1: divided upper sash over a comparatively plain lower sash.
        f.solid(g, c - 0.012, c + 0.012, -0.062, -0.014, meeting + 0.027, t - 0.035)
        mid = (meeting + t) / 2
        f.solid(g, a + 0.035, b - 0.035, -0.062, -0.014, mid - 0.012, mid + 0.012)
    g.finish(f.name + ' | ' + op['name'] + ' sash and muntins', M['trim'] if slider else M['wood'], 0.001)
    if op['shutters']:
        for side in (-1, 1):
            shutter(f, op, side)


def shutter(f, op, side):
    width = 0.42
    c = op['u'] + side * (op['w'] / 2 + 0.09 + width / 2)
    a, b, z, t = c - width / 2, c + width / 2, op['z'] - 0.015, op['z'] + op['h'] + 0.03
    g = Geometry()
    for i in range(3):
        l = a + i * width / 3
        f.solid(g, l + 0.003, l + width / 3 - 0.003, 0.035, 0.082, z, t)
    g.finish(f.name + ' | ' + op['name'] + ' shutter boards ' + str(side), M['blue'])
    g = Geometry()
    for h in (z + 0.14, t - 0.22):
        f.solid(g, a - 0.008, b + 0.008, 0.083, 0.113, h, h + 0.085)
    g.finish(f.name + ' | ' + op['name'] + ' shutter straps ' + str(side), M['blue_edge'])
    beam(f.name + ' | diagonal shutter brace ' + op['name'] + str(side),
         f.p(c - side * width * 0.36, 0.112, z + 0.235),
         f.p(c + side * width * 0.36, 0.112, t - 0.225), 0.07, 0.033, M['blue_edge'])


def raised_panel(f, name, a, b, low, high, mat, depth=0.0):
    # Painted panel and groove share the specified paint; geometry supplies shade.
    f.part(name + ' inset', a, b, depth, depth + 0.008, low, high, mat)
    inset = 0.028
    ring0 = [f.p(a + 0.011, depth + 0.01, low + 0.011), f.p(b - 0.011, depth + 0.01, low + 0.011),
             f.p(b - 0.011, depth + 0.01, high - 0.011), f.p(a + 0.011, depth + 0.01, high - 0.011)]
    ring1 = [f.p(a + inset, depth + 0.027, low + inset), f.p(b - inset, depth + 0.027, low + inset),
             f.p(b - inset, depth + 0.027, high - inset), f.p(a + inset, depth + 0.027, high - inset)]
    g = Geometry()
    g.face(list(reversed(ring0)))
    g.face(ring1)
    for i in range(4):
        j = (i + 1) % 4
        g.face([ring0[i], ring0[j], ring1[j], ring1[i]])
    g.finish(f.name + ' | ' + name, mat)


def garage_door(f, op):
    a, b = op['u'] - op['w'] / 2, op['u'] + op['w'] / 2
    z, t = op['z'], op['z'] + op['h']
    surround(f, op, width=0.13, sill=False)
    f.part('garage opening shadow', a, b, -0.135, -0.10, z, t, M['recess'])
    h = op['h'] / 4
    for row in range(4):
        low = z + row * h
        f.part('garage section %d' % (row + 1), a + 0.025, b - 0.025, -0.098, -0.042,
               low + 0.006, low + h - 0.006, M['garage'])
        for col in range(4):
            l = a + 0.11 + col * (op['w'] - 0.17) / 4
            r = a + 0.11 + (col + 1) * (op['w'] - 0.17) / 4 - 0.065
            raised_panel(f, 'garage panel %d-%d' % (row + 1, col + 1),
                         l, r, low + 0.075, low + h - 0.072, M['panel'], -0.041)


def interior_door_leaf(name, hinge, direction, width, height, mat):
    """Static leaf built before the house-wide mirror; no negative object scales."""
    hinge, along = Vector(hinge), Vector(direction).normalized()
    side = Vector((-along.y, along.x, 0))
    end = hinge + along * width
    g = Geometry()
    g.prism([hinge - side * 0.021, end - side * 0.021,
             end + side * 0.021, hinge + side * 0.021], (0, 0, height))
    # Simple recessed-looking field panels on both sides, with actual thickness.
    for sign in (-1, 1):
        for low, high in ((0.15, 0.72), (0.86, height - 0.16)):
            a = hinge + along * 0.10 + side * (sign * 0.022) + Vector((0, 0, low))
            b = hinge + along * (width - 0.10) + side * (sign * 0.022) + Vector((0, 0, low))
            g.prism([a, b, b + Vector((0, 0, high - low)),
                     a + Vector((0, 0, high - low))], side * (sign * 0.009))
        p = hinge + along * (width - 0.10) + side * (sign * 0.045) + Vector((0, 0, 1.0))
        beam(name + ' lever', p, p - along * 0.115, 0.022, 0.022, M['metal'])
    return g.finish(name + ' static door leaf', mat, 0.002)


def entry_door(f, op):
    a, b = op['u'] - op['w'] / 2, op['u'] + op['w'] / 2
    z, t = op['z'], op['z'] + op['h']
    surround(f, op, width=0.105, sill=False)
    if BUILD_FIRST_FLOOR and FIRST_FLOOR_OPEN_DOORS:
        jamb = Geometry()
        f.solid(jamb, a, a + 0.025, -0.205, -0.015, z, t)
        f.solid(jamb, b - 0.025, b, -0.205, -0.015, z, t)
        f.solid(jamb, a, b, -0.205, -0.015, t - 0.025, t)
        jamb.finish('Interior | front entrance open jamb', M['int_trim'])
        interior_door_leaf('Interior | SkyDiving entry opened inward',
                           f.p(b - 0.035, -0.08, z + 0.025), -f.n,
                           op['w'] - 0.07, op['h'] - 0.05, M['door'])
        f.part('door threshold', a - 0.02, b + 0.02, -0.22, 0.17,
               z - 0.015, INTERIOR_FLOOR_Z, M['concrete'])
        return
    f.part('front door shadow reveal', a, b, -0.13, -0.09, z, t, M['recess'])
    f.part('pale blue gray front door', a + 0.026, b - 0.026, -0.085, -0.028, z + 0.02, t - 0.025, M['door'])
    raised_panel(f, 'door tall upper panel', a + 0.14, b - 0.14, z + 0.80, t - 0.16, M['door'], -0.025)
    raised_panel(f, 'door lower panel', a + 0.14, b - 0.14, z + 0.18, z + 0.68, M['door'], -0.025)
    f.part('door threshold', a - 0.02, b + 0.02, -0.12, 0.17, z - 0.015, z + 0.017, M['concrete'])
    f.part('lock escutcheon', b - 0.14, b - 0.095, -0.022, 0.01, z + 1.0, z + 1.16, M['metal'], 0.008)
    f.part('door lever', b - 0.22, b - 0.105, 0.01, 0.045, z + 1.035, z + 1.06, M['metal'], 0.005)


# ---------------------- roofs / clipped shingle geometry ---------------------
def clip_polygon(subject, boundary):
    """Sutherland-Hodgman clipping in roof-local 2D; boundary must be CCW."""
    result = subject
    for i, a in enumerate(boundary):
        b = boundary[(i + 1) % len(boundary)]
        def distance(p):
            return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
        source, result = result, []
        if not source:
            break
        previous = source[-1]
        dp = distance(previous)
        for current in source:
            dc = distance(current)
            if (dc >= -1e-8) != (dp >= -1e-8):
                factor = dp / (dp - dc)
                result.append((previous[0] + factor * (current[0] - previous[0]),
                               previous[1] + factor * (current[1] - previous[1])))
            if dc >= -1e-8:
                result.append(current)
            previous, dp = current, dc
    return result


def roof_surface(name, points, across):
    points = [Vector(p) for p in points]
    u = Vector(across).normalized()
    normal = (points[1] - points[0]).cross(points[2] - points[0]).normalized()
    if normal.z < 0:
        normal.negate()
    v = normal.cross(u).normalized()
    if v.z < 0:
        u.negate()
        v.negate()
    origin = points[0]
    boundary = [((p - origin).dot(u), (p - origin).dot(v)) for p in points]
    signed = sum(boundary[i][0] * boundary[(i + 1) % len(boundary)][1] -
                 boundary[(i + 1) % len(boundary)][0] * boundary[i][1] for i in range(len(boundary)))
    if signed < 0:
        boundary.reverse()
    geo = Geometry()
    geo.prism(points, -normal * 0.075)
    geo.finish(name + ' | solid roof deck', M['roofbase'])
    if not MODEL_SHINGLES:
        return
    rng = random.Random(SEED + sum(ord(c) for c in name))
    geo = Geometry()
    min_u, max_u = min(p[0] for p in boundary), max(p[0] for p in boundary)
    min_v, max_v = min(p[1] for p in boundary), max(p[1] for p in boundary)
    row = 0
    while min_v + row * SHINGLE_EXPOSURE < max_v:
        y = min_v + row * SHINGLE_EXPOSURE
        x = min_u - SHINGLE_WIDTH + (row % 3) * SHINGLE_WIDTH / 3
        while x < max_u:
            polygon = clip_polygon([(x + 0.0018, y), (x + SHINGLE_WIDTH - 0.0018, y),
                                    (x + SHINGLE_WIDTH - 0.0018, y + SHINGLE_EXPOSURE + 0.042),
                                    (x + 0.0018, y + SHINGLE_EXPOSURE + 0.042)], boundary)
            if len(polygon) >= 3:
                area = abs(sum(polygon[i][0] * polygon[(i + 1) % len(polygon)][1] -
                               polygon[(i + 1) % len(polygon)][0] * polygon[i][1]
                               for i in range(len(polygon))))
                if area > 1e-7:
                    # Butt lifted above prior course; uphill end lies near deck.
                    ring = [origin + u * a + v * b + normal *
                            (0.008 + 0.010 * (1 - (b - y) / (SHINGLE_EXPOSURE + 0.042)))
                            for a, b in polygon]
                    geo.prism(ring, -normal * 0.006, rng.randrange(len(SHINGLES)))
            x += SHINGLE_WIDTH
        row += 1
    geo.finish(name + ' | staggered individual shingles', SHINGLES)


def horizontal_fascia(name, a, b, height=0.18, width=0.105):
    # Horizontal beam's local width maps vertically; depth maps horizontally.
    a, b = Vector(a), Vector(b)
    beam(name, a - Vector((0, 0, height / 2)), b - Vector((0, 0, height / 2)),
         height, width, M['trim'])
    beam(name + ' drip edge', a + Vector((0, 0, 0.009)), b + Vector((0, 0, 0.009)),
         0.036, width + 0.028, M['trim'])


def ridge_caps(name, a, b, width=0.20):
    a, b = Vector(a), Vector(b)
    delta = b - a
    count = max(1, math.ceil(delta.length / 0.23))
    along = delta.normalized()
    across = along.cross(Vector((0, 0, 1)))
    if across.length < 1e-6:
        return
    across.normalize()
    g = Geometry()
    for i in range(count):
        p = a + delta * i / count + Vector((0, 0, 0.030))
        q = a + delta * min((i + 1.14) / count, 1.0) + Vector((0, 0, 0.030))
        # Folded cap, deliberately not a terracotta/barrel tile.
        for side in (-1, 1):
            edge = across * width * side / 2 - Vector((0, 0, 0.043))
            g.prism([p, q, q + edge, p + edge], (0, 0, -0.009), i % len(SHINGLES))
    g.finish(name, SHINGLES)


# -------------------------- foundations and envelopes -------------------------
box('Main foundation', (0, FRONT, 0), (W, BACK, FF), M['concrete'])
box('Projecting garage foundation', (0, 0, 0), (GARAGE_W, FRONT, FF), M['concrete'])
box('Recessed entry porch slab', (GARAGE_W, PORCH_FRONT, 0.025), (W, FRONT, FF), M['concrete'])
entry_center_x = (FOYER_X + STAIR_X0) / 2 if BUILD_FIRST_FLOOR else GARAGE_W + 2.53
step_center_x = entry_center_x if BUILD_FIRST_FLOOR else 8.585
box('Entry threshold step', (step_center_x - 0.575, PORCH_FRONT - 0.30, 0.015),
    (step_center_x + 0.575, PORCH_FRONT, 0.105), M['concrete'])
box('Rear lanai slab', (0, BACK, 0.025), (LANAI_W, BACK + LANAI_D, FF), M['concrete'])
# Replace the sealed plate with an actual stairwell opening for the first floor.
if BUILD_FIRST_FLOOR:
    if BUILD_FIRST_FLOOR_CEILINGS:
        hole_x0, hole_x1 = STAIR_X0 - 0.04, STAIR_X1 + 0.02
        hole_y0, hole_y1 = STAIR_Y0, STAIR_Y1 + 0.10
        ceiling = Geometry()
        for x0, y0, x1, y1 in ((0, FRONT, hole_x0, BACK),
                               (hole_x1, FRONT, W, BACK),
                               (hole_x0, FRONT, hole_x1, hole_y0),
                               (hole_x0, hole_y1, hole_x1, BACK)):
            ceiling.box((x0, y0, INTERIOR_CEILING_Z), (x1, y1, UPPER_FLOOR))
        ceiling.finish('Interior | first floor ceiling and upper plate - stair opening', M['int_ceiling'])
        box('Interior | forward garage ceiling', (0.19, 0.19, GARAGE_EAVE - 0.015),
            (GARAGE_W - 0.19, FRONT, GARAGE_EAVE), M['int_ceiling'])
else:
    box('Upper story sealed underside', (0, FRONT, UPPER_FLOOR - 0.16),
        (W, BACK, UPPER_FLOOR), M['stucco'])

front_garage = Facade('Garage front', (0, 0), (1, 0), (0, -1), GARAGE_W)
wall(front_garage, FF, GARAGE_EAVE,
     [opening('two-car sectional door', GARAGE_W / 2, 4.8768, FF, 2.18, 'garage')], lap=True)
wall(Facade('Garage left', (0, 0), (0, 1), (-1, 0), FRONT), FF, GARAGE_EAVE)
wall(Facade('Garage right return', (GARAGE_W, 0), (0, 1), (1, 0), FRONT), FF, GARAGE_EAVE)
entry = Facade('Recessed entry', (GARAGE_W, FRONT), (1, 0), (0, -1), W - GARAGE_W)
wall(entry, FF, UPPER_FLOOR,
     [opening('leisure room window', 0.93, 0.92, FF + 0.58, 1.52),
      opening('front entrance', entry_center_x - GARAGE_W, 0.965, FF, 2.44, 'entry')], lap=True)
wall(Facade('Left main lower', (0, FRONT), (0, 1), (-1, 0), BACK - FRONT), FF, UPPER_FLOOR)
wall(Facade('Right main lower', (W, FRONT), (0, 1), (1, 0), BACK - FRONT), FF, UPPER_FLOOR)
rear_lower = Facade('Rear ground floor', (0, BACK), (1, 0), (0, 1), W)
wall(rear_lower, FF, UPPER_FLOOR,
     [opening('lanai sliding doors', 2.36, 2.74, FF + 0.025, 2.37, 'slider'),
      opening('great room triple window', 7.35, 2.91, FF + 0.68, 1.68)])

front_upper = Facade('Upper front FH-1', (0, FRONT), (1, 0), (0, -1), W)
wall(front_upper, UPPER_FLOOR, UPPER_EAVE,
     [opening('bedroom 2', 1.08, 0.94, 4.23, 1.68, shutters=True),
      opening('loft left', 6.65, 0.94, 4.23, 1.68, shutters=True),
      opening('loft right', 8.95, 0.94, 4.23, 1.68, shutters=True)], lap=True)
wall(Facade('Upper left', (0, FRONT), (0, 1), (-1, 0), BACK - FRONT), UPPER_FLOOR, UPPER_EAVE,
     [opening('bedroom 3 side', 5.74, 0.94, 4.23, 1.68)], lap=True)
wall(Facade('Upper right', (W, FRONT), (0, 1), (1, 0), BACK - FRONT), UPPER_FLOOR, UPPER_EAVE,
     [opening('stairwell side', 3.29, 0.87, 4.23, 1.68)], lap=True)
wall(Facade('Upper rear', (0, BACK), (1, 0), (0, 1), W), UPPER_FLOOR, UPPER_EAVE,
     [opening('bath rear', 4.80, 0.91, 5.07, 0.69),
      opening('master rear left', 6.48, 0.94, 4.23, 1.68),
      opening('master rear right', 9.08, 0.94, 4.23, 1.68)], lap=True)

# Ivory vertical corner boards, as opposed to C-1's different front treatment.
for x in (0, W):
    for y in (FRONT, BACK):
        box('Upper ivory corner trim', (x - 0.045, y - 0.045, UPPER_FLOOR),
            (x + 0.085, y + 0.085, UPPER_EAVE), M['trim'])
for x in (0, GARAGE_W):
    box('Garage front corner board', (x - 0.04, -0.062, FF),
        (x + 0.105, 0.075, GARAGE_EAVE), M['trim'])
entry.part('right entry corner casing', entry.length - 0.11, entry.length + 0.035,
           0.008, 0.075, FF, GARAGE_EAVE, M['trim'])

# Paired narrow square porch columns at right corner, with block capitals.
for i, x in enumerate((W - 0.48, W - 0.10)):
    box('Porch square column %d' % (i + 1), (x - 0.09, PORCH_FRONT - 0.055, FF),
        (x + 0.09, PORCH_FRONT + 0.125, 2.97), M['trim'], 0.004)
    box('Porch column capital %d' % (i + 1), (x - 0.13, PORCH_FRONT - 0.095, 2.84),
        (x + 0.13, PORCH_FRONT + 0.165, 3.025), M['trim'])
    box('Porch column plinth %d' % (i + 1), (x - 0.105, PORCH_FRONT - 0.07, FF),
        (x + 0.105, PORCH_FRONT + 0.14, FF + 0.12), M['trim'])
box('Porch front lintel', (GARAGE_W, PORCH_FRONT - 0.075, 2.91),
    (W + 0.04, PORCH_FRONT + 0.15, 3.08), M['trim'])
box('Porch right lintel', (W - 0.18, PORCH_FRONT, 2.91), (W + 0.035, FRONT, 3.08), M['trim'])
box('Porch flat soffit', (GARAGE_W, PORCH_FRONT - 0.07, 3.025),
    (W + 0.035, FRONT, 3.055), M['trim'])


# ----------------------- garage gable and merged porch roof -------------------
gxl, gxr = -OVERHANG, GARAGE_W + OVERHANG
gcx = GARAGE_W / 2
gfront = -OVERHANG
gback = FRONT + 0.025
peak = LOW_EAVE + (gxr - gcx) * GARAGE_PITCH
porch_eave_y = PORCH_FRONT - 0.22
porch_back_z = LOW_EAVE + (gback - porch_eave_y) * PORCH_PITCH
join_x = gxr - (porch_back_z - LOW_EAVE) / GARAGE_PITCH

# Gable face follows roof underside and has real vertical battens.
gable_edge_z = LOW_EAVE + OVERHANG * GARAGE_PITCH - 0.09
gable_peak_z = peak - 0.09
g = Geometry()
g.prism([(0, 0, GARAGE_EAVE), (GARAGE_W, 0, GARAGE_EAVE),
         (GARAGE_W, 0, gable_edge_z), (gcx, 0, gable_peak_z), (0, 0, gable_edge_z)], (0, 0.16, 0))
g.finish('FH-1 tan board-and-batten front gable', M['gable'])
g = Geometry()
x = 0.16
while x < GARAGE_W:
    top = gable_peak_z - abs(x - gcx) * GARAGE_PITCH - 0.025
    g.box((x - 0.024, -0.045, GARAGE_EAVE + 0.035), (x + 0.024, -0.006, top))
    x += 0.43
g.finish('Gable vertical battens', M['gable'])
box('Broad horizontal ivory gable frieze', (-0.11, -0.10, GARAGE_EAVE - 0.07),
    (GARAGE_W + 0.11, 0.075, GARAGE_EAVE + 0.145), M['trim'])

roof_surface('Garage left gable roof', [(gxl, gfront, LOW_EAVE), (gcx, gfront, peak),
             (gcx, gback, peak), (gxl, gback, LOW_EAVE)], (0, 1, 0))
# Clipped right slope and porch plane share a valley: no crossing roof sheets.
roof_surface('Garage right gable roof', [(gcx, gfront, peak), (gxr, gfront, LOW_EAVE),
             (gxr, porch_eave_y, LOW_EAVE), (join_x, gback, porch_back_z),
             (gcx, gback, peak)], (0, 1, 0))
roof_surface('Recessed entry shed roof', [(gxr, porch_eave_y, LOW_EAVE),
             (W + OVERHANG, porch_eave_y, LOW_EAVE),
             (W + OVERHANG, gback, porch_back_z), (join_x, gback, porch_back_z)], (1, 0, 0))
ridge_caps('Garage shingle ridge caps', (gcx, gfront, peak), (gcx, gback, peak))
for suffix, a, b in (
        ('left', (gxl, gfront - 0.022, LOW_EAVE), (gcx, gfront - 0.022, peak)),
        ('right', (gcx, gfront - 0.022, peak), (gxr, gfront - 0.022, LOW_EAVE))):
    beam('Garage ivory rake ' + suffix, a, b, 0.16, 0.115, M['trim'])
    beam('Garage rake fine drip ' + suffix,
         Vector(a) + Vector((0, -0.02, 0.07)), Vector(b) + Vector((0, -0.02, 0.07)),
         0.045, 0.14, M['trim'])
horizontal_fascia('Garage left eave', (gxl, gfront, LOW_EAVE), (gxl, gback, LOW_EAVE))
horizontal_fascia('Garage right eave', (gxr, gfront, LOW_EAVE), (gxr, porch_eave_y, LOW_EAVE))
horizontal_fascia('Entry front eave', (gxr, porch_eave_y, LOW_EAVE), (W + OVERHANG, porch_eave_y, LOW_EAVE))
beam('Entry right rake', (W + OVERHANG, porch_eave_y, LOW_EAVE - 0.045),
     (W + OVERHANG, gback, porch_back_z - 0.045), 0.13, 0.11, M['trim'])
# Garage soffit returns below the overhang.
box('Garage left soffit', (gxl, 0, GARAGE_EAVE), (0.02, FRONT, GARAGE_EAVE + 0.07), M['trim'])
box('Garage right soffit', (GARAGE_W - 0.01, 0, GARAGE_EAVE),
    (gxr, porch_eave_y, GARAGE_EAVE + 0.07), M['trim'])
# Three Witchcraft decorative brackets; placement inferred from the color photo.
for i, x in enumerate((1.12, gcx, GARAGE_W - 1.12)):
    ztop = gable_peak_z - abs(x - gcx) * GARAGE_PITCH - 0.035
    box('Gable Witchcraft bracket %d' % (i + 1), (x - 0.055, -0.22, ztop - 0.36),
        (x + 0.055, -0.10, ztop), M['brackets'], 0.006)
    beam('Gable bracket knee %d' % (i + 1), (x, -0.075, ztop - 0.34),
         (x, -0.285, ztop - 0.07), 0.075, 0.075, M['brackets'])


# ------------------------------ upper hipped roof ----------------------------
xl, xr = -OVERHANG, W + OVERHANG
yf, yb = FRONT - OVERHANG, BACK + OVERHANG
cx = W / 2
run = (xr - xl) / 2
rfront = (cx, yf + run, ROOF_EAVE + run * MAIN_PITCH)
rback = (cx, yb - run, ROOF_EAVE + run * MAIN_PITCH)
a, b = (xl, yf, ROOF_EAVE), (xr, yf, ROOF_EAVE)
c, d = (xr, yb, ROOF_EAVE), (xl, yb, ROOF_EAVE)
roof_surface('Main front hip', [a, b, rfront], (1, 0, 0))
roof_surface('Main right hip', [b, c, rback, rfront], (0, 1, 0))
roof_surface('Main rear hip', [c, d, rback], (1, 0, 0))
roof_surface('Main left hip', [d, a, rfront, rback], (0, 1, 0))
for name, p, q in (('front left', a, rfront), ('front right', b, rfront),
                   ('rear right', c, rback), ('rear left', d, rback), ('ridge', rfront, rback)):
    ridge_caps('Main roof cap ' + name, p, q)
for name, p, q in (('front', a, b), ('right', b, c), ('back', c, d), ('left', d, a)):
    horizontal_fascia('Main ivory fascia ' + name, p, q, 0.20, 0.12)
box('Upper front soffit', (xl, yf, UPPER_EAVE), (xr, FRONT + 0.02, ROOF_EAVE - 0.10), M['trim'])
box('Upper rear soffit', (xl, BACK - 0.02, UPPER_EAVE), (xr, yb, ROOF_EAVE - 0.10), M['trim'])
box('Upper left soffit', (xl, FRONT, UPPER_EAVE), (0.02, BACK, ROOF_EAVE - 0.10), M['trim'])
box('Upper right soffit', (W - 0.02, FRONT, UPPER_EAVE), (xr, BACK, ROOF_EAVE - 0.10), M['trim'])


# -------------------------- inferred covered rear lanai -----------------------
# The base-plan lanai is open, without the optional screened extension.
lanai_end = BACK + LANAI_D
for i, x in enumerate((0.16, LANAI_W - 0.16)):
    box('Lanai stucco column %d' % (i + 1), (x - 0.15, lanai_end - 0.30, FF),
        (x + 0.15, lanai_end, 3.025), M['stucco'])
box('Lanai rear header', (0, lanai_end - 0.32, 2.86), (LANAI_W, lanai_end, 3.08), M['stucco'])
box('Lanai flat soffit', (0, BACK, 3.025), (LANAI_W, lanai_end, 3.065), M['trim'])
ly = lanai_end + 0.25
lz = 3.19
attach = lz + (ly - BACK) * 0.28
roof_surface('Lanai inferred shed roof', [(-0.26, ly, lz), (LANAI_W + 0.26, ly, lz),
             (LANAI_W + 0.26, BACK - 0.025, attach + 0.007),
             (-0.26, BACK - 0.025, attach + 0.007)], (1, 0, 0))
horizontal_fascia('Lanai rear ivory fascia', (-0.26, ly, lz), (LANAI_W + 0.26, ly, lz))
for x in (-0.26, LANAI_W + 0.26):
    beam('Lanai side rake', (x, ly, lz - 0.04), (x, BACK, attach - 0.04), 0.13, 0.10, M['trim'])
    # Close the side wedge over the flat ceiling; leave the outdoor area open.
    g = Geometry()
    g.prism([(x, BACK, 3.055), (x, ly - 0.25, 3.055),
             (x, ly - 0.25, lz + 0.07), (x, BACK, attach - 0.07)], (0.04, 0, 0))
    g.finish('Lanai inferred roof side closure', M['stucco'])

# Closure above porch-side header beneath the shed rake.
g = Geometry()
g.prism([(W, PORCH_FRONT, 3.045), (W, FRONT, 3.045),
         (W, FRONT, LOW_EAVE + (FRONT - porch_eave_y) * PORCH_PITCH - 0.08),
         (W, PORCH_FRONT, LOW_EAVE + (PORCH_FRONT - porch_eave_y) * PORCH_PITCH - 0.08)], (-0.10, 0, 0))
g.finish('Entry right roof-side closure', M['stucco'])

# ----------------------- first-floor interior increment ----------------------
# All builders below work in the brochure frame. Geometry.finish() handles the
# right-hand-garage mirror for walls, fixtures, stairs and hardware alike.
# Room names are object metadata, not floating text or extra scene collections.

def interior_partition(name, a, b, doors=(), thickness=INTERIOR_WALL_T):
    """doors = (distance from a, opening width, opening height), in meters."""
    delta = Vector((b[0] - a[0], b[1] - a[1], 0))
    length = delta.length
    tangent = delta.normalized()
    facade = Facade('Interior | ' + name, a, tangent,
                    (-tangent.y, tangent.x), length)
    openings = [opening('passage %d' % i, start + width / 2, width,
                        INTERIOR_FLOOR_Z, height)
                for i, (start, width, height) in enumerate(doors)]
    for start, width, height in doors:
        assert 0 <= start < start + width <= length + 1e-6
        assert 0 < height < INTERIOR_CEILING_Z - INTERIOR_FLOOR_Z
    levels = sorted(set([INTERIOR_FLOOR_Z, INTERIOR_CEILING_Z] +
                        [op['z'] + op['h'] for op in openings]))
    g, base = Geometry(), Geometry()
    for low, high in zip(levels[:-1], levels[1:]):
        for l, r in intervals_without_openings(length, openings, low, high):
            facade.solid(g, l, r, -thickness / 2, thickness / 2, low, high)
    g.finish('Interior | ' + name + ' partition with open doorways', M['int_wall'])
    for l, r in intervals_without_openings(length, openings,
                                           INTERIOR_FLOOR_Z, INTERIOR_FLOOR_Z + 0.10):
        for sign in (-1, 1):
            depths = sorted((sign * thickness / 2, sign * (thickness / 2 + 0.012)))
            facade.solid(base, l, r, *depths, INTERIOR_FLOOR_Z, INTERIOR_FLOOR_Z + 0.10)
    base.finish('Interior | ' + name + ' baseboards', M['int_trim'])
    trim = Geometry()
    for op in openings:
        l, r = op['u'] - op['w'] / 2, op['u'] + op['w'] / 2
        top = op['z'] + op['h']
        # Narrow jambs and casing only; no panel spans the doorway.
        facade.solid(trim, l, l + 0.018, -thickness / 2, thickness / 2,
                     INTERIOR_FLOOR_Z, top)
        facade.solid(trim, r - 0.018, r, -thickness / 2, thickness / 2,
                     INTERIOR_FLOOR_Z, top)
        facade.solid(trim, l, r, -thickness / 2, thickness / 2, top - 0.018, top)
        for sign in (-1, 1):
            d0, d1 = sorted((sign * thickness / 2, sign * (thickness / 2 + 0.015)))
            facade.solid(trim, l - 0.06, l, d0, d1, INTERIOR_FLOOR_Z, top + 0.06)
            facade.solid(trim, r, r + 0.06, d0, d1, INTERIOR_FLOOR_Z, top + 0.06)
            facade.solid(trim, l, r, d0, d1, top, top + 0.06)
    trim.finish('Interior | ' + name + ' door jambs and casing', M['int_trim'])


def interior_floor(name, rect, wood=False, holes=()):
    x0, y0, x1, y1 = rect
    g = Geometry()
    # Separate rectangular floor regions around the garage extension and leisure.
    def subtract(r, h):
        a, b, c, d = r
        l, f, rr, back = max(a, h[0]), max(b, h[1]), min(c, h[2]), min(d, h[3])
        if l >= rr or f >= back:
            return [r]
        return [p for p in ((a, b, l, d), (rr, b, c, d), (l, b, rr, f), (l, back, rr, d))
                if p[2] - p[0] > 1e-6 and p[3] - p[1] > 1e-6]
    regions = [rect]
    for hole in holes:
        regions = [piece for r in regions for piece in subtract(r, hole)]
    for a, b, c, d in regions:
        g.box((a, b, FF), (c, d, INTERIOR_FLOOR_Z - 0.006))
    g.finish('Interior | ' + name + ' floor joint bed', M['int_grout'])
    g = Geometry()
    dx, dy = (0.18, 1.20) if wood else (0.60, 0.60)
    column = 0
    x = x0
    while x < x1 - 1e-6:
        y = y0 - (0.4 * (column % 3) if wood else 0.0)
        while y < y1 - 1e-6:
            tile = (x, max(y, y0), min(x + dx, x1), min(y + dy, y1))
            parts = [tile]
            for hole in holes:
                parts = [piece for r in parts for piece in subtract(r, hole)]
            for a, b, c, d in parts:
                if c - a > 0.004 and d - b > 0.004:
                    g.box((a + 0.001, b + 0.001, INTERIOR_FLOOR_Z - 0.006),
                          (c - 0.001, d - 0.001, INTERIOR_FLOOR_Z))
            y += dy
        x += dx
        column += 1
    obj = g.finish('Interior | ' + name + (' floor planks' if wood else ' floor tiles'),
                   M['int_wood'] if wood else M['int_tile'])
    if obj:
        obj['room'] = name
        obj['walkable'] = True
        obj['finish_note'] = 'Inferred finish; brochure gives layout, not material selections'


def interior_tube(name, a, b, radius, mat, sides=16):
    a, b = Vector(a), Vector(b)
    direction = b - a
    axis = direction.normalized()
    reference = Vector((1, 0, 0)) if abs(axis.z) > 0.9 else Vector((0, 0, 1))
    u = axis.cross(reference).normalized()
    v = axis.cross(u).normalized()
    ring = [a + radius * (u * math.cos(i * math.tau / sides) +
                          v * math.sin(i * math.tau / sides)) for i in range(sides)]
    g = Geometry()
    g.prism(ring, direction)
    return g.finish('Interior | ' + name, mat)


def interior_oval(name, center, profile, mat, sides=32):
    """Closed oval solid, profile = (x radius, y radius, relative height)."""
    x, y, z = center
    rings = [[(x + rx * math.cos(i * math.tau / sides),
               y + ry * math.sin(i * math.tau / sides), z + h)
              for i in range(sides)] for rx, ry, h in profile]
    g = Geometry()
    g.face(list(reversed(rings[0])))
    for lower, upper in zip(rings[:-1], rings[1:]):
        for i in range(sides):
            j = (i + 1) % sides
            g.face([lower[i], lower[j], upper[j], upper[i]])
    g.face(rings[-1])
    return g.finish('Interior | ' + name, mat)


def interior_basin(name, rect, top, depth, mat):
    """Open rectangular basin with a recessed bottom, not a solid countertop."""
    a, b, c, d = rect
    inset = min(0.06, (c - a) / 5, (d - b) / 5)
    g = Geometry()
    g.box((a + inset, b + inset, top - depth - 0.012),
          (c - inset, d - inset, top - depth))
    # Four sloping solid sides join the open top to the bottom.
    outer = [(a, b, top), (c, b, top), (c, d, top), (a, d, top)]
    inner = [(a + inset, b + inset, top - depth),
             (c - inset, b + inset, top - depth),
             (c - inset, d - inset, top - depth),
             (a + inset, d - inset, top - depth)]
    for i in range(4):
        j = (i + 1) % 4
        g.prism([outer[i], inner[i], inner[j], outer[j]], (0, 0, -0.012))
    g.finish('Interior | ' + name + ' recessed basin', mat)
    interior_tube(name + ' drain', ((a + c) / 2, (b + d) / 2, top - depth),
                  ((a + c) / 2, (b + d) / 2, top - depth + 0.003), 0.025, M['int_steel'])


def build_first_floor():
    z, ceiling = INTERIOR_FLOOR_Z, INTERIOR_CEILING_Z
    inset, half = 0.205, INTERIOR_WALL_T / 2
    # The brochure explicitly labels the deep rear-left bay as GARAGE, not a den.
    # Preserve its connection to the projecting two-car garage; do not insert
    # a wall across the complete FRONT line.
    interior_partition('garage to leisure', (GARAGE_EXTENSION_X, FRONT),
                       (GARAGE_EXTENSION_X, SERVICE_REAR_Y), thickness=0.19)
    interior_partition('garage to recessed leisure front', (GARAGE_EXTENSION_X, FRONT),
                       (GARAGE_W, FRONT), thickness=0.19)
    interior_partition('garage rear mud entry', (inset, GARAGE_REAR_Y),
                       (GARAGE_EXTENSION_X, GARAGE_REAR_Y), [(0.60, 0.86, 2.13)], thickness=0.19)
    interior_partition('service rooms to kitchen', (inset, SERVICE_REAR_Y),
                       (GARAGE_EXTENSION_X, SERVICE_REAR_Y), [(0.64, 0.92, 2.13)])
    interior_partition('pantry side', (1.95, GARAGE_REAR_Y),
                       (1.95, SERVICE_REAR_Y), [(0.27, 0.83, 2.13)])
    interior_partition('leisure rear and open foyer passage', (GARAGE_EXTENSION_X, GARAGE_REAR_Y),
                       (STAIR_X0, GARAGE_REAR_Y),
                       [(6.25 - GARAGE_EXTENSION_X, STAIR_X0 - 6.25, 2.44)])
    interior_partition('powder to foyer', (STAIR_X0, FRONT + inset),
                       (STAIR_X0, POWDER_REAR_Y), [(0.66, 0.76, 2.13)])
    interior_partition('powder rear below stair landing', (STAIR_X0, POWDER_REAR_Y),
                       (W - inset, POWDER_REAR_Y))
    interior_partition('enclosed front stair side', (STAIR_X0, POWDER_REAR_Y),
                       (STAIR_X0, GARAGE_REAR_Y))

    # Tile across the open kitchen/cafe/great-room/foyer and service spaces.
    # Leisure flooring changes at the foyer line without an invented dividing wall.
    leisure = (GARAGE_EXTENSION_X + 0.095, FRONT + 0.095, FOYER_X, GARAGE_REAR_Y)
    garage = (inset, FRONT, GARAGE_EXTENSION_X + 0.095, GARAGE_REAR_Y + 0.095)
    interior_floor('kitchen cafe great room foyer and service rooms',
                   (inset, FRONT, W - inset, BACK - inset), holes=(leisure, garage))
    interior_floor('leisure', leisure, wood=True)
    box('Interior | garage rear extension floor finish',
        (inset, FRONT, FF), (GARAGE_EXTENSION_X - 0.095, GARAGE_REAR_Y - 0.095, FF + 0.004),
        M['concrete'])
    box('Interior | garage access threshold', (0.805, GARAGE_REAR_Y - 0.10, FF),
        (1.665, GARAGE_REAR_Y + 0.11, z), M['int_counter'])

    # Door leaves are separate solids; toggling the switch closes these leaves
    # without ever filling their wall openings with hidden shadow/backing panels.
    open_doors = FIRST_FLOOR_OPEN_DOORS
    interior_door_leaf('Interior | garage service door',
                       (0.83, GARAGE_REAR_Y + 0.10, z + 0.01),
                       (0, 1, 0) if open_doors else (1, 0, 0), 0.81, 2.09, M['int_trim'])
    interior_door_leaf('Interior | pantry door',
                       (1.95 + half + 0.025, GARAGE_REAR_Y + 1.075, z + 0.01),
                       (1, 0, 0) if open_doors else (0, -1, 0), 0.78, 2.09, M['int_trim'])
    interior_door_leaf('Interior | powder bath door',
                       (STAIR_X0 + half + 0.025, FRONT + inset + 0.685, z + 0.01),
                       (1, 0, 0) if open_doors else (0, 1, 0), 0.71, 2.09, M['int_trim'])

    # Straight flight occupies the stair strip shown beside foyer/cafe. The exact
    # rise/run and ascent direction are inferred; no code-compliance claim.
    # Ascent is toward the FRONT, exiting onto the future loft above the powder.
    risers = 18
    landing_z = UPPER_FLOOR + 0.018
    rise = (landing_z - z) / risers
    going = (STAIR_Y1 - STAIR_Y0) / (risers - 1)
    stairs, treads = Geometry(), Geometry()
    for i in range(risers - 1):
        rear = STAIR_Y1 - i * going
        front = rear - going
        top = z + (i + 1) * rise
        stairs.box((STAIR_X0 + 0.035, front, z), (STAIR_X1, rear, top - 0.025))
        treads.box((STAIR_X0 + 0.025, front, top - 0.025),
                   (STAIR_X1, rear + 0.015, top))
    stairs.finish('Interior | stair flight solid risers', M['int_trim'])
    stair_obj = treads.finish('Interior | stair treads to future upper floor', M['int_wood'])
    stair_obj['walkable'] = True
    stair_obj['riser_count'] = risers
    stair_obj['riser_m'] = rise
    stair_obj['going_m'] = going
    stair_obj['inferred_direction'] = 'Ascends toward -Y before house mirroring'
    landing = box('Interior | stair upper landing floor',
                  (STAIR_X0, STAIR_Y0 - 0.90, UPPER_FLOOR + 0.001),
                  (STAIR_X1, STAIR_Y0, landing_z), M['int_wood'])
    landing['walkable'] = True
    # Flight handrail, balusters and landing guard use real opaque geometry.
    rail_x = STAIR_X0 + 0.055
    rail_start = (rail_x, STAIR_Y1 - going / 2, z + rise + 0.92)
    rail_end = (rail_x, STAIR_Y0 + going / 2, landing_z - rise + 0.92)
    beam('Interior | stair sloping handrail', rail_start, rail_end, 0.055, 0.055, M['int_wood'])
    for i in range(risers - 1):
        y = STAIR_Y1 - (i + 0.5) * going
        bottom = z + (i + 1) * rise
        interior_tube('stair baluster %02d' % i, (rail_x, y, bottom),
                      (rail_x, y, bottom + 0.92), 0.012, M['metal'], 8)
    for y in (STAIR_Y0 - 0.86, STAIR_Y0):
        box('Interior | landing guard post', (rail_x - 0.025, y - 0.025, landing_z),
            (rail_x + 0.025, y + 0.025, landing_z + 0.95), M['int_trim'])
    beam('Interior | upper landing guard rail', (rail_x, STAIR_Y0 - 0.86, landing_z + 0.95),
         (rail_x, STAIR_Y0, landing_z + 0.95), 0.055, 0.055, M['int_wood'])

    if BUILD_FIRST_FLOOR_FIXTURES:
        build_first_floor_fixtures()
    COL['first_floor_interior'] = True
    COL['first_floor_reference'] = 'honor_page-0002.jpg, base C-1 first-floor plan; mirrored with exterior'
    COL['first_floor_rooms'] = 'Leisure; foyer; powder bath; cafe; great room; kitchen; pantry/service vestibule; garage and rear garage extension'
    COL['first_floor_ceiling_height_m'] = ceiling - z
    COL['first_floor_limitations'] = 'Partitions fitted to existing shell; finishes, service-room labels, fixtures and stair details inferred. Upper-floor interior deferred.'


def build_first_floor_fixtures():
    z, half = INTERIOR_FLOOR_Z, INTERIOR_WALL_T / 2
    counter_z = z + 0.90
    # Kitchen wall run: refrigerator near the pantry, range, base/upper cabinets.
    # A narrow rear-wall gap keeps the existing lanai slider clear.
    for index, (y0, y1) in enumerate(((13.12, 13.92), (14.70, 15.55), (15.55, 16.48))):
        box('Interior | kitchen wall cabinet %d carcass' % index,
            (0.23, y0, z + 0.10), (0.81, y1, counter_z - 0.04), M['int_trim'])
        box('Interior | kitchen wall cabinet %d toe kick' % index,
            (0.24, y0, z), (0.73, y1, z + 0.10), M['int_dark'])
        box('Interior | kitchen wall counter %d' % index,
            (0.22, y0, counter_z - 0.04), (0.86, y1, counter_z), M['int_counter'], 0.003)
        for k in range(2):
            a, b = y0 + (y1 - y0) * k / 2, y0 + (y1 - y0) * (k + 1) / 2
            box('Interior | kitchen lower shaker door', (0.811, a + 0.012, z + 0.12),
                (0.834, b - 0.012, counter_z - 0.075), M['int_trim'], 0.002)
            beam('Interior | kitchen lower cabinet pull', (0.86, b - 0.06, z + 0.56),
                 (0.86, b - 0.06, z + 0.70), 0.015, 0.015, M['metal'])
        box('Interior | kitchen upper cabinet %d' % index, (0.23, y0, z + 1.48),
            (0.57, y1, z + 2.32), M['int_trim'], 0.003)
        beam('Interior | kitchen upper cabinet pull', (0.60, (y0 + y1) / 2, z + 1.56),
             (0.60, (y0 + y1) / 2, z + 1.71), 0.014, 0.014, M['metal'])
        box('Interior | kitchen backsplash %d' % index,
            (0.207, y0, counter_z), (0.225, y1, z + 1.48), M['int_tile'])
    box('Interior | kitchen refrigerator body - assumed appliance', (0.23, 12.19, z),
        (0.96, 13.06, z + 1.95), M['int_steel'], 0.008)
    for a, b in ((12.20, 12.615), (12.63, 13.05)):
        box('Interior | refrigerator front door', (0.963, a, z + 0.05),
            (0.992, b, z + 1.93), M['int_steel'], 0.004)
        beam('Interior | refrigerator handle', (1.025, (a + b) / 2, z + 0.90),
             (1.025, (a + b) / 2, z + 1.40), 0.024, 0.024, M['metal'])
    box('Interior | kitchen range body', (0.24, 13.95, z + 0.06),
        (0.84, 14.67, counter_z - 0.025), M['int_steel'], 0.004)
    box('Interior | range oven glass', (0.844, 14.02, z + 0.20),
        (0.858, 14.60, z + 0.64), M['int_dark'], 0.006)
    beam('Interior | oven handle', (0.89, 14.05, z + 0.73),
         (0.89, 14.56, z + 0.73), 0.025, 0.025, M['int_steel'])
    box('Interior | range cooktop', (0.24, 13.95, counter_z - 0.025),
        (0.85, 14.67, counter_z), M['int_dark'])
    for x in (0.41, 0.68):
        for y in (14.12, 14.48):
            interior_tube('cooktop burner', (x, y, counter_z), (x, y, counter_z + 0.008),
                          0.095, M['int_steel'], 24)
    box('Interior | range hood canopy', (0.22, 13.91, z + 1.66),
        (0.84, 14.71, z + 1.78), M['int_steel'], 0.006)
    box('Interior | range hood flue', (0.23, 14.12, z + 1.78),
        (0.48, 14.50, z + 2.32), M['int_steel'])

    # Long island with working-side sink/dishwasher and an overhanging cafe side.
    # Sink cabinet is hollow at the top so geometry does not fill the bowls.
    box('Interior | island plinth', (2.08, 13.30, z), (3.30, 15.72, z + 0.10), M['int_dark'])
    island = Geometry()
    island.box((2.00, 13.25, z + 0.10), (3.35, 15.77, z + 0.15))
    island.box((3.30, 13.25, z + 0.15), (3.35, 15.77, counter_z - 0.04))
    for a, b in ((13.25, 13.30), (15.72, 15.77)):
        island.box((2.00, a, z + 0.15), (3.35, b, counter_z - 0.04))
    island.finish('Interior | island hollow cabinet carcass', M['int_trim'])
    for a, b in ((13.28, 13.99), (14.02, 14.83), (14.86, 15.73)):
        box('Interior | island working-side door', (1.98, a, z + 0.12),
            (2.01, b, counter_z - 0.05), M['int_trim'])
        beam('Interior | island cabinet pull', (1.95, (a + b) / 2 - 0.08, z + 0.71),
             (1.95, (a + b) / 2 + 0.08, z + 0.71), 0.015, 0.015, M['metal'])
    box('Interior | integrated dishwasher front', (1.958, 13.35, z + 0.12),
        (1.977, 13.96, counter_z - 0.065), M['int_steel'])
    beam('Interior | dishwasher pull', (1.92, 13.42, counter_z - 0.13),
         (1.92, 13.89, counter_z - 0.13), 0.022, 0.022, M['int_steel'])
    # Four counter strips form a genuine hole around the double sink.
    for i, (a, b, c, d) in enumerate(((1.95, 13.20, 2.14, 15.82),
                                      (2.82, 13.20, 3.58, 15.82),
                                      (2.14, 13.20, 2.82, 14.12),
                                      (2.14, 15.00, 2.82, 15.82))):
        box('Interior | island stone countertop segment %d' % i, (a, b, counter_z - 0.04),
            (c, d, counter_z), M['int_counter'], 0.002)
    for i, (a, b) in enumerate(((14.12, 14.55), (14.57, 15.00))):
        interior_basin('kitchen sink bowl %d' % i, (2.14, a, 2.82, b),
                       counter_z, 0.19, M['int_steel'])
    box('Interior | sink center divider', (2.14, 14.55, counter_z - 0.19),
        (2.82, 14.57, counter_z), M['int_steel'])
    for a, b in (((2.87, 14.56, counter_z), (2.87, 14.56, counter_z + 0.29)),
                 ((2.87, 14.56, counter_z + 0.29), (2.58, 14.56, counter_z + 0.29)),
                 ((2.58, 14.56, counter_z + 0.29), (2.58, 14.56, counter_z + 0.23))):
        interior_tube('kitchen sink faucet', a, b, 0.018, M['int_steel'])

    # Shelves in the unlabelled service enclosure are an inferred pantry fit-out.
    for height in (0.35, 0.75, 1.15, 1.55, 1.95):
        box('Interior | pantry shelving', (3.27, GARAGE_REAR_Y + 0.09, z + height),
            (GARAGE_EXTENSION_X - 0.10, SERVICE_REAR_Y - 0.09, z + height + 0.024), M['int_trim'])
    box('Interior | service vestibule bench', (0.23, 11.25, z + 0.39),
        (0.65, 11.94, z + 0.44), M['int_wood'])

    # Narrow powder room: vanity toward the entry, WC toward the stair landing.
    cx = (STAIR_X0 + 0.075 + W - 0.205) / 2
    va, vc = STAIR_X0 + half + 0.04, W - 0.23
    vb, vd = FRONT + 0.24, FRONT + 0.76
    vt = z + 0.85
    box('Interior | powder vanity plinth', (va + 0.045, vb, z), (vc - 0.045, vd - 0.04, z + 0.10), M['int_dark'])
    # Cabinet front and side walls leave the basin volume empty.
    for a, b, c, d in ((va, vb, va + 0.03, vd), (vc - 0.03, vb, vc, vd),
                        (va, vd - 0.03, vc, vd)):
        box('Interior | powder vanity cabinet', (a, b, z + 0.10), (c, d, vt - 0.04), M['int_trim'])
    sink = (cx - 0.22, vb + 0.10, cx + 0.22, vd - 0.075)
    for a, b, c, d in ((va, vb, sink[0], vd), (sink[2], vb, vc, vd),
                        (sink[0], vb, sink[2], sink[1]), (sink[0], sink[3], sink[2], vd)):
        box('Interior | powder vanity stone rim', (a, b, vt - 0.035), (c, d, vt), M['int_counter'])
    interior_basin('powder washbasin', sink, vt, 0.15, M['int_ceramic'])
    interior_tube('powder faucet upright', (cx, vb + 0.045, vt),
                  (cx, vb + 0.045, vt + 0.17), 0.018, M['int_steel'])
    interior_tube('powder faucet spout', (cx, vb + 0.045, vt + 0.17),
                  (cx, vb + 0.17, vt + 0.17), 0.018, M['int_steel'])
    # Metallic mirror approximation remains a lit surface, not an emissive panel.
    box('Interior | powder mirror frame', (va, FRONT + 0.212, z + 1.03),
        (vc, FRONT + 0.235, z + 1.95), M['int_trim'])
    box('Interior | powder mirror - metallic approximation', (va + 0.025, FRONT + 0.236, z + 1.055),
        (vc - 0.025, FRONT + 0.242, z + 1.925), M['int_steel'])
    toilet_y = POWDER_REAR_Y - 0.48
    interior_oval('powder toilet pedestal', (cx, toilet_y, z),
                  [(0.13, 0.21, 0), (0.14, 0.22, 0.16), (0.20, 0.28, 0.34)], M['int_ceramic'])
    # A stepped oval depression creates a visibly open bowl and raised seat rim.
    interior_oval('powder toilet bowl and seat', (cx, toilet_y - 0.025, z),
                  [(0.16, 0.24, 0.27), (0.205, 0.295, 0.39), (0.21, 0.30, 0.43),
                   (0.145, 0.225, 0.43), (0.10, 0.16, 0.31)], M['int_ceramic'])
    box('Interior | powder toilet tank', (cx - 0.20, POWDER_REAR_Y - 0.25, z + 0.32),
        (cx + 0.20, POWDER_REAR_Y - 0.085, z + 0.77), M['int_ceramic'], 0.025)
    box('Interior | powder toilet tank lid', (cx - 0.21, POWDER_REAR_Y - 0.26, z + 0.77),
        (cx + 0.21, POWDER_REAR_Y - 0.075, z + 0.80), M['int_ceramic'], 0.015)


if BUILD_FIRST_FLOOR:
    build_first_floor()

# Selection, cameras, lighting, world and units are unchanged.
# Standard/sRGB color management is configured above.
bpy.context.view_layer.update()
print('Honor FH-1 house created: %d mesh objects in %s.' % (len(COL.objects), COLLECTION_NAME))
print('Front is -Y. Unseen elevations and roof dimensions are approximations.')
if BUILD_FIRST_FLOOR:
    print('First-floor interior added; mirrored with the right-hand garage: %s.' % RIGHT_HAND_GARAGE)
    print('Includes rear garage bay, service/pantry rooms, leisure, foyer, powder, kitchen, cafe and great room.')
    print('Stair flight and ceiling opening included; upper-floor room layout is deferred.')
    print('All materials are lit. Interior finishes and stair details are inferred.')
    print('Reload honor.py in Blender and rerun; re-export the GLB to update the web scene.')
