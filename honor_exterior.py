# Written by GPT-6-astra on medium reasoning on Oct 1 2026

"""Honor / Grand Park — FH-1 exterior reconstruction.

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
  Exterior shell only: backed glazing and closed doors; no interior layout.

Coordinates: meters; X left/right, +Y toward rear, +Z up. Front faces -Y.
Designed for Blender 3.6+ using direct mesh creation, not context-sensitive ops.
No cameras, lights, ground plane, landscaping or world changes.
FLAT_COLORS defaults to True: unlit Solid material swatches, no reflections.
Sets scene-wide Standard/sRGB color management; no companion script required.
Matches swatches, not Solid studio-light shading. Set False for lit materials.
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


# Built-in Solid-swatch appearance. False restores the original lit materials.
FLAT_COLORS = True

if FLAT_COLORS:
    scene = bpy.context.scene
    scene.display_settings.display_device = 'sRGB'
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0
    scene.view_settings.use_curve_mapping = False
    if hasattr(scene.view_settings, 'use_white_balance'):
        scene.view_settings.use_white_balance = False


def flat_shader(mat):
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    shader = nodes.new('ShaderNodeEmission')
    shader.name = 'Honor | flat swatch'
    shader.inputs['Color'].default_value = tuple(mat.diffuse_color)
    shader.inputs['Strength'].default_value = 1.0
    links.new(shader.outputs[0], nodes.get('Material Output').inputs['Surface'])
    return shader


def linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def material(name, rgb, roughness=0.65, noise=0.0, metallic=0.0):
    mat = bpy.data.materials.new('Honor | ' + name)
    mat[TAG] = True
    mat.use_nodes = True
    rgba = tuple(linear(c) for c in rgb) + (1.0,)
    mat.diffuse_color = rgba
    if FLAT_COLORS:
        flat_shader(mat)
        return mat
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
    'Delicate White': {'rgb': (241, 242, 238), 'lrv': 88},
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
    f.part(op['name'] + ' shadow reveal', a, b, -0.11, -0.078, z, t, M['recess'])
    f.part(op['name'] + ' backed glazing', a + 0.04, b - 0.04, -0.075, -0.059,
           z + 0.035, t - 0.035, M['glass'])
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


def entry_door(f, op):
    a, b = op['u'] - op['w'] / 2, op['u'] + op['w'] / 2
    z, t = op['z'], op['z'] + op['h']
    surround(f, op, width=0.105, sill=False)
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
box('Entry threshold step', (8.01, PORCH_FRONT - 0.30, 0.015), (9.16, PORCH_FRONT, 0.105), M['concrete'])
box('Rear lanai slab', (0, BACK, 0.025), (LANAI_W, BACK + LANAI_D, FF), M['concrete'])
# Ceiling closure over the exterior porch; no interior floor plan.
box('Upper story sealed underside', (0, FRONT, UPPER_FLOOR - 0.16), (W, BACK, UPPER_FLOOR), M['stucco'])

front_garage = Facade('Garage front', (0, 0), (1, 0), (0, -1), GARAGE_W)
wall(front_garage, FF, GARAGE_EAVE,
     [opening('two-car sectional door', GARAGE_W / 2, 4.8768, FF, 2.18, 'garage')], lap=True)
wall(Facade('Garage left', (0, 0), (0, 1), (-1, 0), FRONT), FF, GARAGE_EAVE)
wall(Facade('Garage right return', (GARAGE_W, 0), (0, 1), (1, 0), FRONT), FF, GARAGE_EAVE)
entry = Facade('Recessed entry', (GARAGE_W, FRONT), (1, 0), (0, -1), W - GARAGE_W)
wall(entry, FF, UPPER_FLOOR,
     [opening('leisure room window', 0.93, 0.92, FF + 0.58, 1.52),
      opening('front entrance', 2.53, 0.965, FF, 2.44, 'entry')], lap=True)
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

# Selection, cameras, lighting, world and units are unchanged.
# Flat-color mode sets Standard/sRGB color management above.
bpy.context.view_layer.update()
print('Honor FH-1 exterior created: %d mesh objects in %s.' % (len(COL.objects), COLLECTION_NAME))
print('Front is -Y. Unseen elevations and roof dimensions are approximations.')
