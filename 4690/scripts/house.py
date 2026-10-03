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
Interior partitions, closets, cabinetry and fixtures follow the supplied plan.
Furniture, finishes, door heights and fixture details are illustrative estimates.
Optional furniture and ceilings are controlled by the settings below.
No automatic .blend save. Coordinates are in meters.
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
MAKE_INTERIOR = True
MAKE_INTERIOR_FURNITURE = False  # Loose furnishings outside the kitchen.
MAKE_KITCHEN_FURNITURE = True    # Preserve the kitchen stools independently.
MAKE_INTERIOR_CEILINGS = False  # Leave off for an unobstructed top-down inspection.
INTERIOR_CUTAWAY = False      # Hide roofs/ceilings in viewport only, not renders.
INTERIOR_WALL_THICKNESS = .115
INTERIOR_DOOR_HEIGHT = 2.13
MAKE_INTERIOR_DOOR_LEAVES = False  # Keep room/closet frames, omit panels and handles.
INTERIOR_FLOOR_Z = .045       # Above the existing broad porch paving slab.
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
    # Keep the entire doorway south of the shower enclosure (ends y=124).
    p = (446,158)
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

# -------------------------- interior --------------------------
# All plan points below use the same 1440px reference and xy() transform as
# the shell. Room dimensions in the drawing are nominal, not survey dimensions.
# Openings are assembled from jamb segments and headers: no hidden solid wall
# remains behind a door. Interior components live in independent collections.
def build_interior():
    for name in ['Interior walls', 'Interior doors', 'Interior floors',
                 'Interior cabinetry', 'Interior fixtures', 'Interior furniture',
                 'Interior ceilings']:
        col = bpy.data.collections.new(PREFIX + '_' + name)
        root.children.link(col)
        groups[name] = col

    paint = material('Interior warm white plaster', (.86,.84,.78), .82)
    wood = material('Interior oak flooring', (.43,.29,.16), .65, .002)
    tile = material('Interior limestone tile', (.72,.69,.60), .65, .003)
    grout = material('Interior tile grout', (.48,.46,.40), .85)
    cabinet = material('Interior painted cabinetry', (.81,.80,.73), .48)
    oak = material('Interior oak joinery', (.35,.22,.11), .52)
    stone = material('Interior quartz worktops', (.90,.88,.81), .32)
    ceramic = material('Interior white porcelain', (.94,.94,.91), .20)
    metal = material('Interior brushed nickel', (.48,.51,.52), .26)
    metal.node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value = .8
    dark = material('Interior appliance black', (.028,.033,.038), .25)
    fabric = material('Interior oatmeal upholstery', (.64,.59,.49), .95)
    bedding = material('Interior ivory linen', (.88,.86,.79), .95)
    accent = material('Interior muted sage', (.27,.37,.32), .9)
    shower_glass = material('Interior clear shower glass', (.96,.99,.98), .08)
    shower_shader = shower_glass.node_tree.nodes.get('Principled BSDF')
    shower_shader.inputs['Transmission Weight'].default_value = 1.0
    shower_shader.inputs['IOR'].default_value = 1.45
    fz = INTERIOR_FLOOR_Z + .009
    thick = INTERIOR_WALL_THICKNESS

    def rect(name, bounds, low, high, mat, group='Interior cabinetry'):
        return slab(name, bounds, low, high, mat, group)

    def segment(name, a, b, z0, z1, width, mat, group):
        av,bv = Vector(xy(a)),Vector(xy(b))
        delta = bv-av
        middle = (av+bv)/2
        return box(name, (middle.x,middle.y,(z0+z1)/2),
                   (delta.length,width,z1-z0),mat,group,
                   math.atan2(delta.y,delta.x))

    def partition(name, a, b, openings=()):
        # Each opening: (distance from a in IMAGE PIXELS, width in pixels,
        # 'door'/'closet'/'open'/'passage'). 'passage' retains door-height
        # casing without a leaf; 'open' is a taller untrimmed opening.
        av,bv = Vector(a),Vector(b)
        length = (bv-av).length
        direction = (bv-av)/length
        u = Vector((direction.x,-direction.y,0))
        n = Vector((-u.y,u.x,0))
        def p(distance):
            return tuple(av+direction*distance)
        def solid(lo,hi):
            if hi-lo < .01:
                return
            ob = segment(name, p(lo),p(hi),fz,WALL_HEIGHT,thick,paint,'Interior walls')
            ob['reference'] = 'Supplied floorplan; manually traced partition'
            # Baseboards on both sides, stopped at every doorway.
            for side in (-1,1):
                edge = n*side*(thick/2+.009)
                base = segment(name+' skirting',p(lo),p(hi),fz,fz+.105,.018,
                               trim,'Interior walls')
                base.location += edge
        cursor = 0
        for offset,width,kind in sorted(openings):
            if offset < cursor or offset+width > length+.001:
                raise ValueError('Invalid interior opening: '+name)
            solid(cursor,offset)
            height = 2.65 if kind == 'open' else INTERIOR_DOOR_HEIGHT
            segment(name+' opening header',p(offset),p(offset+width),
                    fz+height,WALL_HEIGHT,thick,paint,'Interior walls')
            if kind != 'open':
                left,right = Vector(pt(p(offset),fz)),Vector(pt(p(offset+width),fz))
                for side in (-1,1):
                    off = n*side*(thick/2+.016)
                    for v in (left,right):
                        beam(name+' door casing',v+off,v+off+Vector((0,0,height)),
                             .048,trim,'Interior doors',.035)
                    beam(name+' head casing',left+off+Vector((0,0,height)),
                         right+off+Vector((0,0,height)),.048,trim,'Interior doors',.035)
                for v in (left,right):
                    beam(name+' jamb',v+Vector((0,0,.01)),v+Vector((0,0,height)),
                         .028,trim,'Interior doors',thick)
                clear = width*SCALE-.055
                if kind == 'door' and MAKE_INTERIOR_DOOR_LEAVES:
                    theta = math.radians(72)
                    leaf_u = u*math.cos(theta)+n*math.sin(theta)
                    hinge = left+u*.03
                    center = hinge+leaf_u*clear/2+Vector((0,0,height/2))
                    box(name+' open door leaf',center,(clear,.038,height-.025),
                        cabinet,'Interior doors',math.atan2(leaf_u.y,leaf_u.x))
                    for side in (-1,1):
                        normal = Vector((-leaf_u.y,leaf_u.x,0))*side
                        handle = hinge+leaf_u*(clear-.10)+Vector((0,0,1.0))
                        beam(name+' lever',handle+normal*.045,
                             handle+normal*.045-leaf_u*.10,.018,metal,'Interior doors')
                elif kind == 'closet' and MAKE_INTERIOR_DOOR_LEAVES:
                    # Bifolds parked at each jamb rather than blocking access.
                    for side,v in [(1,left),(-1,right)]:
                        for k in range(2):
                            center = v+u*side*(.04+k*.05)+n*(clear/8)
                            center.z += height/2
                            box(name+' folded closet panel',center,
                                (.027,clear/4,height-.025),cabinet,'Interior doors',
                                math.atan2(u.y,u.x))
            cursor = offset+width
        solid(cursor,length)

    # West bedroom wing: ONE kitchen-side entrance at plan y=500..548.
    # The short passage serves the shared bath straight ahead and the two
    # bedrooms on opposite sides; neither bedroom opens into the kitchen.
    # Cased openings retain door heights and trim, without leaves or handles.
    partition('Bedroom wing east wall',(367,730),(367,224),
              [(182,48,'passage')])
    partition('Bedroom 3 passage entrance',(320,431),(367,431),
              [(4,39,'passage')])
    partition('Bedroom 2 passage entrance',(367,548),(320,548),
              [(4,39,'passage')])
    partition('Bedroom 3 closet front',(160,400),(315,400),[(30,96,'closet')])
    partition('Bedroom 3 closet back',(160,431),(320,431))
    partition('Bedroom 3 closet end',(315,400),(315,431))
    partition('Shared bathroom east wall',(320,431),(320,548),[(43,43,'passage')])
    partition('Shared bathroom south wall',(160,548),(320,548))
    # Keep the linen front beyond the bathroom entry (y=474..517).
    # The old y=504 return crossed that opening, leaving a floating end.
    # A recessed, doorless alcove also eliminates projecting bifold panels.
    partition('Shared bath linen cupboard',(250,522),(320,522),
              [(12,45,'passage')])
    partition('Shared bath linen divider',(250,522),(250,548))
    partition('Bedroom 2 closet front',(160,728),(300,728),[(27,88,'closet')])
    partition('Bedroom 2 closet back',(160,758),(300,758))
    partition('Bedroom 2 closet end',(300,728),(300,758))
    partition('Bedroom 2 to laundry',(300,730),(463,730))
    partition('Laundry west wall',(300,758),(300,813))
    partition('Laundry passage wall',(463,730),(463,813),[(35,44,'open')])
    partition('Garage to laundry',(300,813),(524,813),[(170,46,'door')])
    # The Dining west wall below already covers x=524, y=788..990.
    # Do not generate a second wall/skirting over its y=813..990 section.

    # Preserve the living/kitchen divider and its existing openings.
    # In the kitchen reference photo, this divider is on the LEFT.
    # Appliance positions are defined in photo_kitchen() below.
    living_divider_x = 680 + INTERIOR_WALL_THICKNESS/(2*SCALE)
    partition('Living kitchen angled rear return',(712,540),(living_divider_x,578))
    partition('Living kitchen divider',(living_divider_x,578),(living_divider_x,740),
              [(0,48,'open')])

    # Family/kitchen and the central gallery remain open.
    partition('Living to master',(972,540),(972,740))
    partition('Master suite gallery threshold',(972,740),(1085,740),[(12,86,'open')])
    partition('Master bath approach',(1085,704),(1085,796))
    partition('Dining west wall',(524,788),(524,990))
    partition('Dining north return',(524,788),(597,788))
    # Full-span opening: no isolated 3px pier at its free north end.
    dining_opening_length = math.hypot(708-641,848-788)
    partition('Dining diagonal opening',(641,788),(708,848),
              [(0,dining_opening_length,'open')])
    # Waist-high divider immediately left when entering the front door.
    dining_half_wall_top = fz+.95
    segment('Dining entry half wall',(708,848),(708,902),
            fz,dining_half_wall_top,thick,paint,'Interior walls')
    segment('Dining entry half wall cap',(708,848),(708,902),
            dining_half_wall_top,dining_half_wall_top+.035,
            thick+.04,trim,'Interior walls')
    for side in (-1,1):
        skirting = segment('Dining entry half wall skirting',
                           (708,848),(708,902),fz,fz+.105,.018,
                           trim,'Interior walls')
        skirting.location.x += side*(thick/2+.009)
    # Join the diagonal entrance to the existing exterior west wall.
    partition('Study west entry return',(836,848),(836,902))
    # Reversed endpoints hinge the leaf at the north jamb and swing it
    # into the study, away from the gallery and the closet at x=934.
    partition('Study diagonal entrance',(900,796),(836,848),[(9,55,'door')])
    partition('Study closet north',(900,796),(1032,796))
    partition('Master bath north return',(1032,796),(1085,796))
    partition('Study closet front',(934,827),(1032,827),[(10,78,'closet')])
    partition('Study closet side',(934,796),(934,827))
    # Connecting door at y=954..998, below the linen cupboard ending
    # at y=948 and above the toilet-room partition at y=1005.
    # Build a real opening with jambs/header; the leaf swings into the bath.
    partition('Study to master bath',(1032,796),(1032,1020),
              [(158,44,'door')])
    partition('Master closet north',(1162,742),(1257,742))
    partition('Master closet upper return',(1162,742),(1162,774))
    partition('Master closet upper diagonal',(1162,774),(1198,805))
    partition('Master closet entrance',(1198,805),(1198,895),[(21,47,'door')])
    partition('Master closet lower diagonal',(1198,895),(1162,924))
    partition('Master closet lower return',(1162,924),(1162,956))
    partition('Master closet south',(1162,956),(1280,956))
    # Photo correction: full-height wall return at the end of the vanity,
    # not an accessible linen closet. Preserve the passage to its east.
    master_vanity_return = rect('Master vanity end wall',
                               (1032,921,1085,948),fz,WALL_HEIGHT,
                               paint,'Interior walls')
    # Recess a small cabinet into the north face, beside the vanity mirror.
    medicine_recess = rect('Master medicine cabinet recess cutter',
                           (1045.5,919,1068.5,927),1.17,1.89,None,
                           'Interior cabinetry')
    difference(master_vanity_return,medicine_recess)
    for z0,z1,width in [(fz,fz+.105,.018),(.97,1.01,.025)]:
        segment('Master vanity return front trim',(1035,920.5),(1085,920.5),
                z0,z1,width,trim,'Interior walls')
        segment('Master vanity return end trim',(1085.5,921),(1085.5,948),
                z0,z1,width,trim,'Interior walls')
    partition('Master toilet room north',(1032,1005),(1085,1005))
    partition('Master toilet room east',(1085,1005),(1085,1080),[(9,44,'door')])
    if INCLUDE_POOL_BATH:
        partition('Pool bathroom south',(300,224),(446,224),[(8,46,'door')])
        # Close the missing east return between the exterior corner and
        # the south partition, beside (not in front of) the vanity.
        partition('Pool bathroom east return',(446,188),(446,224))
        # No partition at y=190: it blocked the front of the vanity.
        # The existing south wall at y=224 remains behind the sink.

    # Continuous finish, with room-specific inserts; all inserts share a level.
    prism('Interior continuous oak finish',outline,.002,INTERIOR_FLOOR_Z,wood,
          'Interior floors')
    tile_areas = [
        ('Laundry service strip',[(300,730),(463,730),(463,813),(300,813)]),
        ('Gallery and foyer',[(463,740),(1085,740),(1085,796),(900,796),
                              (836,848),(836,902),(708,902),(708,848),
                              (641,788),(524,788),(524,813),(463,813)]),
        ('Shared bath',[(160,431),(320,431),(320,548),(160,548)]),
        ('Shared bath passage',[(320,431),(367,431),(367,548),(320,548)]),
        # Continue to the bedroom threshold at y=740, and follow the
        # actual closet return/diagonal rather than stopping at y=796.
        ('Master bath',[(1032,796),(1085,796),(1085,740),(1162,740),
                         (1162,774),(1198,805),(1198,895),
                         (1162,924),(1162,956),(1255,956),(1255,1082),
                         (1195,1082),(1195,1110),(1085,1110),(1085,1080),
                         (1032,1080)]),
    ]
    if INCLUDE_POOL_BATH:
        tile_areas.append(('Pool bath',[(300,84),(446,84),(446,224),(300,224)]))

    def inside(p, poly):
        x,y = p
        odd = False
        for i,a in enumerate(poly):
            b = poly[(i+1)%len(poly)]
            if (a[1]>y) != (b[1]>y):
                if x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:
                    odd = not odd
        return odd

    for name,poly in tile_areas:
        prism(name+' tiled floor',poly,INTERIOR_FLOOR_Z, fz-.002,tile,'Interior floors')
        # Clip fine joint lines against the polygon by sampling at 1px steps.
        # One mesh per room avoids thousands of individual tile objects.
        verts,faces = [],[]
        xs,ys = [p[0] for p in poly],[p[1] for p in poly]
        step = .305/SCALE
        def joint(a,b):
            av,bv = Vector(xy(a)),Vector(xy(b))
            normal = Vector((-(bv-av).y,(bv-av).x)).normalized()*.0008
            index = len(verts)
            verts.extend([(v.x,v.y,fz-.0015) for v in
                          (av+normal,bv+normal,bv-normal,av-normal)])
            faces.append(tuple(range(index,index+4)))
        for axis in (0,1):
            low,high = (min(xs),max(xs)) if axis == 0 else (min(ys),max(ys))
            lo,hi = (min(ys),max(ys)) if axis == 0 else (min(xs),max(xs))
            for k in range(math.ceil(low/step),math.floor(high/step)+1):
                fixed = k*step
                start = None
                for t in range(math.floor(lo),math.ceil(hi)+1):
                    p = (fixed,t+.5) if axis == 0 else (t+.5,fixed)
                    valid = t < hi and inside(p,poly)
                    if valid and start is None:
                        start = t
                    elif not valid and start is not None:
                        a,b = ((fixed,start),(fixed,t)) if axis == 0 else ((start,fixed),(t,fixed))
                        joint(a,b)
                        start = None
        mesh(name+' tile joints',verts,faces,grout,'Interior floors')
    prism('Garage concrete floor',[(160,758),(300,758),(300,813),(524,813),
          (524,1240),(186,1240),(186,1067),(160,1067)],
          INTERIOR_FLOOR_Z,fz,concrete,'Interior floors')

    # Fixtures use modeled hollow bowls, not solid blocks painted as sinks.
    def oval(name,p,rx,ry,levels,mat=ceramic,group='Interior fixtures'):
        verts,faces = [],[]
        count = 40
        for z,r in levels:
            for j in range(count):
                t = 2*math.pi*j/count
                base = Vector(pt(p,z))
                verts.append((base.x+rx*r*math.cos(t),base.y+ry*r*math.sin(t),z))
        for i in range(len(levels)-1):
            for j in range(count):
                a = i*count+j
                b = i*count+(j+1)%count
                faces.append((a,b,b+count,a+count))
        faces += [tuple(reversed(range(count))),
                  tuple(range((len(levels)-1)*count,len(levels)*count))]
        ob = mesh(name,verts,faces,mat,group)
        for face in ob.data.polygons:
            if len(face.vertices) == 4:
                face.use_smooth = True
        return ob

    def tap(name,p,z,direction=(0,-1),reach=.14):
        base = Vector(pt(p,z))
        forward = Vector((direction[0],direction[1],0)).normalized()
        beam(name+' faucet riser',base,base+Vector((0,0,.22)),.025,metal,'Interior fixtures')
        beam(name+' faucet spout',base+Vector((0,0,.22)),
             base+forward*reach+Vector((0,0,.22)),.025,metal,'Interior fixtures')

    def worktop(name,bounds,height=.90):
        a,b,c,d = bounds
        # Hollow carcass leaves room for real recessed sink bowls.
        # Keep the full worktop bounds intact while building its carcass.
        for label,panel_bounds in [('west side',(a+1,b+1,a+2,d-1)),
                                   ('east side',(c-2,b+1,c-1,d-1)),
                                   ('north face',(a+2,b+1,c-2,b+2)),
                                   ('south face',(a+2,d-2,c-2,d-1))]:
            rect(name+' '+label,panel_bounds,fz+.09,height-.04,cabinet)
        rect(name+' cabinet bottom',(a+1,b+1,c-1,d-1),fz+.09,fz+.115,cabinet)
        rect(name+' recessed plinth',(a+3,b+3,c-3,d-3),fz,fz+.09,oak)
        top = rect(name+' countertop',bounds,height-.04,height,stone)
        # Fine join lines on all vertical faces remain useful at any orientation.
        count = max(1,round((c-a)*SCALE/.55))
        for i in range(1,count):
            x = a+(c-a)*i/count
            for y in (b+.8,d-.8):
                segment(name+' cabinet seam',(x,y),(x,y+.05),fz+.14,height-.08,
                        .006,oak,'Interior cabinetry')
        return top

    def sink(name,top,p,z=.90,rx=.23,ry=.18,faucet_side='north'):
        # Oval cut is concealed by the rim; the cabinet below is hollow.
        cutter = oval(name+' basin cutter',p,rx*.91,ry*.91,
                      [(z-.28,1),(z+.08,1)],None)
        difference(top,cutter)
        oval(name+' hollow basin',p,rx,ry,
             [(z-.17,.38),(z+.006,1),(z+.019,1),(z+.019,.84),
              (z-.14,.48),(z-.15,.12)])
        # Locate the faucet behind the bowl and aim its spout inward.
        if faucet_side == 'west':
            tap(name,(p[0]-(rx+.04)/SCALE,p[1]),z,(1,0),.18)
        elif faucet_side == 'south':
            tap(name,(p[0],p[1]+(ry+.04)/SCALE),z,(0,1),.18)
        elif faucet_side == 'north':
            tap(name,(p[0],p[1]-ry/SCALE-3),z)
        else:
            raise ValueError('Unsupported faucet side: '+faucet_side)

    def toilet(name,p):
        oval(name+' pedestal',p,.16,.21,[(fz,.8),(fz+.08,1),(fz+.33,.80)])
        oval(name+' bowl and seat',p,.205,.29,
             [(fz+.16,.65),(fz+.40,1),(fz+.43,1),(fz+.43,.78),
              (fz+.25,.42),(fz+.23,.05)])
        x,y = p
        rect(name+' cistern',(x-11,y-23,x+11,y-13),fz+.27,fz+.76,ceramic,
             'Interior fixtures')
        rect(name+' flush button',(x-2,y-20,x+2,y-17),fz+.76,fz+.765,metal,
             'Interior fixtures')

    def tub(name,bounds):
        a,b,c,d = bounds
        oval(name+' hollow bathtub',((a+c)/2,(b+d)/2),(c-a)*SCALE/2,(d-b)*SCALE/2,
             [(fz,.83),(fz+.50,1),(fz+.54,1),(fz+.54,.85),
              (fz+.12,.69),(fz+.10,.05)])
        tap(name,((a+c)/2,b+2),fz+.54)

    def shower(name,bounds):
        a,b,c,d = bounds
        rect(name+' shower tray',bounds,fz,fz+.055,ceramic,'Interior fixtures')
        rect(name+' drain',((a+c)/2-2,(b+d)/2-2,(a+c)/2+2,(b+d)/2+2),
             fz+.055,fz+.058,metal,'Interior fixtures')
        # Open entry on the left; partial clear screen on the lower edge.
        segment(name+' glass screen',(a+(c-a)*.35,d),(c,d),fz+.07,2.12,.012,
                shower_glass,'Interior fixtures')
        for x in (a+(c-a)*.35,c):
            beam(name+' screen post',pt((x,d),fz),pt((x,d),2.13),.025,metal,
                 'Interior fixtures')
        back = (c-5,(b+d)/2)
        beam(name+' shower riser',pt(back,1.02),pt(back,2.18),.026,metal,'Interior fixtures')
        head = Vector(pt(back,2.18))
        beam(name+' shower arm',head,head+Vector((-.22,0,0)),.024,metal,'Interior fixtures')
        box(name+' shower head',head+Vector((-.22,0,-.018)),(.18,.18,.035),metal,
            'Interior fixtures')

    # KITCHEN_PHOTO_OVERHAUL_V3
    def photo_kitchen():
        cg = 'Interior cabinetry'
        fg = 'Interior fixtures'

        white = material('Kitchen ivory enamel', (.92,.90,.83), .34)
        inset = material('Kitchen recessed panels', (.84,.82,.74), .43)
        granite = material('Kitchen dark green granite', (.03,.05,.04), .23, .001)
        honey = material('Kitchen honey oak', (.57,.31,.095), .42, .001)
        splash = material('Kitchen cream backsplash', (.80,.75,.63), .43)
        hardware = material('Kitchen satin pulls', (.49,.45,.32), .24)
        hardware.node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value = .8

        nodes = granite.node_tree.nodes
        links = granite.node_tree.links
        noise = nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = 125
        noise.inputs['Detail'].default_value = 3
        ramp = nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position = .28
        ramp.color_ramp.elements[0].color = (.009,.016,.012,1)
        ramp.color_ramp.elements[1].position = .78
        ramp.color_ramp.elements[1].color = (.21,.24,.18,1)
        links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
        links.new(ramp.outputs['Color'],
                  nodes.get('Principled BSDF').inputs['Base Color'])

        def block(name, bounds, low, high, mat=white, group=cg):
            return rect('Kitchen '+name, bounds, low, high, mat, group)

        def soft(ob):
            bevel = ob.modifiers.new('Kitchen softened edges', 'BEVEL')
            bevel.width = .004
            bevel.segments = 2
            return ob

        # u runs along the cabinet front; v points into its body.
        def q(origin, u, v, z, facing):
            x,y = origin
            if facing == 'east':
                return pt((x-v/SCALE, y+u/SCALE), z)
            if facing == 'west':
                return pt((x+v/SCALE, y+u/SCALE), z)
            return pt((x+u/SCALE, y+v/SCALE), z)

        def panel(name, origin, u, v, z, w, d, h, facing, mat=white):
            size = (d,w,h) if facing in ('east','west') else (w,d,h)
            return box('Kitchen '+name, q(origin,u,v,z,facing),
                       size, mat, cg)

        def door(name, origin, u, w, low, high, facing, drawer=False):
            mid = (low+high)/2
            panel(name+' inset', origin,u,-.012,mid,
                  w-.008,.023,high-low-.008,facing,inset)
            for side in (-1,1):
                panel(name+' stile', origin,u+side*(w/2-.024),-.028,mid,
                      .042,.026,high-low,facing)
            for z in (low+.021, high-.021):
                panel(name+' rail', origin,u,-.028,z,
                      w-.08,.026,.042,facing)
            z = mid if drawer else high-.09
            if drawer:
                beam('Kitchen drawer pull',
                     q(origin,u-.055,-.065,z,facing),
                     q(origin,u+.055,-.065,z,facing),
                     .023,hardware,cg)
            else:
                panel(name+' knob', origin,u+w*.29,-.063,z,
                      .025,.027,.025,facing,hardware)

        def unit(name, origin, width, facing='east', depth=.59,
                 low=None, high=.905, drawers=False):
            bottom = fz+.11 if low is None else low
            panel(name+' bottom', origin,0,depth/2,bottom,
                  width,depth,.022,facing)
            panel(name+' back', origin,0,depth-.01,(bottom+high)/2,
                  width,.02,high-bottom,facing)
            for side in (-1,1):
                panel(name+' side', origin,side*(width/2-.01),
                      depth/2,(bottom+high)/2,
                      .02,depth,high-bottom,facing)
            if low is None:
                panel(name+' toe kick', origin,0,depth/2+.04,fz+.05,
                      width-.04,depth-.08,.10,facing,dark)
            if drawers:
                for i in range(3):
                    a = bottom+(high-bottom)*i/3+.005
                    b = bottom+(high-bottom)*(i+1)/3-.005
                    door(name+' drawer',origin,0,width-.008,
                         a,b,facing,True)
            else:
                count = max(1,math.ceil(width/.53))
                for i in range(count):
                    w = width/count
                    door(name+' door',origin,-width/2+(i+.5)*w,
                         w-.008,bottom+.005,high-.005,facing)

        # Oak replaces kitchen tile; laundry and gallery finishes stay intact.
        floor_poly = [(367,500),(530,500),(607,440),(712,540),
                      (680,578),(680,740),(463,740),(367,730)]
        prism('Kitchen honey oak floor',floor_poly,
              INTERIOR_FLOOR_Z,fz-.002,honey,'Interior floors')
        boards = [
            material('Kitchen oak board %02d' % i,
                     (.52+i*.02,.27+i*.013,.075+i*.007),.42,.0007)
            for i in range(6)
        ]
        for ix,x in enumerate(range(370,710,7)):
            for y in range(383+(ix%3)*19,740,57):
                a,b = x+.05,max(y+.05,440)
                c,d = x+6.95,min(y+56.95,740)
                corners = ((a,b),(c,b),(c,d),(a,d))
                if d > b and all(inside(p,floor_poly) for p in corners):
                    rect('Kitchen staggered oak plank',(a,b,c,d),
                         fz-.002,fz-.001,boards[(ix+y//57)%6],
                         'Interior floors')

        # Start the west run beyond the existing bedroom doorway.
        block('west backing',(371,603,374,730),fz,2.65,paint)
        block('rear backing',(374,730,617,733),fz,2.65,paint)
        block('west backsplash',(374,604,374.8,729),.945,1.49,splash)
        block('rear backsplash',(375,729,560,729.8),.945,1.49,splash)

        for y in range(609,729,12):
            center = Vector(pt((375,y),1.18))
            offsets = ((0,-.035,0),(0,0,.045),
                       (0,.035,0),(0,0,-.045))
            mesh('Kitchen backsplash diamond',
                 [tuple(center+Vector(v)) for v in offsets],
                 [(0,1,2,3)],hardware,cg)
        for x in range(385,558,12):
            center = Vector(pt((x,728.8),1.18))
            offsets = ((-.035,0,0),(0,0,.045),
                       (.035,0,0),(0,0,-.045))
            mesh('Kitchen rear backsplash diamond',
                 [tuple(center+Vector(v)) for v in offsets],
                 [(0,1,2,3)],hardware,cg)

        for a,b in ((604,629),(672,697)):
            unit('west drawer stack',(405,(a+b)/2),
                 (b-a)*SCALE,drawers=True)
            unit('west upper',(392,(a+b)/2),(b-a)*SCALE,
                 depth=.34,low=1.49,high=2.40)
        unit('corner upper',(392,713),32*SCALE,
             depth=.34,low=1.49,high=2.40)
        block('corner base',(375,699,405,729),fz+.11,.905)
        soft(block('west front granite',(372,601,409,629),
                   .905,.945,granite))
        soft(block('west rear granite',(372,672,409,732),
                   .905,.945,granite))

        for a,b in ((409,451),(451,493),(493,535),
                    (535,560)):
            unit('rear base',((a+b)/2,699),(b-a)*SCALE,'north')
            unit('rear upper',((a+b)/2,712),(b-a)*SCALE,
                 'north',depth=.34,low=1.49,high=2.40)
        soft(block('rear granite',(409,696,561,732),
                   .905,.945,granite))

        # Stainless range and over-range microwave on photograph's right.
        block('range body',(374,630,406,671),fz,.905,metal,fg)
        block('range glass top',(373,630,407,671),.905,.932,dark,fg)
        for x in (382,398):
            for y in (640,661):
                oval('Kitchen burner rim',(x,y),.108,.108,
                     [(.932,1),(.935,1)],metal)
                oval('Kitchen burner glass',(x,y),.094,.094,
                     [(.935,1),(.937,1)],dark)
        block('oven window',(406,634,407,667),fz+.18,.70,dark,fg)
        beam('Kitchen oven handle',pt((409,635),.77),
             pt((409,666),.77),.031,metal,fg)
        for y in (636,645,656,665):
            box('Kitchen range control',pt((407.5,y),.85),
                (.026,.035,.035),hardware,fg)
        block('microwave shell',(374,630,396,671),1.53,1.99,metal,fg)
        block('microwave window',(396,633,396.6,660),1.60,1.92,dark,fg)
        beam('Kitchen microwave pull',pt((398,664),1.60),
             pt((398,664),1.91),.025,metal,fg)
        unit('microwave bridge',(392,650.5),41*SCALE,
             depth=.34,low=2.01,high=2.40)

        # Back-left refrigerator: paired doors, dispenser and freezer drawer.
        block('refrigerator carcass',(563,687,615,729),fz,2.12,dark,fg)
        for a,b in ((564,588),(589,614)):
            soft(block('refrigerator door',(a,685,b,687),
                       .70,2.10,metal,fg))
        soft(block('freezer drawer',(564,685,614,687),
                   fz+.04,.685,metal,fg))
        block('water dispenser',(568,684.5,580,685),1.12,1.46,dark,fg)
        for x in (585,592):
            beam('Kitchen fridge pull',pt((x,683),1.05),
                 pt((x,683),1.76),.029,metal,fg)
        beam('Kitchen freezer pull',pt((569,683),.58),
             pt((609,683),.58),.03,metal,fg)
        block('fridge left filler',(561,688,563,731),fz,2.42)
        block('fridge right filler',(615,688,617,731),fz,2.42)
        unit('fridge bridge',(589,712),52*SCALE,'north',
             depth=.34,low=2.16,high=2.40)

        # Capture the island assembly so every component moves together.
        island_before = set(root.all_objects)
        # Two-level sink bar, with seating toward the living-room divider.
        # Leave a circulation gap between its south end and rear counter.
        unit('sink base',(543,580),58*SCALE,'west',depth=.64)
        block('dishwasher body',(544,610,576,639),fz+.10,.90,metal,fg)
        block('dishwasher front',(542,610,544,639),fz+.11,.88,metal,fg)
        block('dishwasher controls',(541.7,610,542,639),.81,.88,dark,fg)
        beam('Kitchen dishwasher pull',pt((540,613),.76),
             pt((540,636),.76),.027,metal,fg)
        block('bar closed end',(543,639,578,641),fz,.905)
        block('bar beadboard backing',(577,556,580,641),fz,1.095)
        for y in range(557,641,2):
            block('beadboard groove',(580,y,580.18,y+.20),
                  fz+.09,1.08,inset)
        for y in (557,640):
            block('bar end post',(577,y-1,582,y+1),fz,1.10)

        # The diagram has a 45-degree change of direction (135-degree
        # inside angle), not a square L or a small clipped corner.
        def island_slab(name, polygon, low, high, mat):
            return prism(name, polygon, low, high, mat, cg)

        # Closed custom carcass follows the diagonal; no backwards-facing
        # rectangular unit protrudes into the working aisle.
        return_body = [(524,500),(576,552),(543,552),
                       (543,565),(500,522)]
        island_slab('Kitchen diagonal return cabinet',return_body,
                    fz+.10,.905,white)
        island_slab('Kitchen diagonal return plinth',
                    [(524,503),(572,551),(541,551),(541,560),(504,523)],
                    fz,fz+.10,dark)
        island_slab('Kitchen diagonal beadboard backing',
                    [(523,499),(580,556),(577,557.24),(520.88,501.12)],
                    fz,1.095,white)
        # Vertical beading and trim follow the actual diagonal face.
        for i in range(1,39):
            t = i/39
            p = (523+57*t+.10,499+57*t-.10)
            segment('Kitchen diagonal beadboard groove',p,
                    (p[0]+.14,p[1]+.14),fz+.09,1.08,.003,inset,cg)
        for z in (fz+.08,1.065):
            beam('Kitchen diagonal backing trim',pt((523,499),z),
                 pt((580,556),z),.035,white,cg)
        for t in (.22,.65):
            x,y = 523+57*t,499+57*t
            beam('Kitchen diagonal bar bracket',pt((x,y),.91),
                 pt((x+10,y-10),1.075),.045,white,cg)

        # Both long edges turn diagonally, with a continuous mitered slab.
        top = island_slab('Kitchen sink bar granite',
                    [(522,496),(580,554),(580,643),(540,643),
                     (540,570.57),(493.72,524.28)],
                    .905,.945,granite)
        for y in (570,592):
            cutter = rect('Kitchen sink cutter',
                          (548,y-9,571,y+9),.70,1.02,None,fg)
            difference(top,cutter)
            verts,faces = [],[]
            for z,rx,ry in ((.950,.240,.191),
                           (.950,.220,.172),
                           (.770,.17,.12)):
                base = Vector(pt((559.5,y),z))
                verts.extend([
                    tuple(base+Vector((sx*rx,sy*ry,0)))
                    for sx,sy in ((-1,-1),(1,-1),(1,1),(-1,1))
                ])
            for row in range(2):
                for j in range(4):
                    faces.append((
                        row*4+j,row*4+(j+1)%4,
                        (row+1)*4+(j+1)%4,(row+1)*4+j
                    ))
            faces.append((8,9,10,11))
            mesh('Kitchen stainless double sink bowl',
                 verts,faces,metal,fg)
            oval('Kitchen sink drain',(559.5,y),.032,.032,
                 [(.771,1),(.774,1)],dark)
        soft(top)

        base = Vector(pt((574.5,581),.945))
        points = [base,base+Vector((0,0,.22))]
        points += [
            base+Vector((
                -.115+.115*math.cos(math.pi*i/16),0,
                .22+.115*math.sin(math.pi*i/16)
            ))
            for i in range(1,17)
        ]
        points.append(base+Vector((-.23,0,.16)))
        for a,b in zip(points,points[1:]):
            beam('Kitchen high arch faucet',a,b,.025,metal,fg)
        beam('Kitchen faucet lever',pt((575,584),.99),
             pt((575,588),1.08),.018,metal,fg)
        # Constant-width ledge: one straight arm plus one diagonal arm.
        # Miter both edges at the bend rather than retaining a square elbow.
        soft(island_slab('Kitchen raised breakfast ledge',
                        [(521,497),(538.68,479.32),(603,543.64),
                         (603,643),(578,643),(578,554)],
                   1.095,1.14,granite))
        for y in (557,590,632):
            beam('Kitchen bar bracket',pt((580,y),.91),
                 pt((594,y),1.075),.045,white,cg)

        island_objects = set(root.all_objects)-island_before

        # Soffits and recessed lenses; leave scene lighting unchanged.
        block('west soffit',(370,601,400,735),2.43,2.68)
        block('rear soffit',(400,704,618,735),2.43,2.68)
        lens = material('Kitchen warm downlight lenses',(1.0,.84,.53),.25)
        shader = lens.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Emission Color'].default_value = (1.0,.78,.43,1)
        shader.inputs['Emission Strength'].default_value = 2.0
        lights = [(397,y) for y in (614,650,690,720)]
        lights += [(x,707) for x in (438,480,524,587)]
        for p in lights:
            oval('Kitchen downlight rim',p,.066,.066,
                 [(2.419,1),(2.432,1)],metal,cg)
            oval('Kitchen downlight lens',p,.052,.052,
                 [(2.417,1),(2.420,1)],lens,cg)

        for x,h in ((467,.20),(481,.17),(494,.15)):
            oval('Kitchen ceramic canister',(x,718),.065,.065,
                 [(.946,1),(.946+h,1)],ceramic)
            oval('Kitchen canister lid',(x,718),.07,.07,
                 [(.946+h,1),(.963+h,1)],white)

        stools_before = set(root.all_objects)
        if MAKE_KITCHEN_FURNITURE:
            group = 'Interior furniture'
            for y in (558,597,636):
                center = Vector(pt((619,y),fz))
                box('Kitchen oak stool seat',center+Vector((0,0,.77)),
                    (.43,.46,.06),honey,group)
                for sx in (-1,1):
                    for sy in (-1,1):
                        beam('Kitchen stool leg',
                             center+Vector((sx*.23,sy*.23,0)),
                             center+Vector((sx*.16,sy*.17,.75)),
                             .037,honey,group)
                for sx in (-1,1):
                    beam('Kitchen stool foot rail',
                         center+Vector((sx*.20,-.20,.29)),
                         center+Vector((sx*.20,.20,.29)),
                         .025,honey,group)
                for i in range(5):
                    beam('Kitchen stool back spindle',
                         center+Vector((.19,-.18+i*.09,.79)),
                         center+Vector((.25,-.18+i*.09,1.35)),
                         .019,honey,group)
                beam('Kitchen stool crest',
                     center+Vector((.25,-.24,1.36)),
                     center+Vector((.25,.24,1.36)),
                     .055,honey,group)

        island_objects.update(set(root.all_objects)-stools_before)
        island_shift_x = -.40  # Meters toward the west kitchen run.
        for ob in island_objects:
            ob.location.x += island_shift_x
        root['kitchen_island_shift_x'] = island_shift_x
        # Retain the south/fridge gap; only world X changes.
        assert (540-409)*SCALE+island_shift_x > 1.80

        root['kitchen_reference'] = (
            'Photo overhaul V3; living divider at photo left; '
            'dimensions estimated'
        )

    photo_kitchen()

    shared = worktop('Shared bath double vanity',(219,437,311,466),.86)
    for x in (235,291):
        sink('Shared bath basin',shared,(x,451),.86,.205,.17)
        rect('Shared bath mirror',(x-12,434,x+12,435),1.04,2.08,metal,'Interior fixtures')
    # Tank rear is 23 plan pixels behind the bowl center. Place that
    # rear face against the bathroom side of the y=431 partition.
    shared_toilet_y = 431 + thick/(2*SCALE) + 23
    toilet('Shared bath toilet',(190,shared_toilet_y))
    tub('Shared bath tub',(167,505,245,542))
    master = worktop('Master double vanity',(1037,801,1073,921),.86)
    for y in (826,895):
        sink('Master vanity basin',master,(1054,y),.86,.21,.18,
             faucet_side='west')
        rect('Master vanity mirror',(1034,y-16,1035,y+16),1.04,2.16,metal,'Interior fixtures')
    # Tank rear meets the south face of the toilet-room north wall.
    master_toilet_y = 1005 + thick/(2*SCALE) + 23
    toilet('Master enclosed toilet',(1060,master_toilet_y))
    tub('Master soaking tub',(1095,1058,1181,1103))
    def master_walk_in_shower():
        group = 'Interior fixtures'
        # Enlarged photo-estimated footprint, without moving the tub or shell.
        # Positive plan Y points toward the FRONT of the house.
        a,b,c,d = 1188,964,1248,1076
        entry_end = 1014
        top = 2.50
        wall_outer = a-thick/SCALE
        east_wall_face = 1255-WALL_THICKNESS/(2*SCALE)
        south_wall_face = 1082-WALL_THICKNESS/(2*SCALE)
        north_wall_face = 956+thick/(2*SCALE)
        rect('Master shower tray',(a,b,c,d),fz,fz+.025,ceramic,group)
        center_x = (a+c)/2
        rect('Master shower drain',(center_x-3,1051,center_x+3,1057),
             fz+.025,fz+.028,metal,group)
        rect('Master shower north tiled wall',
             (wall_outer,north_wall_face-.2,east_wall_face+.2,b),fz,top,tile,group)
        rect('Master shower east tiled wall',
             (c,b,east_wall_face+.2,south_wall_face+.2),fz,top,tile,group)
        rect('Master shower south tiled wall',
             (wall_outer,d-1,east_wall_face+.2,south_wall_face+.2),fz,top,tile,group)

        # Bathroom-facing partition replaces the old full glass screen.
        # Build around an actual viewing opening: no solid wall behind glass.
        # The north end remains a doorless, unobstructed walk-in entrance.
        win_a,win_b = 1021,1066
        sill,lintel = fz+1.10,fz+2.02
        for label,y0,y1,z0,z1 in [
                ('entry pier',entry_end,win_a,fz,top),
                ('far pier',win_b,d-1,fz,top),
                ('below window',win_a,win_b,fz,sill),
                ('above window',win_a,win_b,lintel,top)]:
            rect('Master shower window wall '+label,
                 (wall_outer,y0,a,y1),z0,z1,tile,group)
        # Pale stone reveals finish all four sides of the inset window.
        trim_px = .025/SCALE
        for y in (win_a,win_b):
            rect('Master shower window jamb',
                 (wall_outer-.15,y-trim_px/2,a+.15,y+trim_px/2),
                 sill,lintel,stone,group)
        for z in (sill,lintel):
            rect('Master shower window horizontal reveal',
                 (wall_outer-.15,win_a,a+.15,win_b),
                 z-.0125,z+.0125,stone,group)
        glass_x = (wall_outer+a)/2
        segment('Master shower viewing window glass',
                (glass_x,win_a+trim_px/2),(glass_x,win_b-trim_px/2),
                sill+.0125,lintel-.0125,.01,shower_glass,group)

        # Controls and shower head are on the far SOUTH/front-of-house wall.
        # Their projection is northward (+world Y), into the shower.
        mount = (center_x,d-3)
        for z in (1.08,2.02):
            beam('Master shower riser fixing',pt((center_x,d-1),z),
                 pt(mount,z),.03,metal,group)
        beam('Master shower riser',pt(mount,1.02),
             pt(mount,2.16),.026,metal,group)
        head = Vector(pt(mount,2.16))+Vector((0,.35,0))
        beam('Master shower arm',pt(mount,2.16),head,.026,metal,group)
        box('Master shower rain head',head+Vector((0,0,-.02)),
            (.24,.24,.04),metal,group)
        box('Master shower mixer',pt((center_x,d-2),1.05),
            (.12,.04,.12),metal,group)
        beam('Master shower mixer spindle',pt((center_x,d-2),1.05),
             pt((center_x,d-5),1.05),.025,metal,group)
        beam('Master shower mixer lever',pt((center_x,d-5),1.05),
             pt((center_x+4,d-5),1.05),.018,metal,group)

        # These geometry checks run when the script is regenerated.
        assert (entry_end-b)*SCALE > .90
        assert (c-a)*SCALE > 1.10
        assert wall_outer > 1181  # Keep clear of the existing soaking tub.
        assert entry_end < win_a < win_b < d-1
        assert b < d-3-.35/SCALE < d-1
        root['master_shower_reference'] = (
            'User description: large walk-in, interior viewing window, '
            'south-wall controls/head; dimensions estimated'
        )

    master_walk_in_shower()
    if INCLUDE_POOL_BATH:
        pooltop = worktop('Pool bath vanity',(365,194,438,220),.86)
        sink('Pool bath basin',pooltop,(402,207),.86,faucet_side='south')
        toilet('Pool bath toilet',(329,119))
        # Dedicated pool enclosure; do not alter the master shower.
        # North wall is tiled, both ends are glazed, and the south-facing
        # sliding panel is parked behind the fixed panel on the right.
        # All panels share the tray footprint and meet continuous framing.
        sg = 'Interior fixtures'
        a,b,c,d = 357,90,439,124
        mid = (a+c)/2
        sill,head = fz+.09,2.13
        rect('Pool shower tray',(a,b,c,d),fz,fz+.055,ceramic,sg)
        rect('Pool shower drain',(mid-2,105,mid+2,109),
             fz+.055,fz+.058,metal,sg)
        rect('Pool shower tiled back',(a,89.7,c,90.7),fz,head,tile,sg)
        for x in (a,c):
            segment('Pool shower side curb',(x,b),(x,d),fz,sill,.05,ceramic,sg)
            segment('Pool shower side glass',(x,b+.8),(x,d),
                    sill,head,.01,shower_glass,sg)
            for y in (b,d):
                beam('Pool shower corner post',pt((x,y),sill),
                     pt((x,y),head),.025,metal,sg)
            beam('Pool shower side top rail',pt((x,b),head),
                 pt((x,d),head),.025,metal,sg)
        segment('Pool shower front curb',(a,d),(c,d),
                fz,sill,.055,ceramic,sg)
        for z in (sill,head):
            beam('Pool shower sliding track',pt((a,d-1),z),
                 pt((c,d-1),z),.035,metal,sg,.06)
        segment('Pool shower fixed front glass',(mid,d),(c,d),
                sill+.02,head-.02,.01,shower_glass,sg)
        segment('Pool shower parked sliding glass',(mid+.5,d-2),(c-.5,d-2),
                sill+.02,head-.02,.01,shower_glass,sg)
        for x,y in ((mid,d),(mid+.5,d-2),(c-.5,d-2)):
            beam('Pool shower panel edge',pt((x,y),sill+.02),
                 pt((x,y),head-.02),.016,metal,sg)
        beam('Pool shower sliding handle',pt((mid+3,d-3),.95),
             pt((mid+3,d-3),1.18),.022,metal,sg)
        # Mount fittings to the tiled north wall, not the exterior doorway.
        beam('Pool shower riser',pt((420,92),1.0),
             pt((420,92),2.02),.026,metal,sg)
        beam('Pool shower arm',pt((420,92),2.02),
             pt((420,105),2.02),.026,metal,sg)
        box('Pool shower head',pt((420,105),2.00),
            (.18,.18,.035),metal,sg)
        box('Pool shower mixer',pt((420,92),1.02),
            (.10,.045,.10),metal,sg)

    # Laundry occupies the service strip between the bedroom and garage.
    for name,bounds in [('Washer',(305,736,338,775)),('Dryer',(345,736,379,775))]:
        a,b,c,d = bounds
        rect(name+' enamel cabinet',bounds,fz,.89,ceramic,'Interior fixtures')
        rect(name+' top lid',(a+3,b+3,c-3,d-6),.89,.91,metal,'Interior fixtures')
        rect(name+' controls',(a+2,b+1,c-2,b+5),.91,1.0,dark,'Interior fixtures')
    laundry = worktop('Laundry utility counter',(387,734,459,768))
    sink('Laundry utility sink',laundry,(442,751),rx=.22,ry=.21)
    rect('Laundry wall cabinets',(303,733,426,750),1.48,2.30,cabinet)

    def closet(name,bounds,levels=(1.72,)):
        a,b,c,d = bounds
        for z in levels:
            rect(name+' shelf',(a,b,c,d),z,z+.025,cabinet)
        if len(levels) == 1:
            segment(name+' hanging rail',(a,(b+d)/2),(c,(b+d)/2),1.57,1.60,
                    .028,metal,'Interior cabinetry')
    closet('Bedroom 3 wardrobe',(169,408,308,425))
    closet('Bedroom 2 wardrobe',(169,735,293,751))
    closet('Study storage',(940,802,1025,821))
    closet('Shared bath linen',(256,526,313,541),(.35,.70,1.05,1.40,1.75))
    # Small recessed white-panel medicine cabinet, as in the supplied photo.
    # It faces north from the restored return, not east from the vanity wall.
    med_white = material('Medicine cabinet white enamel',(.94,.93,.88),.38)
    rect('Master medicine cabinet back',(1046,926,1068,927),
         1.18,1.88,med_white)
    for x0,x1 in ((1046,1047),(1067,1068)):
        rect('Master medicine cabinet side',(x0,921,x1,926),
             1.18,1.88,med_white)
    for z in (1.18,1.42,1.65,1.86):
        rect('Master medicine cabinet shelf',(1047,921.5,1067,926),
             z,z+.02,med_white)
    # Only the frame projects from the wall; the cabinet body is recessed.
    rect('Master medicine cabinet white panel',(1046,920.5,1068,921.3),
         1.19,1.87,med_white)
    for x in (1046,1068):
        beam('Master medicine cabinet side trim',pt((x,920.1),1.18),
             pt((x,920.1),1.88),.03,med_white,'Interior cabinetry')
    for z in (1.18,1.88):
        beam('Master medicine cabinet horizontal trim',pt((1046,920.1),z),
             pt((1068,920.1),z),.03,med_white,'Interior cabinetry')
    rect('Master medicine cabinet inset panel',(1048,920.15,1066,920.5),
         1.23,1.83,cabinet)
    closet('Master walk-in north shelving',(1170,749,1245,773))
    closet('Master walk-in south shelving',(1170,927,1269,949))
    for z in (.36,.72,1.08,1.44,1.80):
        rect('Master closet east shelves',(1248,781,1271,919),z,z+.025,cabinet)
    segment('Master closet east hanging rail',(1239,785),(1239,918),1.59,1.62,
            .028,metal,'Interior cabinetry')

    # Optional illustrative loose furnishings; never use these as measured data.
    if MAKE_INTERIOR_FURNITURE:
        group = 'Interior furniture'
        def furniture(name,p,size,z,mat,angle=0):
            return box(name,pt(p,z),size,mat,group,angle)
        def bed(name,p,width=1.52):
            x,y = p
            furniture(name+' frame',p,(width+.12,2.14,.28),fz+.20,oak)
            furniture(name+' mattress',p,(width,2.02,.23),fz+.455,bedding)
            furniture(name+' blanket',(x,y+22),(width+.015,1.16,.045),fz+.59,accent)
            furniture(name+' headboard',(x,y-55),(width+.18,.085,1.1),fz+.59,oak)
            for side in (-1,1):
                furniture(name+' pillow',(x+side*width*.24/SCALE,y-34),
                          (width*.40,.43,.12),fz+.63,bedding)
                furniture(name+' nightstand',(x+side*(width/2+.34)/SCALE,y-40),
                          (.46,.44,.48),fz+.24,oak)
        def table(name,p,width,depth,height=.75):
            x,y = p
            furniture(name+' top',p,(width,depth,.055),fz+height,oak)
            for sx in (-1,1):
                for sy in (-1,1):
                    q = (x+sx*(width/2-.08)/SCALE,y+sy*(depth/2-.08)/SCALE)
                    furniture(name+' leg',q,(.055,.055,height-.03),fz+height/2,oak)
        def chair(name,p,angle=0):
            base = Vector(pt(p))
            def local(label,x,y,z,size,mat):
                offset = Vector((x*math.cos(angle)-y*math.sin(angle),
                                 x*math.sin(angle)+y*math.cos(angle),fz+z))
                box(name+' '+label,base+offset,size,mat,group,angle)
            local('seat',0,0,.45,(.46,.46,.09),fabric)
            local('back',0,.20,.73,(.46,.065,.57),fabric)
            for x in (-.17,.17):
                for y in (-.17,.17):
                    local('leg',x,y,.22,(.035,.035,.44),oak)
        def sofa(name,p,width=2.20,angle=0):
            base = Vector(pt(p))
            def local(label,x,y,z,size,mat=fabric):
                offset = Vector((x*math.cos(angle)-y*math.sin(angle),
                                 x*math.sin(angle)+y*math.cos(angle),fz+z))
                box(name+' '+label,base+offset,size,mat,group,angle)
            local('base',0,0,.24,(width,.88,.30))
            local('back',0,.36,.64,(width,.18,.70))
            for x in (-width/2+.09,width/2-.09):
                local('arm',x,0,.52,(.18,.88,.45))
            for i in range(3):
                local('seat cushion',-width/3+i*width/3,-.03,.46,
                      ((width-.40)/3,.66,.16))
        bed('Bedroom 3 bed',(252,315))
        bed('Bedroom 2 bed',(252,633))
        bed('Master king bed',(1148,644),1.93)
        furniture('Bedroom 3 dresser',(340,307),(.43,1.15,.85),fz+.425,oak)
        furniture('Bedroom 2 dresser',(340,635),(.43,1.15,.85),fz+.425,oak)
        sofa('Family room sofa',(475,402),2.35,math.pi)
        table('Family coffee table',(474,346),1.15,.62,.40)
        furniture('Family media console',(559,209),(1.37,.45,.58),fz+.29,oak)
        furniture('Family television',(559,204),(1.30,.045,.76),1.30,dark)
        furniture('Family optional fireplace',(482,210),(1.36,.62,1.16),fz+.58,stone)
        furniture('Family fireplace inset',(482,227),(.88,.025,.60),fz+.55,dark)
        sofa('Living room sofa',(845,608),2.25)
        table('Living coffee table',(846,665),1.18,.62,.40)
        chair('Living accent chair',(931,673),-math.pi/2)
        table('Dining table',(613,887),1.02,1.88)
        for x,angle in [(566,-math.pi/2),(660,math.pi/2)]:
            for y in (855,896,936):
                chair('Dining chair',(x,y),angle)
        table('Study desk',(963,970),1.48,.68)
        chair('Study desk chair',(963,924),math.pi)
        furniture('Study bookcase',(854,949),(.33,1.65,1.85),fz+.925,oak)
        chair('Master sitting chair left',(1150,485),.35)
        chair('Master sitting chair right',(1222,487),-.35)
        table('Master sitting side table',(1187,490),.40,.40,.48)
        # Bar-height oak stools are built by photo_kitchen().
        table('Garage workbench',(423,1197),2.40,.66,.91)

    if MAKE_INTERIOR_CEILINGS:
        prism('Interior ceiling slab',outline,WALL_HEIGHT,WALL_HEIGHT+.08,paint,
              'Interior ceilings')
    root['interior_reference'] = 'User supplied 4690 Deer Creek floorplan, 1440px'
    root['interior_accuracy'] = 'Manual tracing; not construction or survey geometry'


if MAKE_INTERIOR:
    build_interior()

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

# Optional inspection mode affects generated roof/ceiling collections only.
# Render visibility, cameras, lights and unrelated scene objects are unchanged.
if MAKE_INTERIOR and INTERIOR_CUTAWAY:
    groups['Roofs'].hide_viewport = True
    groups['Interior ceilings'].hide_viewport = True

# House geometry only: no site, pool, cameras, lights, or presentation setup.
