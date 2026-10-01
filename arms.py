"""Reconstruct the two drone-arm variants in arms.jpg.
Run from Blender's Text Editor (Open > arms.py > Run Script).
Photo-based approximation, NOT a dimensionally verified flight-ready part.
Dimensions below are millimeters. Only the generated collection is replaced.
Uses Blender's Exact Boolean solver; no external packages or image needed.
"""
import math
import bpy
import bmesh
from mathutils import Vector

# ---- Adjustable photo-estimated dimensions (mm) ----
MOTOR_X = 100.0
MOTOR_RADIUS = 22.0
ROOT_HALF_WIDTH = 25.0
ROOT_THICKNESS = 12.0
TIP_THICKNESS = 4.0
ROOT_HOLE_DIAMETER = 3.4
MOTOR_HOLE_DIAMETER = 3.2
MOTOR_HOLE_SPACING = 16.0
BRACE_X = 52.0
BRACE_WIDTH = 14.0
SIDE_SLOT_LENGTH = 8.0
SIDE_SLOT_HEIGHT = 1.8
ARM_SEPARATION = 69.0
EDGE_BEVEL = 0.35
COLLECTION_NAME = 'Drone Arms - photo reconstruction'
SETUP_CAMERA = True


def activate(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def move_to_collection(obj):
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)
    output.objects.link(obj)


def normals(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()


def prism(name, points, bottom, top):
    # bottom can be a function of x, giving the tapered underside.
    n = len(points)
    verts = [(x, y, bottom(x) if callable(bottom) else bottom)
             for x, y in points]
    verts += [(x, y, top) for x, y in points]
    faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
    faces += [(i, (i + 1) % n, (i + 1) % n + n, i + n)
              for i in range(n)]
    mesh = bpy.data.meshes.new(name + ' mesh')
    mesh.from_pydata(verts, [], faces)
    normals(mesh)
    obj = bpy.data.objects.new(name, mesh)
    output.objects.link(obj)
    return obj


def boolean(obj, cutter, operation='DIFFERENCE'):
    activate(obj)
    mod = obj.modifiers.new('Applied ' + operation, 'BOOLEAN')
    mod.operation = operation
    mod.solver = 'EXACT'
    mod.object = cutter
    bpy.ops.object.modifier_apply(modifier=mod.name)
    mesh = cutter.data
    bpy.data.objects.remove(cutter, do_unlink=True)
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)


def cylinder(x, y, radius):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=64, radius=radius, depth=40, location=(x, y, -5))
    obj = bpy.context.object
    move_to_collection(obj)
    return obj


def rounded_polygon(points, radius=3.0, steps=10):
    # Round corners with quadratic Bezier segments, preserving straight rails.
    result = []
    for i, p in enumerate(points):
        p = Vector(p)
        prev = Vector(points[i - 1])
        nxt = Vector(points[(i + 1) % len(points)])
        d = min(radius, (prev - p).length * 0.35,
                (nxt - p).length * 0.35)
        a = p + (prev - p).normalized() * d
        b = p + (nxt - p).normalized() * d
        for j in range(steps + 1):
            t = j / steps
            q = (1 - t)**2 * a + 2 * (1 - t) * t * p + t*t * b
            result.append((q.x, q.y))
    return result


def underside(x):
    t = max(0.0, min(1.0, x / (MOTOR_X - 12)))
    return -(ROOT_THICKNESS * (1 - t) + TIP_THICKNESS * t)


def capsule_points(cx, cz, length, height):
    r = height / 2
    half = max(0.0, length / 2 - r)
    points = []
    for center, start in [(cx + half, -90), (cx - half, 90)]:
        for i in range(25):
            angle = math.radians(start + i * 180 / 24)
            points.append((center + r * math.cos(angle),
                           cz + r * math.sin(angle)))
    return points


def side_slot(arm, braced):
    # Tunnel along Y pierces the two rails, but not the center brace.
    x = BRACE_X + BRACE_WIDTH / 2 + 9 if braced else BRACE_X
    z = underside(x) / 2
    cutter = prism('side-slot cutter', capsule_points(
        x, z, SIDE_SLOT_LENGTH, SIDE_SLOT_HEIGHT), -40, 40)
    # Map prism's XY profile into XZ, and its extrusion into Y.
    for v in cutter.data.vertices:
        x0, y0, z0 = v.co
        v.co = (x0, z0, y0)
    normals(cutter.data)
    boolean(arm, cutter)


def build_arm(name, y_offset, braced):
    # Wide two-bolt root, narrow rails and an integrated circular motor pad.
    outline = rounded_polygon([
        (0, -ROOT_HALF_WIDTH), (0, ROOT_HALF_WIDTH),
        (9, ROOT_HALF_WIDTH), (MOTOR_X - 13, 16),
        (MOTOR_X - 13, -16), (9, -ROOT_HALF_WIDTH)], 4)
    arm = prism(name, outline, underside, 0)
    disk = prism('motor pad', [
        (MOTOR_X + MOTOR_RADIUS * math.cos(i * math.tau / 128),
         MOTOR_RADIUS * math.sin(i * math.tau / 128))
        for i in range(128)], -TIP_THICKNESS, 0)
    boolean(arm, disk, 'UNION')

    window = prism('rounded lightening-window cutter', rounded_polygon([
        (17, -16), (17, 16), (MOTOR_X - 18, 11),
        (MOTOR_X - 12, 7), (MOTOR_X - 12, -7),
        (MOTOR_X - 18, -11)], 7, 16), -25, 5)
    if braced:
        # Remove a strip from the cutter, leaving a solid crossbar in the arm.
        x0 = BRACE_X - BRACE_WIDTH / 2
        x1 = BRACE_X + BRACE_WIDTH / 2
        strip = prism('brace mask', [(x0, -35), (x1, -35),
                                    (x1, 35), (x0, 35)], -30, 10)
        boolean(window, strip)
    boolean(arm, window)

    for y in (-ROOT_HALF_WIDTH + 5, ROOT_HALF_WIDTH - 5):
        boolean(arm, cylinder(5.5, y, ROOT_HOLE_DIAMETER / 2))
    half = MOTOR_HOLE_SPACING / 2
    for dx in (-half, half):
        for dy in (-half, half):
            boolean(arm, cylinder(MOTOR_X + dx, dy,
                                  MOTOR_HOLE_DIAMETER / 2))
    side_slot(arm, braced)
    normals(arm.data)
    arm.data.materials.append(material)
    bevel = arm.modifiers.new('Subtle edge rounding', 'BEVEL')
    bevel.width = EDGE_BEVEL
    bevel.segments = 3
    bevel.limit_method = 'ANGLE'
    bevel.angle_limit = math.radians(25)
    arm.location.y = y_offset
    arm['reference'] = r'C:\Users\timh\Downloads\arms.jpg'
    arm['dimensions_note'] = 'Estimated millimeters; verify before manufacturing.'
    return arm


if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
old = bpy.data.collections.get(COLLECTION_NAME)
if old:
    for obj in list(old.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(old)
output = bpy.data.collections.new(COLLECTION_NAME)
bpy.context.scene.collection.children.link(output)
material = bpy.data.materials.get('Drone arm neutral gray')
if material is None:
    material = bpy.data.materials.new('Drone arm neutral gray')
material.diffuse_color = (0.52, 0.54, 0.56, 1)
material.use_nodes = True
bsdf = material.node_tree.nodes.get('Principled BSDF')
if bsdf:
    bsdf.inputs['Base Color'].default_value = material.diffuse_color
    bsdf.inputs['Roughness'].default_value = 0.65

scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 0.001
scene.unit_settings.length_unit = 'MILLIMETERS'
open_arm = build_arm('Arm A - open window', ARM_SEPARATION / 2, False)
braced_arm = build_arm('Arm B - center brace', -ARM_SEPARATION / 2, True)

if SETUP_CAMERA:
    target = Vector((55, 0, -3))
    data = bpy.data.cameras.new('Drone arms camera')
    camera = bpy.data.objects.new('Drone arms camera', data)
    output.objects.link(camera)
    camera.location = (8, -145, 210)
    camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
    data.type = 'ORTHO'
    data.ortho_scale = 180
    data.clip_end = 2000
    scene.camera = camera
    for name, location, energy, size in [
        ('Arms key', (20, -60, 160), 350000, 110),
        ('Arms fill', (95, 75, 110), 200000, 90)]:
        light_data = bpy.data.lights.new(name, 'AREA')
        light_data.energy = energy
        light_data.shape = 'DISK'
        light_data.size = size
        light = bpy.data.objects.new(name, light_data)
        output.objects.link(light)
        light.location = location
        light.rotation_euler = (target - light.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100

activate(open_arm)
braced_arm.select_set(True)
# Frame just the two parts in any available 3D view.
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            space = area.spaces.active
            space.clip_end = 10000
            space.region_3d.view_location = (55, 0, -3)
            space.region_3d.view_distance = 190
            if SETUP_CAMERA:
                space.region_3d.view_rotation = camera.rotation_euler.to_quaternion()
            space.region_3d.view_perspective = 'ORTHO'
print('Created both drone arms. Dimensions are photo-estimated, not certified.')
