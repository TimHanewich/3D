# MADE BY GPT-6-sol on high reasoning

"""A stylized Blender model of the custom quadcopter in the three supplied photos.

Run this Python file in Blender's Text Editor. Measurements are illustrative,
not a dimensionally accurate or flight-ready reproduction. Re-running replaces
only objects previously created in the 'Photo Drone (Generated)' collection.
Front is -Y; back is +Y. No image files or external assets are required.
"""

import math
import bpy
from mathutils import Vector

COLLECTION_NAME = "Photo Drone (Generated)"
PREFIX = "Photo Drone | "
collection = bpy.data.collections.get(COLLECTION_NAME)
if collection is None:
    collection = bpy.data.collections.new(COLLECTION_NAME)
    bpy.context.scene.collection.children.link(collection)
else:
    for obj in list(collection.objects):
        if obj.name.startswith(PREFIX):
            bpy.data.objects.remove(obj, do_unlink=True)


def material(name, rgb, metallic=0.0, roughness=0.62):
    name = "Photo Drone - " + name
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*rgb, 1.0)
    mat.use_nodes = True
    shader = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if shader:
        shader.inputs['Base Color'].default_value = (*rgb, 1.0)
        shader.inputs['Metallic'].default_value = metallic
        shader.inputs['Roughness'].default_value = roughness
    return mat


white = material("white printed frame", (0.81, 0.83, 0.80))
edge_white = material("bright brackets and ties", (0.90, 0.91, 0.87))
black = material("motor black", (0.022, 0.025, 0.029), 0.22, 0.38)
prop_mat = material("smoky propellers", (0.080, 0.087, 0.093), 0.30, 0.25)
red = material("red motor bases and cables", (0.64, 0.024, 0.028))
yellow = material("yellow cables", (0.96, 0.61, 0.027))
teal = material("teal cables", (0.015, 0.51, 0.49))
wire_black = material("black cables and straps", (0.030, 0.032, 0.034))
silver = material("silver battery foil", (0.53, 0.55, 0.56), 0.68, 0.30)
gold = material("gold connectors", (0.64, 0.38, 0.085), 0.70, 0.25)
blue = material("blue battery tape", (0.020, 0.21, 0.58))
board = material("controller board", (0.035, 0.19, 0.12))
lens_glass = material("camera lens", (0.045, 0.080, 0.10), 0.32, 0.14)


def mesh_object(name, verts, faces, mat, bevel=0):
    mesh = bpy.data.meshes.new(PREFIX + name + " mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(PREFIX + name, mesh)
    collection.objects.link(obj)
    mesh.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("Slightly softened edges", 'BEVEL')
        mod.width = bevel
        mod.segments = 2
    return obj


def box(name, center, size, mat, bevel=0.008):
    x, y, z = center
    a, b, c = (v / 2 for v in size)
    vertices = [
        (x-a, y-b, z-c), (x+a, y-b, z-c),
        (x+a, y+b, z-c), (x-a, y+b, z-c),
        (x-a, y-b, z+c), (x+a, y-b, z+c),
        (x+a, y+b, z+c), (x-a, y+b, z+c),
    ]
    faces = [(3, 2, 1, 0), (0, 1, 5, 4), (1, 2, 6, 5),
             (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)]
    return mesh_object(name, vertices, faces, mat, bevel)


def polygon_plate(name, points, low, high, mat, bevel=0.004):
    """Extrude a simple XY outline into a shallow solid."""
    signed_area = sum(points[i][0] * points[(i+1) % len(points)][1]
                      - points[(i+1) % len(points)][0] * points[i][1]
                      for i in range(len(points)))
    if signed_area < 0:
        points = list(reversed(points))
    n = len(points)
    vertices = [(x, y, low) for x, y in points]
    vertices += [(x, y, high) for x, y in points]
    faces = [tuple(reversed(range(n))), tuple(range(n, 2*n))]
    faces += [(i, (i+1) % n, (i+1) % n + n, i+n) for i in range(n)]
    return mesh_object(name, vertices, faces, mat, bevel)


def cylinder(name, center, radius, depth, mat, axis=(0, 0, 1), sides=24):
    """Cylinder along any direction, without using context-dependent operators."""
    origin = Vector(center)
    rotation = Vector((0, 0, 1)).rotation_difference(Vector(axis).normalized())
    vertices = []
    for height in (-depth/2, depth/2):
        for i in range(sides):
            theta = 2 * math.pi * i / sides
            local = Vector((radius * math.cos(theta), radius * math.sin(theta), height))
            vertices.append(tuple(origin + rotation @ local))
    faces = [tuple(reversed(range(sides))), tuple(range(sides, 2*sides))]
    faces += [(i, (i+1) % sides, (i+1) % sides + sides, i+sides)
              for i in range(sides)]
    return mesh_object(name, vertices, faces, mat)


def tube(name, points, radius, mat, sides=7):
    """A rounded polyline for wires, aerial leads and small hoses."""
    points = [Vector(p) for p in points]
    vertices = []
    for i, point in enumerate(points):
        tangent = (points[min(i+1, len(points)-1)]
                   - points[max(i-1, 0)]).normalized()
        reference = Vector((0, 0, 1))
        if abs(tangent.dot(reference)) > 0.94:
            reference = Vector((0, 1, 0))
        u = tangent.cross(reference).normalized()
        v = tangent.cross(u).normalized()
        for j in range(sides):
            angle = 2 * math.pi * j / sides
            vertices.append(tuple(point + radius * (u*math.cos(angle) + v*math.sin(angle))))
    faces = [tuple(reversed(range(sides))),
             tuple(range((len(points)-1)*sides, len(points)*sides))]
    for i in range(len(points)-1):
        for j in range(sides):
            nj = (j+1) % sides
            faces.append((i*sides+j, i*sides+nj,
                          (i+1)*sides+nj, (i+1)*sides+j))
    return mesh_object(name, vertices, faces, mat)


def frustum(name, x, y, bottom_z, top_z, bottom_size, top_size, mat):
    """Square-sided taper, like the conspicuous white antenna housing."""
    verts = []
    for z, (width, depth) in ((bottom_z, bottom_size), (top_z, top_size)):
        verts.extend(((x-width/2, y-depth/2, z), (x+width/2, y-depth/2, z),
                      (x+width/2, y+depth/2, z), (x-width/2, y+depth/2, z)))
    faces = [(3, 2, 1, 0), (4, 5, 6, 7)]
    faces += [(i, (i+1) % 4, (i+1) % 4 + 4, i+4) for i in range(4)]
    return mesh_object(name, verts, faces, mat, 0.006)


# TWO WHITE DECKS, the exposed central electronics, and four diagonal arms.
box("lower flight-controller deck", (0, 0, 0.41), (2.06, 1.64, 0.12), white)
box("flight controller board", (0, -0.04, 0.54), (1.05, 0.76, 0.065), board)
for sx in (-1, 1):
    for sy in (-1, 1):
        label = ("L" if sx < 0 else "R") + ("F" if sy < 0 else "B")
        start = Vector((sx*0.63, sy*0.47))
        end = Vector((sx*2.53, sy*1.70))
        direction = (end-start).normalized()
        normal = Vector((-direction.y, direction.x))
        outline = [tuple(start + normal*0.24), tuple(end + normal*0.19),
                   tuple(end - normal*0.19), tuple(start - normal*0.24)]
        polygon_plate(label + " diagonal white arm", outline, 0.27, 0.41, white)
        cylinder(label + " motor mounting plate", (end.x, end.y, 0.39),
                 0.37, 0.12, edge_white)
        for bx, by in ((0.85, 0.61),):
            cylinder(label + " arm bolt", (sx*bx, sy*by, 0.49),
                     0.040, 0.036, silver, sides=12)

for sx in (-1, 1):
    for sy in (-1, 1):
        label = ("L" if sx < 0 else "R") + ("F" if sy < 0 else "B")
        cylinder(label + " silver deck standoff", (sx*0.81, sy*0.56, 0.56),
                 0.075, 0.26, silver, sides=12)
box("upper printed deck", (0, 0, 0.74), (2.10, 1.62, 0.085), edge_white)
for sx in (-1, 1):
    for sy in (-1, 1):
        cylinder("deck screw %s %s" % (sx, sy),
                 (sx*0.81, sy*0.56, 0.80), 0.064, 0.032, silver, sides=12)

# FOUR BRUSHLESS MOTORS: red lower bells, black cans, silver nuts.
# Propellers are deliberately posed, not animated.
def propeller(label, x, y, z, rotation):
    """Two gently swept, pitched blades with a genuine thin 3D profile."""
    stations = [(0.13, 0.16, 0.00), (0.30, 0.20, 0.018),
                (0.58, 0.17, 0.09), (0.92, 0.080, 0.16)]
    for blade in range(2):
        angle = rotation + blade*math.pi
        vertices = []
        for layer in (0, 1):
            for rad, width, sweep in stations:
                for edge in (-1, 1):
                    transverse = sweep + edge*width/2
                    px = x + rad*math.cos(angle) - transverse*math.sin(angle)
                    py = y + rad*math.sin(angle) + transverse*math.cos(angle)
                    pitch = edge*0.024 * (1 - rad/1.1)
                    vertices.append((px, py, z + pitch - layer*0.018))
        faces = []
        count = len(stations)
        for i in range(count-1):
            a = i*2
            b = a+2
            faces += [(a, b, b+1, a+1),
                      (8+a+1, 8+b+1, 8+b, 8+a),
                      (a, 8+a, 8+b, b),
                      (a+1, b+1, 8+b+1, 8+a+1)]
        faces += [(0, 1, 9, 8), (6, 14, 15, 7)]
        mesh_object(label + " prop blade " + str(blade+1), vertices, faces, prop_mat)


for sx in (-1, 1):
    for sy in (-1, 1):
        label = ("left" if sx < 0 else "right") + (" front" if sy < 0 else " rear")
        mx, my = sx*2.53, sy*1.70
        cylinder(label + " red motor base", (mx, my, 0.52), 0.235, 0.12, red)
        cylinder(label + " brushless motor", (mx, my, 0.67), 0.215, 0.22, black)
        cylinder(label + " motor cap", (mx, my, 0.79), 0.13, 0.045, black)
        propeller(label, mx, my, 0.83, 0.24 if sx == sy else -0.22)
        cylinder(label + " propeller nut", (mx, my, 0.86), 0.076, 0.11,
                 silver, sides=12)

# CENTRAL FOIL-WRAPPED BATTERY: deliberately visible on top, like the photos.
box("silver LiPo battery", (0, 0.02, 1.00), (1.30, 1.75, 0.38), silver, 0.035)
box("blue tape across battery", (0, 0.03, 1.20), (1.34, 0.34, 0.012), blue, 0.002)
for y in (-0.49, 0.49):
    box("battery velcro top %+.2f" % y,
        (0, y, 1.21), (1.42, 0.145, 0.028), wire_black, 0.008)
    for sx in (-1, 1):
        box("battery velcro side %+.2f %s" % (y, sx),
            (sx*0.666, y, 1.00), (0.028, 0.145, 0.40), wire_black, 0.004)

# FRONT CAMERA: a fork-shaped white 3D-printed housing, exposed black lens,
# and the smaller, slightly tilted antenna above it.
box("camera mount base", (-0.38, -1.00, 0.87), (0.90, 0.53, 0.20), white)
for x, label in ((-0.73, "left"), (-0.03, "right")):
    box("camera fork " + label, (x, -1.10, 1.36),
        (0.18, 0.39, 0.89), edge_white, 0.010)
box("camera between forks", (-0.38, -1.10, 1.29),
    (0.44, 0.32, 0.30), black, 0.016)
cylinder("camera lens housing", (-0.38, -1.34, 1.29), 0.155, 0.19,
         black, (0, -1, 0))
cylinder("camera lens ring", (-0.38, -1.437, 1.29), 0.121, 0.025,
         silver, (0, -1, 0))
cylinder("camera glass", (-0.38, -1.451, 1.29), 0.086, 0.023,
         lens_glass, (0, -1, 0))
cylinder("short antenna socket", (-0.38, -1.02, 1.84),
         0.080, 0.12, gold)
tube("short tilted black aerial",
     [(-0.38, -1.02, 1.88), (-0.43, -1.02, 2.10),
      (-0.50, -1.02, 2.39)], 0.046, black, sides=12)

# TALL WHITE TAPERED AERIAL HOUSING toward the back with gold connector.
cylinder("antenna tower stem", (0.48, 0.74, 0.98), 0.17, 0.44, white)
frustum("tapered rear antenna tower", 0.48, 0.74, 1.16, 1.82,
        (0.79, 0.65), (0.35, 0.34), edge_white)
cylinder("tower side bolt", (0.875, 0.74, 1.37), 0.064, 0.047,
         silver, (1, 0, 0), sides=12)
cylinder("gold antenna connector", (0.48, 0.74, 1.88),
         0.080, 0.14, gold, sides=12)
cylinder("long black rubber antenna", (0.48, 0.74, 2.41),
         0.069, 0.95, black, sides=16)
cylinder("antenna tip", (0.48, 0.74, 2.89), 0.072, 0.085, black, sides=16)

# The exposed bundles looping along each white arm are an important part of
# this particular home-built quadcopter's silhouette.
for sx in (-1, 1):
    for sy in (-1, 1):
        tag = ("L" if sx < 0 else "R") + ("F" if sy < 0 else "B")
        for i, (mat, z_offset) in enumerate(((yellow, 0.00), (teal, 0.045),
                                             (red, 0.090), (wire_black, 0.135))):
            lateral = (i - 1.5)*0.047
            points = [
                (sx*2.45, sy*1.68, 0.52+z_offset),
                (sx*2.10 + lateral, sy*1.44, 0.57+z_offset),
                (sx*1.80 + lateral, sy*1.36, 0.66+z_offset),
                (sx*1.44 + lateral, sy*1.06, 0.64+z_offset),
                (sx*1.08, sy*0.79, 0.64+z_offset),
                (sx*0.73, sy*0.50, 0.60+z_offset),
            ]
            tube(tag + " wire " + str(i+1), points, 0.017, mat)
        box(tag + " white wire tie", (sx*1.67, sy*1.25, 0.80),
            (0.10, 0.13, 0.030), edge_white, 0.004)

# A few loose connections and the gold/yellow battery connector at the back.
tube("battery red power lead",
     [(0.41, 0.72, 1.14), (0.72, 0.98, 1.13),
      (0.90, 1.24, 0.96), (1.05, 1.43, 0.82)], 0.026, red)
tube("battery black power lead",
     [(0.32, 0.74, 1.15), (0.58, 1.04, 1.19),
      (0.85, 1.31, 0.94), (1.05, 1.48, 0.79)], 0.026, wire_black)
box("yellow power connector", (1.08, 1.49, 0.81),
    (0.38, 0.27, 0.22), yellow, 0.016)
for x in (0.99, 1.17):
    cylinder("connector socket %.2f" % x, (x, 1.638, 0.81),
             0.049, 0.016, black, (0, 1, 0), sides=12)

# View the new parts without deleting or changing unrelated scene objects.
for obj in bpy.context.selected_objects:
    obj.select_set(False)
for obj in collection.objects:
    if obj.name.startswith(PREFIX):
        obj.select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects.get(
    PREFIX + "upper printed deck")
