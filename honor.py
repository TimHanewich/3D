# MADE BY GPT-6.1-sol on low reasoning

"""HONOR — brochure-based C-1 reconstruction.
Run in Blender's Scripting workspace with Run Script (Alt-P).
Only replaces the HONOR collection; other scene objects are preserved.
Meters; front is -Y. Geometry traced from the supplied page-2 plan.

SCALE: approximately 27.3 image pixels/foot, calibrated to the garage
18'4\" width and lanai 16'4\" width. Printed room sizes are clear sizes;
wall centerline extents will differ. This is a visualization, not a survey.
Ground ceiling 9'4\", upper ceiling 8'8\". Floor structure, wall thickness,
roof pitch, non-front windows and fixtures are inferred. The apparent
second 'Garage' label is retained as garage storage, NOT an extra room.
Base layout: three bedrooms, loft, leisure room, standard master bath.
Optional fourth bedroom, bath and lanai extension are not modeled.

Hide 'HONOR / Roof' and 'HONOR / Upper' to inspect the ground floor.
Hide Roof only for upstairs. Labels are hidden in renders by default.
No external assets, packages or image files are needed.
"""
import bpy
import math
from mathutils import Vector

SHOW_LABELS = False
ADD_FURNITURE = True
S = 0.3048 / 27.3
GROUND = 0.12
H0 = 2.8448
STRUCTURE = 0.25
UPPER = GROUND + H0 + STRUCTURE
H1 = 2.6416
EXTERIOR = 0.20
PARTITION = 0.115

# Remove our own previous build only.
old = bpy.data.collections.get('HONOR')
if old:
    def discard(c):
        for child in list(c.children):
            discard(child)
        for obj in list(c.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(c)
    discard(old)
root = bpy.data.collections.new('HONOR')
bpy.context.scene.collection.children.link(root)
collections = {}
for key in ('Ground', 'Upper', 'Roof', 'Site', 'Labels', 'Presentation'):
    c = bpy.data.collections.new('HONOR / ' + key)
    root.children.link(c)
    collections[key] = c
collections['Labels'].hide_render = True
collections['Labels'].hide_viewport = not SHOW_LABELS

def material(name, color, roughness=0.65, metallic=0.0):
    m = bpy.data.materials.new('Honor ' + name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Metallic'].default_value = metallic
    return m
stucco = material('sage stucco', (0.60, 0.64, 0.56))
siding = material('sage siding', (0.48, 0.55, 0.50))
white = material('ivory trim', (0.91, 0.90, 0.85))
inside = material('interior plaster', (0.85, 0.82, 0.75))
concrete = material('concrete', (0.56, 0.57, 0.55))
wood = material('oak floors', (0.48, 0.31, 0.17))
tile = material('cream floor tile', (0.70, 0.68, 0.59))
roofmat = material('brown roof tiles', (0.25, 0.13, 0.09))
door_mat = material('blue entry', (0.27, 0.40, 0.44))
garage_mat = material('garage gray', (0.30, 0.34, 0.31))
glass = material('blue glazing', (0.07, 0.16, 0.20), 0.15, 0.35)
metal = material('hardware', (0.12, 0.13, 0.12), 0.25, 0.6)
grass = material('lawn', (0.13, 0.25, 0.07))
fabric = material('linen', (0.66, 0.65, 0.57))
# Fine relief on the tiled roof; actual roof planes and ridge caps are geometry.
n = roofmat.node_tree.nodes
l = roofmat.node_tree.links
tex = n.new('ShaderNodeTexNoise')
tex.inputs['Scale'].default_value = 65
tex.inputs['Detail'].default_value = 2
bump = n.new('ShaderNodeBump')
bump.inputs['Strength'].default_value = 0.45
bump.inputs['Distance'].default_value = 0.045
l.new(tex.outputs['Fac'], bump.inputs['Height'])
l.new(bump.outputs['Normal'], n.get('Principled BSDF').inputs['Normal'])

def mesh(name, verts, faces, mat, group):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    collections[group].objects.link(obj)
    if mat:
        data.materials.append(mat)
    return obj

def box(name, center, size, mat, group='Ground'):
    x, y, z = center
    a, b, c = (v / 2 for v in size)
    verts = [(x+dx*a, y+dy*b, z+dz*c) for dx,dy,dz in
             [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
              (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    return mesh(name, verts, [(0,3,2,1),(4,5,6,7),(0,1,5,4),
                             (1,2,6,5),(2,3,7,6),(3,0,4,7)], mat, group)

def xy(px, py):
    return ((px-453)*S, (2435-py)*S)

def rect(name, x0, y0, x1, y1, z, depth, mat, group='Ground'):
    a, b = xy(x0,y0), xy(x1,y1)
    return box(name, ((a[0]+b[0])/2,(a[1]+b[1])/2,z),
               (abs(b[0]-a[0]),abs(b[1]-a[1]),depth), mat, group)

def beam(name, a, b, width, mat, group):
    a, b = Vector(a), Vector(b)
    obj = box(name, (a+b)/2, (width,width,(b-a).length), mat, group)
    obj.rotation_euler = (b-a).to_track_quat('Z','Y').to_euler()
    return obj

# Each opening is (start pixel, end pixel, sill meters, head meters, type).
# Horizontal wall opening positions are X; vertical wall positions are image Y.
def wall(name, a, b, base, height, group, openings=(), exterior=False):
    horizontal = a[1] == b[1]
    lo, hi = sorted((a[0],b[0]) if horizontal else (a[1],b[1]))
    fixed = a[1] if horizontal else a[0]
    thick = EXTERIOR if exterior else PARTITION
    mat = (siding if group == 'Upper' else stucco) if exterior else inside
    def piece(u, v, z0, z1, suffix):
        if v-u < 0.01 or z1-z0 < 0.001:
            return
        pt = xy((u+v)/2,fixed) if horizontal else xy(fixed,(u+v)/2)
        dims = ((v-u)*S,thick,z1-z0) if horizontal else (thick,(v-u)*S,z1-z0)
        box(name+' '+suffix, (*pt,base+(z0+z1)/2), dims, mat, group)
        if exterior and group == 'Upper':
            # Thin lap-siding shadow courses on both faces, clipped to solid wall pieces.
            z = math.ceil(z0/0.18)*0.18
            while z < z1:
                for side in (-1,1):
                    p = list(pt)
                    p[1 if horizontal else 0] += side*(thick/2+0.007)
                    d = ((v-u)*S,0.016,0.018) if horizontal else (0.016,(v-u)*S,0.018)
                    box(name+' siding course', (*p,base+z),d,siding,group)
                z += 0.18
    cursor = lo
    for u,v,sill,head,kind in sorted(openings):
        piece(cursor,u,0,height,'pier')
        piece(u,v,0,sill,'sill wall')
        piece(u,v,head,height,'lintel')
        opening(name, horizontal, fixed, u,v,base+sill,base+head,kind,group)
        cursor = v
    piece(cursor,hi,0,height,'solid')

def opening(name, horizontal, fixed, u,v,z0,z1,kind,group):
    pt = xy((u+v)/2,fixed) if horizontal else xy(fixed,(u+v)/2)
    width, height = (v-u)*S,z1-z0
    def part(label, along, z, w,h,depth,mat):
        p = list(pt)
        p[0 if horizontal else 1] += along
        dims = (w,depth,h) if horizontal else (depth,w,h)
        return box(name+' '+label,(*p,z),dims,mat,group)
    if kind == 'pass':
        return
    is_window = kind in ('window','slider')
    panelmat = glass if is_window else (garage_mat if kind=='garage' else door_mat)
    part(kind,0,(z0+z1)/2,width,height,0.045,panelmat)
    for d in (-1,1):
        part('jamb',d*(width/2+0.035),(z0+z1)/2,0.09,height+0.16,0.25,white)
    part('head casing',0,z1+0.045,width+0.18,0.10,0.26,white)
    if is_window:
        part('sill casing',0,z0-0.035,width+0.22,0.10,0.28,white)
        cols = 3 if kind=='slider' else 3
        rows = 1 if kind=='slider' else 4
        for i in range(1,cols):
            part('mullion',-width/2+i*width/cols,(z0+z1)/2,0.025,height,0.12,white)
        for i in range(1,rows):
            part('muntin',0,z0+i*height/rows,width,0.025,0.12,white)
    elif kind=='garage':
        for row in range(4):
            for col in range(4):
                part('raised garage panel',-width/2+(col+0.5)*width/4,
                     z0+(row+0.5)*height/4,width/4-0.09,height/4-0.08,0.075,garage_mat)
    else:
        for f,h in ((0.18,0.32),(0.53,0.88),(0.87,0.25)):
            part('door panel',0,z0+height*f,width*0.72,h,0.075,panelmat)
        part('handle',width*0.35,z0+1.02,0.035,0.13,0.13,metal)

# Ground slabs: rear/main, garage projection, lanai, porch.
rect('Ground main slab',453,895,1348,1863,GROUND-0.10,0.20,concrete)
rect('Garage slab',453,1502,980,2435,GROUND-0.09,0.18,concrete)
rect('Lanai paving',453,665,896,895,GROUND-0.07,0.14,tile)
rect('Entry paving',980,1863,1348,1985,GROUND-0.05,0.10,concrete)
# Perimeter including the garage's stepped return.
wall('Left exterior',(453,895),(453,2435),GROUND,H0,'Ground',exterior=True)
wall('Rear exterior',(453,895),(1348,895),GROUND,H0,'Ground',
     [(534,785,0,2.32,'slider'),(980,1244,0.85,2.34,'window')],True)
wall('Right exterior',(1348,895),(1348,1863),GROUND,H0,'Ground',exterior=True)
wall('Front house',(780,1863),(1348,1863),GROUND,H0,'Ground',
     [(1007,1097,0.65,2.30,'window'),(1140,1227,0,2.40,'door')],True)
wall('Garage return',(980,1863),(980,2435),GROUND,H0,'Ground',exterior=True)
wall('Garage front',(453,2435),(980,2435),GROUND,H0,'Ground',
     [(492,939,0,2.42,'garage')],True)
# Garage storage leg and leisure/foyer partitions.
wall('Garage leisure division',(780,1502),(780,1863),GROUND,H0,'Ground')
wall('Garage storage rear',(453,1502),(780,1502),GROUND,H0,'Ground',
     [(520,595,0,2.1,'door')])
wall('Mudroom kitchen',(453,1343),(780,1343),GROUND,H0,'Ground',
     [(530,621,0,2.2,'pass')])
wall('Mudroom right',(780,1343),(780,1502),GROUND,H0,'Ground')
wall('Mudroom closet',(621,1343),(621,1497),GROUND,H0,'Ground',
     [(1393,1467,0,2.1,'door')])
wall('Leisure cafe',(780,1502),(1243,1502),GROUND,H0,'Ground',
     [(1007,1114,0,2.30,'pass')])
wall('Powder north',(1243,1650),(1348,1650),GROUND,H0,'Ground')
wall('Powder foyer',(1243,1650),(1243,1863),GROUND,H0,'Ground',
     [(1717,1791,0,2.10,'door')])
# Open-plan ground floor: no invented wall between kitchen, cafe and great room.
rect('Kitchen tiled floor',463,905,839,1341,GROUND+0.009,0.018,tile)
rect('Living floor',840,905,1337,1494,GROUND+0.008,0.016,wood)
rect('Leisure floor',790,1513,1113,1852,GROUND+0.008,0.016,wood)
rect('Foyer tile',1114,1503,1237,1854,GROUND+0.009,0.018,tile)
rect('Powder tile',1250,1658,1339,1853,GROUND+0.009,0.018,tile)

# Upper rectangle matches page-2 upper floor; image X offset 1039, Y offset 7.
# The right-hand stair opening remains genuinely open in the slab.
rect('Upper slab west',453,895,1235,1863,UPPER-STRUCTURE/2,STRUCTURE,wood,'Upper')
rect('Upper slab rear stair landing',1235,895,1348,1384,UPPER-STRUCTURE/2,STRUCTURE,wood,'Upper')
rect('Upper slab stair foot',1235,1747,1348,1863,UPPER-STRUCTURE/2,STRUCTURE,wood,'Upper')
wall('Upper rear',(453,895),(1348,895),UPPER,H1,'Upper',
     [(844,929,1.2,2.25,'window'),(985,1067,0.78,2.27,'window'),
      (1223,1308,0.78,2.27,'window')],True)
wall('Upper front',(453,1863),(1348,1863),UPPER,H1,'Upper',
     [(497,586,0.65,2.32,'window'),(1005,1091,0.65,2.32,'window'),
      (1218,1307,0.65,2.32,'window')],True)
wall('Upper left',(453,895),(453,1863),UPPER,H1,'Upper',
     [(1298,1385,0.8,2.25,'window')],True)
wall('Upper right',(1348,895),(1348,1863),UPPER,H1,'Upper',
     [(1523,1601,0.8,2.25,'window')],True)
# Upper bedroom / bathroom / utility layout traced from the brochure.
upper_walls = [
 ('Master west',(959,895),(959,1450),[(1315,1392,0,2.1,'door')]),
 ('Master closet front',(1058,1387),(1348,1387),[]),
 ('Master closet back',(1058,1320),(1348,1320),[(1156,1276,0,2.2,'slider')]),
 ('Master closet return',(1058,1320),(1058,1450),[]),
 ('Bath bedroom3',(453,1110),(777,1110),[]),
 ('Master WIC',(631,895),(631,1110),[(1006,1074,0,2.1,'door')]),
 ('Bath WC',(777,1080),(959,1080),[(824,897,0,2.1,'door')]),
 ('WC south',(777,1173),(959,1173),[]),
 ('Service spine',(777,1080),(777,1450),[(1112,1170,0,2.1,'door')]),
 ('HVAC south',(777,1268),(959,1268),[]),
 ('Laundry front',(777,1450),(959,1450),[(871,947,0,2.1,'door')]),
 ('Bedroom3 hall',(671,1110),(671,1450),[(1375,1448,0,2.1,'door')]),
 ('Bedroom3 closet',(453,1417),(671,1417),[(480,604,0,2.1,'slider')]),
 ('Bedroom3 closet front',(453,1483),(671,1483),[]),
 ('Bedroom2 hall',(671,1549),(671,1863),[(1551,1627,0,2.1,'door')]),
 ('Bedroom2 closet',(453,1549),(671,1549),[(477,604,0,2.1,'slider')]),
 ('Bath2 west',(777,1549),(777,1863),[]),
 ('Bath2 east',(929,1549),(929,1863),[]),
 ('Bath2 north',(777,1549),(929,1549),[(787,862,0,2.1,'door')]),
]
for name,a,b,holes in upper_walls:
    wall(name,a,b,UPPER,H1,'Upper',holes)
for name,x0,y0,x1,y1 in [ ('Master bath',637,903,950,1106),
                         ('WC',784,1087,952,1167),('Laundry',784,1275,950,1444),
                         ('Bath2',784,1556,923,1855)]:
    rect(name+' tile',x0,y0,x1,y1,UPPER+0.012,0.024,tile,'Upper')

# Stairs rise toward the rear (+Y), in the right-hand plan strip.
nsteps = 17
start_y, end_y = 1747,1345
for i in range(nsteps):
    y0 = start_y-(start_y-end_y)*(i+1)/nsteps
    y1 = start_y-(start_y-end_y)*i/nsteps
    top = GROUND+(UPPER-GROUND)*(i+1)/nsteps
    rect('Stair %02d'%(i+1),1246,y0,1337,y1,(GROUND+top)/2,top-GROUND,wood)
# Sloping rail, plus upper landing guards.
p0=xy(1240,start_y); p1=xy(1240,end_y)
beam('Stair handrail',(*p0,GROUND+0.95),(*p1,UPPER+0.95),0.055,white,'Ground')
for i in range(0,nsteps,2):
    f=i/(nsteps-1)
    p=(p0[0],p0[1]+f*(p1[1]-p0[1]))
    z=GROUND+f*(UPPER-GROUND)
    beam('Stair baluster',(*p,z),(*p,z+0.92),0.035,white,'Ground')
a,b=xy(1238,1385),xy(1238,1747)
beam('Loft guard top',(*a,UPPER+1),(*b,UPPER+1),0.06,white,'Upper')
for i in range(19):
    f=i/18
    p=(a[0],a[1]+f*(b[1]-a[1]))
    beam('Loft guard spindle',(*p,UPPER),(*p,UPPER+1),0.035,white,'Upper')

# Hipped C-1 roofs. Long ridge runs along Y; equal slopes on all hips.
def hip(name,x0,y0,x1,y1,eave,pitch=0.45):
    a,b=xy(x0,y0),xy(x1,y1)
    xmin,xmax=sorted((a[0],b[0])); ymin,ymax=sorted((a[1],b[1]))
    w,d=xmax-xmin,ymax-ymin
    rise=min(w,d)*pitch/2
    if d >= w:
        r0=((xmin+xmax)/2,ymin+w/2,eave+rise)
        r1=((xmin+xmax)/2,ymax-w/2,eave+rise)
        faces=[(0,1,4),(1,2,5,4),(2,3,5),(3,0,4,5)]
    else:
        r0=(xmin+d/2,(ymin+ymax)/2,eave+rise)
        r1=(xmax-d/2,(ymin+ymax)/2,eave+rise)
        faces=[(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4)]
    verts=[(xmin,ymin,eave),(xmax,ymin,eave),(xmax,ymax,eave),(xmin,ymax,eave),r0,r1]
    obj=mesh(name,verts,faces,roofmat,'Roof')
    solid=obj.modifiers.new('Roof thickness','SOLIDIFY'); solid.thickness=0.09
    for i in range(4):
        beam(name+' fascia',verts[i],verts[(i+1)%4],0.14,white,'Roof')
    if (Vector(r1)-Vector(r0)).length > 0.01:
        beam(name+' ridge cap',r0,r1,0.12,roofmat,'Roof')
    for i,r in ((0,r0),(1,r0 if d>=w else r1),(2,r1),(3,r1 if d>=w else r0)):
        beam(name+' hip cap',verts[i],r,0.10,roofmat,'Roof')
hip('Main hip roof',418,860,1383,1898,UPPER+H1+0.12,0.45)
# Garage's lower roof overlaps the upper body's front rather than covering the whole garage leg.
hip('Garage hip roof',418,1808,1009,2470,GROUND+H0+0.14,0.45)
# Shallow front porch canopy/roof apron, rising back against upper front wall.
a,b=xy(965,1988),xy(1380,1830)
x0,x1=sorted((a[0],b[0])); yf,yb=sorted((a[1],b[1]))
mesh('Entry shed roof',[(x0,yf,GROUND+H0+0.14),(x1,yf,GROUND+H0+0.14),
                       (x1,yb,GROUND+H0+0.82),(x0,yb,GROUND+H0+0.82)],
     [(0,1,2,3)],roofmat,'Roof')
beam('Porch front fascia',(x0,yf,GROUND+H0+0.12),(x1,yf,GROUND+H0+0.12),0.15,white,'Roof')
# Lanai roof is inferred; the rendering only shows the front.
hip('Lanai hip roof',421,634,930,913,GROUND+H0+0.10,0.25)
for px,py in ((467,679),(882,679),(1312,1964)):
    p=xy(px,py)
    box('Square porch column',(*p,GROUND+H0/2),(0.16,0.16,H0),white)
    box('Column capital',(*p,GROUND+H0-0.10),(0.25,0.25,0.20),white)
# Front and rear corner trim upstairs.
for px in (453,1348):
    for py in (895,1863):
        p=xy(px,py)
        box('Upper corner board',(*p,UPPER+H1/2),(0.13,0.13,H1),white,'Upper')
# C-1 garage decorative eave brackets.
for px in (486,635,785,942):
    p=xy(px,2435)
    box('Garage eave bracket', (p[0],p[1]-0.13,GROUND+H0-0.14),
        (0.075,0.31,0.28),white)

# Simplified fitted cabinets and furnishings (not construction-level fixtures).
def fixture(name,x0,y0,x1,y1,base,height,mat,group):
    return rect(name,x0,y0,x1,y1,base+height/2,height,mat,group)
fixture('Kitchen base cabinets',466,917,524,1245,GROUND,0.88,white,'Ground')
fixture('Kitchen countertop',463,914,530,1248,GROUND+0.88,0.045,tile,'Ground')
fixture('Kitchen island cabinetry',626,1007,751,1232,GROUND,0.88,white,'Ground')
fixture('Island worktop',621,1002,756,1238,GROUND+0.88,0.055,tile,'Ground')
fixture('Island sink',635,1103,683,1172,GROUND+0.934,0.015,metal,'Ground')
fixture('Refrigerator',466,1250,529,1333,GROUND,1.95,metal,'Ground')
fixture('Cooktop',469,1049,522,1109,GROUND+0.928,0.012,metal,'Ground')
# Small bath fixture helper uses spheres scaled into ceramic forms.
def ellipsoid(name,px,py,z,size,mat,group):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,location=(*xy(px,py),z))
    obj=bpy.context.object; obj.name=name
    for c in list(obj.users_collection): c.objects.unlink(obj)
    collections[group].objects.link(obj)
    obj.scale=size
    obj.data.materials.append(mat)
    return obj

def toilet(px,py,base,group):
    ellipsoid('Toilet bowl',px,py,base+0.37,(0.20,0.28,0.15),white,group)
    fixture('Toilet cistern',px-18,py-28,px+18,py-12,base,0.72,white,group)
    fixture('Toilet pedestal',px-10,py-8,px+10,py+15,base,0.30,white,group)
fixture('Powder vanity',1253,1800,1335,1851,GROUND,0.83,white,'Ground')
toilet(1294,1700,GROUND,'Ground')
fixture('Master double vanity',641,905,812,955,UPPER,0.83,white,'Upper')
for px in (675,766):
    ellipsoid('Master basin',px,930,UPPER+0.85,(0.20,0.15,0.025),white,'Upper')
fixture('Master shower tray',821,906,950,978,UPPER,0.07,white,'Upper')
toilet(905,1132,UPPER,'Upper')
fixture('Bath2 tub',789,1787,920,1851,UPPER,0.50,white,'Upper')
fixture('Bath2 vanity',869,1585,920,1695,UPPER,0.83,white,'Upper')
toilet(878,1744,UPPER,'Upper')
for py in (1324,1400):
    fixture('Laundry appliance',791,py-28,845,py+28,UPPER,0.92,white,'Upper')
if ADD_FURNITURE:
    for name,px,py,w,d in [('Master',1154,1115,165,195),
                          ('Bedroom2',550,1705,130,180),('Bedroom3',553,1255,130,175)]:
        fixture(name+' bed frame',px-w/2,py-d/2,px+w/2,py+d/2,UPPER,0.25,wood,'Upper')
        fixture(name+' mattress',px-w/2+4,py-d/2+4,px+w/2-4,py+d/2-4,UPPER+0.25,0.20,fabric,'Upper')
        fixture(name+' pillows',px-w/2+12,py-d/2+10,px+w/2-12,py-d/2+44,UPPER+0.45,0.09,white,'Upper')
    fixture('Great room sofa',1110,1135,1305,1210,GROUND,0.72,fabric,'Ground')
    fixture('Coffee table',1120,1245,1245,1303,GROUND,0.42,wood,'Ground')
    fixture('Cafe table',903,1376,1036,1455,GROUND,0.74,wood,'Ground')
    fixture('Leisure sofa',824,1630,895,1805,GROUND,0.72,fabric,'Ground')

# Room tags: optional viewport aid, never included in the beauty render.
def label(text,px,py,z):
    data=bpy.data.curves.new(text,'FONT'); data.body=text
    data.size=0.28; data.align_x='CENTER'
    obj=bpy.data.objects.new(text,data); collections['Labels'].objects.link(obj)
    obj.location=(*xy(px,py),z+0.025); data.materials.append(metal)
for text,px,py,z in [('GARAGE',696,2190,GROUND),('GARAGE STORAGE',609,1710,GROUND),
                    ('LEISURE',950,1750,GROUND),('FOYER',1175,1615,GROUND),
                    ('POWDER',1295,1760,GROUND),('KITCHEN',640,1298,GROUND),
                    ('GREAT ROOM',1063,1040,GROUND),('CAFE',957,1390,GROUND),
                    ('LANAI',675,780,GROUND),('MASTER',1135,1220,UPPER),
                    ('BEDROOM 3',556,1350,UPPER),('BEDROOM 2',556,1800,UPPER),
                    ('LOFT',1090,1750,UPPER),('BATH 2',852,1680,UPPER),
                    ('UTILITY',891,1390,UPPER)]:
    label(text,px,py,z)

# Simple site and photographic front three-quarter camera.
box('Lawn',(5,8,-0.20),(30,40,0.20),grass,'Site')
rect('Driveway',492,2438,939,3010,-0.065,0.07,concrete,'Site')
rect('Front path',1138,1977,1240,2700,-0.054,0.08,concrete,'Site')
for px,py in ((1050,2000),(1310,2025),(400,2490),(1000,2460)):
    ellipsoid('Low foundation shrub',px,py,0.28,(0.48,0.43,0.40),grass,'Site')
scene=bpy.context.scene
scene.unit_settings.system='METRIC'; scene.unit_settings.length_unit='METERS'
scene.render.engine='CYCLES'
scene.cycles.samples=48
scene.render.resolution_x=1600; scene.render.resolution_y=1200
scene.render.resolution_percentage=100
world=bpy.data.worlds.new('Honor daylight'); scene.world=world
world.use_nodes=True
world.node_tree.nodes.get('Background').inputs[0].default_value=(0.65,0.78,0.92,1)
world.node_tree.nodes.get('Background').inputs[1].default_value=0.55
sun_data=bpy.data.lights.new('Honor sun','SUN'); sun_data.energy=3.0
sun_data.angle=math.radians(12)
sun=bpy.data.objects.new('Honor sun',sun_data); collections['Presentation'].objects.link(sun)
sun.rotation_euler=(math.radians(28),math.radians(-25),math.radians(-30))
cam_data=bpy.data.cameras.new('Honor camera')
cam=bpy.data.objects.new('Honor camera',cam_data); collections['Presentation'].objects.link(cam)
cam.location=(20,-24,12)
target=Vector((5,8,3.5))
cam.rotation_euler=(target-Vector(cam.location)).to_track_quat('-Z','Y').to_euler()
cam_data.type='PERSP'; cam_data.lens=44; cam_data.clip_end=250
scene.camera=cam
# Convenient second camera for plan inspection.
plan_data=bpy.data.cameras.new('Honor plan camera')
plan=bpy.data.objects.new('Honor plan camera',plan_data)
collections['Presentation'].objects.link(plan)
plan.location=(5,9,40); plan.rotation_euler=(0,0,0)
plan_data.type='ORTHO'; plan_data.ortho_scale=26
for area in bpy.context.screen.areas if bpy.context.screen else []:
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_distance=32
        area.spaces.active.region_3d.view_location=(5,8,3)
        area.spaces.active.clip_end=500
root['source']='Honor brochure, pages 1 and 2; C-1 elevation; base three-bedroom plan'
root['accuracy']='Approximate visualization: traced plan, inferred wall/roof structure and hidden elevations'
root['plan_scale_pixels_per_foot']=27.3
print('HONOR created. Hide Roof to inspect upstairs; hide Upper as well for ground floor.')
