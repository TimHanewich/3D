"""Photo-based Pyper rover reconstruction. Run in Blender's Text Editor.
Creates ONLY one mesh object (a joined multipart visual assembly).
No camera, lights, ground, render setup, or changes to scene units.
Hidden parts and dimensions are estimated; not a functional CAD design.
Model coordinates are millimeters, converted to meters at the end.
"""
import bpy
import bmesh
import math
from mathutils import Vector

NAME = 'Pyper'
COLLECTION = 'Pyper model'
SCALE = 0.001
WHEEL_RADIUS = 48.0
WHEEL_WIDTH = 12.0
WHEEL_TEETH = 24
WHEELBASE = 174.0
TRACK = 170.0
DECK_Z = 50.0
JOIN_PARTS = True

if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
old = bpy.data.collections.get(COLLECTION)
if old:
    for obj in list(old.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(old)
collection = bpy.data.collections.new(COLLECTION)
bpy.context.scene.collection.children.link(collection)
parts = []


def material(name, color, metallic=0.0, roughness=0.45):
    mat = bpy.data.materials.get('Pyper ' + name)
    if mat is None:
        mat = bpy.data.materials.new('Pyper ' + name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    if shader:
        shader.inputs['Base Color'].default_value = (*color, 1)
        shader.inputs['Metallic'].default_value = metallic
        shader.inputs['Roughness'].default_value = roughness
    return mat


blue = material('cyan printed plastic', (0.005, 0.38, 0.67))
gear_blue = material('blue gears', (0.006, 0.20, 0.68))
yellow = material('yellow gearbox', (1.0, 0.66, 0.006))
black = material('black hardware', (0.012, 0.016, 0.020))
steel = material('motor steel', (0.48, 0.52, 0.55), 0.7, 0.32)
white = material('motor end cap', (0.74, 0.76, 0.73))
servo_blue = material('servo blue casing', (0.025, 0.04, 0.48), 0, 0.23)
red = material('red wire', (0.65, 0.015, 0.012))
brown = material('brown wire', (0.19, 0.048, 0.018))
orange = material('orange wire', (0.91, 0.25, 0.009))
label = material('servo label', (0.08, 0.26, 0.20))


def active(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def register(obj, name, mat, bevel=0):
    obj.name = name
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    collection.objects.link(obj)
    obj.data.materials.append(mat)
    parts.append(obj)
    if bevel:
        active(obj)
        mod = obj.modifiers.new('Small molded edges', 'BEVEL')
        mod.width = bevel
        mod.segments = 2
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def box(name, center, size, mat, bevel=0.4):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    obj = bpy.context.object
    obj.scale = size
    active(obj)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return register(obj, name, mat, bevel)


def cylinder(name, center, radius, depth, mat, axis=(0, 0, 1), vertices=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                       depth=depth, location=center)
    obj = bpy.context.object
    obj.rotation_euler = Vector(axis).to_track_quat('Z', 'Y').to_euler()
    return register(obj, name, mat, 0.15)


def bar(name, a, b, width, thickness, mat):
    a, b = Vector(a), Vector(b)
    obj = box(name, (a + b) / 2, (width, thickness, (b-a).length), mat)
    obj.rotation_euler = (b-a).to_track_quat('Z', 'Y').to_euler()
    return obj


def mesh_object(name, verts, faces, mat):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return register(obj, name, mat)


def plate(points, z, thickness):
    n = len(points)
    verts = [(x, y, zz) for zz in (z-thickness, z) for x, y in points]
    faces = [tuple(reversed(range(n))), tuple(range(n, 2*n))]
    faces += [(i, (i+1)%n, (i+1)%n+n, i+n) for i in range(n)]
    return mesh_object('Shaped blue chassis', verts, faces, blue)


def toothed_ring(name, center, radius, inner, depth, teeth, mat, phase=0):
    # Tooth profile is a printed tread/gear approximation, not involute CAD.
    n = teeth * 6
    radii = [radius-3.2, radius-3.2, radius, radius, radius, radius-3.2]
    cx, cy, cz = center
    verts = []
    for y in (cy-depth/2, cy+depth/2):
        for inside in (False, True):
            for i in range(n):
                a = math.tau*i/n + phase
                r = inner if inside else radii[i%6]
                verts.append((cx+r*math.cos(a), y, cz+r*math.sin(a)))
    faces = []
    for i in range(n):
        j = (i+1)%n
        faces.extend([(i,j,j+2*n,i+2*n),
                      (i+n,i+3*n,j+3*n,j+n),
                      (i,i+n,j+n,j),
                      (i+2*n,j+2*n,j+3*n,i+3*n)])
    return mesh_object(name, verts, faces, mat)


def wheel(x, y):
    z = WHEEL_RADIUS
    prefix = ('Front' if x < 0 else 'Rear') + (' left' if y > 0 else ' right')
    toothed_ring(prefix+' toothed rim', (x,y,z), WHEEL_RADIUS,
                 WHEEL_RADIUS-10, WHEEL_WIDTH, WHEEL_TEETH, blue)
    cylinder(prefix+' hub', (x,y,z), 10, WHEEL_WIDTH+7, blue, (0,1,0))
    for i in range(4):
        a = math.pi/4 + i*math.pi/2
        bar(prefix+' spoke', (x,y,z),
            (x+(WHEEL_RADIUS-7)*math.cos(a),y,z+(WHEEL_RADIUS-7)*math.sin(a)),
            7, WHEEL_WIDTH-2, blue)
    outward = 1 if y > 0 else -1
    cylinder(prefix+' axle cap', (x,y+outward*11,z), 3.7, 4, black, (0,1,0))
    cylinder(prefix+' axle', (x,y-outward*15,z), 2.7, 27, steel, (0,1,0))
    box(prefix+' bearing mount', (x,y-outward*21,46), (17,10,17), blue)


# Photo-estimated T-shaped platform: front axle crossbar, narrow neck,
# and a broad, smoothly rounded main deck rather than a faceted rectangle.
# X points from the front servo toward the rear motor; Y is across the rover.
def deck_curve(a, b, c, d, steps=16):
    points = []
    for i in range(1, steps + 1):
        t = i / steps
        u = 1 - t
        points.append((u**3*a[0] + 3*u*u*t*b[0] + 3*u*t*t*c[0] + t**3*d[0],
                       u**3*a[1] + 3*u*u*t*b[1] + 3*u*t*t*c[1] + t**3*d[1]))
    return points


# Upper half, starting at the front outside corner. The crossbar spans
# the front bearings; its inset rear edge leaves visible wheel clearance.
deck_upper = [(-102, 0), (-102, 64)]
deck_upper += deck_curve((-102,64), (-102,67), (-100,69), (-97,69), 6)
deck_upper += [(-75,69)]
deck_upper += deck_curve((-75,69), (-72,69), (-70,67), (-70,64), 6)
deck_upper += [(-70,32), (-57,32)]
# Angular shoulder: straight diagonal flare with distinct corners,
# matching the transition behind the front axle in the reference.
deck_upper += [(-30,49), (-9,59)]
deck_upper += deck_curve((-9,59), (18,67), (57,67), (80,58))
deck_upper += deck_curve((80,58), (99,51), (108,29), (108,0), 20)
# Reflect the outline for the largely symmetric, partly occluded far side.
deck_outline = deck_upper + [(x,-y) for x,y in reversed(deck_upper[1:-1])]
plate(deck_outline, DECK_Z, 3.5)
for x in (-WHEELBASE/2, WHEELBASE/2):
    for y in (-TRACK/2, TRACK/2):
        wheel(x,y)
# Front steering linkage beneath the deck (occluded details approximated).
bar('Front steering tie rod', (-87,-66,43), (-87,66,43), 4,4, blue)
for side in (-1,1):
    bar('Front steering arm', (-87,side*64,44), (-67,side*49,44), 5,4, blue)

# Upright small servo on the front crossmember.
box('Micro servo', (-77,-10,66), (24,13,28), servo_blue, 1)
box('Servo mounting flange', (-77,-10,52), (35,15,3), servo_blue)
box('Servo front label border', (-77,-16.7,65), (19,0.5,21), black, 0)
box('Servo green label', (-77,-17.05,65), (16,0.3,17), label, 0)
cylinder('Servo output boss', (-83,-10,81), 5,4, servo_blue)
box('Servo horn', (-75,-10,84), (23,4,2), white)
for x in (-92,-62):
    cylinder('Servo mounting screw', (x,-10,55), 2,3, black, vertices=12)

# Yellow DC gearmotor mounted at the rear; silver can points toward the front.
box('Gearmotor yellow housing', (63,4,72), (43,25,32), yellow, 2)
box('Gearmotor raised cover', (68,4,89), (29,21,3), yellow)
cylinder('DC motor metal can', (31,4,74), 11,23, steel, (1,0,0))
cylinder('Motor pale end cap', (18,4,74), 10,4, white, (1,0,0))
cylinder('Motor rear inset', (15.8,4,74), 5,1.1, black, (1,0,0))
cylinder('Motor bearing', (15,4,74), 2.3,2, steel, (1,0,0))
for y in (-4,12):
    box('Motor electrical terminal', (20,y,82), (3,2,3), steel)
# Thin motor retaining strap.
box('Motor strap top', (34,4,85.5), (3,24,2), white)
for y in (-8,16):
    box('Motor strap side', (34,y,74), (3,2,22), white)

for side in (-1,1):
    y = 4 + side*18
    box('Gearbox mounting upright', (55,y,70), (10,4,37), blue)
    box('Gearbox mounting foot', (59,y,52), (24,12,4), blue)
    for x,z in ((55,80),(55,58)):
        cylinder('Gearbox bracket screw', (x,y+side*3,z), 2.4,3, black, (0,1,0),12)
    # Small output gear and larger axle gear; centers separated for meshing.
    toothed_ring('Motor output pinion', (66,4+side*25,74), 15,4,7,16,gear_blue)
    cylinder('Pinion center', (66,4+side*25,74),4.3,8,white,(0,1,0))
    toothed_ring('Rear axle drive gear', (87,4+side*32,48),22,7,8,20,gear_blue)
    cylinder('Drive gear hub',(87,4+side*32,48),9,10,gear_blue,(0,1,0))
    for i in range(4):
        a = i*math.pi/2
        bar('Drive gear web',(87,4+side*32,48),
            (87+18*math.cos(a),4+side*32,48+18*math.sin(a)),5,7,gear_blue)
    box('Rear axle upright',(87,4+side*40,61),(12,7,28),blue)
    box('Rear axle bracket foot',(87,4+side*40,52),(23,16,4),blue)
    cylinder('Rear bracket bolt',(87,4+side*40,76),2.2,4,black)

for x,y in ((45,-30),(73,-35),(80,27),(45,28),(18,-36),(96,-18)):
    cylinder('Deck screw head',(x,y,52),2.2,2,black,vertices=12)
    cylinder('Deck screw tip',(x,y,54),0.9,3,black,vertices=12)


def wire(name, coords, mat, radius=0.65):
    curve = bpy.data.curves.new(name,'CURVE')
    curve.dimensions = '3D'
    curve.resolution_u = 16
    curve.bevel_depth = radius
    curve.bevel_resolution = 3
    spline = curve.splines.new('BEZIER')
    spline.bezier_points.add(len(coords)-1)
    for point, co in zip(spline.bezier_points, coords):
        point.co = co
        point.handle_left_type = 'AUTO'
        point.handle_right_type = 'AUTO'
    obj = bpy.data.objects.new(name,curve)
    collection.objects.link(obj)
    curve.materials.append(mat)
    active(obj)
    bpy.ops.object.convert(target='MESH')
    parts.append(bpy.context.object)


# Three-lead loop emerging from the servo, as visible in the reference.
for i,mat in enumerate((brown,red,orange)):
    dy = i*1.4
    wire('Servo lead '+str(i),[(-66,-8+dy,66),(-49,-3+dy,82),
        (-52,7+dy,99),(-88,20+dy,101),(-108,6+dy,85),
        (-89,-2+dy,79)],mat)
box('Servo cable connector',(-89,0,79),(13,6,5),black)
wire('Motor positive lead',[(20,-4,83),(38,-16,88),(84,-12,101),
                          (100,1,133),(78,8,111),(55,9,92)],red,0.8)
wire('Motor negative lead',[(20,12,83),(30,15,96),(52,20,123),
                          (70,12,126),(58,9,93)],black,0.75)

# Join the visual assembly without a destructive solid union. Material colors
# and disconnected component islands are retained for easy later editing.
if JOIN_PARTS:
    bpy.ops.object.select_all(action='DESELECT')
    for obj in parts:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    model = bpy.context.object
    model.name = NAME
    bpy.context.scene.cursor.location  # Do not alter the user's cursor.
    # Bake coordinates in meters without changing global scene units.
    world = model.matrix_world.copy()
    for v in model.data.vertices:
        v.co = (world @ v.co) * SCALE
    model.matrix_world.identity()
    model['reference'] = r'C:\Users\timh\Downloads\pyper.jpg'
    model['note'] = 'Photo-estimated visual reconstruction; hidden details approximate.'
else:
    for obj in parts:
        obj.location *= SCALE
        obj.scale *= SCALE
print('Pyper model created. No camera, lights, scenery, or scene settings added.')
