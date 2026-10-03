"""4690 Deer Creek Boulevard — exterior reference reconstruction.
Run in Blender's Scripting workspace (Text > Open > Run Script).
No external packages or image files required. Designed for Blender 4.x/5.x.
Only objects in the generated H4690 collection are replaced on rerun.

REFERENCE / ACCURACY NOTES
Floorplan coordinates were manually traced from the supplied 1440px image.
Scale: approximately 207 image pixels = 13 feet. Front = negative world Y.
The plan is not a survey; wall heights, roof layout/pitch, window elevations,
and finishes are photo-based estimates. Optional rear pool bathroom is included;
its existence is not confirmed by the photographs.
Roof intersections are overlapping hip volumes, not construction-ready framing.
House geometry and materials only, including the porch and covered lanai.
No pool, spa, screen enclosure, landscaping, driveway, or walkway.
No cameras, lights, world setup, render settings, or viewport configuration.
No interior partitions or automatic .blend save. Coordinates are in meters.
Existing unrelated scene objects and presentation settings are left untouched.
"""
import math
import random
import bpy
import bmesh
from mathutils import Vector

# -------------------------- editable settings --------------------------
SCALE = 13.0 * 0.3048 / 207.0
WALL_HEIGHT = 3.20
WALL_THICKNESS = 0.22
ROOF_PITCH = 0.36
ROOF_OVERHANG_PX = 24
MAKE_ROOF_TILES = True
INCLUDE_POOL_BATH = True
PREFIX = 'H4690'
random.seed(4690)


def xy(p):
    return ((p[0] - 710) * SCALE, (1080 - p[1]) * SCALE)


def pt(p, z=0):
    return (*xy(p), z)


# Do not clear the user's scene or remove unrelated collections.
if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
old = bpy.data.collections.get(PREFIX)
if old:
    for obj in list(old.all_objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for child in list(old.children):
        bpy.data.collections.remove(child)
    bpy.data.collections.remove(old)
root = bpy.data.collections.new(PREFIX)
bpy.context.scene.collection.children.link(root)
groups = {}
for name in ['Shell', 'Openings', 'Trim', 'Roofs']:
    col = bpy.data.collections.new(PREFIX + '_' + name)
    root.children.link(col)
    groups[name] = col


def material(name, color, roughness=0.6, noise=0):
    m = bpy.data.materials.get(PREFIX + '_' + name)
    if m is None:
        m = bpy.data.materials.new(PREFIX + '_' + name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    n = m.node_tree.nodes
    n.clear()
    output = n.new('ShaderNodeOutputMaterial')
    shader = n.new('ShaderNodeBsdfPrincipled')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = roughness
    m.node_tree.links.new(shader.outputs['BSDF'], output.inputs['Surface'])
    if noise:
        tex = n.new('ShaderNodeTexNoise')
        tex.inputs['Scale'].default_value = 95
        bump = n.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = 0.28
        bump.inputs['Distance'].default_value = noise
        m.node_tree.links.new(tex.outputs['Fac'], bump.inputs['Height'])
        m.node_tree.links.new(bump.outputs['Normal'], shader.inputs['Normal'])
    return m


stucco = material('Warm ivory stucco', (0.73, 0.66, 0.49), noise=0.014)
trim = material('Cream trim and aluminum', (0.91, 0.89, 0.78), 0.4)
roofmat = material('Silver ivory concrete tile', (0.63, 0.66, 0.63), noise=0.009)
tilemats = [material('Tile variation %02d' % i, (0.57+i*.019, 0.60+i*.018, 0.57+i*.019)) for i in range(6)]
glass = material('Blue green glazing', (0.09, 0.20, 0.21), 0.16)
glass.node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value = 0.30
shadow = material('Dark reveal', (0.035, 0.045, 0.038))
pavers = material('Terracotta stone paving', (0.53, 0.40, 0.30), noise=0.016)
coping = material('Pale pool coping', (0.83, 0.82, 0.68), noise=0.009)
concrete = material('Garage seam finish', (.63, .60, .52), noise=.016)


def mesh(name, verts, faces, mat, group='Shell'):
    data = bpy.data.meshes.new(PREFIX + '_' + name)
    data.from_pydata(verts, [], faces)
    data.update()
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(data)
    bm.free()
    obj = bpy.data.objects.new(name, data)
    groups[group].objects.link(obj)
    if mat:
        data.materials.append(mat)
    return obj


def box(name, center, size, mat, group='Shell', angle=0):
    x, y, z = (s / 2 for s in size)
    verts = [(a*x, b*y, c*z) for a, b, c in
             [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
              (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    ob = mesh(name, verts, [(0,3,2,1),(4,5,6,7),(0,1,5,4),
                          (1,2,6,5),(2,3,7,6),(3,0,4,7)], mat, group)
    ob.location = center
    ob.rotation_euler.z = angle
    return ob


def prism(name, polygon, bottom, top, mat, group='Shell'):
    n = len(polygon)
    vs = [pt(p, bottom) for p in polygon] + [pt(p, top) for p in polygon]
    fs = [tuple(reversed(range(n))), tuple(range(n, 2*n))]
    fs += [(i, (i+1)%n, (i+1)%n+n, i+n) for i in range(n)]
    return mesh(name, vs, fs, mat, group)


def slab(name, bounds, bottom, top, mat, group='Shell'):
    a,b,c,d = bounds
    return prism(name, [(a,b),(c,b),(c,d),(a,d)], bottom, top, mat, group)


def beam(name, a, b, width, mat=trim, group='Trim', depth=None):
    a, b = Vector(a), Vector(b)
    ob = box(name, (a+b)/2, (width, depth or width, (b-a).length), mat, group)
    ob.rotation_euler = (b-a).to_track_quat('Z', 'Y').to_euler()
    return ob


def difference(ob, cutter):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    mod = ob.modifiers.new('Actual opening', 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.solver = 'EXACT'
    mod.object = cutter
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter, do_unlink=True)


# Clockwise image-space outline, including entry recess and angled lanai walls.
outline = [(160,216),(300,216),(300,84),(446,84),(446,188),
           (607,188),(607,440),(712,540),(972,540),(1100,414),
           (1257,414),(1257,740),(1280,740),(1280,956),
           (1255,956),(1255,1082),(1195,1082),(1195,1110),
           (1085,1110),(1085,1080),(1032,1080),(1032,1020),
           (836,1020),(836,902),(708,902),(708,990),(524,990),
           (524,1240),(186,1240),(186,1067),(160,1067)]
if not INCLUDE_POOL_BATH:
    outline = [(160,216),(446,216),(446,188)] + outline[6:]
prism('Footprint foundation', outline, -.22, 0, coping)
walls = []
for i, a in enumerate(outline):
    b = outline[(i+1) % len(outline)]
    av, bv = Vector(xy(a)), Vector(xy(b))
    mid = (av+bv)/2
    ob = box('Exterior wall %02d' % i, (*mid, WALL_HEIGHT/2),
             ((bv-av).length + .04, WALL_THICKNESS, WALL_HEIGHT),
             stucco, angle=math.atan2(bv.y-av.y, bv.x-av.x))
    walls.append((a,b,ob))


def nearest_wall(p):
    p = Vector(xy(p))
    best = None
    for a,b,ob in walls:
        a,b = Vector(xy(a)), Vector(xy(b))
        ab = b-a
        t = max(0, min(1, (p-a).dot(ab)/ab.length_squared))
        dist = (p-(a+t*ab)).length
        if best is None or dist < best[0]:
            best = (dist, ob, ab.normalized())
    return best[1], best[2]


def arch_shape(width, bottom, spring, rise, segments=28):
    return [(-width/2,bottom),(width/2,bottom)] + [
        (width/2*math.cos(math.pi*i/segments),
         spring + rise*math.sin(math.pi*i/segments)) for i in range(segments+1)]


def facade_prism(name, p, tangent, profile, depth, offset, mat, group='Openings'):
    u = Vector((tangent[0], tangent[1], 0))
    n = Vector((-u.y,u.x,0))
    base = Vector(pt(p))
    verts = [tuple(base+u*x+n*(offset+d)+Vector((0,0,z)))
             for d in (-depth/2, depth/2) for x,z in profile]
    k = len(profile)
    faces = [tuple(reversed(range(k))),tuple(range(k,2*k))]
    faces += [(i,(i+1)%k,(i+1)%k+k,i+k) for i in range(k)]
    return mesh(name, verts, faces, mat, group)


def opening(name, p, width, bottom=.65, spring=2.35, rise=.38, door=False):
    wall, u2 = nearest_wall(p)
    profile = arch_shape(width,bottom,spring,rise) if rise else [
        (-width/2,bottom),(width/2,bottom),(width/2,spring),(-width/2,spring)]
    cut = facade_prism('Temporary opening',p,u2,profile,.65,0,None)
    difference(wall,cut)
    facade_prism(name+' glazing',p,u2,profile,.028,0,glass)
    u = Vector((*u2,0)); n = Vector((-u.y,u.x,0)); base = Vector(pt(p))
    def q(x,z,offset):
        return base+u*x+n*offset+Vector((0,0,z))
    # Trim on both faces avoids dependence on polygon winding.
    for offset in (-.145,.145):
        for i,(x,z) in enumerate(profile):
            xx,zz = profile[(i+1)%len(profile)]
            beam(name+' surround',q(x,z,offset),q(xx,zz,offset),.075)
        beam(name+' center mullion',q(0,bottom,offset),q(0,spring+rise,offset),.043)
        beam(name+' transom',q(-width/2,spring,offset),q(width/2,spring,offset),.045)
        if not door:
            for z in (bottom+(spring-bottom)*.40,bottom+(spring-bottom)*.75):
                beam(name+' horizontal muntin',q(-width/2,z,offset),q(width/2,z,offset),.027)
            for x in (-width/4,width/4):
                beam(name+' vertical muntin',q(x,bottom,offset),q(x,spring,offset),.027)
        if rise:
            for angle in (math.pi/4, math.pi/2, 3*math.pi/4):
                beam(name+' fanlight',q(0,spring,offset),
                     q(width/2*math.cos(angle),spring+rise*math.sin(angle),offset),.025)


def double_entry(p, width=1.74, bottom=.055, spring=2.22, rise=.54):
    # Two solid leaves, not the continuous glazing used for windows/sliders.
    name = 'Recessed double entry'
    wall, u2 = nearest_wall(p)
    profile = arch_shape(width,bottom,spring,rise)
    difference(wall,facade_prism('Entry cutter',p,u2,profile,.65,0,None))
    door_finish = material('Entry painted warm cream', (.68, .61, .46), .38)
    panel_finish = material('Entry raised panels', (.75, .68, .53), .40)
    hardware = material('Entry aged bronze hardware', (.16, .105, .045), .26)
    hardware.node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value = .75
    u = Vector((*u2,0)); n = Vector((-u.y,u.x,0)); base = Vector(pt(p))
    def q(x,z,offset):
        return base+u*x+n*offset+Vector((0,0,z))
    def rectangle(x0,x1,z0,z1):
        return [(x0,z0),(x1,z0),(x1,z1),(x0,z1)]

    # Dark backing makes the narrow perimeter and meeting gaps legible.
    facade_prism(name+' reveal',p,u2,
                 rectangle(-width/2,width/2,bottom,spring),.018,0,shadow)
    for side, label in [(-1,'left'),(1,'right')]:
        x0, x1 = (-width/2+.055,-.008) if side < 0 else (.008,width/2-.055)
        z0, z1 = bottom+.012, spring-.045
        facade_prism(name+' '+label+' solid door',p,u2,
                     rectangle(x0,x1,z0,z1),.09,0,door_finish)
        # Raised rectangular panels and hardware on both faces, matching the
        # existing surround convention without assuming wall winding.
        for offset in (-.055,.055):
            face = -1 if offset < 0 else 1
            for low, high in [(z0+.16,z0+.69),(z0+.84,z1-.16)]:
                panel = rectangle(x0+.12,x1-.12,low,high)
                facade_prism(name+' '+label+' raised panel',p,u2,
                             panel,.018,offset,panel_finish)
                for i,(x,z) in enumerate(panel):
                    xx,zz = panel[(i+1)%len(panel)]
                    beam(name+' panel molding',q(x,z,offset+face*.013),
                         q(xx,zz,offset+face*.013),.022,trim,'Openings')
            handle_x = -.12 if side < 0 else .12
            facade_prism(name+' '+label+' handle backplate',p,u2,
                         rectangle(handle_x-.026,handle_x+.026,.91,1.21),
                         .018,face*.065,hardware)
            for z in (.96,1.16):
                beam(name+' handle mounting',q(handle_x,z,face*.07),
                     q(handle_x,z,face*.115),.022,hardware,'Openings')
            beam(name+' '+label+' pull handle',q(handle_x,.96,face*.115),
                 q(handle_x,1.16,face*.115),.025,hardware,'Openings')

    # Glazing exists only in the fanlight above the two rectangular leaves.
    fanlight = [(width/2*math.cos(math.pi*i/28),
                 spring+rise*math.sin(math.pi*i/28)) for i in range(29)]
    facade_prism(name+' arched transom glass',p,u2,fanlight,.028,0,glass)
    for offset in (-.145,.145):
        for i,(x,z) in enumerate(profile):
            xx,zz = profile[(i+1)%len(profile)]
            beam(name+' surround',q(x,z,offset),q(xx,zz,offset),.085)
        beam(name+' transom rail',q(-width/2,spring,offset),
             q(width/2,spring,offset),.09)
        for angle in (math.pi/4,math.pi/2,3*math.pi/4):
            beam(name+' fanlight spoke',q(0,spring,offset),
                 q(width/2*math.cos(angle),spring+rise*math.sin(angle),offset),.025)
    facade_prism(name+' threshold',p,u2,
                 rectangle(-width/2,width/2,.035,bottom+.012),.30,0,coping)


# Front-facing windows: pair in garage wing, dining, study, master bath.
for p in [(264,1240),(447,1240),(610,990),(923,1020)]:
    opening('Front arched window',p,1.12,.68,2.31,.43)
opening('Far right front arched window',(1140,1110),1.12,.68,2.31,.43)
double_entry((772,902))
# Left elevation bedroom and bath openings, plus front side garage window.
for p,w,z in [((160,250),.80,.85),((160,474),.64,1.40),((160,633),1.20,.76),
              ((201,216),.94,.83)]:
    opening('West elevation window',p,w,z,2.36,0)
def pool_bath_door():
    # Pool-facing side of the bath projection: wall (446,84)-(446,188).
    p = (446,136)
    name = 'Pool bath exterior door'
    width, bottom, top = .96, .035, 2.20
    wall,u2 = nearest_wall(p)
    u = Vector((*u2,0)); n = Vector((-u.y,u.x,0)); base = Vector(pt(p))
    def q(x,z,offset):
        return base+u*x+n*offset+Vector((0,0,z))
    def rectangle(x0,x1,z0,z1):
        return [(x0,z0),(x1,z0),(x1,z1),(x0,z1)]
    profile = rectangle(-width/2,width/2,bottom,top)
    difference(wall,facade_prism('Pool bath door cutter',p,u2,profile,.65,0,None))
    finish = material('Pool bath door ivory paint', (.83, .81, .70), .40)
    hardware = material('Pool bath door bronze hardware', (.16, .105, .045), .28)
    hardware.node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value = .75
    facade_prism(name+' dark reveal',p,u2,profile,.018,0,shadow)
    facade_prism(name+' solid leaf',p,u2,
                 rectangle(-width/2+.035,width/2-.035,bottom+.012,top-.035),
                 .09,0,finish)
    for sign in (-1,1):
        off = sign*.145
        for x in (-width/2,width/2):
            beam(name+' jamb trim',q(x,bottom,off),q(x,top,off),.075)
        beam(name+' header trim',q(-width/2,top,off),q(width/2,top,off),.075)
        for low,high in [(.20,.86),(1.08,2.02)]:
            panel = rectangle(-width/2+.14,width/2-.14,low,high)
            facade_prism(name+' raised panel',p,u2,panel,.02,sign*.052,finish)
            for i,(x,z) in enumerate(panel):
                xx,zz = panel[(i+1)%len(panel)]
                beam(name+' panel molding',q(x,z,sign*.064),
                     q(xx,zz,sign*.064),.022,trim,'Openings')
        x = width/2-.14
        facade_prism(name+' handle backplate',p,u2,
                     rectangle(x-.025,x+.025,.93,1.07),.02,sign*.063,hardware)
        beam(name+' handle stem',q(x,1.0,sign*.065),
             q(x,1.0,sign*.105),.022,hardware,'Openings')
        beam(name+' lever handle',q(x,1.0,sign*.105),
             q(x-.10,1.0,sign*.105),.022,hardware,'Openings')
    facade_prism(name+' threshold',p,u2,
                 rectangle(-width/2,width/2,.01,bottom+.012),.30,0,coping)


if INCLUDE_POOL_BATH:
    opening('Pool bath window',(300,155),.60,1.55,2.38,0)
    pool_bath_door()
for p,w in [((1257,460),1.20),((1200,414),1.40)]:
    opening('Master sitting window',p,w,.70,2.45,.20)
def french_doors(name,p,width,bottom=.035,top=2.62):
    # Closed hinged French doors: separate framed leaves, ten glass lights
    # per leaf, and paired hardware. Preserve the existing wall openings.
    wall,u2 = nearest_wall(p)
    u = Vector((*u2,0)); n = Vector((-u.y,u.x,0)); base = Vector(pt(p))
    paint = material('French door white paint', (.94, .93, .88), .35)
    hardware = material('French door satin brass', (.48, .36, .17), .28)
    hardware.node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value = .75
    def q(x,z,offset):
        return base+u*x+n*offset+Vector((0,0,z))
    def rectangle(x0,x1,z0,z1):
        return [(x0,z0),(x1,z0),(x1,z1),(x0,z1)]
    def piece(label,x0,x1,z0,z1,mat=paint,depth=.065,offset=0):
        return facade_prism(name+' '+label,p,u2,rectangle(x0,x1,z0,z1),
                            depth,offset,mat)
    profile = rectangle(-width/2,width/2,bottom,top)
    difference(wall,facade_prism(name+' cutter',p,u2,profile,.65,0,None))
    # Full-depth jambs and head, with casing on both wall faces.
    for x0,x1 in [(-width/2,-width/2+.045),(width/2-.045,width/2)]:
        piece('jamb',x0,x1,bottom,top,depth=WALL_THICKNESS)
    piece('head',-width/2,width/2,top-.045,top,depth=WALL_THICKNESS)
    for offset in (-.145,.145):
        for x in (-width/2,width/2):
            beam(name+' casing',q(x,bottom,offset),q(x,top,offset),.075,paint)
        beam(name+' head casing',q(-width/2,top,offset),
             q(width/2,top,offset),.075,paint)
    piece('threshold',-width/2,width/2,.015,bottom+.012,coping,.28)

    # The broad living-room opening gets fixed glazed sidelights rather
    # than two implausibly wide hinged leaves; the other sets are pairs.
    inner = width/2-.055
    door_half = .90 if width > 2.60 else inner
    panels = [('left leaf',-door_half,-.006,True),
              ('right leaf',.006,door_half,True)]
    if width > 2.60:
        panels = [('left sidelight',-inner,-door_half-.025,False)] + panels
        panels += [('right sidelight',door_half+.025,inner,False)]
        for x in (-door_half-.0125,door_half+.0125):
            piece('sidelight mullion',x-.022,x+.022,bottom,top,depth=.10)
    for label,x0,x1,is_door in panels:
        z0,z1 = bottom+.016,top-.055
        stile = .09
        gx0,gx1 = x0+stile,x1-stile
        gz0,gz1 = z0+.18,z1-.10
        piece(label+' left stile',x0,gx0,z0,z1)
        piece(label+' right stile',gx1,x1,z0,z1)
        piece(label+' bottom rail',gx0,gx1,z0,gz0)
        piece(label+' top rail',gx0,gx1,gz1,z1)
        # Real individual panes separated by narrow white glazing bars.
        columns,rows = 2,5
        bar_width = .024
        for col in range(columns):
            for row in range(rows):
                a = gx0+(gx1-gx0)*col/columns
                b = gx0+(gx1-gx0)*(col+1)/columns
                c = gz0+(gz1-gz0)*row/rows
                d = gz0+(gz1-gz0)*(row+1)/rows
                piece(label+' glass pane',a,b,c,d,glass,.018)
        for col in range(1,columns):
            x = gx0+(gx1-gx0)*col/columns
            piece(label+' vertical glazing bar',x-bar_width/2,x+bar_width/2,gz0,gz1,depth=.045)
        for row in range(1,rows):
            z = gz0+(gz1-gz0)*row/rows
            piece(label+' horizontal glazing bar',gx0,gx1,z-bar_width/2,z+bar_width/2,depth=.045)
        if is_door:
            left = label == 'left leaf'
            handle_x = x1-stile/2 if left else x0+stile/2
            hinge_x = x0 if left else x1
            direction = -1 if left else 1
            for sign in (-1,1):
                for z in (.32,1.30,2.35):
                    piece(label+' hinge',hinge_x-.017,hinge_x+.017,z-.05,z+.05,
                          hardware,.025,sign*.04)
                piece(label+' handle plate',handle_x-.022,handle_x+.022,.95,1.10,
                      hardware,.016,sign*.043)
                beam(name+' handle spindle',q(handle_x,1.02,sign*.043),
                     q(handle_x,1.02,sign*.09),.022,hardware,'Openings')
                beam(name+' '+label+' lever',q(handle_x,1.02,sign*.09),
                     q(handle_x+direction*.10,1.02,sign*.09),.022,hardware,'Openings')
                piece(label+' lock plate',handle_x-.022,handle_x+.022,1.17,1.215,
                      hardware,.016,sign*.043)


# All four house-to-pool openings are French doors, not sliders.
# The separate solid pool bath door above is deliberately unchanged.
french_doors('Family room pool French doors',(607,322),2.44)
french_doors('Living room pool French doors',(850,540),3.50)
french_doors('Angled family pool French doors',(659.5,490),1.75)
french_doors('Angled master pool French doors',(1038,475),1.75)


def garage_door(p,width):
    wall,u = nearest_wall(p)
    profile = [(-width/2,.01),(width/2,.01),(width/2,2.45),(-width/2,2.45)]
    difference(wall,facade_prism('Garage cutter',p,u,profile,.65,0,None))
    facade_prism('Garage door',p,u,profile,.065,0,trim)
    uu = Vector((*u,0)); nn = Vector((-u.y,u.x,0)); base = Vector(pt(p))
    for off in (-.13,.13):
        for row in range(1,5):
            z = row*.49
            beam('Garage sectional seam',base-uu*width/2+nn*off+Vector((0,0,z)),
                 base+uu*width/2+nn*off+Vector((0,0,z)),.012,concrete,'Openings')
        for col in range(max(2,round(width/.70))):
            count = max(2,round(width/.70))
            x = -width/2+(col+.5)*width/count
            for row in range(4):
                small = [(x-width/count*.37,.14+row*.56),(x+width/count*.37,.14+row*.56),
                         (x+width/count*.37,.49+row*.56),(x-width/count*.37,.49+row*.56)]
                facade_prism('Recessed garage panel',p,u,small,.012,off,coping)


# Plan has a long double opening and a shorter single opening on the driveway side.
garage_door((160,933),4.20)
garage_door((186,1155),2.40)

# Low equipment-screen wall on the west side, just behind the garage doors.
# Visual estimates only: follows the supplied open-ended, clipped-corner plan.
# The double garage opening ends near plan y=823; y=800 leaves it clear.
def garage_equipment_screen():
    anchor = Vector(xy((160,800)))
    anchor.x -= WALL_THICKNESS/2-.01
    height = 1.14
    thickness = .18
    # Out from the house, diagonal toward the rear, then parallel to house.
    # Positive world Y is rearward. The far end intentionally stays open.
    path = [anchor,
            anchor+Vector((-2.05,0)),
            anchor+Vector((-2.75,.70)),
            anchor+Vector((-2.75,2.05))]

    def strip_polygon(width,end_extension=0):
        points = [p.copy() for p in path]
        points[0] -= (path[1]-path[0]).normalized()*end_extension
        points[-1] += (path[-1]-path[-2]).normalized()*end_extension
        directions = [(points[i+1]-points[i]).normalized() for i in range(len(points)-1)]
        normals = [Vector((-d.y,d.x)) for d in directions]
        offsets = []
        for i in range(len(points)):
            if i == 0:
                offsets.append(normals[0]*width/2)
            elif i == len(points)-1:
                offsets.append(normals[-1]*width/2)
            else:
                bisector = normals[i-1]+normals[i]
                offsets.append(bisector*(width/2/bisector.dot(normals[i])))
        return ([p+n for p,n in zip(points,offsets)]+
                [p-n for p,n in reversed(list(zip(points,offsets)))])

    def solid_strip(name,width,bottom,top,mat,end_extension=0):
        polygon = strip_polygon(width,end_extension)
        count = len(polygon)
        verts = [(p.x,p.y,z) for z in (bottom,top) for p in polygon]
        faces = [tuple(reversed(range(count))),tuple(range(count,2*count))]
        faces += [(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)]
        return mesh(name,verts,faces,mat,'Shell')

    wall = solid_strip('Garage equipment screening wall',thickness,-.04,height,stucco)
    # Small square through-openings grouped near the house, as in the photo.
    # Cut the screening wall only, never the house or garage-door geometry.
    for row,count in enumerate((4,5,4)):
        for col in range(count):
            distance = .90+(col-(count-1)/2)*.18
            cutter = box('Equipment screen vent cutter',
                         (anchor.x-distance,anchor.y,.38+row*.18),
                         (.105,thickness+.30,.105),None,'Shell')
            difference(wall,cutter)
    cap = solid_strip('Equipment screen pale coping',.23,height,height+.055,trim,.02)
    bevel = cap.modifiers.new('Soft coping edges','BEVEL')
    bevel.width = .008
    bevel.segments = 2


garage_equipment_screen()

# Front porch and signature three-bay arched colonnade.
slab('Front porch paving',(524,902,1032,1080),-.04,.035,pavers,'Shell')
for x in (541,684,845,1011):
    base = pt((x,1068),1.38)
    box('Porch square pier',base,(.29,.34,2.76),stucco,'Trim')
    box('Pier plinth',pt((x,1068),.16),(.43,.46,.32),trim,'Trim')
    box('Pier capital',pt((x,1068),2.65),(.45,.47,.18),trim,'Trim')
for a,b in [(541,684),(684,845),(845,1011)]:
    p = ((a+b)/2,1068)
    width = (b-a)*SCALE
    header = box('Porch arch spandrel',pt(p,2.99),(width,.30,1.10),stucco,'Trim')
    prof = arch_shape(width-.29,-.10,2.23,.65)
    difference(header,facade_prism('Porch arch void',p,(1,0),prof,.80,0,None))
    for i in range(28):
        t0,t1 = math.pi*i/28,math.pi*(i+1)/28
        center = Vector(pt(p))
        beam('Porch arch molding',center+Vector(((width-.29)/2*math.cos(t0),-.19,2.23+.65*math.sin(t0))),
             center+Vector(((width-.29)/2*math.cos(t1),-.19,2.23+.65*math.sin(t1))),.065)
# White ornamental double gate with fixed side panels, photo-inspired.
# Fit the center porch bay rather than leaving a short floating fence.
def front_gate():
    paint = material('Gate white enamel', (.94, .93, .88), .30)
    base = Vector(pt(((684+845)/2,1068)))
    half_span = (845-684)*SCALE/2-.145
    half_gate = .78
    gap = .014
    bottom = .12
    def q(x,z,y=0):
        return base+Vector((x,y,z))
    def top(x):
        # Raised center, gently descending shoulders toward the piers.
        return 1.16+.49*(.5+.5*math.cos(math.pi*x/half_span))
    def bar(name,x0,z0,x1,z1,width=.025,y=0):
        return beam('Entry gate '+name,q(x0,z0,y),q(x1,z1,y),width,paint,'Trim')
    def rod(name,points,radius=.012,y=0):
        # Round-section metalwork, kept as one mesh per continuous curve.
        verts, faces = [], []
        count = len(points)
        for i,(x,z) in enumerate(points):
            a = points[max(0,i-1)]; b = points[min(count-1,i+1)]
            dx,dz = b[0]-a[0],b[1]-a[1]
            length = math.hypot(dx,dz)
            nx,nz = -dz/length,dx/length
            for j in range(8):
                angle = 2*math.pi*j/8
                c,s = math.cos(angle),math.sin(angle)
                verts.append(tuple(q(x+radius*c*nx,z+radius*c*nz,y+radius*s)))
        for i in range(count-1):
            for j in range(8):
                a = i*8+j; b = i*8+(j+1)%8
                faces.append((a,b,b+8,a+8))
        faces += [tuple(reversed(range(8))),tuple(range((count-1)*8,count*8))]
        ob = mesh('Entry gate '+name,verts,faces,paint,'Trim')
        for polygon in ob.data.polygons:
            if len(polygon.vertices) == 4:
                polygon.use_smooth = True
    def finial(x,z):
        # Small spear-shaped tips, not oversized fence spikes.
        verts = [tuple(q(x,z)),tuple(q(x-.027,z+.045)),
                 tuple(q(x,z+.045,-.021)),tuple(q(x+.027,z+.045)),
                 tuple(q(x,z+.045,.021)),tuple(q(x,z+.12))]
        faces = [(0,2,1),(0,3,2),(0,4,3),(0,1,4),
                 (5,1,2),(5,2,3),(5,3,4),(5,4,1)]
        mesh('Entry gate spear finial',verts,faces,paint,'Trim')

    # Two independent leaves and two stationary infill panels.
    sections = [('left side',-half_span,-half_gate-.035),
                ('left leaf',-half_gate+gap,-gap),
                ('right leaf',gap,half_gate-gap),
                ('right side',half_gate+.035,half_span)]
    for label,a,b in sections:
        for x in (a,b):
            bar(label+' stile',x,bottom,x,top(x),.035)
        bar(label+' bottom rail',a,bottom,b,bottom,.035)
        bar(label+' lower rail',a,.27,b,.27,.025)
        rod(label+' curved top',[(a+(b-a)*i/40,top(a+(b-a)*i/40))
                                for i in range(41)],.018)
        count = max(2,round((b-a)/.12))
        for i in range(1,count):
            x = a+(b-a)*i/count
            z = top(x)+.065
            bar(label+' upright',x,bottom,x,z,.018)
            finial(x,z)

    # Slender hinge posts, caps, and visible hinge collars.
    for x in (-half_gate-.018,half_gate+.018):
        bar('hinge post',x,.035,x,top(x)+.13,.055)
        box('Entry gate post cap',q(x,top(x)+.13),(.075,.075,.035),paint,'Trim')
        for z in (.37,1.17):
            box('Entry gate hinge',q(x,z,-.012),(.085,.075,.07),paint,'Trim')
    for x in (-half_span,half_span):
        for z in (.30,1.10):
            box('Entry gate pier fixing',q(x,z),(.07,.09,.08),paint,'Trim')

    # Mirrored C-scroll flourishes near the meeting stiles. Each belongs
    # to its own leaf; nothing bridges the opening except the latch.
    for side in (-1,1):
        for zc,flip in [(.72,1),(1.02,-1)]:
            points = []
            for i in range(65):
                t = i/64
                angle = -math.pi/2+t*2.2*math.pi
                radius = .13*(1-.78*t)
                points.append((side*(.18+radius*math.cos(angle)),
                               zc+flip*radius*math.sin(angle)))
            rod('ornamental scroll',points,.009,-.035)
        # Swept stem ties the scrolls into the lower framework.
        rod('scroll stem',[(side*(.10+.06*math.sin(math.pi*i/40)),
                            .27+.89*i/40) for i in range(41)],.009,-.035)
        rod('handle',[(side*.065,.83),(side*.065,.98)],.014,-.07)
    box('Entry gate latch',q(0,.92,-.045),(.12,.05,.035),paint,'Trim')


front_gate()


# Photo-inspired cast-concrete balustrades on either side of the entry.
# Low solid rails with shaped balusters, not metal pickets or solid walls.
def front_balustrades():
    stone = material('Porch cream cast concrete', (.89, .86, .75), .60, .004)
    floor = .035
    def run(name,a,b,start_inset,end_inset):
        av,bv = Vector(pt(a)),Vector(pt(b))
        direction = (bv-av).normalized()
        av += direction*start_inset
        bv -= direction*end_inset
        length = (bv-av).length
        angle = math.atan2(direction.y,direction.x)
        middle = (av+bv)/2
        def rail(label,z0,z1,depth):
            box(name+' '+label,(middle.x,middle.y,(z0+z1)/2),
                (length,depth,z1-z0),stone,'Trim',angle)
        rail('bottom plinth',floor,.15,.22)
        rail('plinth molding',.15,.19,.24)
        rail('handrail underside',.84,.88,.20)
        rail('broad concrete handrail',.88,.97,.27)
        rail('handrail top molding',.97,.995,.29)

        count = max(1,math.floor(length/.25))
        # Turned profile: narrow neck, rounded lower body, molded collars.
        profile = [(0,.052),(.06,.052),(.10,.063),(.16,.063),
                   (.22,.053),(.34,.075),(.45,.071),(.56,.052),
                   (.69,.037),(.82,.038),(.89,.052),(.94,.058),(1,.058)]
        segments = 24
        for i in range(count):
            center = av+direction*(length*(i+.5)/count)
            box(name+' baluster square foot',(center.x,center.y,.225),
                (.14,.14,.07),stone,'Trim',angle)
            box(name+' baluster square capital',(center.x,center.y,.81),
                (.14,.14,.06),stone,'Trim',angle)
            verts,faces = [],[]
            for t,radius in profile:
                z = .26+t*(.78-.26)
                for j in range(segments):
                    theta = 2*math.pi*j/segments
                    verts.append((center.x+radius*math.cos(theta),
                                  center.y+radius*math.sin(theta),z))
            for row in range(len(profile)-1):
                for j in range(segments):
                    a0 = row*segments+j
                    b0 = row*segments+(j+1)%segments
                    faces.append((a0,b0,b0+segments,a0+segments))
            faces += [tuple(reversed(range(segments))),
                      tuple(range((len(profile)-1)*segments,len(profile)*segments))]
            ob = mesh(name+' shaped concrete baluster',verts,faces,stone,'Trim')
            for polygon in ob.data.polygons:
                if len(polygon.vertices) == 4:
                    polygon.use_smooth = True

    # Front runs stop at the existing pier faces; never cross the gate bay.
    run('Left porch balustrade',(541,1068),(684,1068),.145,.145)
    run('Right porch balustrade',(845,1068),(1011,1068),.145,.145)
    # Front railings only; both porch sides remain open.


front_balustrades()
# Broad, shallow corner courses, matching the front and rear elevations.
# Each course is one L-shaped piece wrapping both exterior wall faces.
# Six almost-continuous courses replace the small widely spaced tabs.
def house_corner_blocks():
    courses = 6
    bottom,top = .025,WALL_HEIGHT
    pitch = (top-bottom)/courses
    joint = .018
    wall_face = -WALL_THICKNESS/2
    outside = wall_face-.035
    inside = wall_face+.008   # Slight embed into stucco; no floating trim.
    # Front corners only; the two rear corners have plain stucco.
    # sx/sy point into the house on each face.
    corners = [(186,1240,1,1,.52,.52,'Left front'),
               (524,1240,-1,1,.52,.52,'Right front'),
               (1032,1080,1,1,.52,.52,'Gable flank left'),
               (1255,1082,-1,1,.52,.52,'Gable flank right')]
    for x,y,sx,sy,reach_u,reach_v,label in corners:
        profile = [(outside,outside),(reach_u,outside),(reach_u,inside),
                   (inside,inside),(inside,reach_v),(outside,reach_v)]
        base = Vector(pt((x,y)))
        for row in range(courses):
            z0 = bottom+row*pitch+joint/2
            z1 = bottom+(row+1)*pitch-joint/2
            verts = [(base.x+sx*u,base.y+sy*v,z)
                     for z in (z0,z1) for u,v in profile]
            count = len(profile)
            faces = [tuple(reversed(range(count))),tuple(range(count,2*count))]
            faces += [(i,(i+1)%count,(i+1)%count+count,i+count)
                      for i in range(count)]
            ob = mesh(label+' wraparound corner block %02d' % (row+1),
                      verts,faces,trim,'Trim')
            bevel = ob.modifiers.new('Soft cast-stucco edges','BEVEL')
            bevel.width = .005
            bevel.segments = 2


house_corner_blocks()

# -------------------------- roofs --------------------------
# Roof components remain separately editable. Tiles are suppressed wherever
# another roof is higher, including the front-facing gable over the bath window.
FRONT_GABLE_NAME = 'Right front window gable'
roof_specs = [
    ('Garage hip',(160,735,524,1240),3.25),
    ('West bedroom family hip',(160,212,608,816),3.25),
    ('Main entry living hip',(520,515,1100,1080),3.48),
    ('Master suite hip',(969,414,1258,1083),3.25),
    (FRONT_GABLE_NAME,(1085,950,1195,1110),3.25),
]
if INCLUDE_POOL_BATH:
    roof_specs.append(('Pool bath hip',(300,84,446,238),3.20))
roofs = []
for name,(a,b,c,d),eave in roof_specs:
    o = ROOF_OVERHANG_PX
    xmin,ymax = xy((a-o,b-o)); xmax,ymin = xy((c+o,d+o))
    roofs.append((name,xmin,xmax,ymin,ymax,eave))


def roof_z(r,x,y):
    name,a,b,c,d,z = r
    if not (a-1e-5 <= x <= b+1e-5 and c-1e-5 <= y <= d+1e-5):
        return -100
    if name == FRONT_GABLE_NAME:
        # Ridge runs front-to-back; no hip slope across the front triangle.
        return z+ROOF_PITCH*min(x-a,b-x)
    return z+ROOF_PITCH*min(x-a,b-x,y-c,d-y)


gable_roof = next(r for r in roofs if r[0] == FRONT_GABLE_NAME)
for r in roofs:
    name,a,b,c,d,z = r
    h = min(b-a,d-c)/2
    corners = [(a,c,z),(b,c,z),(b,d,z),(a,d,z)]
    if name == FRONT_GABLE_NAME:
        peak = z+(b-a)/2*ROOF_PITCH
        ridge = [((a+b)/2,c,peak),((a+b)/2,d,peak)]
        faces = [(0,4,5,3),(4,1,2,5)]
    elif b-a <= d-c:
        ridge = [((a+b)/2,c+h,z+h*ROOF_PITCH),((a+b)/2,d-h,z+h*ROOF_PITCH)]
        faces = [(0,1,4),(1,2,5,4),(2,3,5),(3,0,4,5)]
    else:
        ridge = [(a+h,(c+d)/2,z+h*ROOF_PITCH),(b-h,(c+d)/2,z+h*ROOF_PITCH)]
        faces = [(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4)]
    ob = mesh(name,corners+ridge,faces,roofmat,'Roofs')
    solid = ob.modifiers.new('Roof thickness','SOLIDIFY'); solid.thickness=.065
    if name == FRONT_GABLE_NAME:
        # Stucco face is centered on the existing window and meets the wall.
        wall_half = (1195-1085)*SCALE/2
        shoulder = peak-wall_half*ROOF_PITCH-.07
        facade_prism('Right front gable stucco face',(1140,1110),(1,0),
                     [(-wall_half,WALL_HEIGHT-.03),(wall_half,WALL_HEIGHT-.03),
                      (wall_half,shoulder),(0,peak-.07),(-wall_half,shoulder)],
                     WALL_THICKNESS,0,stucco,'Shell')
        # Broad cream rake boards outline the peak; no horizontal gutter
        # across the triangle. Matching soffits close the front overhang.
        wall_y = xy((1140,1110))[1]
        for edge in (corners[0],corners[1]):
            beam('Front gable sloping fascia',edge,ridge[0],.17,trim,'Roofs',.19)
            beam('Front gable lower molding',Vector(edge)+Vector((0,-.04,-.10)),
                 Vector(ridge[0])+Vector((0,-.04,-.10)),.045,trim,'Trim')
            mesh('Front gable soffit',
                 [(edge[0],c,edge[2]-.07),((a+b)/2,c,peak-.07),
                  ((a+b)/2,wall_y,peak-.07),(edge[0],wall_y,edge[2]-.07)],
                 [(0,1,2,3)],trim,'Roofs')
        eave_edges = [(corners[0],corners[3]),(corners[1],corners[2])]
    else:
        eave_edges = [(corners[i],corners[(i+1)%4]) for i in range(4)]
    for q0,q1 in eave_edges:
        # Remove only the stretches of existing fascia/gutter buried by
        # the new gable so a straight bar cannot cross its front face.
        start,end = Vector(q0),Vector(q1)
        steps = max(1,math.ceil((end-start).length/.04))
        run = None
        for i in range(steps+1):
            visible = False
            if i < steps:
                mid = start+(end-start)*((i+.5)/steps)
                visible = (name == FRONT_GABLE_NAME or
                           roof_z(gable_roof,mid.x,mid.y) <= mid.z+.025)
            if visible and run is None:
                run = i
            elif not visible and run is not None:
                v0 = start+(end-start)*(run/steps)
                v1 = start+(end-start)*(i/steps)
                beam('Eave fascia',v0,v1,.14,trim,'Roofs',.17)
                beam('Rain gutter',v0+Vector((0,0,.035)),
                     v1+Vector((0,0,.035)),.07,trim,'Roofs')
                run = None
    beam('Roof ridge cap',ridge[0],ridge[1],.16,roofmat,'Roofs')

if MAKE_ROOF_TILES:
    verts,faces,mi = [],[],[]
    # Small curved concrete-tile patches, assembled into one mesh rather than
    # thousands of separate objects. Shape follows the hip envelope.
    for r in roofs:
        _,a,b,c,d,z = r
        nx,ny = math.ceil((b-a)/.27),math.ceil((d-c)/.37)
        dx,dy = (b-a)/nx,(d-c)/ny
        for ix in range(nx):
            for iy in range(ny):
                x,y = a+(ix+.5)*dx,c+(iy+.5)*dy
                if roof_z(r,x,y) < max(roof_z(rr,x,y) for rr in roofs)-.015:
                    continue
                start = len(verts)
                for j in range(2):
                    for k in range(5):
                        xx = a+(ix+k/4)*dx
                        yy = c+(iy+j)*dy
                        zz = roof_z(r,xx,yy)+.025+.025*math.sin(math.pi*k/4)+(.012 if j==0 else 0)
                        verts.append((xx,yy,zz))
                color = random.randrange(len(tilemats))
                for k in range(4):
                    faces.append((start+k,start+k+1,start+k+6,start+k+5)); mi.append(color)
    ob = mesh('Individual curved concrete roof tiles',verts,faces,None,'Roofs')
    for m in tilemats:
        ob.data.materials.append(m)
    for p,i in zip(ob.data.polygons,mi):
        p.material_index=i

# Flat covered lanai tucked between the family room and master wing.
lanai = [(607,410),(1100,410),(1100,414),(972,540),(712,540),(607,440)]
prism('Lanai paving',lanai,-.03,.025,pavers,'Shell')
prism('Covered lanai roof',lanai,3.03,3.18,roofmat,'Roofs')
beam('Lanai rear fascia',pt((607,410),3.08),pt((1100,410),3.08),.18)
for x in (617,1090):
    box('Lanai support',pt((x,420),1.50),(.20,.20,3.00),stucco,'Trim')

# House geometry only: no site, pool, cameras, lights, or presentation setup.
