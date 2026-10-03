"""4690 Deer Creek Boulevard — exterior reference reconstruction.
Run in Blender's Scripting workspace (Text > Open > Run Script).
No external packages or image files required. Designed for Blender 4.x/5.x.
Only objects in the generated H4690 collection are replaced on rerun.

REFERENCE / ACCURACY NOTES
Floorplan coordinates were manually traced from the supplied 1440px image.
Scale: approximately 207 image pixels = 13 feet. Front = negative world Y.
The plan is not a survey; wall heights, roof layout/pitch, window elevations,
spa, cage dimensions and finishes are photo-based estimates. Optional rear
pool bathroom is included; its existence is not confirmed by the photographs.
Pool outline follows the plan; raised spa is inferred from the pool photograph.
Roof intersections are overlapping hip volumes, not construction-ready framing.
No interior partitions, furniture, landscaping that hides the facade, or automatic
.blend save. Cameras and lighting are provided. All lengths are in meters.
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
MAKE_SCREEN_MESH = True
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
for name in ['Shell', 'Openings', 'Trim', 'Roofs', 'Pool', 'Enclosure', 'Site', 'Cameras']:
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
blue = material('Waterline mosaic blue', (0.055, 0.28, 0.40), 0.26)
plaster = material('Pool interior turquoise', (0.16, 0.56, 0.58), 0.35)
water = material('Pool water', (0.08, 0.55, 0.59), 0.10)
ws = water.node_tree.nodes.get('Principled BSDF')
for socket in ('Transmission Weight', 'Transmission'):
    if socket in ws.inputs:
        ws.inputs[socket].default_value = 0.65
ws.inputs['IOR'].default_value = 1.333
wn = water.node_tree.nodes.new('ShaderNodeTexNoise')
wn.inputs['Scale'].default_value = 4.5
wb = water.node_tree.nodes.new('ShaderNodeBump')
wb.inputs['Strength'].default_value = .18
wb.inputs['Distance'].default_value = .05
water.node_tree.links.new(wn.outputs['Fac'], wb.inputs['Height'])
water.node_tree.links.new(wb.outputs['Normal'], ws.inputs['Normal'])
grass = material('Lawn', (0.16, 0.25, 0.07), noise=.035)
concrete = material('Driveway concrete', (.63, .60, .52), noise=.016)
screen = material('Insect screen', (.16, .20, .19))
sn = screen.node_tree.nodes
sn.clear()
so = sn.new('ShaderNodeOutputMaterial')
st = sn.new('ShaderNodeBsdfTransparent')
sd = sn.new('ShaderNodeBsdfDiffuse')
sd.inputs['Color'].default_value = (.13, .17, .15, 1)
sm = sn.new('ShaderNodeMixShader')
sm.inputs[0].default_value = .045
screen.node_tree.links.new(st.outputs[0], sm.inputs[1])
screen.node_tree.links.new(sd.outputs[0], sm.inputs[2])
screen.node_tree.links.new(sm.outputs[0], so.inputs['Surface'])


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


# Front-facing windows: pair in garage wing, dining, study, master bath.
for p in [(264,1240),(447,1240),(610,990),(923,1020)]:
    opening('Front arched window',p,1.12,.68,2.31,.43)
opening('Bath privacy window',(1140,1110),1.20,1.40,2.26,.25)
opening('Recessed double entry',(772,902),1.74,.03,2.22,.54,True)
# Left elevation bedroom and bath openings, plus front side garage window.
for p,w,z in [((160,250),.80,.85),((160,474),.64,1.40),((160,633),1.20,.76),
              ((201,216),.94,.83)]:
    opening('West elevation window',p,w,z,2.36,0)
if INCLUDE_POOL_BATH:
    opening('Pool bath window',(300,155),.60,1.55,2.38,0)
for p,w in [((1257,460),1.20),((1200,414),1.40)]:
    opening('Master sitting window',p,w,.70,2.45,.20)
# Large rear sliding glass openings on the lanai.
opening('Family room pool slider',(607,322),2.44,.035,2.62,0,True)
opening('Living room pool slider',(850,540),3.50,.035,2.62,0,True)
opening('Angled master pool door',(1038,475),1.75,.035,2.62,0,True)


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

# Front porch and signature three-bay arched colonnade.
slab('Front porch paving',(524,902,1032,1080),-.04,.035,pavers,'Site')
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
# Small white decorative gate at recessed entry, visible in reference.
for x in range(733,816,9):
    beam('Entry gate picket',pt((x,1042),.08),pt((x,1042),.89+.17*math.sin((x-733)/83*math.pi)),.023)
for z in (.23,.73):
    beam('Entry gate rail',pt((727,1042),z),pt((821,1042),z),.035)
# Quoin-like corner blocks seen on the garage wing.
for x,y in [(186,1240),(524,1240),(160,216),(1257,414)]:
    for z in (.36,.85,1.34,1.83,2.32,2.81):
        box('Corner stucco quoin',pt((x,y),z),(.38,.37,.22),trim,'Trim')

# -------------------------- roofs --------------------------
# Hip components are deliberately separate and editable. The overlaid tiles are
# suppressed wherever another hip is higher, reducing visible intersection clutter.
roof_specs = [
    ('Garage hip',(160,735,524,1240),3.25),
    ('West bedroom family hip',(160,212,608,816),3.25),
    ('Main entry living hip',(520,515,1100,1080),3.48),
    ('Master suite hip',(969,414,1258,1083),3.25),
    ('Bath projection hip',(1082,950,1258,1110),3.23),
]
if INCLUDE_POOL_BATH:
    roof_specs.append(('Pool bath hip',(300,84,446,238),3.20))
roofs = []
for name,(a,b,c,d),eave in roof_specs:
    o = ROOF_OVERHANG_PX
    xmin,ymax = xy((a-o,b-o)); xmax,ymin = xy((c+o,d+o))
    roofs.append((name,xmin,xmax,ymin,ymax,eave))


def roof_z(r,x,y):
    _,a,b,c,d,z = r
    if not (a-1e-5 <= x <= b+1e-5 and c-1e-5 <= y <= d+1e-5):
        return -100
    return z+ROOF_PITCH*min(x-a,b-x,y-c,d-y)


for r in roofs:
    name,a,b,c,d,z = r
    h = min(b-a,d-c)/2
    corners = [(a,c,z),(b,c,z),(b,d,z),(a,d,z)]
    if b-a <= d-c:
        ridge = [((a+b)/2,c+h,z+h*ROOF_PITCH),((a+b)/2,d-h,z+h*ROOF_PITCH)]
        faces = [(0,1,4),(1,2,5,4),(2,3,5),(3,0,4,5)]
    else:
        ridge = [(a+h,(c+d)/2,z+h*ROOF_PITCH),(b-h,(c+d)/2,z+h*ROOF_PITCH)]
        faces = [(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4)]
    ob = mesh(name,corners+ridge,faces,roofmat,'Roofs')
    solid = ob.modifiers.new('Roof thickness','SOLIDIFY'); solid.thickness=.065
    for i in range(4):
        q0,q1 = corners[i],corners[(i+1)%4]
        beam('Eave fascia',q0,q1,.14,trim,'Roofs',.17)
        beam('Rain gutter',Vector(q0)+Vector((0,0,.035)),Vector(q1)+Vector((0,0,.035)),.07,trim,'Roofs')
    beam('Hip ridge cap',ridge[0],ridge[1],.16,roofmat,'Roofs')

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
prism('Lanai paving',lanai,-.03,.025,pavers,'Pool')
prism('Covered lanai roof',lanai,3.03,3.18,roofmat,'Roofs')
beam('Lanai rear fascia',pt((607,410),3.08),pt((1100,410),3.08),.18)
for x in (617,1090):
    box('Lanai support',pt((x,420),1.50),(.20,.20,3.00),stucco,'Trim')

# -------------------------- pool and site --------------------------
pool_outline = [(684,147),(715,119),(810,119),(840,147),(1128,147),
                (1163,179),(1163,281),(1095,347),(929,347),(909,328),
                (816,328),(784,297),(715,297),(715,250),(684,221)]
deck_outline = [(447,81),(1258,81),(1258,410),(607,410),(607,188),(447,188)]
# Pool cavity genuinely cuts through the deck and lawn, not a blue slab on top.
lawn = slab('Lawn ground',(-430,-270,1750,1740),-1.80,-.13,grass,'Site')
difference(lawn,prism('Ground pool excavation',pool_outline,-2.0,.30,None,'Pool'))
deck = prism('Pool deck',deck_outline,-.12,.005,pavers,'Pool')
difference(deck,prism('Deck pool opening',pool_outline,-.30,.30,None,'Pool'))
prism('Pool bottom',pool_outline,-1.49,-1.44,plaster,'Pool')
for i,p in enumerate(pool_outline):
    q = pool_outline[(i+1)%len(pool_outline)]
    av,bv = Vector(pt(p)),Vector(pt(q)); mid = (av+bv)/2
    angle = math.atan2(bv.y-av.y,bv.x-av.x)
    box('Pool basin wall',(*mid[:2],-.73),((bv-av).length,.12,1.44),plaster,'Pool',angle)
    box('Blue waterline tile',(*mid[:2],-.12),((bv-av).length,.135,.25),blue,'Pool',angle)
    box('Wide cream pool coping',(*mid[:2],.035),((bv-av).length+.035,.43,.10),coping,'Pool',angle)
mesh('Water surface',[pt(p,-.16) for p in pool_outline],[tuple(range(len(pool_outline)))],water,'Pool')
# Broad shallow entry steps at the angular end of the pool.
for i,(bounds,top) in enumerate([((718,251,781,278),-.28),((724,278,786,296),-.47),((749,298,806,316),-.66)]):
    slab('Submerged entry step %d'%i,bounds,-1.43,top,plaster,'Pool')
# Photo shows a raised square spa at the far end; its exact location is uncertain.
spa_bounds = (851,88,970,145)
spa = slab('Raised spa body',spa_bounds,-.10,.42,blue,'Pool')
difference(spa,slab('Spa hollow',(860,96,961,138),-.01,.65,None,'Pool'))
slab('Spa water',(860,96,961,138),.28,.29,water,'Pool')
for a,b in [((851,88),(970,88)),((970,88),(970,145)),((970,145),(851,145)),((851,145),(851,88))]:
    beam('Spa coping',pt(a,.43),pt(b,.43),.16,coping,'Pool')
# Suggest paving joints without a heavyweight individual paver array.
for y in range(90,411,24):
    # Only left deck strip: never lay joint geometry across the water.
    beam('Deck paving joint',pt((620,y),.012),pt((668,y),.012),.009,concrete,'Pool')

# Screen enclosure: white aluminum posts, horizontal rails, pitched roof frames.
x0,x1 = 607,1258
y0,y1 = 81,410
cage_eave,cage_ridge = 3.55,4.95
xm = (x0+x1)/2
for y in (y0,163,245,327,y1):
    roofline = [(x0,y,cage_eave),(xm,y,cage_ridge),(x1,y,cage_eave)]
    for x in (x0,x1):
        beam('Screen cage upright',pt((x,y),.03),pt((x,y),cage_eave),.055,trim,'Enclosure')
    for a,b in zip(roofline,roofline[1:]):
        beam('Screen roof rib',pt(a[:2],a[2]),pt(b[:2],b[2]),.055,trim,'Enclosure')
for x in (x0,(x0+xm)/2,xm,(xm+x1)/2,x1):
    z = cage_eave+(cage_ridge-cage_eave)*(1-abs(x-xm)/(xm-x0))
    beam('Screen roof purlin',pt((x,y0),z),pt((x,y1),z),.045,trim,'Enclosure')
for a,b in [((x0,y0),(x1,y0)),((x1,y0),(x1,y1)),((x0,y0),(x0,y1))]:
    for z in (.09,1.12,2.35,cage_eave):
        beam('Screen horizontal rail',pt(a,z),pt(b,z),.045,trim,'Enclosure')
    if MAKE_SCREEN_MESH:
        mesh('Fine transparent screen',[pt(a,.04),pt(b,.04),pt(b,cage_eave),pt(a,cage_eave)],[(0,1,2,3)],screen,'Enclosure')
for x in (735,866,996,1127):
    beam('Rear screen upright',pt((x,y0),.03),pt((x,y0),cage_eave),.055,trim,'Enclosure')
if MAKE_SCREEN_MESH:
    for a,b in [(x0,xm),(xm,x1)]:
        za = cage_ridge if a==xm else cage_eave
        zb = cage_ridge if b==xm else cage_eave
        mesh('Roof insect screen',[pt((a,y0),za),pt((b,y0),zb),pt((b,y1),zb),pt((a,y1),za)],[(0,1,2,3)],screen,'Enclosure')
    mesh('Screen gable',[pt((x0,y0),cage_eave),pt((x1,y0),cage_eave),pt((xm,y0),cage_ridge)],[(0,1,2)],screen,'Enclosure')

# Driveway side apron and front walkway, approximate because plan omits site.
prism('Side entry driveway',[(-310,780),(148,780),(148,1068),(174,1068),
                            (174,1300),(-20,1530),(-310,1530)],-.12,-.045,concrete,'Site')
prism('Front walk',[(714,1080),(817,1080),(817,1130),(735,1210),
                    (665,1280),(560,1350),(270,1410),(252,1370),
                    (526,1305),(632,1230),(704,1160)],-.10,-.025,concrete,'Site')
# Driveway control joints.
for y in (910,1090,1270,1450):
    beam('Driveway control joint',pt((-310,y),-.039),pt((130,y),-.039),.014,shadow,'Site')

# -------------------------- presentation --------------------------
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'METERS'
scene.render.engine = 'CYCLES'
scene.cycles.samples = 48
scene.cycles.use_denoising = True
scene.render.resolution_x = 1600
scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.world = bpy.data.worlds.new(PREFIX+'_Daylight')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.68,.79,1,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .45
sun_data = bpy.data.lights.new(PREFIX+'_Sun','SUN'); sun_data.energy=2.6
sun_data.angle=math.radians(10)
sun = bpy.data.objects.new('Afternoon sun',sun_data); groups['Cameras'].objects.link(sun)
sun.rotation_euler = (math.radians(28),math.radians(-24),math.radians(-38))


def camera(name,location,target,lens=42):
    data = bpy.data.cameras.new(PREFIX+'_'+name)
    ob = bpy.data.objects.new(name,data); groups['Cameras'].objects.link(ob)
    ob.location=location
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
    data.lens=lens; data.clip_end=500
    return ob


scene.camera=camera('Front exterior',(-1,-30,6.0),(0,4,1.7),40)
camera('Driveway exterior',(-28,-12,5.2),(-6,5,1.8),43)
camera('Pool exterior',(9,22,2.6),(0,9,1.3),22)
camera('Aerial overview',(-30,-30,35),(0,9,0),43)
plan_cam=camera('Plan verification',(0,9,45),(0,9,0),45)
plan_cam.data.type='ORTHO'; plan_cam.data.ortho_scale=30
# Add project metadata inside the blend; makes assumptions visible later.
root['reference_scale_m_per_pixel']=SCALE
root['accuracy']='Manually traced plan; photo-estimated elevations, roof and site. Not surveyed.'
root['orientation']='Front is -Y; garage driveway is -X; pool is +Y.'
root['roof_note']='Editable overlapping hip components; not a watertight construction roof.'
for screen_ui in bpy.data.screens:
    for area in screen_ui.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.clip_end=500
            area.spaces.active.region_3d.view_distance=40
            area.spaces.active.region_3d.view_location=(0,8,1.5)
bpy.ops.object.select_all(action='DESELECT')
print('4690 exterior generated. Cameras: Front / Driveway / Pool / Aerial / Plan verification.')
print('No .blend file saved automatically. Save As to preserve the generated model.')
