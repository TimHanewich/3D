# Written by GPT-6-astra on medium reasoning on Oct 1 2026

"""Honor / Grand Park — FH-1 exterior and both interior floors.

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
  First-floor increment: den, foyer, powder bath, kitchen, cafe, great room,
  service vestibule/pantry, rear garage extension and straight stair flight.
  den.png revision encloses the former leisure room with a solid rear wall
  and foyer-side inward double doors near the cafe end. Existing floor/window
  locations are retained; DEN_DOORS_OPEN controls the static door positions.
  Interior traced from honor_page-0002.jpg and fitted to the existing shell;
  small partition offsets and the entry-door alignment are adjusted to fit.
  The brochure's rear 11'4\" x 13'1\" GARAGE bay remains part of the garage.
  Interior finishes, service-room labels, cabinets and stair details inferred.
  Both floors have clear glazing and statically open room doors by default.
  Upper floor: master bedroom, standard master bath and separate WC, walk-in
  and reach-in closets, bedrooms 2/3 with closets, bath 2, utility, HVAC and loft.
  Upper ceiling is 8'8\" above its finished floor. All partitions, doors, floors,
  trim and fixtures mirror together with the retained FH-1 exterior openings.
  Stair extents and the upper opening follow the main plan independently: low
  rear treads pass below the floor plate, preserving the straight master/loft
  wall and full-width reach-in closet. The powder room occupies the space below
  the high front treads, with clipped partitions and a sloping ceiling. Room
  sizes remain approximate; brochure dimensions are reference metadata only.
  Shared floor plate and finishes have one aligned, genuinely open stairwell.
  User stair revision: carpeted treads, risers, nosings and upper landing; solid
  drywall half-walls replace the flight and loft-edge balusters/wood rails.
  Carpet color and half-wall height are placeholders adjustable below. The
  lower side closure and powder clearance are retained; both arrivals stay open.
  User flooring revision: the former upstairs oak planks are used throughout
  downstairs indoor rooms; all upstairs room floors and stairs use matching
  carpet, including upstairs bath/utility/closet floors. Shower/tub surfaces,
  garage, porch and lanai remain unchanged. No new roof or footprint.
  Optional master bath and tray ceiling are omitted. Refrigerator and laundry
  appliances are optional and disabled; utility connections/HVAC are inferred.
  SECOND_FLOOR_CUTAWAY omits main roof/soffits and upper ceiling for inspection;
  restore False and rerun before a complete-house export. No loose furniture
  or lights are added. Interior finishes and equipment details are inferred.
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
BUILD_FIRST_FLOOR_CEILINGS = True  # Upper-floor support remains when floor 2 is on
BUILD_FIRST_FLOOR_FIXTURES = True  # Kitchen, pantry shelves and powder fixtures
FIRST_FLOOR_REFRIGERATOR = False  # Brochure marks the refrigerator optional
FIRST_FLOOR_OPEN_DOORS = True     # Static open leaves for walkthrough access
FIRST_FLOOR_CLEAR_GLASS = True    # Ground-floor glazing; upper switch is separate
INTERIOR_WALL_T = 0.115
INTERIOR_FLOOR_Z = FF + 0.018
INTERIOR_CEILING_Z = INTERIOR_FLOOR_Z + (9 + 4 / 12) * 0.3048
# Traced from honor_page-0002.jpg and fitted to the existing exterior footprint.
# These partitions/finishes are visual approximations, not construction drawings.
GARAGE_EXTENSION_X = 3.70
GARAGE_REAR_Y = 10.25
SERVICE_REAR_Y = 12.05
FOYER_X = 7.45
# den.png: enclose the former leisure room; double doors open into the den
# near the cafe end of the foyer. Width/height inferred to fit the existing shell.
DEN_DOOR_WIDTH = 1.50
DEN_DOOR_HEIGHT = 2.13
DEN_DOOR_REAR_MARGIN = 0.20
DEN_DOORS_OPEN = True            # Static 90-degree inward leaves; False closes both
DEN_DOOR_Y1 = GARAGE_REAR_Y - DEN_DOOR_REAR_MARGIN
DEN_DOOR_Y0 = DEN_DOOR_Y1 - DEN_DOOR_WIDTH
assert FRONT + 0.205 < DEN_DOOR_Y0 < DEN_DOOR_Y1 < GARAGE_REAR_Y
assert 0.10 < DEN_DOOR_WIDTH / 2 - 0.027
assert DEN_DOOR_HEIGHT < INTERIOR_CEILING_Z - INTERIOR_FLOOR_Z
STAIR_X0, STAIR_X1 = 8.82, W - 0.205
STAIR_Y0, STAIR_Y1 = 7.55, 12.07  # upper/front arrival to lower/rear foot, traced from plan
STAIR_RISERS = 18               # Inferred vertical fit; not a construction specification
STAIR_SOFFIT_THICKNESS = 0.12
# User revision: carpeted stairs and solid drywall instead of open balusters.
# Color and half-wall height are visual placeholders, not confirmed selections.
STAIR_CARPET_RGB = (0.69, 0.67, 0.63)
STAIR_DRYWALL_HEIGHT = 1.02
assert STAIR_DRYWALL_HEIGHT > 0
assert isinstance(STAIR_RISERS, int) and STAIR_RISERS > 1
assert STAIR_SOFFIT_THICKNESS > 0.025
POWDER_REAR_Y = 8.68             # Powder room extends beneath the high end of the flight
assert 0 < GARAGE_EXTENSION_X < GARAGE_W < FOYER_X < STAIR_X0 < STAIR_X1 < W
assert FRONT < GARAGE_REAR_Y < SERVICE_REAR_Y < BACK
assert INTERIOR_FLOOR_Z < INTERIOR_CEILING_Z < UPPER_FLOOR


# Second floor uses the same unmirrored brochure frame as the first floor.
BUILD_SECOND_FLOOR = True
BUILD_SECOND_FLOOR_CEILINGS = True
BUILD_SECOND_FLOOR_FIXTURES = True
SECOND_FLOOR_OPEN_DOORS = True
SECOND_FLOOR_CLEAR_GLASS = True
SECOND_FLOOR_LAUNDRY_APPLIANCES = False  # Brochure labels washer/dryer optional
SECOND_FLOOR_CUTAWAY = False     # True omits main roof/soffits and upper ceiling
SECOND_FLOOR_Z = UPPER_FLOOR + 0.018
SECOND_CEILING_Z = SECOND_FLOOR_Z + (8 + 8 / 12) * 0.3048
# The low rear steps are beneath the upper floor, not inside its opening.
# This keeps the master/loft boundary straight, as drawn in the main plan.
STAIR_HOLE = (STAIR_X0 - 0.04, STAIR_Y0, STAIR_X1 + 0.02, 11.39)
STAIR_LANDING = (STAIR_X0, STAIR_Y0 - 0.90, STAIR_X1, STAIR_Y0)
# Traced main upper plan, not the optional master-bath inset. These centerlines
# are fitted to the FH-1 shell; they are not exact brochure room dimensions.
UP_BED_X = 3.60
UP_SUITE_X = 5.64
UP_BATH2_X = 5.35
UP_BED2_REAR = 9.72
UP_CLOSET_SPLIT = 10.40
UP_BED3_CLOSET_REAR = 11.10
UP_HALL_REAR = 10.82
UP_UTILITY_REAR = 12.85
UP_HVAC_REAR = 13.95
UP_BED3_REAR = 14.60
UP_WC_REAR = 14.98
UP_WIC_X = 2.02
UP_REACHIN_X = 2.42
UP_MASTER_FRONT = 11.50
UP_MASTER_CLOSET_X = 6.85
UP_MASTER_CLOSET_END_X = W - 0.205
UP_MASTER_CLOSET_REAR = UP_MASTER_FRONT + 0.72
PLAN_REFERENCE_IMAGE = r'C:\Users\timh\Downloads\ilovepdf_pages-to-jpg\honor_page-0002.jpg'
assert SECOND_FLOOR_Z < SECOND_CEILING_Z < UPPER_EAVE
assert UP_BED_X < UP_BATH2_X < UP_SUITE_X < UP_MASTER_CLOSET_X < UP_MASTER_CLOSET_END_X
assert FRONT + 0.205 < STAIR_LANDING[1] < STAIR_HOLE[1] < STAIR_HOLE[3] < BACK - 0.205
assert STAIR_HOLE[3] + INTERIOR_WALL_T / 2 < UP_MASTER_FRONT
assert STAIR_Y0 < POWDER_REAR_Y < STAIR_HOLE[3] < STAIR_Y1
assert UP_MASTER_CLOSET_REAR < UP_BED3_REAR < UP_WC_REAR < BACK - 0.205


def stair_underside_z(y):
    """Continuous sloping underside, independent of the stepped walking surface."""
    rise = (SECOND_FLOOR_Z - INTERIOR_FLOOR_Z) / STAIR_RISERS
    going = (STAIR_Y1 - STAIR_Y0) / (STAIR_RISERS - 1)
    return max(INTERIOR_FLOOR_Z,
               INTERIOR_FLOOR_Z + (STAIR_Y1 - y) * rise / going - STAIR_SOFFIT_THICKNESS)


def under_stair_ceiling(y):
    return min(INTERIOR_CEILING_Z, stair_underside_z(y))


# Geometric sanity checks, not building-code or structural certification.
# Evaluate before clearing the previously generated collection.
_stair_rise = (SECOND_FLOOR_Z - INTERIOR_FLOOR_Z) / STAIR_RISERS
_stair_going = (STAIR_Y1 - STAIR_Y0) / (STAIR_RISERS - 1)
_stair_edge_step = math.floor((STAIR_Y1 - STAIR_HOLE[3]) / _stair_going) + 1
STAIR_REAR_CLEARANCE = (INTERIOR_CEILING_Z - INTERIOR_FLOOR_Z
                        - _stair_edge_step * _stair_rise)
assert STAIR_REAR_CLEARANCE > 2.0, 'Upper floor intrudes into stair headroom'
assert under_stair_ceiling(POWDER_REAR_Y + INTERIOR_WALL_T / 2) - INTERIOR_FLOOR_Z > 2.0


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
COL['floor_plan_reference_image'] = PLAN_REFERENCE_IMAGE
COL['floor_plan_variant'] = 'Main C-1 plan; prior FH-1 exterior, mirror and den customization retained'
# Published areas are source annotations, not measurements of this fitted mesh.
for area_name, sqft in (('first_floor', 1017), ('second_floor', 1126),
                         ('living', 2143), ('garage', 566), ('lanai', 131),
                         ('entry', 53), ('total', 2893)):
    COL['brochure_' + area_name + '_area_sqft'] = sqft
COL['brochure_area_note'] = 'Source labels only; not calculated mesh areas'
COL['stair_rear_clearance_m'] = STAIR_REAR_CLEARANCE
COL['stair_finish'] = 'User requested carpet on treads, risers and upper landing; color inferred'
COL['stair_separator'] = 'User requested solid drywall instead of open balusters'
COL['stair_drywall_height_m'] = STAIR_DRYWALL_HEIGHT


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


# Interior finishes are shared by both floors, not additional exterior paints.
if BUILD_FIRST_FLOOR or BUILD_SECOND_FLOOR:
    M.update({
        'int_wall': material('Interior | warm off-white drywall - inferred', (0.88, 0.87, 0.83), 0.83),
        'int_trim': material('Interior | white doors and millwork - inferred', (0.94, 0.935, 0.91), 0.56),
        'int_ceiling': material('Interior | matte white ceiling', (0.93, 0.93, 0.90), 0.92),
        'int_tile': material('Interior | warm light tile - inferred', (0.76, 0.74, 0.68), 0.55),
        'int_grout': material('Interior | fine warm grout', (0.57, 0.55, 0.50), 0.88),
        'int_wood': material('Interior | pale oak floors and cabinetry - inferred', (0.64, 0.51, 0.36), 0.65),
        'int_carpet': material('Interior | upstairs and stair carpet - neutral color placeholder',
                               STAIR_CARPET_RGB, 0.98, noise=0.002),
        'int_counter': material('Interior | pale stone worktop - inferred', (0.88, 0.875, 0.84), 0.34),
        'int_ceramic': material('Interior | white sanitary ceramic', (0.94, 0.95, 0.93), 0.22),
        'int_steel': material('Interior | brushed appliance steel', (0.60, 0.62, 0.64), 0.30, metallic=0.8),
        'int_dark': material('Interior | appliance glass and recesses', (0.06, 0.075, 0.08), 0.24),
        'int_glass': material('Interior | clear architectural glazing', (0.98, 0.995, 1.0), 0.08),
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
    ground_level = bottom < UPPER_FLOOR - 0.1
    lined = BUILD_FIRST_FLOOR if ground_level else BUILD_SECOND_FLOOR
    floor_z = INTERIOR_FLOOR_Z if ground_level else SECOND_FLOOR_Z
    ceiling_z = INTERIOR_CEILING_Z if ground_level else SECOND_CEILING_Z
    if lined:
        # Both stories get lining and trim with genuine window/door openings.
        lining, skirting = Geometry(), Geometry()
        for low, high in zip(levels[:-1], levels[1:]):
            low, high = max(low, floor_z), min(high, ceiling_z)
            if high <= low:
                continue
            for l, r in intervals_without_openings(facade.length, openings, low, high):
                facade.solid(lining, l, r, -0.205, -0.19, low, high)
        for l, r in intervals_without_openings(facade.length, openings,
                                               floor_z, floor_z + 0.10):
            facade.solid(skirting, l, r, -0.218, -0.205,
                         floor_z, floor_z + 0.10)
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
    clear = ((BUILD_FIRST_FLOOR and FIRST_FLOOR_CLEAR_GLASS)
             if z < UPPER_FLOOR - 0.1 else
             (BUILD_SECOND_FLOOR and SECOND_FLOOR_CLEAR_GLASS))
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
# A shared structural plate and finish layers use exactly the same stair hole.
# When the second floor is enabled it retains its structural support even if
# the first-floor inspection switch removes the deeper ceiling layer.
if BUILD_FIRST_FLOOR or BUILD_SECOND_FLOOR:
    if BUILD_SECOND_FLOOR or (BUILD_FIRST_FLOOR and BUILD_FIRST_FLOOR_CEILINGS):
        hole_x0, hole_y0, hole_x1, hole_y1 = STAIR_HOLE
        plate_bottom = (INTERIOR_CEILING_Z if BUILD_FIRST_FLOOR and
                        BUILD_FIRST_FLOOR_CEILINGS else UPPER_FLOOR - 0.12)
        ceiling = Geometry()
        for x0, y0, x1, y1 in ((0, FRONT, hole_x0, BACK),
                               (hole_x1, FRONT, W, BACK),
                               (hole_x0, FRONT, hole_x1, hole_y0),
                               (hole_x0, hole_y1, hole_x1, BACK)):
            ceiling.box((x0, y0, plate_bottom), (x1, y1, UPPER_FLOOR))
        ceiling.finish('Interior | shared upper floor plate - stair opening', M['int_ceiling'])
    if BUILD_FIRST_FLOOR and BUILD_FIRST_FLOOR_CEILINGS:
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
     [opening('den window', 0.93, 0.92, FF + 0.58, 1.52),
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
if not (BUILD_SECOND_FLOOR and SECOND_FLOOR_CUTAWAY):
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

def interior_partition(name, a, b, doors=(), thickness=INTERIOR_WALL_T,
                       floor_z=INTERIOR_FLOOR_Z, ceiling_z=INTERIOR_CEILING_Z,
                       under_stairs=False):
    """doors = (distance from a, opening width, opening height), in meters."""
    delta = Vector((b[0] - a[0], b[1] - a[1], 0))
    length = delta.length
    assert length > 0 and floor_z < ceiling_z
    tangent = delta.normalized()
    facade = Facade('Interior | ' + name, a, tangent,
                    (-tangent.y, tangent.x), length)

    def solid(geo, l, r, d0, d1, low, high):
        if not under_stairs:
            facade.solid(geo, l, r, d0, d1, low, high)
            return
        # Axis-aligned wall cells, clipped in Y/Z before extrusion across X.
        # This clips headers and casing too, without collapsed/inverted boxes.
        assert abs(tangent.x) < 1e-6 or abs(tangent.y) < 1e-6
        corners = [facade.p(u, d, low) for u in (l, r) for d in (d0, d1)]
        x0, x1 = min(p.x for p in corners), max(p.x for p in corners)
        y0, y1 = min(p.y for p in corners), max(p.y for p in corners)
        source = [(y0, low), (y1, low), (y1, high), (y0, high)]
        ring = []
        previous = source[-1]
        dp = previous[1] - stair_underside_z(previous[0])
        for current in source:
            dc = current[1] - stair_underside_z(current[0])
            if (dc <= 0) != (dp <= 0):
                factor = dp / (dp - dc)
                ring.append((previous[0] + factor * (current[0] - previous[0]),
                             previous[1] + factor * (current[1] - previous[1])))
            if dc <= 0:
                ring.append(current)
            previous, dp = current, dc
        if len(ring) >= 3:
            geo.prism([(x0, y, z) for y, z in ring], (x1 - x0, 0, 0))

    openings = [opening('passage %d' % i, start + width / 2, width,
                        floor_z, height)
                for i, (start, width, height) in enumerate(doors)]
    previous_end = -1.0
    for start, width, height in sorted(doors):
        assert 0 <= start < start + width <= length + 1e-6
        assert start >= previous_end and 0 < height < ceiling_z - floor_z
        previous_end = start + width
    levels = sorted(set([floor_z, ceiling_z] +
                        [op['z'] + op['h'] for op in openings]))
    g, base = Geometry(), Geometry()
    for low, high in zip(levels[:-1], levels[1:]):
        for l, r in intervals_without_openings(length, openings, low, high):
            solid(g, l, r, -thickness / 2, thickness / 2, low, high)
    suffix = ' partition with open doorways' if doors else ' solid partition'
    obj = g.finish('Interior | ' + name + suffix, M['int_wall'])
    for l, r in intervals_without_openings(length, openings, floor_z, floor_z + 0.10):
        for sign in (-1, 1):
            depths = sorted((sign * thickness / 2, sign * (thickness / 2 + 0.012)))
            solid(base, l, r, *depths, floor_z, floor_z + 0.10)
    base.finish('Interior | ' + name + ' baseboards', M['int_trim'])
    trim = Geometry()
    for op in openings:
        l, r = op['u'] - op['w'] / 2, op['u'] + op['w'] / 2
        top = op['z'] + op['h']
        # Narrow jambs and casing only; no panel spans the doorway.
        solid(trim, l, l + 0.018, -thickness / 2, thickness / 2, floor_z, top)
        solid(trim, r - 0.018, r, -thickness / 2, thickness / 2, floor_z, top)
        solid(trim, l, r, -thickness / 2, thickness / 2, top - 0.018, top)
        for sign in (-1, 1):
            d0, d1 = sorted((sign * thickness / 2, sign * (thickness / 2 + 0.015)))
            solid(trim, l - 0.06, l, d0, d1, floor_z, top + 0.06)
            solid(trim, r, r + 0.06, d0, d1, floor_z, top + 0.06)
            solid(trim, l, r, d0, d1, top, top + 0.06)
    trim.finish('Interior | ' + name + ' door jambs and casing', M['int_trim'])
    return obj


def subtract_rect(rect, hole):
    """Disjoint rectangular remainder; shared by slabs, floors and counters."""
    a, b, c, d = rect
    l, f = max(a, hole[0]), max(b, hole[1])
    r, back = min(c, hole[2]), min(d, hole[3])
    if l >= r or f >= back:
        return [rect]
    return [p for p in ((a, b, l, d), (r, b, c, d), (l, b, r, f), (l, back, r, d))
            if p[2] - p[0] > 1e-6 and p[3] - p[1] > 1e-6]


def interior_floor(name, rect, wood=False, holes=(),
                   slab_z=FF, floor_z=INTERIOR_FLOOR_Z, carpet=False):
    x0, y0, x1, y1 = rect
    assert x0 < x1 and y0 < y1 and slab_z < floor_z - 0.006
    assert not (wood and carpet), 'Choose one floor finish'
    g = Geometry()
    regions = [rect]
    for hole in holes:
        regions = [piece for r in regions for piece in subtract_rect(r, hole)]
    if carpet:
        # Continuous broadloom, not carpet-colored planks or tiles. Retain all
        # room exclusions and the stair opening through the full finish depth.
        for a, b, c, d in regions:
            g.box((a, b, slab_z), (c, d, floor_z))
        obj = g.finish('Interior | ' + name + ' continuous carpet floor', M['int_carpet'])
        if obj:
            obj['room'] = name
            obj['walkable'] = True
            obj['finish'] = 'Carpet'
            obj['finish_note'] = 'User requested; matches stair carpet; neutral color placeholder'
        return obj
    for a, b, c, d in regions:
        g.box((a, b, slab_z), (c, d, floor_z - 0.006))
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
                parts = [piece for r in parts for piece in subtract_rect(r, hole)]
            for a, b, c, d in parts:
                if c - a > 0.004 and d - b > 0.004:
                    g.box((a + 0.001, b + 0.001, floor_z - 0.006),
                          (c - 0.001, d - 0.001, floor_z))
            y += dy
        x += dx
        column += 1
    obj = g.finish('Interior | ' + name + (' floor planks' if wood else ' floor tiles'),
                   M['int_wood'] if wood else M['int_tile'])
    if obj:
        obj['room'] = name
        obj['walkable'] = True
        obj['finish'] = 'Oak planks' if wood else 'Tile'
        obj['finish_note'] = ('User requested downstairs oak planks matching the former upstairs finish'
                              if wood else 'Inferred finish; brochure gives layout, not material selections')
    return obj


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


def build_stair_landing():
    """Carpeted arrival, flush with the existing upper finished-floor level."""
    x0, y0, x1, y1 = STAIR_LANDING
    landing = box('Interior | carpeted stair upper landing',
                  (x0, y0, UPPER_FLOOR), (x1, y1, SECOND_FLOOR_Z), M['int_carpet'])
    landing['walkable'] = True
    landing['finish'] = 'Carpet; user requested; neutral color placeholder'
    return landing


def build_first_floor():
    z, ceiling = INTERIOR_FLOOR_Z, INTERIOR_CEILING_Z
    inset, half = 0.205, INTERIOR_WALL_T / 2
    # The brochure explicitly labels the deep rear-left bay as GARAGE, not a den.
    # Preserve its connection to the projecting two-car garage; do not insert
    # a wall across the complete FRONT line.
    interior_partition('garage to den', (GARAGE_EXTENSION_X, FRONT),
                       (GARAGE_EXTENSION_X, SERVICE_REAR_Y), thickness=0.19)
    interior_partition('garage to recessed den front', (GARAGE_EXTENSION_X, FRONT),
                       (GARAGE_W, FRONT), thickness=0.19)
    interior_partition('garage rear mud entry', (inset, GARAGE_REAR_Y),
                       (GARAGE_EXTENSION_X, GARAGE_REAR_Y), [(0.60, 0.86, 2.13)], thickness=0.19)
    interior_partition('service rooms to kitchen', (inset, SERVICE_REAR_Y),
                       (GARAGE_EXTENSION_X, SERVICE_REAR_Y), [(0.64, 0.92, 2.13)])
    interior_partition('pantry side', (1.95, GARAGE_REAR_Y),
                       (1.95, SERVICE_REAR_Y), [(0.27, 0.83, 2.13)])
    # den.png replaces the old wide leisure-to-cafe opening with a solid wall.
    # End the rear wall at the den/foyer junction: the foyer stays open to cafe.
    interior_partition('den rear enclosure', (GARAGE_EXTENSION_X, GARAGE_REAR_Y),
                       (FOYER_X, GARAGE_REAR_Y))
    interior_partition('den to foyer double doorway', (FOYER_X, FRONT + inset),
                       (FOYER_X, GARAGE_REAR_Y),
                       [(DEN_DOOR_Y0 - FRONT - inset, DEN_DOOR_WIDTH, DEN_DOOR_HEIGHT)])
    # Both leaves swing into the room (-X before the house-wide mirror), never
    # into the foyer. A single clear opening has no central post or backing slab.
    hinge_x = FOYER_X - half - 0.025
    leaf_width = DEN_DOOR_WIDTH / 2 - 0.027
    for label, hinge_y, closed_direction in (
            ('front', DEN_DOOR_Y0 + 0.025, (0, 1, 0)),
            ('rear', DEN_DOOR_Y1 - 0.025, (0, -1, 0))):
        leaf = interior_door_leaf('Interior | den double door ' + label,
                                  (hinge_x, hinge_y, z + 0.01),
                                  (-1, 0, 0) if DEN_DOORS_OPEN else closed_direction,
                                  leaf_width, DEN_DOOR_HEIGHT - 0.04, M['int_trim'])
        leaf['room'] = 'Den'
        leaf['reference'] = 'den.png; inward-opening paired doors on foyer wall'
        leaf['open_angle_degrees'] = 90 if DEN_DOORS_OPEN else 0
    interior_partition('powder to foyer', (STAIR_X0, FRONT + inset),
                       (STAIR_X0, POWDER_REAR_Y), [(0.66, 0.76, 2.13)], under_stairs=True)
    interior_partition('powder rear beneath flight', (STAIR_X0, POWDER_REAR_Y),
                       (W - inset, POWDER_REAR_Y), under_stairs=True)
    interior_partition('enclosed front stair side', (STAIR_X0, POWDER_REAR_Y),
                       (STAIR_X0, GARAGE_REAR_Y), under_stairs=True)
    if BUILD_FIRST_FLOOR_CEILINGS:
        # Close the powder ceiling beneath the high treads, not across the hole.
        # The structural floor covers the rest of the room toward the entry.
        rise = (SECOND_FLOOR_Z - z) / STAIR_RISERS
        going = (STAIR_Y1 - STAIR_Y0) / (STAIR_RISERS - 1)
        transition_y = STAIR_Y1 - (ceiling + STAIR_SOFFIT_THICKNESS - z) * going / rise
        end_y = POWDER_REAR_Y + half
        cuts = sorted(set([STAIR_Y0, end_y] +
                          [y for y in (transition_y,) if STAIR_Y0 < y < end_y]))
        soffit = Geometry()
        for y0, y1 in zip(cuts[:-1], cuts[1:]):
            z0, z1 = under_stair_ceiling(y0), under_stair_ceiling(y1)
            soffit.prism([(STAIR_X0 - half, y0, z0 - 0.012),
                          (W - inset, y0, z0 - 0.012),
                          (W - inset, y1, z1 - 0.012),
                          (STAIR_X0 - half, y1, z1 - 0.012)], (0, 0, 0.012))
        soffit.finish('Interior | powder sloping ceiling beneath stairs', M['int_ceiling'])

    # User flooring revision: reuse the former upstairs oak plank material,
    # board size and stagger downstairs, including kitchen, foyer and powder.
    # Preserve room masks, finished elevations and the concrete garage bay.
    den = (GARAGE_EXTENSION_X + 0.095, FRONT + 0.095, FOYER_X, GARAGE_REAR_Y)
    garage = (inset, FRONT, GARAGE_EXTENSION_X + 0.095, GARAGE_REAR_Y + 0.095)
    interior_floor('kitchen cafe great room foyer powder and service rooms',
                   (inset, FRONT, W - inset, BACK - inset), wood=True, holes=(den, garage))
    interior_floor('den', den, wood=True)
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

    # The upper plan shows the arrival toward the front, above the powder room.
    # The low rear steps continue beneath the upper plate; the opening need not
    # extend all the way to the foot. Rise/run and construction remain inferred.
    risers = STAIR_RISERS
    landing_z = SECOND_FLOOR_Z
    rise = (landing_z - z) / risers
    going = (STAIR_Y1 - STAIR_Y0) / (risers - 1)
    stairs, treads = Geometry(), Geometry()
    for i in range(risers - 1):
        rear = STAIR_Y1 - i * going
        front = rear - going
        top = z + (i + 1) * rise
        # A sloping closed underside leaves the powder usable below the high
        # end. The former floor-to-tread blocks would fill that room entirely.
        x0 = STAIR_X0
        stairs.prism([(x0, front, stair_underside_z(front)),
                      (x0, rear, stair_underside_z(rear)),
                      (x0, rear, top - 0.025),
                      (x0, front, top - 0.025)], (STAIR_X1 - x0, 0, 0))
        # Carpet replaces the old tread finish at the same walking elevation;
        # the vertical strip wraps each riser up to the carpeted nosing.
        treads.box((STAIR_X0, front, top - 0.025),
                   (STAIR_X1, rear + 0.015, top))
        treads.box((STAIR_X0, rear, top - rise),
                   (STAIR_X1, rear + 0.012, top - 0.025))
    # The last riser is the edge of the upper floor plate, not another tread.
    treads.box((STAIR_X0, STAIR_Y0, landing_z - rise),
               (STAIR_X1, STAIR_Y0 + 0.012, landing_z))
    stairs.finish('Interior | stair flight structure and sloping underside', M['int_trim'])
    # Continue the cafe-facing enclosure from its old endpoint to the foot.
    # Follow the actual first-step underside (which meets the finished floor),
    # rather than a full-width block that would obstruct the stair entrance.
    side_start = GARAGE_REAR_Y
    first_step_front = STAIR_Y1 - going
    assert POWDER_REAR_Y < side_start < first_step_front
    side_x = STAIR_X0 - half
    lower_side = Geometry()
    lower_side.prism([(side_x, side_start, z),
                      (side_x, STAIR_Y1, z),
                      (side_x, first_step_front, stair_underside_z(first_step_front)),
                      (side_x, side_start, stair_underside_z(side_start))],
                     (INTERIOR_WALL_T, 0, 0))
    lower_side.finish('Interior | lower stair side enclosure to first riser', M['int_wall'])
    # Carry the room-side baseboard around the tapered bottom of the panel.
    trim_transition = STAIR_Y1 - (STAIR_SOFFIT_THICKNESS + 0.10) * going / rise
    trim_ys = sorted(set([side_start, first_step_front, STAIR_Y1] +
                         [y for y in (trim_transition,) if side_start < y < first_step_front]))
    base_profile = [(side_x - 0.012, side_start, z), (side_x - 0.012, STAIR_Y1, z)]
    for y in reversed(trim_ys[:-1]):
        base_profile.append((side_x - 0.012, y, min(z + 0.10, stair_underside_z(y))))
    lower_base = Geometry()
    lower_base.prism(base_profile, (0.012, 0, 0))
    lower_base.finish('Interior | lower stair side baseboard', M['int_trim'])
    stair_obj = treads.finish('Interior | carpeted stair treads nosings and risers',
                              M['int_carpet'], 0.002)
    stair_obj['walkable'] = True
    stair_obj['riser_count'] = risers
    stair_obj['riser_m'] = rise
    stair_obj['going_m'] = going
    stair_obj['finish'] = 'Carpet; user requested; neutral color placeholder'
    stair_obj['inferred_direction'] = 'Ascends toward -Y before house mirroring'
    build_stair_landing()

    # Solid drywall replaces the entire sloping rail/baluster assembly. The
    # lower edge meets the retained enclosure and powder wall, never filling
    # the room below the flight. End faces close the panel at both stair ends.
    ceiling_transition = STAIR_Y1 - (ceiling + STAIR_SOFFIT_THICKNESS - z) * going / rise
    side_ys = sorted(set([STAIR_Y0, first_step_front, STAIR_Y1] +
                         [y for y in (ceiling_transition,)
                          if STAIR_Y0 < y < first_step_front]))
    profile = [(side_x, y, under_stair_ceiling(y)) for y in side_ys]
    profile.extend([(side_x, STAIR_Y1, z + rise + STAIR_DRYWALL_HEIGHT),
                    (side_x, STAIR_Y0, landing_z + STAIR_DRYWALL_HEIGHT)])
    separator = Geometry()
    separator.prism(profile, (INTERIOR_WALL_T, 0, 0))
    separator_obj = separator.finish('Interior | solid drywall stair half-wall', M['int_wall'])
    separator_obj['finish'] = 'Drywall separator; user requested; height inferred'
    if not BUILD_SECOND_FLOOR:
        # Still close the loft edge in first-floor-only inspection mode.
        hx0, hy0, hx1, hy1 = STAIR_HOLE
        upper_guard('loft stair edge', (hx0 - half, hy0), (hx0 - half, hy1))

    if BUILD_FIRST_FLOOR_FIXTURES:
        build_first_floor_fixtures()
    COL['first_floor_interior'] = True
    COL['first_floor_finish'] = 'User requested former upstairs oak planks throughout downstairs indoor rooms; garage unchanged'
    COL['first_floor_reference'] = 'honor_page-0002.jpg with den.png enclosure revision; mirrored with exterior'
    COL['first_floor_rooms'] = 'Den; foyer; powder bath; cafe; great room; kitchen; pantry/service vestibule; garage and rear garage extension'
    COL['den_reference'] = 'den.png: solid rear wall and foyer-side inward double doors'
    COL['den_door_opening_width_m'] = DEN_DOOR_WIDTH
    COL['den_doors_open'] = DEN_DOORS_OPEN
    COL['first_floor_ceiling_height_m'] = ceiling - z
    COL['first_floor_optional_refrigerator'] = FIRST_FLOOR_REFRIGERATOR
    COL['first_floor_limitations'] = ('Partitions fitted to existing shell; prior den enclosure retained. '
                                      'Finishes, service-room labels and stair construction inferred. '
                                      'Powder walls/ceiling follow the stair underside; '
                                      'upper stair opening ends before the low rear steps.')


def build_first_floor_fixtures():
    z, half = INTERIOR_FLOOR_Z, INTERIOR_WALL_T / 2
    counter_z = z + 0.90
    # Kitchen wall run: refrigerator near the pantry, range, base/upper cabinets.
    # A narrow rear-wall gap keeps the existing lanai slider clear.
    for index, (y0, y1) in enumerate(((13.12, 14.60), (15.38, 15.94), (15.94, 16.80))):
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
    # Keep the labelled optional refrigerator bay empty unless requested.
    if FIRST_FLOOR_REFRIGERATOR:
        box('Interior | kitchen optional refrigerator body', (0.23, 12.19, z),
            (0.96, 13.06, z + 1.95), M['int_steel'], 0.008)
        for a, b in ((12.20, 12.615), (12.63, 13.05)):
            box('Interior | refrigerator front door', (0.963, a, z + 0.05),
                (0.992, b, z + 1.93), M['int_steel'], 0.004)
            beam('Interior | refrigerator handle', (1.025, (a + b) / 2, z + 0.90),
                 (1.025, (a + b) / 2, z + 1.40), 0.024, 0.024, M['metal'])
    # Range sits farther toward the lanai than the island sink in the plan.
    box('Interior | kitchen range body', (0.24, 14.63, z + 0.06),
        (0.84, 15.35, counter_z - 0.025), M['int_steel'], 0.004)
    box('Interior | range oven glass', (0.844, 14.70, z + 0.20),
        (0.858, 15.28, z + 0.64), M['int_dark'], 0.006)
    beam('Interior | oven handle', (0.89, 14.73, z + 0.73),
         (0.89, 15.24, z + 0.73), 0.025, 0.025, M['int_steel'])
    box('Interior | range cooktop', (0.24, 14.63, counter_z - 0.025),
        (0.85, 15.35, counter_z), M['int_dark'])
    for x in (0.41, 0.68):
        for y in (14.80, 15.16):
            interior_tube('cooktop burner', (x, y, counter_z), (x, y, counter_z + 0.008),
                          0.095, M['int_steel'], 24)
    box('Interior | range hood canopy', (0.22, 14.59, z + 1.66),
        (0.84, 15.39, z + 1.78), M['int_steel'], 0.006)
    box('Interior | range hood flue', (0.23, 14.80, z + 1.78),
        (0.48, 15.18, z + 2.32), M['int_steel'])

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


# ----------------------------- second-floor interior -------------------------
def upper_partition(name, a, b, doors=()):
    """Door specs: (start, width, style, hinge_at_end, inward_normal_sign).

    All coordinates remain in the brochure frame until Geometry.finish().
    The same opening spec produces both the wall hole and its door leaves.
    """
    delta = Vector((b[0] - a[0], b[1] - a[1], 0))
    tangent = delta.normalized()
    normal = Vector((-tangent.y, tangent.x, 0))
    half, height = INTERIOR_WALL_T / 2, 2.13
    # No upstairs partition may bridge the stair opening, even above a door.
    bounds = (min(a[0], b[0]) - abs(normal.x) * half,
              min(a[1], b[1]) - abs(normal.y) * half,
              max(a[0], b[0]) + abs(normal.x) * half,
              max(a[1], b[1]) + abs(normal.y) * half)
    assert not rectangles_overlap(bounds, STAIR_HOLE), name + ' crosses the stairwell'
    obj = interior_partition('Upper | ' + name, a, b,
                             [(d[0], d[1], height) for d in doors],
                             floor_z=SECOND_FLOOR_Z, ceiling_z=SECOND_CEILING_Z)
    obj['floor_level'] = 2
    f = Facade('Interior | Upper | ' + name, a, tangent, normal, delta.length)
    for index, (start, width, style, hinge_end, swing) in enumerate(doors):
        label = 'Interior | Upper | ' + name + ' door %d' % (index + 1)
        if style == 'swing':
            assert swing in (-1, 1)
            along = start + width - 0.027 if hinge_end else start + 0.027
            hinge = f.p(along, swing * (half + 0.025), SECOND_FLOOR_Z + 0.01)
            direction = (normal * swing if SECOND_FLOOR_OPEN_DOORS else
                         tangent * (-1 if hinge_end else 1))
            leaf = interior_door_leaf(label, hinge, direction, width - 0.054,
                                      height - 0.04, M['int_trim'])
            leaf['open_angle_degrees'] = 90 if SECOND_FLOOR_OPEN_DOORS else 0
        elif style == 'bypass':
            # Two overlapping sliding leaves; no swing into a bedroom or closet.
            leaf_width = (width - 0.036) / 2 + 0.025
            for k in range(2):
                left = start + 0.018
                if k and not SECOND_FLOOR_OPEN_DOORS:
                    left = start + width - 0.018 - leaf_width
                depth = -0.038 + k * 0.045
                leaf = f.part('bypass leaf %d-%d' % (index, k), left, left + leaf_width,
                              depth, depth + 0.03, SECOND_FLOOR_Z + 0.012,
                              SECOND_FLOOR_Z + height - 0.025, M['int_trim'], 0.002)
                leaf['slid_open'] = SECOND_FLOOR_OPEN_DOORS
                f.part('bypass pull %d-%d' % (index, k), left + leaf_width - 0.075,
                       left + leaf_width - 0.055, depth - 0.012, depth,
                       SECOND_FLOOR_Z + 0.95, SECOND_FLOOR_Z + 1.10, M['metal'])
            f.part('overhead bypass track %d' % index, start, start + width,
                   -0.047, 0.047, SECOND_FLOOR_Z + height - 0.025,
                   SECOND_FLOOR_Z + height - 0.018, M['int_steel'])
        else:
            raise ValueError('Unknown upper door style: ' + style)


def rectangles_overlap(a, b):
    return (min(a[2], b[2]) - max(a[0], b[0]) > 1e-6 and
            min(a[3], b[3]) - max(a[1], b[1]) > 1e-6)


def upper_guard(name, a, b):
    """Solid drywall half-wall on the loft edge; no posts, spindles or wood rail."""
    # Start at the structural plate so there is no gap beneath the wall finish.
    a, b = Vector((a[0], a[1], UPPER_FLOOR)), Vector((b[0], b[1], UPPER_FLOOR))
    delta = b - a
    assert delta.length > 1e-6
    normal = Vector((-delta.y, delta.x, 0)).normalized() * INTERIOR_WALL_T / 2
    g = Geometry()
    g.prism([a - normal, b - normal, b + normal, a + normal],
            (0, 0, SECOND_FLOOR_Z + STAIR_DRYWALL_HEIGHT - UPPER_FLOOR))
    obj = g.finish('Interior | Upper | ' + name + ' solid drywall half-wall', M['int_wall'])
    obj['finish'] = 'Drywall separator; user requested; height inferred'
    return obj


def upper_basin(name, f, rect, top, depth, mat):
    """Recessed bowl in a fixture-local frame, with an open top."""
    a, b, c, d = rect
    inset = min(0.07, (c - a) / 5, (d - b) / 5)
    g = Geometry()
    f.solid(g, a + inset, c - inset, b + inset, d - inset,
            top - depth - 0.014, top - depth)
    rim = [f.p(a, b, top), f.p(c, b, top), f.p(c, d, top), f.p(a, d, top)]
    bottom = [f.p(a + inset, b + inset, top - depth),
              f.p(c - inset, b + inset, top - depth),
              f.p(c - inset, d - inset, top - depth),
              f.p(a + inset, d - inset, top - depth)]
    for i in range(4):
        j = (i + 1) % 4
        g.prism([rim[i], bottom[i], bottom[j], rim[j]], (0, 0, -0.014))
    g.finish('Interior | Upper | ' + name + ' open bowl', mat)
    interior_tube('Upper | ' + name + ' drain',
                  f.p((a + c) / 2, (b + d) / 2, top - depth),
                  f.p((a + c) / 2, (b + d) / 2, top - depth + 0.004),
                  0.024, M['int_steel'])


def upper_vanity(name, origin, tangent, length, sinks=1):
    z = SECOND_FLOOR_Z
    f = Facade('Interior | Upper | ' + name, origin, tangent,
               (-tangent[1], tangent[0]), length)
    g = Geometry()
    f.solid(g, 0.04, length - 0.04, 0.04, 0.49, z, z + 0.10)
    g.finish(f.name + ' recessed toe kick', M['int_dark'])
    g = Geometry()
    f.solid(g, 0, length, 0, 0.55, z + 0.10, z + 0.15)
    f.solid(g, 0, 0.025, 0, 0.55, z + 0.15, z + 0.82)
    f.solid(g, length - 0.025, length, 0, 0.55, z + 0.15, z + 0.82)
    # Cabinet doors enclose the front without filling the sink volume.
    for k in range(sinks * 2):
        a, b = k * length / (sinks * 2), (k + 1) * length / (sinks * 2)
        f.solid(g, a + 0.006, b - 0.006, 0.525, 0.55, z + 0.12, z + 0.81)
        beam(f.name + ' pull', f.p((a + b) / 2 - 0.05, 0.575, z + 0.72),
             f.p((a + b) / 2 + 0.05, 0.575, z + 0.72), 0.014, 0.014, M['metal'])
    g.finish(f.name + ' hollow cabinet and doors', M['int_trim'])
    holes = [(length * (k + 0.5) / sinks - 0.22, 0.14,
              length * (k + 0.5) / sinks + 0.22, 0.47) for k in range(sinks)]
    parts = [(0, 0, length, 0.59)]
    for hole in holes:
        parts = [piece for r in parts for piece in subtract_rect(r, hole)]
    g = Geometry()
    for a, b, c, d in parts:
        f.solid(g, a, c, b, d, z + 0.82, z + 0.86)
    g.finish(f.name + ' counter with real sink cutouts', M['int_counter'], 0.002)
    for k, hole in enumerate(holes):
        upper_basin(name + ' sink %d' % (k + 1), f, hole, z + 0.86, 0.17, M['int_ceramic'])
        center = (hole[0] + hole[2]) / 2
        interior_tube('Upper | ' + name + ' faucet', f.p(center, 0.085, z + 0.86),
                      f.p(center, 0.085, z + 1.04), 0.016, M['int_steel'])
        interior_tube('Upper | ' + name + ' spout', f.p(center, 0.085, z + 1.04),
                      f.p(center, 0.24, z + 1.04), 0.016, M['int_steel'])
    f.part('mirror frame', 0.03, length - 0.03, -0.01, 0.015,
           z + 1.08, z + 2.10, M['int_trim'])
    f.part('mirror - metallic approximation', 0.055, length - 0.055, 0.016, 0.021,
           z + 1.105, z + 2.075, M['int_steel'])


def upper_toilet(name, origin, tangent):
    z = SECOND_FLOOR_Z
    f = Facade('Interior | Upper | ' + name, origin, tangent,
               (-tangent[1], tangent[0]), 1.0)
    for label, profile in (
            ('pedestal', [(0.13, 0.21, 0), (0.14, 0.22, 0.16), (0.20, 0.28, 0.34)]),
            ('bowl and seat', [(0.16, 0.24, 0.27), (0.205, 0.295, 0.39),
                               (0.21, 0.30, 0.43), (0.145, 0.225, 0.43),
                               (0.10, 0.16, 0.31)])):
        rings = [[f.p(rx * math.cos(k * math.tau / 32),
                      0.47 + ry * math.sin(k * math.tau / 32), z + h)
                  for k in range(32)] for rx, ry, h in profile]
        g = Geometry()
        g.face(list(reversed(rings[0])))
        for lower, upper in zip(rings[:-1], rings[1:]):
            for k in range(32):
                j = (k + 1) % 32
                g.face([lower[k], lower[j], upper[j], upper[k]])
        g.face(rings[-1])
        g.finish(f.name + ' ' + label, M['int_ceramic'])
    f.part('tank', -0.20, 0.20, 0, 0.18, z + 0.32, z + 0.77, M['int_ceramic'], 0.02)
    f.part('tank lid', -0.21, 0.21, -0.01, 0.19, z + 0.77, z + 0.80, M['int_ceramic'], 0.012)
    f.part('flush lever', 0.12, 0.17, 0.18, 0.195, z + 0.65, z + 0.69, M['int_steel'])


def upper_shelf(name, rect, rod_a, rod_b):
    a, b, c, d = rect
    z = SECOND_FLOOR_Z
    box('Interior | Upper | ' + name + ' shelf', (a, b, z + 1.78),
        (c, d, z + 1.81), M['int_trim'])
    interior_tube('Upper | ' + name + ' hanging rail',
                  (rod_a[0], rod_a[1], z + 1.64),
                  (rod_b[0], rod_b[1], z + 1.64), 0.017, M['int_steel'])


def build_second_floor_fixtures():
    z = SECOND_FLOOR_Z
    # Standard plan: rear double vanity, shower, separate WC, walk-in closet.
    upper_vanity('master double vanity', (4.00, BACK - 0.24), (-1, 0), 1.90, 2)
    upper_vanity('bath 2 vanity', (UP_BATH2_X - 0.09, 8.36), (0, 1), 0.80)
    upper_toilet('master WC', (UP_SUITE_X - 0.13, 14.48), (0, 1))
    upper_toilet('bath 2 WC', (UP_BATH2_X - 0.12, 7.90), (0, 1))

    # Real recessed tub, rather than a solid block occupying its bathing space.
    f = Facade('Interior | Upper | bath 2 tub', (3.70, FRONT + 0.24), (1, 0), (0, 1), 1.55)
    g = Geometry()
    for a, b, c, d in ((0, 0, 0.09, 0.75), (1.46, 0, 1.55, 0.75),
                        (0.09, 0, 1.46, 0.09), (0.09, 0.66, 1.46, 0.75)):
        f.solid(g, a, c, b, d, z, z + 0.52)
    g.finish(f.name + ' apron and rim', M['int_ceramic'], 0.012)
    upper_basin('bath 2 tub', f, (0.09, 0.09, 1.46, 0.66), z + 0.52, 0.39, M['int_ceramic'])
    f.part('tiled front-wall surround', 0, 1.55, -0.022, -0.005,
           z + 0.52, z + 2.10, M['int_tile'])
    interior_tube('Upper | bath 2 tub spout', f.p(1.54, 0.38, z + 0.72),
                  f.p(1.36, 0.38, z + 0.72), 0.018, M['int_steel'])
    interior_tube('Upper | bath 2 shower riser', f.p(1.54, 0.38, z + 1.03),
                  f.p(1.54, 0.38, z + 1.97), 0.016, M['int_steel'])
    interior_tube('Upper | bath 2 shower head', f.p(1.54, 0.38, z + 1.97),
                  f.p(1.40, 0.38, z + 1.97), 0.055, M['int_steel'])

    # Keep the existing rear bath window unobstructed by full-height tile.
    sx0, sx1, sy0, sy1 = 4.10, UP_SUITE_X - 0.08, 15.93, BACK - 0.24
    f = Facade('Interior | Upper | master shower', (sx0, sy0), (1, 0), (0, 1), sx1 - sx0)
    upper_basin('master shower pan', f, (0, 0, sx1 - sx0, sy1 - sy0),
                z + 0.075, 0.045, M['int_ceramic'])
    box(f.name + ' front curb', (sx0, sy0 - 0.035, z),
        (sx1, sy0 + 0.035, z + 0.09), M['int_counter'])
    box(f.name + ' side glass', (sx0 - 0.014, sy0, z + 0.09),
        (sx0 - 0.004, sy1, z + 2.06), M['int_glass'])
    span = sx1 - sx0
    for k in range(2):
        left = sx0 + 0.018
        if k and not SECOND_FLOOR_OPEN_DOORS:
            left = sx0 + span / 2 - 0.018
        yy = sy0 + 0.016 * k
        box(f.name + ' sliding glass %d' % k, (left, yy, z + 0.10),
            (left + span / 2, yy + 0.008, z + 2.04), M['int_glass'])
        beam(f.name + ' glass pull %d' % k, (left + span / 2 - 0.08, yy - 0.018, z + 0.95),
             (left + span / 2 - 0.08, yy - 0.018, z + 1.17), 0.016, 0.016, M['int_steel'])
    for h in (0.095, 2.055):
        box(f.name + ' sliding track', (sx0, sy0 - 0.016, z + h),
            (sx1, sy0 + 0.045, z + h + 0.02), M['int_steel'])
    box(f.name + ' low rear tile below window', (sx0, sy1 + 0.01, z + 0.08),
        (sx1, sy1 + 0.027, z + 1.60), M['int_tile'])
    box(f.name + ' side tile', (sx1, sy0, z + 0.08),
        (sx1 + 0.014, sy1, z + 2.12), M['int_tile'])
    interior_tube('Upper | master shower mixer', (sx1 - 0.025, 16.40, z + 1.10),
                  (sx1 - 0.045, 16.40, z + 1.10), 0.045, M['int_steel'])
    interior_tube('Upper | master shower head', (sx1 - 0.02, 16.40, z + 2.0),
                  (sx1 - 0.22, 16.40, z + 2.0), 0.055, M['int_steel'])

    upper_shelf('bedroom 2 closet', (0.27, 10.05, 2.34, 10.32), (0.32, 10.02), (2.29, 10.02))
    upper_shelf('bedroom 3 closet', (0.27, 10.48, 2.34, 10.75), (0.32, 10.78), (2.29, 10.78))
    upper_shelf('master reach-in', (UP_MASTER_CLOSET_X + 0.08, 11.59,
                                  UP_MASTER_CLOSET_END_X - 0.08, 11.92),
                (UP_MASTER_CLOSET_X + 0.12, 11.95), (UP_MASTER_CLOSET_END_X - 0.12, 11.95))
    upper_shelf('walk-in side', (0.25, 14.74, 0.65, BACK - 0.26),
                (0.69, 14.85), (0.69, BACK - 0.60))
    upper_shelf('walk-in rear', (0.66, BACK - 0.60, UP_WIC_X - 0.08, BACK - 0.26),
                (0.76, BACK - 0.64), (UP_WIC_X - 0.12, BACK - 0.64))

    # Mechanical equipment is an inferred placeholder; enclosure follows plan.
    box('Interior | Upper | HVAC equipment', (3.78, 13.04, z + 0.06),
        (4.50, 13.76, z + 1.78), M['int_steel'], 0.006)
    for k in range(10):
        box('Interior | Upper | HVAC grille slot', (3.88, 13.022, z + 0.30 + k * 0.07),
            (4.40, 13.039, z + 0.32 + k * 0.07), M['int_dark'])
    for k, y in enumerate((11.34, 12.18)):
        box('Interior | Upper | laundry connection box %d' % k,
            (UP_BED_X + 0.058, y - 0.13, z + 0.93),
            (UP_BED_X + 0.09, y + 0.13, z + 1.10), M['int_trim'])
        if SECOND_FLOOR_LAUNDRY_APPLIANCES:
            box('Interior | Upper | optional laundry appliance %d' % k,
                (UP_BED_X + 0.13, y - 0.34, z),
                (UP_BED_X + 0.81, y + 0.34, z + 0.90), M['int_trim'], 0.008)
            interior_tube('Upper | laundry appliance front %d' % k,
                          (UP_BED_X + 0.81, y, z + 0.45),
                          (UP_BED_X + 0.83, y, z + 0.45), 0.23, M['int_dark'], 32)


def build_second_floor():
    before = {obj.name for obj in COL.objects}
    inset, z = 0.205, SECOND_FLOOR_Z
    front, rear = FRONT + inset, BACK - inset
    bx, sx = UP_BED_X, UP_SUITE_X
    # Each partition is emitted once; shared room boundaries are not doubled.
    walls = [
        ('bedroom 2 east', (bx, front), (bx, UP_BED2_REAR), ()),
        ('bath 2 east', (UP_BATH2_X, front), (UP_BATH2_X, UP_BED2_REAR), ()),
        ('bath 2 hall entry', (bx, UP_BED2_REAR), (UP_BATH2_X, UP_BED2_REAR),
         ((0.18, 0.82, 'swing', False, -1),)),
        ('bedroom 2 hall and closet front', (inset, UP_BED2_REAR), (bx, UP_BED2_REAR),
         ((0.35, 1.50, 'bypass', False, 1), (2.42, 0.82, 'swing', True, -1))),
        ('bedroom closets shared back', (inset, UP_CLOSET_SPLIT), (UP_REACHIN_X, UP_CLOSET_SPLIT), ()),
        ('bedroom closets east', (UP_REACHIN_X, UP_BED2_REAR),
         (UP_REACHIN_X, UP_BED3_CLOSET_REAR), ()),
        ('bedroom 3 closet front', (inset, UP_BED3_CLOSET_REAR),
         (UP_REACHIN_X, UP_BED3_CLOSET_REAR), ((0.35, 1.50, 'bypass', False, 1),)),
        ('bedroom 3 hall entry', (UP_REACHIN_X, UP_HALL_REAR), (bx, UP_HALL_REAR),
         ((0.14, 0.86, 'swing', True, 1),)),
        ('bedroom 3 and service spine', (bx, UP_HALL_REAR), (bx, UP_WC_REAR), ()),
        ('bedroom 3 rear', (inset, UP_BED3_REAR), (bx, UP_BED3_REAR), ()),
        ('utility hall entry', (bx, UP_HALL_REAR), (sx, UP_HALL_REAR),
         ((1.12, 0.78, 'swing', True, 1),)),
        ('HVAC service entry', (bx, UP_UTILITY_REAR), (sx, UP_UTILITY_REAR),
         ((1.08, 0.80, 'swing', True, 1),)),
        ('HVAC to WC', (bx, UP_HVAC_REAR), (sx, UP_HVAC_REAR), ()),
        ('master WC entry', (bx, UP_WC_REAR), (sx, UP_WC_REAR),
         ((0.16, 0.78, 'swing', False, -1),)),
        ('suite service and bath boundary', (sx, UP_HALL_REAR), (sx, rear),
         ((15.07 - UP_HALL_REAR, 0.80, 'swing', False, 1),)),
        ('walk-in closet entry', (UP_WIC_X, UP_BED3_REAR), (UP_WIC_X, rear),
         ((0.27, 0.80, 'swing', True, 1),)),
        ('master bedroom loft entry', (sx, UP_MASTER_FRONT), (UP_MASTER_CLOSET_END_X, UP_MASTER_FRONT),
         ((0.13, 0.88, 'swing', False, 1),)),
        ('master reach-in west', (UP_MASTER_CLOSET_X, UP_MASTER_FRONT),
         (UP_MASTER_CLOSET_X, UP_MASTER_CLOSET_REAR), ()),
        ('master reach-in bedroom opening', (UP_MASTER_CLOSET_X, UP_MASTER_CLOSET_REAR),
         (UP_MASTER_CLOSET_END_X, UP_MASTER_CLOSET_REAR),
         (((UP_MASTER_CLOSET_END_X - UP_MASTER_CLOSET_X - 1.65) / 2,
           1.65, 'bypass', False, 1),)),
    ]
    # Validate every opening before generating any upstairs partitions.
    for name, a, b, doors in walls:
        length = math.hypot(b[0] - a[0], b[1] - a[1])
        for start, width, style, hinge, swing in doors:
            assert 0.06 <= start and start + width <= length - 0.06 + 1e-6, name
    for name, a, b, doors in walls:
        upper_partition(name, a, b, doors)

    wc = (bx, UP_HVAC_REAR, sx, UP_WC_REAR)
    closet3 = (inset, UP_CLOSET_SPLIT, UP_REACHIN_X, UP_BED3_CLOSET_REAR)
    master_closet = (UP_MASTER_CLOSET_X, UP_MASTER_FRONT,
                     UP_MASTER_CLOSET_END_X, UP_MASTER_CLOSET_REAR)
    bedroom3_hall = (UP_REACHIN_X, UP_CLOSET_SPLIT, bx, UP_HALL_REAR)
    # User requested ALL upstairs room floors carpeted, including bath, utility
    # and closet floors. Shower/tub surfaces remain their separate fixtures.
    # Room regions and full-depth stair exclusions are otherwise unchanged.
    rooms = [
        ('Bedroom 2', (inset, front, bx, UP_BED2_REAR), (), '11 ft 2 in x 10 ft 10 in'),
        ('Bedroom 2 closet', (inset, UP_BED2_REAR, UP_REACHIN_X, UP_CLOSET_SPLIT), (), ''),
        ('Bedroom 3', (inset, UP_CLOSET_SPLIT, bx, UP_BED3_REAR),
         (closet3, bedroom3_hall), '11 ft 2 in x 10 ft 9 in'),
        ('Bedroom 3 closet', closet3, (), ''),
        ('Bath 2', (bx, front, UP_BATH2_X, UP_BED2_REAR), (), ''),
        ('Utility', (bx, UP_HALL_REAR, sx, UP_UTILITY_REAR), (), ''),
        ('HVAC', (bx, UP_UTILITY_REAR, sx, UP_HVAC_REAR), (), ''),
        ('Master WC', wc, (), ''),
        ('Master walk-in closet', (inset, UP_BED3_REAR, UP_WIC_X, rear), (), ''),
        ('Master bath', (UP_WIC_X, UP_BED3_REAR, sx, rear), (wc,), ''),
        ('Master bedroom', (sx, UP_MASTER_FRONT, W - inset, rear),
         (master_closet,), '13 ft 9 in x 15 ft 1 in'),
        ('Master reach-in closet', master_closet, (), ''),
    ]
    covered = []
    for name, rect, holes, brochure_size in rooms:
        pieces = [rect]
        for hole in holes:
            pieces = [p for r in pieces for p in subtract_rect(r, hole)]
        for piece in pieces:
            assert not rectangles_overlap(piece, STAIR_HOLE), name + ' overlaps stair opening'
            assert not any(rectangles_overlap(piece, r) for r in covered), name + ' floor overlap'
        covered.extend(pieces)
        obj = interior_floor('Upper | ' + name, rect, holes=holes,
                             slab_z=UPPER_FLOOR, floor_z=z, carpet=True)
        if obj:
            obj['room'] = name
            obj['brochure_room_size_reference'] = brochure_size
            obj['dimension_note'] = 'Fitted to existing shell; source label is not an as-built measurement'
    exclusions = tuple(covered) + (STAIR_HOLE, STAIR_LANDING)
    if not BUILD_FIRST_FLOOR:
        build_stair_landing()  # Carpet stays consistent in upper-floor-only mode.
    loft = interior_floor('Upper | loft and connecting hall',
                          (inset, front, W - inset, rear), holes=exclusions,
                          slab_z=UPPER_FLOOR, floor_z=z, carpet=True)
    loft['room'] = 'Loft and hall'
    loft['brochure_room_size_reference'] = 'Loft: 11 ft 0 in x 16 ft 0 in'

    # Solid drywall replaces the loft balusters. Keep its full thickness on
    # the floor-plate side of the hole, with no wall across the front arrival.
    hx0, hy0, hx1, hy1 = STAIR_HOLE
    guard_x = hx0 - INTERIOR_WALL_T / 2
    upper_guard('loft stair edge', (guard_x, hy0), (guard_x, hy1))
    # The straight master/closet wall closes the rear of this opening. A second
    # rear guard would overlap that wall; leave the front stair arrival open.
    if BUILD_SECOND_FLOOR_CEILINGS and not SECOND_FLOOR_CUTAWAY:
        box('Interior | Upper | flat 8 ft 8 in ceiling', (inset, front, SECOND_CEILING_Z),
            (W - inset, rear, SECOND_CEILING_Z + 0.10), M['int_ceiling'])
    if BUILD_SECOND_FLOOR_FIXTURES:
        build_second_floor_fixtures()
    for obj in COL.objects:
        if obj.name not in before:
            obj['floor_level'] = 2
            obj['reference'] = 'honor_page-0002.jpg main upper plan; standard bath; mirrored with shell'
    COL['second_floor_interior'] = True
    COL['second_floor_finish'] = 'User requested matching carpet in all upstairs rooms, halls and closets; shower/tub surfaces unchanged'
    COL['second_floor_rooms'] = '; '.join(room[0] for room in rooms) + '; Loft and hall'
    COL['second_floor_ceiling_height_m'] = SECOND_CEILING_Z - z
    COL['second_floor_doors_open'] = SECOND_FLOOR_OPEN_DOORS
    COL['second_floor_cutaway'] = SECOND_FLOOR_CUTAWAY
    COL['second_floor_limitations'] = ('Plan fitted to existing FH-1 shell; stair opening corrected '
                                      'to preserve the straight master/loft wall and reach-in closet. '
                                      'Finishes, fixture details and door sizes inferred. '
                                      'Optional master bath and recessed ceiling not included.')


if BUILD_FIRST_FLOOR:
    build_first_floor()
if BUILD_SECOND_FLOOR:
    build_second_floor()

# Selection, cameras, lighting, world and units are unchanged.
# Standard/sRGB color management is configured above.
bpy.context.view_layer.update()
print('Honor FH-1 house created: %d mesh objects in %s.' % (len(COL.objects), COLLECTION_NAME))
print('Front is -Y. Unseen elevations and roof dimensions are approximations.')
if BUILD_FIRST_FLOOR:
    print('First-floor interior added; mirrored with the right-hand garage: %s.' % RIGHT_HAND_GARAGE)
    print('Includes rear garage bay, service/pantry rooms, enclosed den, foyer, powder, kitchen, cafe and great room.')
    print('Downstairs indoor flooring: former upstairs oak planks; garage, porch and lanai unchanged.')
    print('Den: solid rear wall and inward-opening foyer double doors; DEN_DOORS_OPEN = %s.' % DEN_DOORS_OPEN)
    print('Plan-aligned stairs: carpeted treads, risers and landing; solid drywall separators, no balusters.')
    print('Neutral carpet color and drywall half-wall height are placeholders; powder clearance retained.')
    print('Optional kitchen refrigerator: %s.' % FIRST_FLOOR_REFRIGERATOR)
if BUILD_SECOND_FLOOR:
    print('Second floor: master suite, bedrooms 2/3, bath 2, closets, utility, HVAC and loft.')
    print('All upstairs room floors and stairs: matching carpet; shower/tub surfaces unchanged.')
    print('Upper ceiling: 8 ft 8 in. Standard master bath; optional appliances: %s.' % SECOND_FLOOR_LAUNDRY_APPLIANCES)
    print('Room sizes fitted to the FH-1 shell; straight master boundary and full-width reach-in closet.')
    if SECOND_FLOOR_CUTAWAY:
        print('CUTAWAY ACTIVE: main roof and upper ceiling omitted. Disable before full-house export.')
if BUILD_FIRST_FLOOR or BUILD_SECOND_FLOOR:
    print('All materials are lit. Interior finishes, fixture details and stair dimensions are inferred.')
    print('Reload honor.py in Blender and rerun; inspect both floors, then re-export the GLB.')
