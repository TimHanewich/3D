# Writen by GPT-6.1-sol on High reasoning

"""
DRONE2 - editable, photo-inspired quadcopter reconstruction.

This .bpy file is ordinary Python source, not a .blend file or an add-on.
In Blender: Scripting > Text Editor > Open (show All Files if necessary),
select drone2.bpy, then Run Script / Alt-P. Save the resulting scene as
drone2.blend using File > Save As.

Designed around Blender's standard bpy/bmesh API. No external packages.
The proportions and hidden parts are estimates, NOT a measured CAD model.
The photos depict a white printed frame, four red/black outrunner motors,
three-bladed props, exposed ESCs/wires, a foil battery with blue tape and
black straps, a front FPV camera/short antenna, and a rear antenna mast.

All construction dimensions below are in MILLIMETRES. Geometry is converted
into metres for Blender. Front is -Y, right is +X, up is +Z.
Re-running replaces only this script's generated collection in its own scene.
Other scenes are not cleared. Props and the camera head have separate pivots.
The script builds a scene but does not render or overwrite a .blend by default.
"""

import math
import os
import random

import bpy
import bmesh
from mathutils import Vector


# ------------------------------ OPTIONS ----------------------------------
SIZE_MULTIPLIER = 1.0
MOTOR_X = 102.0
MOTOR_Y = 98.0
PROP_RADIUS = 63.5
CAMERA_TILT_DEGREES = -6.0
SAVE_BLEND = False
BLEND_PATH = r"C:\Users\timh\Downloads\bpy\drone2.blend"
SCENE_NAME = "Drone2 - photo reconstruction"
COLLECTION_NAME = "DRONE2 - generated model"
MM = 0.001 * SIZE_MULTIPLIER
RNG = random.Random(2205)
SCENE = None
TOP = None
ROOT = None
GROUP = None
MAT = {}


def vmm(values):
    return Vector(values) * MM


def begin_scene():
    global SCENE, TOP, ROOT, GROUP
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    SCENE = bpy.data.scenes.get(SCENE_NAME)
    if SCENE is None:
        SCENE = bpy.data.scenes.new(SCENE_NAME)
    if bpy.context.window is None:
        raise RuntimeError("Run this script with a Blender window/context available.")
    bpy.context.window.scene = SCENE

    old = bpy.data.collections.get(COLLECTION_NAME)
    if old:
        # Only touch objects belonging to this generated collection.
        for obj in list(old.all_objects):
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if data is not None and data.users == 0:
                for store in (bpy.data.meshes, bpy.data.curves,
                              bpy.data.cameras, bpy.data.lights):
                    if store.get(data.name) == data:
                        store.remove(data)
                        break
        def remove_children(collection):
            for child in list(collection.children):
                remove_children(child)
                bpy.data.collections.remove(child)
        remove_children(old)
        bpy.data.collections.remove(old)

    TOP = bpy.data.collections.new(COLLECTION_NAME)
    SCENE.collection.children.link(TOP)
    GROUP = TOP
    ROOT = bpy.data.objects.new("Drone2 | move entire aircraft", None)
    TOP.objects.link(ROOT)
    ROOT.empty_display_type = 'PLAIN_AXES'
    ROOT.empty_display_size = 25 * MM
    ROOT["description"] = "Approximate reconstruction from the three supplied photos"
    ROOT["front_axis"] = "-Y"
    ROOT["estimated_motor_diagonal_mm"] = math.hypot(2*MOTOR_X, 2*MOTOR_Y)
    ROOT["construction_units"] = "millimetres, converted to metres"
    ROOT["not_measured_CAD"] = True
    SCENE.unit_settings.system = 'METRIC'
    SCENE.unit_settings.scale_length = 1.0
    SCENE.unit_settings.length_unit = 'MILLIMETERS'


def group(name):
    global GROUP
    GROUP = bpy.data.collections.new(name)
    TOP.children.link(GROUP)
    return GROUP


def register(obj, material=None, drone=True):
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)
    GROUP.objects.link(obj)
    if drone:
        obj.parent = ROOT
    if material is not None and hasattr(obj.data, 'materials'):
        obj.data.materials.append(material)
    return obj


def active(obj):
    # Make newly linked objects available before invoking context operators.
    bpy.context.view_layer.update()
    for selected in list(bpy.context.selected_objects):
        selected.select_set(False)
    obj.hide_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def parent_preserving(obj, parent):
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world


def empty(name, location):
    obj = bpy.data.objects.new(name, None)
    register(obj)
    obj.location = vmm(location)
    obj.empty_display_type = 'PLAIN_AXES'
    obj.empty_display_size = 8 * MM
    return obj


def mesh_object(name, vertices, faces, material=None, smooth=False):
    mesh = bpy.data.meshes.new(name + " mesh")
    mesh.from_pydata([tuple(vmm(v)) for v in vertices], [], faces)
    mesh.validate()
    mesh.update()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    register(obj, material)
    for polygon in mesh.polygons:
        polygon.use_smooth = smooth
    return obj


def bevel(obj, width=0.5, segments=3):
    mod = obj.modifiers.new("Soft manufactured edges", 'BEVEL')
    mod.width = width * MM
    mod.segments = segments
    mod.limit_method = 'ANGLE'
    return obj


def box(name, center, dimensions, material=None, radius=0.5, angle=0.0):
    x, y, z = (d / 2 for d in dimensions)
    verts = [(-x,-y,-z), (x,-y,-z), (x,y,-z), (-x,y,-z),
             (-x,-y,z), (x,-y,z), (x,y,z), (-x,y,z)]
    faces = [(0,3,2,1), (4,5,6,7), (0,1,5,4),
             (1,2,6,5), (2,3,7,6), (3,0,4,7)]
    obj = mesh_object(name, verts, faces, material)
    obj.location = vmm(center)
    obj.rotation_euler.z = angle
    if radius:
        bevel(obj, radius)
    return obj


def cylinder(name, center, radius, depth, material=None, axis=(0,0,1),
             vertices=48, edge=0.25):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=radius*MM, depth=depth*MM,
        location=tuple(vmm(center)))
    obj = bpy.context.object
    obj.name = name
    register(obj, material)
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = Vector(axis).normalized().to_track_quat('Z', 'Y')
    for polygon in obj.data.polygons:
        polygon.use_smooth = abs(polygon.normal.z) < 0.5
    if edge:
        bevel(obj, edge, 2)
    return obj


def rod(name, a, b, radius, material, vertices=32):
    a, b = Vector(a), Vector(b)
    return cylinder(name, (a+b)/2, radius, (b-a).length, material,
                    axis=b-a, vertices=vertices, edge=min(radius*.15, .2))


def sphere(name, center, dimensions, material):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=24, ring_count=12, radius=1.0, location=tuple(vmm(center)))
    obj = bpy.context.object
    obj.name = name
    obj.scale = Vector(dimensions) * (MM/2)
    register(obj, material)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def torus(name, center, major, minor, material, axis=(0,0,1)):
    bpy.ops.mesh.primitive_torus_add(
        major_segments=32, minor_segments=10,
        major_radius=major*MM, minor_radius=minor*MM,
        location=tuple(vmm(center)))
    obj = bpy.context.object
    obj.name = name
    register(obj, material)
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = Vector(axis).normalized().to_track_quat('Z', 'Y')
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def wire(name, points, radius, material, cyclic=False, smooth=True):
    data = bpy.data.curves.new(name + " path", 'CURVE')
    data.dimensions = '3D'
    data.resolution_u = 12
    data.bevel_depth = radius * MM
    data.bevel_resolution = 3
    data.use_fill_caps = True
    spline = data.splines.new('BEZIER' if smooth else 'POLY')
    if smooth:
        spline.bezier_points.add(len(points)-1)
        for point, coordinates in zip(spline.bezier_points, points):
            point.co = vmm(coordinates)
            point.handle_left_type = 'AUTO'
            point.handle_right_type = 'AUTO'
    else:
        spline.points.add(len(points)-1)
        for point, coordinates in zip(spline.points, points):
            point.co = (*vmm(coordinates), 1.0)
    spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, data)
    return register(obj, material)


def boolean(target, tool, operation='DIFFERENCE'):
    # Apply earlier bevels before a union; cutters intentionally have no bevel.
    active(target)
    mod = target.modifiers.new("Machined opening / joined print", 'BOOLEAN')
    mod.operation = operation
    mod.solver = 'EXACT'
    mod.object = tool
    try:
        bpy.ops.object.modifier_apply(modifier=mod.name)
    except Exception:
        if mod.name in target.modifiers:
            target.modifiers.remove(mod)
        raise
    data = tool.data
    bpy.data.objects.remove(tool, do_unlink=True)
    if data and data.users == 0:
        bpy.data.meshes.remove(data)
    return target


def tapered_box(name, center_xy, zbottom, ztop, bottom, top, material):
    x, y = center_xy
    verts = []
    for z, (w,d) in ((zbottom,bottom), (ztop,top)):
        verts.extend([(x-w/2,y-d/2,z), (x+w/2,y-d/2,z),
                      (x+w/2,y+d/2,z), (x-w/2,y+d/2,z)])
    faces = [(0,3,2,1), (4,5,6,7), (0,1,5,4),
             (1,2,6,5), (2,3,7,6), (3,0,4,7)]
    return mesh_object(name, verts, faces, material)


def text(name, body, center, size, material, rotation=(0,0,0)):
    data = bpy.data.curves.new(name + " lettering", 'FONT')
    data.body = body
    data.align_x = 'CENTER'
    data.align_y = 'CENTER'
    data.size = size * MM
    data.extrude = 0.01 * MM
    obj = bpy.data.objects.new(name, data)
    register(obj, material)
    obj.location = vmm(center)
    obj.rotation_euler = rotation
    return obj


# ------------------------------ MATERIALS --------------------------------
def material(name, color, metallic=0, roughness=.45):
    mat = bpy.data.materials.get("D2 | " + name)
    if mat is None:
        mat = bpy.data.materials.new("D2 | " + name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    output = mat.node_tree.nodes.new('ShaderNodeOutputMaterial')
    shader = mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Metallic'].default_value = metallic
    shader.inputs['Roughness'].default_value = roughness
    mat.node_tree.links.new(shader.outputs['BSDF'], output.inputs['Surface'])
    mat.diffuse_color = (*color, 1)
    return mat, shader


def noise_surface(mat, scale, distance, strength=.25):
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    tex = nodes.new('ShaderNodeTexNoise')
    tex.inputs['Scale'].default_value = scale
    tex.inputs['Detail'].default_value = 3.0
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = strength
    bump.inputs['Distance'].default_value = distance * MM
    links.new(tex.outputs['Fac'], bump.inputs['Height'])
    shader = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
    links.new(bump.outputs['Normal'], shader.inputs['Normal'])
    return tex, bump


def make_materials():
    specs = {
        'white': ('Warm white printed polymer', (.78,.77,.72), 0,.55),
        'black': ('Black motor anodizing', (.014,.018,.022), .55,.27),
        'redmetal': ('Red motor anodizing', (.50,.014,.024), .7,.27),
        'copper': ('Exposed copper windings', (.65,.23,.065), .82,.25),
        'steel': ('Screw heads and shafts', (.46,.51,.55), .9,.23),
        'brass': ('Antenna connector brass', (.62,.40,.10), .82,.23),
        'prop': ('Glossy smoky graphite props', (.065,.074,.082), .48,.20),
        'foil': ('Wrinkled silver battery foil', (.57,.61,.64), .88,.32),
        'tape': ('Blue painter tape', (.015,.20,.58), 0,.8),
        'strap': ('Black hook and loop straps', (.012,.015,.02), 0,.94),
        'rubber': ('Black cable insulation', (.008,.012,.016), 0,.46),
        'redwire': ('Red cable insulation', (.55,.015,.020), 0,.4),
        'yellow': ('Yellow phase wires', (.82,.60,.018), 0,.4),
        'teal': ('Turquoise phase wires', (.006,.42,.39), 0,.38),
        'tie': ('White nylon cable ties', (.85,.85,.78), 0,.45),
        'pcb': ('Green circuit board', (.018,.11,.065), .12,.57),
        'chip': ('Electronic chip packages', (.016,.018,.023), .05,.55),
        'label': ('Printed pale lettering', (.80,.81,.74), 0,.65),
        'tan': ('Tan retaining rubber band', (.49,.35,.19), 0,.65),
        'endwrap': ('Dark woven battery end tape', (.035,.040,.043), .12,.65),
        'amber': ('Yellow power connector housing', (.82,.40,.02), 0,.43),
        'glass': ('Blue black camera lens', (.012,.038,.060), .38,.10),
        'pupil': ('Camera lens central aperture', (.003,.004,.008), .05,.16),
    }
    for key, (name,color,metal,rough) in specs.items():
        MAT[key], shader = material(name, color, metal, rough)
        if key == 'glass':
            socket = shader.inputs.get('Transmission Weight') or shader.inputs.get('Transmission')
            if socket is not None:
                socket.default_value = .18
            shader.inputs['IOR'].default_value = 1.46

    _, plastic_bump = noise_surface(MAT['white'], 125, .06, .2)
    nodes = MAT['white'].node_tree.nodes
    links = MAT['white'].node_tree.links
    wave = nodes.new('ShaderNodeTexWave')
    wave.wave_type = 'BANDS'
    wave.bands_direction = 'Z'
    # Object coordinates are metres; about 0.2 mm printed-layer spacing.
    wave.inputs['Scale'].default_value = 820 / SIZE_MULTIPLIER
    wave.inputs['Distortion'].default_value = .15
    layer_bump = nodes.new('ShaderNodeBump')
    layer_bump.inputs['Strength'].default_value = .17
    layer_bump.inputs['Distance'].default_value = .025 * MM
    links.new(wave.outputs['Color'], layer_bump.inputs['Height'])
    links.new(plastic_bump.outputs['Normal'], layer_bump.inputs['Normal'])
    shader = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
    links.new(layer_bump.outputs['Normal'], shader.inputs['Normal'])
    noise_surface(MAT['foil'], 22, .16, .42)
    noise_surface(MAT['tape'], 160, .07, .32)
    noise_surface(MAT['strap'], 210, .11, .6)
    noise_surface(MAT['prop'], 170, .014, .12)
    noise_surface(MAT['endwrap'], 140, .06, .3)


# --------------------------- HARDWARE / FRAME ----------------------------
def screw(name, x, y, surface_z, radius=2.7, protruding=False):
    cylinder(name + " washer", (x,y,surface_z+.32), radius+1, .65, MAT['steel'], edge=.12)
    head = cylinder(name + " socket head", (x,y,surface_z+1.6), radius, 2.5,
                    MAT['steel'], edge=0)
    socket = cylinder("temporary hex recess", (x,y,surface_z+2.65), radius*.48,
                      1.15, None, vertices=6, edge=0)
    boolean(head, socket)
    bevel(head, .16, 2)
    if protruding:
        cylinder(name + " black nut", (x,y,surface_z+1.6), radius+1.1,
                 2.4, MAT['black'], vertices=6)
        cylinder(name + " exposed thread", (x,y,surface_z+4), 1.5,
                 4, MAT['steel'], edge=.05)
        for dz in (-1.3,-.6,.1,.8):
            torus(name + " thread ridge", (x,y,surface_z+4+dz), 1.5,.12,MAT['steel'])


def make_frame():
    group("01 | white printed frame and fasteners")
    lower = box("Lower electronics deck", (0,0,6), (83,165,4.5), MAT['white'], 0)
    bevel(lower, 2.5, 4)
    upper = box("Upper deck with integral X arms", (0,0,30), (86,177,5.5), MAT['white'], 0)
    for sx in (-1,1):
        for sy in (-1,1):
            a = Vector((sx*30,sy*55,30))
            b = Vector((sx*MOTOR_X,sy*MOTOR_Y,30))
            direction = b-a
            arm = box("temporary solid arm", (a+b)/2,
                      (direction.length+12,23,5.5), None, 0,
                      math.atan2(direction.y,direction.x))
            boolean(upper, arm, 'UNION')
            pad = cylinder("temporary motor pad", b, 18.2,5.5,None,edge=0)
            boolean(upper,pad,'UNION')
            hole_center = a.lerp(b,.63)
            cut = cylinder("temporary arm lightening hole", hole_center, 4.0,12,None,edge=0)
            boolean(upper,cut)
            for dx,dy in ((-8,-8),(8,-8),(-8,8),(8,8)):
                cut = cylinder("temporary motor screw hole", (b.x+dx,b.y+dy,30),
                               1.55,12,None,vertices=24,edge=0)
                boolean(upper,cut)
    # Small deck holes appear near the camera and rear mast in the photos.
    for x in (-31,31):
        for y in (-70,70):
            boolean(upper,cylinder("temporary deck hole",(x,y,30),3.1,12,None,edge=0))
    bevel(upper,.75,3)
    for x in (-33,33):
        for y in (-60,60):
            cylinder("Printed deck spacer",(x,y,18),5.4,19.5,MAT['white'],edge=.6)
            screw("Deck M3 fastener",x,y,32.75,protruding=True)
            cylinder("Short underside screw foot",(x,y,1.8),3.4,3.5,MAT['steel'],vertices=6)
    for y in (-44,44):
        for x in (-24,24):
            box("Battery anti-slip pad",(x,y,34.5),(6,20,3.2),MAT['rubber'],.65)
    for sx in (-1,1):
        for sy in (-1,1):
            cylinder("Motor mounting underside screw",(sx*MOTOR_X,sy*MOTOR_Y,26.4),
                     3.3,2.0,MAT['steel'])


def make_electronics():
    group("02 | exposed flight electronics")
    box("Power distribution PCB",(0,3,11),(48,52,1.6),MAT['pcb'],.5)
    box("Flight controller PCB",(0,-5,21),(36,36,1.4),MAT['pcb'],.5)
    for x in (-15,15):
        for y in (-20,10):
            cylinder("Controller vibration isolator",(x,y,16.5),2.1,8,MAT['rubber'])
    box("Flight controller processor",(0,-4,22.3),(10,10,1.1),MAT['chip'],.2)
    for i in range(9):
        x, y = RNG.uniform(-19,19), RNG.uniform(-17,23)
        box("PCB surface component %02d" % i,(x,y,12.4),
            (RNG.uniform(2,4),RNG.uniform(2,5),1.2),MAT['chip'],.1)
    box("USB port metal shield",(0,-23.6,22.5),(7.4,5.5,3),MAT['steel'],.2)
    box("USB port dark opening",(0,-26.45,22.5),(5.2,.35,1.7),MAT['chip'],.1)
    for sx in (-1,1):
        for i in range(9):
            cylinder("Gold header pin",(sx*16.3,-16+i*3.1,23.1),.55,3.1,MAT['brass'],vertices=12,edge=.06)
    cylinder("Small board capacitor",(16,18,16),3.1,8,MAT['black'])
    cylinder("Capacitor silver top",(16,18,20.2),2.8,.6,MAT['steel'])
    wire("Controller red supply",[(20,18,12),(24,9,23),(22,-15,26),(14,-21,24)],.85,MAT['redwire'])
    wire("Controller black supply",[(17,18,12),(20,7,24),(19,-15,26),(11,-21,24)],.85,MAT['rubber'])


# -------------------------- MOTORS / PROPELLERS ---------------------------
def prop_blade(name, handedness):
    # True three-dimensional pitched/cambered blade, not a flat paddle.
    stations = [(6,4.5,-.8,24),(13,8,-1.5,22),(23,13.5,-2.8,18),
                (36,17.5,-2.0,14),(48,15,0.5,11),(58,8.2,3.0,8),
                (PROP_RADIUS,.8,4.2,7)]
    verts, faces = [], []
    nr, nc = 25, 8
    for layer in (-1,1):
        for i in range(nr):
            r = 6+(PROP_RADIUS-6)*i/(nr-1)
            j = next((j for j in range(len(stations)-1)
                      if r <= stations[j+1][0]),len(stations)-2)
            a,b = stations[j],stations[j+1]
            t = (r-a[0])/(b[0]-a[0])
            chord,sweep,pitch = [a[k]+t*(b[k]-a[k]) for k in (1,2,3)]
            pitch = math.radians(pitch)*handedness
            thickness = .72-.36*i/(nr-1)
            for k in range(nc):
                u = k/(nc-1)
                yc = (u-.5)*chord
                z = yc*math.sin(pitch)+.65*math.sin(math.pi*u)+layer*thickness/2
                verts.append((r,sweep*handedness+yc*math.cos(pitch),z))
    per_layer = nr*nc
    for layer in (0,1):
        off = layer*per_layer
        for i in range(nr-1):
            for k in range(nc-1):
                a = off+i*nc+k
                faces.append((a,a+1,a+nc+1,a+nc))
    for i in range(nr-1):
        for k in (0,nc-1):
            a,b = i*nc+k,(i+1)*nc+k
            faces.append((a,b,b+per_layer,a+per_layer))
    for i in (0,nr-1):
        for k in range(nc-1):
            a = i*nc+k
            faces.append((a,a+1,a+1+per_layer,a+per_layer))
    return mesh_object(name,verts,faces,MAT['prop'],smooth=True)


def make_motor(sx,sy,index):
    label = ("Front" if sy < 0 else "Rear") + (" right" if sx > 0 else " left")
    group("03.%d | %s motor and three-blade rotor" % (index,label))
    x,y = sx*MOTOR_X,sy*MOTOR_Y
    base = cylinder(label+" red slotted motor base",(x,y,36.1),14.1,7.2,MAT['redmetal'],edge=0)
    for i in range(6):
        ang = 2*math.pi*i/6
        cut = box("temporary motor base vent",(x+13*math.cos(ang),y+13*math.sin(ang),36.3),
                  (4,6,2.8),None,0,ang)
        boolean(base,cut)
    bevel(base,.35,2)
    cylinder(label+" central stator",(x,y,48),8.8,17,MAT['black'])
    for i in range(12):
        a = 2*math.pi*i/12
        c = (x+9.6*math.cos(a),y+9.6*math.sin(a),52.2)
        for dz in (-1.2,0,1.2):
            torus(label+" visible copper winding",(c[0],c[1],c[2]+dz),
                  2.15,.47,MAT['copper'],axis=(math.cos(a),math.sin(a),0))
    bell = cylinder(label+" ventilated black motor bell",(x,y,50.5),14.1,20.4,MAT['black'],edge=0)
    boolean(bell,cylinder("temporary hollow bell",(x,y,51.4),12.1,19.8,None,edge=0))
    for i in range(8):
        a = 2*math.pi*i/8
        boolean(bell,box("temporary bell cooling window",(x+13.3*math.cos(a),y+13.3*math.sin(a),55),
                         (4.5,6.1,6.3),None,0,a))
    bevel(bell,.23,2)
    cylinder(label+" top bearing",(x,y,61),5.8,3,MAT['black'])
    cylinder(label+" steel prop shaft",(x,y,64),2.5,10,MAT['steel'])
    text(label+" motor marking","RS 2205",(x,y-14.22,46.5),3.0,MAT['label'],
         (math.pi/2,0,0))
    pivot = empty(label+" | ROTOR PIVOT",(x,y,64))
    pivot["blade_count"] = 3
    pivot["rotation_direction"] = "CW" if sx*sy > 0 else "CCW"
    pivot["prop_diameter_mm"] = PROP_RADIUS*2
    hub = cylinder(label+" propeller central hub",(x,y,64),6.4,3,MAT['prop'])
    parent_preserving(hub,pivot)
    hand = 1 if sx*sy > 0 else -1
    for blade_index in range(3):
        obj = prop_blade(label+" prop blade %d" % (blade_index+1),hand)
        obj.parent = pivot
        obj.location = (0,0,0)
        obj.rotation_euler.z = blade_index*2*math.pi/3
    nut = cylinder(label+" prop locknut",(x,y,68.3),4.45,5.4,MAT['steel'],vertices=6,edge=0)
    boolean(nut,cylinder("temporary shaft socket",(x,y,70.7),2.25,2,None,edge=0))
    bevel(nut,.3,2)
    parent_preserving(nut,pivot)
    washer = cylinder(label+" prop nut washer",(x,y,65.7),5.4,.75,MAT['steel'])
    parent_preserving(washer,pivot)
    pivot.rotation_euler.z = math.radians((17,49,82,8)[index-1])


# ----------------------------- STRAPS / PACK -----------------------------
def rounded_path(xhalf,zbottom,ztop,radius,y=0):
    points = []
    corners = ((xhalf-radius,ztop-radius,0),
               (-xhalf+radius,ztop-radius,90),
               (-xhalf+radius,zbottom+radius,180),
               (xhalf-radius,zbottom+radius,270))
    for cx,cz,start in corners:
        for i in range(7):
            angle = math.radians(start+90*i/6)
            points.append((cx+radius*math.cos(angle),y,cz+radius*math.sin(angle)))
    return points


def band(name,points,width,thickness,material,width_axis=(0,1,0)):
    # Rectangular-section ribbon swept around a closed path.
    verts,faces = [],[]
    axis = Vector(width_axis).normalized()
    for i,p in enumerate(points):
        p = Vector(p)
        tangent = (Vector(points[(i+1)%len(points)])-Vector(points[i-1])).normalized()
        normal = tangent.cross(axis).normalized()
        for side,depth in ((-1,-1),(1,-1),(1,1),(-1,1)):
            verts.append(p+axis*side*width/2+normal*depth*thickness/2)
    for i in range(len(points)):
        nxt = (i+1)%len(points)
        for j in range(4):
            faces.append((4*i+j,4*i+(j+1)%4,4*nxt+(j+1)%4,4*nxt+j))
    return mesh_object(name,verts,faces,material)


def make_battery():
    group("04 | stacked silver battery, blue tape and fabric straps")
    for i in range(4):
        box("Foil wrapped cell layer %d" % (i+1),(0,0,44+12*i),
            (52,150,11.6),MAT['foil'],2.1)
    box("Top foil wrapper",(0,0,86.2),(52,150,.8),MAT['foil'],.25)
    for sy in (-1,1):
        box("Folded foil pack end",(0,sy*72,62),(53,8,47),MAT['foil'],3.5)
        box("Dark reinforced battery end",(0,sy*76.1,62),(45,1.0,40),MAT['endwrap'],.45)
        # Visible crosshatched reinforcement on the end faces, as in the photos.
        for i in range(-10,11):
            box("Fine end tape vertical fiber",(i*2.05,sy*76.7,62),
                (.23,.12,37),MAT['label'],0)
        for i in range(10):
            box("Fine end tape cross fiber",(0,sy*76.78,44+i*4),
                (43,.12,.18),MAT['steel'],0)
        box("Worn pale label remnant",(0,sy*59,86.8),(21,16,.25),MAT['label'],.12)
    for sx in (-1,1):
        for i in range(4):
            wire("Foil side seam",[(sx*26.1,-69,39.7+i*12),
                 (sx*26.4,0,39.9+i*12),(sx*26.1,69,39.7+i*12)],
                 .16,MAT['steel'])
    band("Blue tape wrapped around battery middle",rounded_path(27.0,37.0,87.3,3.1),
         29,.38,MAT['tape'])
    flap = mesh_object("Irregular folded edge of blue tape",
        [(-27.35,-14.4,85),(-27.4,8.5,84),(-28.1,14.8,70),
         (-27.6,4.5,60),(-27.45,-2,64),(-27.45,-14.2,71)],
        [(0,1,2,3,4,5)],MAT['tape'])
    solid = flap.modifiers.new("Tape thickness",'SOLIDIFY')
    solid.thickness = .18*MM
    for y in (-44,43):
        band("Black battery securing strap",rounded_path(28,34.5,88.2,3.5,y),
             13,.9,MAT['strap'])
        box("Strap overlap on top",(0,y,89.15),(34,13,1.1),MAT['strap'],.5)
        box("Strap buckle",(28.7,y,41.5),(3.2,17,7),MAT['black'],.4)
    wire("Battery positive cable",[(12,76,46),(22,88,42),(35,112,27),(39,128,21)],1.9,MAT['redwire'])
    wire("Battery negative cable",[(5,76,45),(16,89,39),(31,111,25),(33,128,21)],1.9,MAT['rubber'])
    make_power_connector((36,135,21))
    for i in range(4):
        wire("Balance lead %d" % (i+1),[(-8+i*2,76,45),(-6+i*2,91,38),
             (8+i*2,105,31),(9+i*2,117,28)],.48,
             MAT['redwire'] if i==0 else MAT['rubber'])
    box("White four way balance connector",(12,120,28),(12,9,6),MAT['tie'],.7)
    for i in range(4):
        box("Balance connector socket",(8+i*2.7,124.65,28),(1.5,.4,2.8),MAT['chip'],.1)


def make_power_connector(center):
    x,y,z = center
    body = box("Disconnected yellow XT-style power plug",center,(16,16,9),MAT['amber'],0)
    for dx in (-4,4):
        boolean(body,cylinder("temporary connector socket",(x+dx,y+6,z),2.5,5,
                              None,axis=(0,1,0),edge=0))
        cylinder("Brass power plug contact",(x+dx,y+4,z),1.55,2.0,
                 MAT['brass'],axis=(0,1,0))
    bevel(body,.8,3)
    box("Power plug grip ridge",(x,y-5,z+4.8),(17,2,1.5),MAT['amber'],.25)


# --------------------------- ARM ESCs / WIRING ----------------------------
def arm_point(sx,sy,t,lateral=0,z=35):
    a = Vector((sx*34,sy*55,0))
    b = Vector((sx*MOTOR_X,sy*MOTOR_Y,0))
    u = (b-a).normalized()
    n = Vector((-u.y,u.x,0))
    point = a.lerp(b,t)+n*lateral
    point.z = z
    return point


def make_arm_wiring(sx,sy):
    name = ("Front" if sy<0 else "Rear")+(" right" if sx>0 else " left")
    group("05 | "+name+" ESC, cable loops and zip ties")
    c = arm_point(sx,sy,.43,0,36)
    u = (arm_point(sx,sy,1)-arm_point(sx,sy,0)).normalized()
    u.z = 0
    n = Vector((-u.y,u.x,0))
    angle = math.atan2(u.y,u.x)
    box(name+" ESC PCB",c,(27,11.5,1.7),MAT['pcb'],.3,angle)
    box(name+" ESC silver heat spreader",c+Vector((0,0,1.4)),
        (25,10.2,1.2),MAT['foil'],.35,angle)
    for t in (-7,0,7):
        box(name+" ESC MOSFET",c+u*t+Vector((0,0,2.2)),
            (4.3,5.4,1.3),MAT['chip'],.2,angle)
    text(name+" ESC label","ESC 20A",c+Vector((0,0,3.0)),2.5,MAT['label'],(0,0,angle))
    for j,(key,offset) in enumerate((('yellow',-3.8),('teal',0),('rubber',3.8))):
        # Deliberately slightly untidy, visible loops matching the handmade build.
        points = [arm_point(sx,sy,.56,offset,38),arm_point(sx,sy,.70,offset+7,42),
                  arm_point(sx,sy,.81,offset+8,31),arm_point(sx,sy,.56,offset+11,26),
                  arm_point(sx,sy,.48,offset+6,31),arm_point(sx,sy,.84,offset,37),
                  arm_point(sx,sy,.97,offset,40)]
        wire(name+" "+key+" motor phase loop",points,1.05,MAT[key])
        solder = arm_point(sx,sy,.58,offset,37.5)
        sphere(name+" solder joint",solder,(2.2,2.2,1.5),MAT['steel'])
    for j,key in enumerate(('redwire','rubber')):
        offset = -2+j*4
        wire(name+" ESC supply "+key,
            [arm_point(sx,sy,.28,offset,37),arm_point(sx,sy,.07,offset,36),
             (sx*31,sy*42,27),(sx*26,sy*20,18)],1.05,MAT[key])
    wire(name+" thin white control lead",
         [arm_point(sx,sy,.25,4,37),(sx*32,sy*45,29),(sx*19,sy*14,23)],.46,MAT['tie'])
    for t in (.32,.70):
        c0 = arm_point(sx,sy,t,0,0)
        path = rounded_path(11,26.5,44.3,3.0)
        points = [c0+n*p[0]+Vector((0,0,p[2])) for p in path]
        band(name+" white cable tie",points,2.1,.65,MAT['tie'],u)
        lock = c0+n*10.8+Vector((0,0,42.4))
        box(name+" cable tie locking head",lock,(3.8,4.1,3.3),MAT['tie'],.4,angle)
        rod(name+" cable tie clipped tail",lock,lock+n*9+Vector((0,0,-7)),.62,MAT['tie'])


# ------------------------ CAMERA / FRONT ANTENNA -------------------------
def make_camera():
    group("06 | front printed FPV camera pedestal and adjustable head")
    box("Camera mounting foot",(0,-78,35),(54,35,4.5),MAT['white'],2)
    post = tapered_box("Tapered slotted camera pedestal",(0,-80),37,95,
                       (36,25),(25,17),MAT['white'])
    for x in (-7.5,7.5):
        boolean(post,box("temporary camera pedestal slot",(x,-80,65),
                         (4.2,40,29),None,0))
    bevel(post,.8,3)
    for x in (-21,21):
        for y in (-88,-69):
            screw("Camera foot screw",x,y,37.25)
    rod("Camera transverse adjustment bolt",(-20,-80,82),(20,-80,82),2,MAT['steel'])
    for sx in (-1,1):
        cylinder("Camera pivot nut",(sx*20,-80,82),4.5,3.2,MAT['black'],
                 axis=(1,0,0),vertices=6)
    pivot = empty("Camera head | TILT PIVOT",(0,-80,95))
    pivot["tilt_degrees"] = CAMERA_TILT_DEGREES
    before = set(GROUP.objects)
    box("U bracket lower shelf",(0,-85,97),(43,20,5.5),MAT['white'],.8)
    for sx in (-1,1):
        box("Tall white camera bracket cheek",(sx*18,-85,118),(7.4,19,42),MAT['white'],.6)
    box("Black FPV camera housing",(0,-88,111),(25,18,21),MAT['chip'],2.0)
    cylinder("FPV camera lens barrel",(0,-100,111),8.6,10,MAT['black'],axis=(0,-1,0))
    torus("Lens front retaining ring",(0,-105.3,111),7.3,.65,MAT['black'],axis=(0,-1,0))
    cylinder("Lens optical glass",(0,-105.7,111),6.7,.75,MAT['glass'],axis=(0,-1,0),edge=.15)
    cylinder("Lens visible central aperture",(0,-106.15,111),3.0,.18,MAT['pupil'],axis=(0,-1,0),edge=.04)
    torus("Inner optical ring",(0,-106.27,111),4.5,.16,MAT['glass'],axis=(0,-1,0))
    sphere("Lens tiny reflected highlight",(-1.9,-106.35,113.4),(.7,.12,.7),MAT['label'])
    for sx in (-1,1):
        cylinder("Camera cheek mounting screw",(sx*14.7,-88,111),2.4,2,
                 MAT['steel'],axis=(1,0,0),vertices=6)
    # Exposed transmitter and seven-segment display on the bracket's rear.
    box("Vertical FPV transmitter PCB",(0,-76,124),(18,2.2,24),MAT['pcb'],.3)
    box("Transmitter shield",(0,-74.4,123),(12,1,14),MAT['steel'],.2)
    box("Transmitter dark channel display",(0,-73.7,129),(7,.4,9),MAT['chip'],.1)
    for dx,dz,w,h in ((0,3,3.3,.5),(0,0,3.3,.5),(0,-3,3.3,.5),
                       (-1.8,1.5,.5,2.4),(1.8,1.5,.5,2.4),
                       (-1.8,-1.5,.5,2.4),(1.8,-1.5,.5,2.4)):
        box("Unlit display segment",(dx,-73.42,129+dz),(w,.12,h),MAT['label'],.03)
    for sx in (-1,1):
        for i in range(5):
            sphere("Transmitter solder pad",(sx*7.4,-74.75,116+i*4),(1.0,.4,1.0),MAT['brass'])
    rod("Short antenna connector",(0,-79,136),(-1,-80,142),2.05,MAT['brass'])
    rod("Short antenna lower sleeve",(-1,-80,141),(-3.4,-81,154),2.4,MAT['rubber'])
    rod("Short antenna upper whip",(-3.4,-81,153),(-6.6,-82.3,174),1.2,MAT['rubber'])
    wire("Camera tan retaining band front",[(-12,-97,98),(-15,-104,109),
         (-12,-99,123),(0,-83,134),(9,-77,132),(11,-76,117),
         (10,-87,100),(-3,-96,96)],1.4,MAT['tan'],cyclic=True)
    wire("Camera second tan retaining strand",[(-10,-98,98),(-13,-105,109),
         (-10,-100,123),(2,-83,134),(10,-76,131),(12,-77,116),
         (9,-88,99),(-2,-97,96)],.85,MAT['tan'],cyclic=True)
    for obj in set(GROUP.objects)-before:
        parent_preserving(obj,pivot)
    pivot.rotation_euler.x = math.radians(CAMERA_TILT_DEGREES)
    wire("Camera power red wire",[(4,-74,119),(12,-68,111),(19,-64,95),
         (24,-55,88),(29,-44,39),(24,-28,22)],.72,MAT['redwire'])
    wire("Camera power black wire",[(0,-74,117),(9,-67,109),(16,-63,94),
         (21,-54,88),(26,-43,39),(21,-28,22)],.72,MAT['rubber'])
    box("Camera white inline connector",(22,-52,90),(7,9,5),MAT['tie'],.45)


# --------------------------- REAR ANTENNA MAST ---------------------------
def make_rear_antenna():
    group("07 | tall rear antenna and tapered white printed mount")
    cylinder("Rear antenna mast base",(0,83,36),13,6,MAT['white'],edge=.7)
    cylinder("Tall white rear antenna support",(0,83,79),7.5,82,MAT['white'],edge=.8)
    for z in (55,87):
        boolean_tool = box("temporary mast cable slot",(0,83,z),(5,24,7),None,0)
        mast = next(o for o in GROUP.objects if o.name.startswith("Tall white rear antenna support"))
        boolean(mast,boolean_tool)
    # Hollow tapered printed shroud: broad at its bottom, narrow at the SMA.
    bpy.ops.mesh.primitive_cone_add(vertices=64,radius1=24*MM,radius2=9*MM,
                                   depth=36*MM,location=tuple(vmm((0,83,135))))
    shroud = bpy.context.object
    shroud.name = "White hollow tapered antenna shroud"
    register(shroud,MAT['white'])
    bpy.ops.mesh.primitive_cone_add(vertices=64,radius1=20.7*MM,radius2=6.6*MM,
                                   depth=33*MM,location=tuple(vmm((0,83,132.8))))
    cutter = bpy.context.object
    cutter.name = "temporary hollow shroud interior"
    register(cutter)
    boolean(shroud,cutter)
    boolean(shroud,box("temporary rear coax entry slot",(0,102,122),(6,20,13),None,0))
    for sx in (-1,1):
        boolean(shroud,box("temporary shroud screw recess",(sx*16,83,129),(12,6,11),None,0))
        cylinder("Antenna shroud side screw",(sx*15,83,126.8),2.8,2.5,
                 MAT['steel'],axis=(sx,0,.35))
    bevel(shroud,.6,3)
    cylinder("SMA antenna mounting washer",(0,83,153.5),7.1,1.8,MAT['steel'])
    cylinder("SMA bulkhead threaded base",(0,83,157),4.5,6,MAT['brass'])
    cylinder("SMA connector hex coupling",(0,83,163.5),5.7,8,MAT['brass'],vertices=6,edge=.25)
    cylinder("SMA connector polished collar",(0,83,169.0),4.9,3.2,MAT['steel'])
    cylinder("Long black rear antenna rubber body",(0,83,194),4.7,47,MAT['rubber'],edge=.8)
    for z in (211,213,215):
        torus("Rear antenna moulded grip ring",(0,83,z),4.65,.4,MAT['rubber'])
    sphere("Rear antenna rounded cap",(0,83,218),(9.4,9.4,9.5),MAT['rubber'])
    wire("Copper coloured rear coax cable",[(0,102,122),(9,100,106),(13,96,84),
         (12,95,61),(17,98,39),(7,103,25),(-9,76,17)],1.05,MAT['copper'])
    # Two narrow white ties keep the coax close to the support tube.
    for z in (63,94):
        torus("White mast coax cable tie",(0,83,z),8.7,.65,MAT['tie'])
        box("Mast cable tie latch",(8.8,88,z),(3.2,4.2,3.3),MAT['tie'],.3)
    for x in (-9,9):
        screw("Rear mast base screw",x,83,39)


# --------------------------- MODEL-ONLY FINISH ----------------------------
def finish_scene():
    # Remove the previous version's world only when no other scene uses it.
    # The generated collection (including its old floor/lights/cameras) was
    # already replaced by begin_scene(). No unrelated objects are deleted.
    world = bpy.data.worlds.get("D2 | neutral studio world")
    if world is not None:
        if SCENE.world == world:
            SCENE.world = None
        if world.users == 0:
            bpy.data.worlds.remove(world)

    SCENE["notes"] = "Photographic approximation; no dimensions were supplied. Front = -Y."
    SCENE["usage"] = "Model only. Materials retained. Rotate rotor/camera pivots; move aircraft root."
    active(ROOT)
    # Show colors using built-in material-preview illumination. This does NOT
    # add lights, camera objects, a floor, or an environment object to the model.
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces.active
                space.clip_start = .001*SIZE_MULTIPLIER
                space.clip_end = 100*SIZE_MULTIPLIER
                space.shading.type = 'MATERIAL'
                space.shading.use_scene_world = False
                space.shading.use_scene_lights = False
                # Keep editable pivots, but hide helper axes and the dotted
                # parent-child relationship guides. Actual drone wires stay.
                space.overlay.show_extras = False
                space.overlay.show_relationship_lines = False
                region = space.region_3d
                region.view_perspective = 'PERSP'
                region.view_location = vmm((0,0,87))
                region.view_distance = .62*SIZE_MULTIPLIER
                region.view_rotation = Vector((425,-565,280)).to_track_quat('Z','Y')
    if SAVE_BLEND:
        if os.path.exists(BLEND_PATH):
            print("Not overwriting an existing .blend:",BLEND_PATH)
        else:
            os.makedirs(os.path.dirname(BLEND_PATH),exist_ok=True)
            bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print("DRONE2 complete: colored aircraft only, %d editable objects." % len(TOP.all_objects))
    print("No floor, lights, viewing cameras, or reference planes were created.")
    print("Front is -Y. Dimensions are estimates; this is not a flight/engineering model.")
    print("Use File > Save As to save the generated Blender project as drone2.blend.")


def main():
    if SIZE_MULTIPLIER <= 0:
        raise ValueError("SIZE_MULTIPLIER must be positive")
    if PROP_RADIUS <= 58:
        raise ValueError("This blade profile requires PROP_RADIUS greater than 58 mm")
    begin_scene()
    make_materials()
    make_frame()
    make_electronics()
    index = 0
    for sy in (-1,1):
        for sx in (-1,1):
            index += 1
            make_motor(sx,sy,index)
    make_battery()
    for sy in (-1,1):
        for sx in (-1,1):
            make_arm_wiring(sx,sy)
    make_camera()
    make_rear_antenna()
    finish_scene()


if __name__ == '__main__':
    main()
