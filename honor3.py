# Made by GPT-6-astra on low reasoning on October 1

"""HONOR / FH-1 -- brochure-based architectural reconstruction.
Run inside Blender's Text Editor (not a stand-alone Python interpreter).

Reference: the two Honor brochure images supplied with the request.
The supplied plan is labelled C-1; its base layout is used with the FH-1
facade: brown shingle hip roof, front garage gable, tan lap siding,
board-and-batten gable, blue board shutters and blue entry door.

Measurements are in metres. Plan coordinates are traced from the supplied
image; scale is calibrated approximately to the 18'-4\" wide garage.
Ground ceiling 9'-4\", upper ceiling 8'-8\". Wall thicknesses, roof pitch,
structural floor depth, window/door heights and unseen finishes are inferred.
The unusually deep L-shaped garage is intentional: both areas labelled
Garage in the plan are retained. Optional room/bath/lanai variants omitted.

Only mesh model objects are created. No cameras, lights, ground, landscaping,
annotations or render rig. Existing unrelated mesh objects are preserved;
existing scene cameras/lights and an earlier Honor generated collection are
removed. Roof and upper floor have separate collections for inspection.
No external assets or add-ons needed. Does not save/overwrite a .blend file.
"""

import bpy
import math
import random
from mathutils import Vector

ROOT = 'HONOR_FH1'
S = 0.01095                       # metres / plan-image pixel
F0 = 0.18                        # finished ground floor
H0 = 2.8448                       # 9 feet 4 inches
F1 = F0 + H0 + 0.28               # structural floor allowance
H1 = 2.6416                       # 8 feet 8 inches
EAVE = F1 + H1 + 0.12
EXT = 0.20
INT = 0.115
DETAIL_SIDING = True
DETAIL_SHINGLES = True
rng = random.Random(31)


def purge_collection(collection):
    for child in list(collection.children):
        purge_collection(child)
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(collection)


old = bpy.data.collections.get(ROOT)
if old:
    purge_collection(old)
for obj in list(bpy.context.scene.objects):
    if obj.type in {'CAMERA', 'LIGHT'}:
        bpy.data.objects.remove(obj, do_unlink=True)

scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0
root = bpy.data.collections.new(ROOT)
scene.collection.children.link(root)
COLS = {}
for name in ('01_Foundation', '02_Ground_Walls', '03_Upper_Floor',
             '04_Upper_Walls', '05_Doors_Windows', '06_Exterior_Trim',
             '07_Roofs', '08_Stair', '09_Cabinets_Fixtures'):
    coll = bpy.data.collections.new(name)
    root.children.link(coll)
    COLS[name] = coll
ACTIVE = COLS['02_Ground_Walls']


def material(name, color, roughness=0.65, metal=0.0):
    mat = bpy.data.materials.get('Honor_' + name)
    if mat is None:
        mat = bpy.data.materials.new('Honor_' + name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (*color, 1)
        bsdf.inputs['Roughness'].default_value = roughness
        bsdf.inputs['Metallic'].default_value = metal
    return mat


TAN = material('Warm_tan_siding', (0.57, 0.50, 0.38))
STUCCO = material('Side_stucco', (0.62, 0.58, 0.48))
WHITE = material('Ivory_trim', (0.88, 0.86, 0.79))
BLUE = material('Slate_blue', (0.105, 0.19, 0.245))
BLUE_EDGE = material('Blue_shutter_braces', (0.065, 0.12, 0.17))
WOOD = material('Walnut_garage', (0.22, 0.125, 0.085))
PANEL = material('Walnut_panels', (0.29, 0.175, 0.125))
FRAME = material('Dark_window_frame', (0.095, 0.085, 0.065), 0.4)
GLASS = material('Blue_gray_glass', (0.13, 0.21, 0.25), 0.13, 0.22)
bsdf = GLASS.node_tree.nodes.get('Principled BSDF')
if bsdf:
    sock = bsdf.inputs.get('Transmission Weight') or bsdf.inputs.get('Transmission')
    if sock:
        sock.default_value = 0.65
    bsdf.inputs['IOR'].default_value = 1.45
PLASTER = material('Interior_plaster', (0.82, 0.80, 0.74))
CONCRETE = material('Concrete', (0.46, 0.45, 0.42))
FLOOR = material('Interior_floor', (0.62, 0.55, 0.43))
TILE = material('Pale_tile', (0.76, 0.73, 0.65))
CERAMIC = material('Porcelain', (0.9, 0.9, 0.86), 0.25)
METAL = material('Hardware', (0.30, 0.32, 0.33), 0.24, 0.8)
ROOF = material('Brown_shingle_base', (0.19, 0.115, 0.072))
SHINGLES = [material('Shingle_%02d' % i,
                    (0.22 + i * 0.009, 0.137 + i * 0.006, 0.085 + i * 0.004))
            for i in range(8)]


def mesh(name, verts, faces, mat, collection=None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    (collection or ACTIVE).objects.link(obj)
    if mat:
        data.materials.append(mat)
    return obj


def box(name, center, size, mat, collection=None):
    x, y, z = center
    a, b, c = (v / 2 for v in size)
    verts = [(x-a,y-b,z-c), (x+a,y-b,z-c), (x+a,y+b,z-c), (x-a,y+b,z-c),
             (x-a,y-b,z+c), (x+a,y-b,z+c), (x+a,y+b,z+c), (x-a,y+b,z+c)]
    return mesh(name, verts, [(0,3,2,1), (4,5,6,7), (0,1,5,4),
                             (1,2,6,5), (2,3,7,6), (3,0,4,7)], mat, collection)


def beam(name, a, b, width, depth, mat, collection=None):
    a, b = Vector(a), Vector(b)
    obj = box(name, (0, 0, 0), (width, depth, (b-a).length), mat, collection)
    obj.location = (a+b)/2
    obj.rotation_euler = (b-a).to_track_quat('Z', 'Y').to_euler()
    return obj


def P(x, y):
    """Brochure ground-plan pixel coordinates, front at negative Y."""
    return ((x-450)*S, (2435-y)*S)


def rect(name, x0, y0, x1, y1, bottom, height, mat, collection=None):
    a, b = P(x0, y0), P(x1, y1)
    return box(name, ((a[0]+b[0])/2, (a[1]+b[1])/2, bottom+height/2),
               (abs(b[0]-a[0]), abs(b[1]-a[1]), height), mat, collection)


def local_box(name, a, tangent, normal, u, v, z, w, d, h, mat, coll=None):
    p = Vector((a[0], a[1], 0)) + tangent*u + normal*v
    obj = box(name, (0,0,0), (w,d,h), mat, coll)
    obj.location = (p.x,p.y,z)
    obj.rotation_euler.z = math.atan2(tangent.y,tangent.x)
    return obj


def shutter(name, a, t, n, u, v, bottom, height, width):
    coll = COLS['06_Exterior_Trim']
    for j in range(4):
        local_box(name+' board', a,t,n,u-width/2+(j+0.5)*width/4,v,
                  bottom+height/2,width/4-0.008,0.045,height,BLUE,coll)
    for z in (bottom+0.14, bottom+height-0.14):
        local_box(name+' crossbar',a,t,n,u,v+0.028,z,width,0.038,0.085,BLUE_EDGE,coll)
    def point(uu, zz):
        p = Vector((a[0],a[1],zz))+t*uu+n*(v+0.055)
        return p
    beam(name+' diagonal',point(u-width*0.40,bottom+0.19),
         point(u+width*0.40,bottom+height-0.19),0.065,0.04,BLUE_EDGE,coll)


def opening_detail(name, a, t, n, offset, width, sill, height, kind, face):
    coll = COLS['05_Doors_Windows']
    # 'passage' deliberately leaves a real, unfilled opening.
    if kind == 'passage':
        return
    v = face + 0.022
    bottom, top = sill, sill+height
    trim = WHITE if kind not in {'interior'} else PLASTER
    for u in (offset-width/2-0.04, offset+width/2+0.04):
        local_box(name+' jamb',a,t,n,u,v,bottom+height/2,0.09,0.10,height+0.14,trim,coll)
    local_box(name+' lintel',a,t,n,offset,v,top+0.045,width+0.18,0.10,0.09,trim,coll)
    if kind in {'window','shutters','slider'}:
        local_box(name+' sill',a,t,n,offset,v+0.025,bottom-0.035,width+0.24,0.16,0.075,WHITE,coll)
        local_box(name+' glazing',a,t,n,offset,0,bottom+height/2,width-0.07,0.018,height-0.06,GLASS,coll)
        # FH-1 has dark frames and simple divided lights, unlike white C-1 grids.
        for u in (offset-width/2+0.027, offset+width/2-0.027):
            local_box(name+' frame',a,t,n,u,v,bottom+height/2,0.05,0.055,height,FRAME,coll)
        for z in (bottom+0.025,top-0.025):
            local_box(name+' frame',a,t,n,offset,v,z,width,0.055,0.05,FRAME,coll)
        divisions = 3 if kind == 'slider' or width > 2.2 else 2
        for j in range(1,divisions):
            local_box(name+' mullion',a,t,n,offset-width/2+width*j/divisions,v,
                      bottom+height/2,0.035,0.055,height,FRAME,coll)
        if kind != 'slider':
            for frac in (0.50,0.77):
                local_box(name+' horizontal muntin',a,t,n,offset,v,bottom+height*frac,
                          width,0.055,0.025,FRAME,coll)
        if kind == 'shutters':
            for side in (-1,1):
                shutter(name+' shutter',a,t,n,offset+side*(width/2+0.30),
                        v+0.005,bottom,height,0.43)
    else:
        color = WOOD if kind == 'garage' else BLUE if kind == 'entry' else WHITE
        local_box(name+' leaf',a,t,n,offset,0,bottom+height/2,width-0.025,0.055,height-0.015,color,coll)
        cols, rows = (4,4) if kind == 'garage' else (1,3)
        for row in range(rows):
            for col in range(cols):
                local_box(name+' inset panel',a,t,n,
                          offset-width/2+(col+0.5)*width/cols,0.036,
                          bottom+(row+0.5)*height/rows,width/cols-0.13,0.026,
                          height/rows-0.12,PANEL if kind=='garage' else color,coll)
        if kind != 'garage':
            local_box(name+' handle',a,t,n,offset+width*0.34,0.085,bottom+1.0,
                      0.10,0.055,0.035,METAL,coll)


def wall(name, pa, pb, bottom, height, mat=PLASTER, thickness=INT,
         holes=(), siding=False, outward=1):
    """Opening tuple: (distance from pa, width, relative sill, height, type).
    Walls and individual siding courses are segmented around every opening;
    there are no black window rectangles pasted over solid wall geometry.
    """
    a, b = P(*pa), P(*pb)
    t = Vector((b[0]-a[0],b[1]-a[1],0))
    length = t.length
    t.normalize()
    n = Vector((t.y,-t.x,0))*outward
    # local_box expects normal pointing to its local +Y. An outward normal
    # can point to -Y as well; symmetric box cross-sections remain identical.
    cuts = [0.0,length]
    for u,w,s,h,k in holes:
        cuts.extend([max(0,u-w/2),min(length,u+w/2)])
    cuts = sorted(set(cuts))
    for lo,hi in zip(cuts[:-1],cuts[1:]):
        mid = (lo+hi)/2
        intervals = [(0,height)]
        for u,w,s,h,k in holes:
            if u-w/2 < mid < u+w/2:
                new = []
                for z0,z1 in intervals:
                    if z0 < s:
                        new.append((z0,min(z1,s)))
                    if z1 > s+h:
                        new.append((max(z0,s+h),z1))
                intervals = new
        for z0,z1 in intervals:
            if z1-z0 > 0.001:
                local_box(name,a,t,n,mid,0,bottom+(z0+z1)/2,hi-lo,
                          thickness,z1-z0,mat)
                if siding and DETAIL_SIDING:
                    pitch=0.15
                    for row in range(int(height/pitch)+1):
                        low=max(z0,row*pitch)
                        high=min(z1,(row+1)*pitch-0.006)
                        if high > low:
                            local_box(name+' lap siding',a,t,n,mid,thickness/2+0.018,
                                      bottom+(low+high)/2,hi-lo,0.035,high-low,TAN,
                                      COLS['06_Exterior_Trim'])
    for i,(u,w,s,h,k) in enumerate(holes):
        opening_detail(name+' opening '+str(i+1),a,t,n,u,w,bottom+s,h,k,thickness/2)


def H(pixels, width, sill, height, kind='window'):
    return (pixels*S,width,sill,height,kind)


# Ground floor: garage is an L, not a simple rectangular two-car box.
ACTIVE = COLS['01_Foundation']
rect('Main ground slab',450,895,1350,1860,F0-0.18,0.18,CONCRETE)
rect('Forward garage slab',450,1860,980,2435,0,0.14,CONCRETE)
rect('Garage rear bay floor',450,1500,780,1860,F0,0.025,CONCRETE)
rect('Entry porch slab',980,1860,1350,1980,0.01,0.17,CONCRETE)
rect('Entry shallow step',1105,1980,1260,2010,0.0,0.085,CONCRETE)
rect('Lanai slab 16ft4 by 8ft',450,655,897,895,0.01,0.17,CONCRETE)
rect('Great room and cafe floor',780,895,1350,1500,F0,0.018,FLOOR)
rect('Kitchen tile',450,895,835,1340,F0,0.018,TILE)
rect('Leisure floor',780,1500,1115,1860,F0,0.018,FLOOR)
rect('Foyer tile',1115,1500,1245,1860,F0,0.018,TILE)
rect('Powder tile',1245,1640,1350,1860,F0,0.018,TILE)

ACTIVE = COLS['02_Ground_Walls']
wall('Garage front', (450,2435),(980,2435),F0,H0,STUCCO,EXT,
     [H(265,4.88,0,2.38,'garage')],True)
wall('West exterior',(450,2435),(450,895),F0,H0,STUCCO,EXT,outward=-1)
wall('Garage east return',(980,2435),(980,1860),F0,H0,STUCCO,EXT)
wall('Leisure front',(780,1860),(1115,1860),F0,H0,STUCCO,EXT,
     [H(270,0.91,0.65,1.65)],True)
wall('Entry door wall',(1115,1860),(1245,1860),F0,H0,STUCCO,EXT,
     [H(66,0.96,0,2.42,'entry')],True)
wall('Powder front',(1245,1860),(1350,1860),F0,H0,STUCCO,EXT,siding=True)
wall('East exterior',(1350,1860),(1350,895),F0,H0,STUCCO,EXT)
wall('Rear exterior',(450,895),(1350,895),F0,H0,STUCCO,EXT,
     [H(205,2.74,0,2.35,'slider'),H(658,2.83,0.65,1.70)],outward=-1)
wall('Garage leisure separation',(780,1860),(780,1500),F0,H0)
wall('Garage mudroom separation',(450,1500),(780,1500),F0,H0,
     holes=[H(103,0.82,0,2.10,'interior')])
wall('Garage step return',(780,1860),(980,1860),F0,H0,PLASTER,EXT)
wall('Mudroom kitchen wall',(450,1340),(780,1340),F0,H0,
     holes=[H(118,0.90,0,2.15,'passage')])
wall('Mudroom east wall',(780,1500),(780,1340),F0,H0)
wall('Mudroom closet',(620,1500),(620,1340),F0,H0,
     holes=[H(89,0.85,0,2.1,'interior')])
wall('Leisure cafe opening',(780,1500),(1245,1500),F0,H0,
     holes=[H(281,1.22,0,2.42,'passage')])
wall('Powder west',(1245,1860),(1245,1640),F0,H0,
     holes=[H(108,0.76,0,2.1,'interior')])
wall('Powder stair wall',(1245,1640),(1350,1640),F0,H0)

# Upper slab, split around the stairwell rather than blocking the stairs.
ACTIVE = COLS['03_Upper_Floor']
rect('Upper slab main',450,895,1245,1860,F1-0.28,0.28,PLASTER)
rect('Upper slab east rear',1245,895,1350,1390,F1-0.28,0.28,PLASTER)
rect('Upper slab east front landing',1245,1750,1350,1860,F1-0.28,0.28,PLASTER)
rect('Upper floor finish main',450,895,1245,1860,F1,0.018,FLOOR)
rect('Upper floor finish rear',1245,895,1350,1390,F1,0.018,FLOOR)
rect('Upper floor finish landing',1245,1750,1350,1860,F1,0.018,FLOOR)
rect('Master bath tile',625,895,955,1115,F1,0.026,TILE)
rect('Bath two tile',770,1555,930,1860,F1,0.026,TILE)
rect('Laundry tile',775,1275,955,1455,F1,0.026,TILE)

ACTIVE = COLS['04_Upper_Walls']
wall('Upper FH1 front',(450,1860),(1350,1860),F1,H1,TAN,EXT,
     [H(90,0.94,0.67,1.72,'shutters'),H(595,0.94,0.67,1.72,'shutters'),
      H(805,0.94,0.67,1.72,'shutters')],True)
wall('Upper west',(450,1860),(450,895),F1,H1,TAN,EXT,
     [H(515,0.91,0.78,1.40)],True,outward=-1)
wall('Upper east',(1350,1860),(1350,895),F1,H1,TAN,EXT,
     [H(292,0.91,0.78,1.40)],True)
wall('Upper rear',(450,895),(1350,895),F1,H1,TAN,EXT,
     [H(430,0.91,1.25,0.91),H(580,0.91,0.78,1.4),H(820,0.91,0.78,1.4)],
     True,outward=-1)
# Upper plan traced in the same coordinate system as ground (second plan X-1040).
wall('Bedroom2 east',(770,1860),(770,1555),F1,H1)
wall('Bedroom2 hall',(450,1555),(770,1555),F1,H1,
     holes=[H(265,0.83,0,2.1,'interior')])
wall('Bedroom2 wardrobe face',(450,1490),(665,1490),F1,H1,
     holes=[H(105,1.55,0,2.1,'interior')])
wall('Wardrobe hall end',(665,1555),(665,1425),F1,H1)
wall('Bedroom3 wardrobe face',(450,1425),(665,1425),F1,H1,
     holes=[H(105,1.55,0,2.1,'interior')])
wall('Bedroom3 hall',(665,1455),(770,1455),F1,H1,
     holes=[H(51,0.84,0,2.1,'interior')])
wall('Bedroom3 east',(770,1455),(770,1115),F1,H1)
wall('Bedroom3 north',(450,1115),(770,1115),F1,H1)
wall('Master walkin east',(625,1115),(625,895),F1,H1,
     holes=[H(70,0.83,0,2.1,'interior')])
wall('Master suite west',(955,1455),(955,895),F1,H1,
     holes=[H(67,0.86,0,2.1,'interior'),H(416,0.83,0,2.1,'interior')])
wall('Master closet front',(1055,1390),(1350,1390),F1,H1)
wall('Master closet rear',(1055,1325),(1350,1325),F1,H1,
     holes=[H(150,1.85,0,2.1,'interior')])
wall('Master closet end',(1055,1390),(1055,1325),F1,H1)
wall('Master hall return',(955,1455),(1055,1455),F1,H1)
wall('Master hall side',(1055,1455),(1055,1390),F1,H1)
wall('Laundry hall',(770,1455),(955,1455),F1,H1,
     holes=[H(130,0.83,0,2.1,'interior')])
wall('Laundry HVAC',(770,1275),(955,1275),F1,H1,
     holes=[H(126,0.78,0,2.1,'interior')])
wall('HVAC toilet',(770,1175),(955,1175),F1,H1)
wall('WC west',(770,1175),(770,1085),F1,H1)
wall('WC door',(770,1085),(955,1085),F1,H1,
     holes=[H(70,0.76,0,2.1,'interior')])
wall('Bath2 hall',(770,1555),(930,1555),F1,H1,
     holes=[H(50,0.76,0,2.1,'interior')])
wall('Bath2 loft',(930,1860),(930,1555),F1,H1)

# Straight stair on the east wall. Ground plan arrow rises toward the front.
ACTIVE = COLS['08_Stair']
stair_x0,stair_x1=1247,1338
back_y,front_y=1338,1750
count=18
rise=(F1-F0)/count
for i in range(count):
    y0=back_y+(front_y-back_y)*i/count
    y1=back_y+(front_y-back_y)*(i+1)/count
    rect('Stair tread %02d' % (i+1),stair_x0,y0,stair_x1,y1,
         F0+i*rise,rise,FLOOR)
a=P(stair_x0,back_y)
b=P(stair_x0,front_y)
beam('Stair handrail',(a[0],a[1],F0+0.92),(b[0],b[1],F1+0.92),
     0.065,0.065,WOOD)
for i in range(count+1):
    frac=i/count
    x=a[0]
    y=a[1]+(b[1]-a[1])*frac
    z=F0+(F1-F0)*frac
    box('Stair baluster',(x,y,z+0.44),(0.032,0.032,0.88),WHITE)
for py in (1390,1750):
    px,yy=P(stair_x0,py)
    box('Upper stair newel',(px,yy,F1+0.48),(0.085,0.085,0.96),WHITE)
# Upstairs guard along the open edge; lower stair rail remains below it.
a=P(stair_x0,1390); b=P(stair_x0,1750)
beam('Loft stair guard top',(a[0],a[1],F1+1.0),(b[0],b[1],F1+1.0),0.06,0.06,WOOD)
for i in range(25):
    y=a[1]+(b[1]-a[1])*i/24
    box('Loft guard spindle',(a[0],y,F1+0.5),(0.028,0.028,1.0),WHITE)

# Fixed furnishings only: provide spatial cues without decorating the scene.
ACTIVE = COLS['09_Cabinets_Fixtures']

def cabinet(name,x0,y0,x1,y1,base=F0,height=0.88):
    rect(name,x0,y0,x1,y1,base,height,WHITE)
    rect(name+' countertop',x0-2,y0-2,x1+2,y1+2,base+height,0.045,TILE)


cabinet('Kitchen west base cabinets',462,925,520,1240)
cabinet('Kitchen island',626,1006,751,1234)
rect('Island sink rim',631,1095,680,1165,F0+0.928,0.014,METAL)
rect('Island sink basin',636,1100,675,1160,F0+0.943,0.008,FRAME)
rect('Dishwasher face',624,1174,628,1225,F0+0.10,0.70,METAL)
rect('Refrigerator',463,1246,524,1325,F0,1.98,METAL)
rect('Cooktop',463,1045,519,1112,F0+0.928,0.018,FRAME)
for x in (476,506):
    for y in (1062,1092):
        rect('Cooktop burner',x-8,y-8,x+8,y+8,F0+0.947,0.005,METAL)
rect('Range hood',462,1045,516,1110,F0+1.65,0.20,METAL)
cabinet('Master double vanity',635,906,802,960,F1)
cabinet('Bath2 vanity',865,1568,921,1700,F1)
cabinet('Powder vanity',1252,1795,1339,1848,F0)


def basin(name,x,y,z):
    px,py=P(x,y)
    box(name+' rim',(px,py,z),(0.43,0.34,0.035),CERAMIC)
    box(name+' inset',(px,py,z+0.018),(0.32,0.24,0.008),GLASS)
    box(name+' tap',(px,py+0.18,z+0.09),(0.035,0.04,0.18),METAL)


for x in (666,761):
    basin('Master basin',x,934,F1+0.94)
basin('Bath2 basin',893,1608,F1+0.94)
basin('Powder basin',1295,1820,F0+0.94)


def toilet(name,x,y,base):
    px,py=P(x,y)
    box(name+' pedestal',(px,py,base+0.19),(0.26,0.43,0.38),CERAMIC)
    box(name+' bowl',(px,py-0.06,base+0.39),(0.39,0.54,0.13),CERAMIC)
    box(name+' seat opening',(px,py-0.07,base+0.461),(0.23,0.32,0.008),FRAME)
    box(name+' tank',(px,py+0.22,base+0.56),(0.40,0.15,0.45),CERAMIC)


toilet('Powder WC',1295,1690,F0)
toilet('Master WC',903,1130,F1)
toilet('Bath2 WC',883,1740,F1)
rect('Bath2 tub',780,1790,917,1849,F1,0.48,CERAMIC)
rect('Bath2 tub recess',788,1796,909,1843,F1+0.48,0.01,GLASS)
rect('Master shower tray',812,906,947,982,F1,0.08,CERAMIC)
rect('Master shower glazing',814,982,948,984,F1+0.08,2.0,GLASS)
for name,y in (('Washer',1320),('Dryer',1395)):
    rect(name,782,y-28,838,y+28,F1,0.91,WHITE)
    rect(name+' control strip',783,y-27,790,y+27,F1+0.80,0.09,METAL)

# Roof geometry, with thin solids and individual flat shingle faces.
# Flat shingles are used deliberately: the barrel tiles belong to C-1/I-1.
ACTIVE = COLS['07_Roofs']

def roof_surface(name, points, tiles=True):
    pts=[Vector(p) for p in points]
    # Ensure upper-facing winding for consistent lighting / thickness.
    if (pts[1]-pts[0]).cross(pts[2]-pts[0]).z < 0:
        pts.reverse()
    vertices=[tuple(p) for p in pts]+[tuple(p-Vector((0,0,0.09))) for p in pts]
    n=len(pts)
    faces=[tuple(range(n)),tuple(reversed(range(n,2*n)))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh(name,vertices,faces,ROOF)
    if not (tiles and DETAIL_SHINGLES):
        return
    normal=(pts[1]-pts[0]).cross(pts[2]-pts[0]).normalized()
    # Project onto roof-plane coordinates; clip each shingle to convex roof face.
    e=Vector((normal.y,-normal.x,0))
    if e.length < 0.001:
        e=Vector((1,0,0))
    e.normalize()
    f=normal.cross(e).normalized()
    if f.z < 0:
        e=-e
        f=-f
    origin=pts[0]
    poly=[((p-origin).dot(e),(p-origin).dot(f)) for p in pts]
    if sum(poly[i][0]*poly[(i+1)%n][1]-poly[(i+1)%n][0]*poly[i][1] for i in range(n)) < 0:
        poly.reverse()
    def clip(subject, aa, bb):
        def side(p):
            return (bb[0]-aa[0])*(p[1]-aa[1])-(bb[1]-aa[1])*(p[0]-aa[0])
        out=[]
        for j,p in enumerate(subject):
            q=subject[(j+1)%len(subject)]
            sp,sq=side(p),side(q)
            if sp >= -1e-8:
                out.append(p)
            if (sp >= 0) != (sq >= 0):
                k=sp/(sp-sq)
                out.append((p[0]+k*(q[0]-p[0]),p[1]+k*(q[1]-p[1])))
        return out
    xmin,xmax=min(p[0] for p in poly),max(p[0] for p in poly)
    ymin,ymax=min(p[1] for p in poly),max(p[1] for p in poly)
    verts=[]; faces=[]; indices=[]
    row=0
    v=ymin
    while v < ymax:
        u=xmin-0.34*(row%2)
        while u < xmax:
            subject=[(u+0.004,v+0.006),(u+0.665,v+0.006),
                     (u+0.665,v+0.194),(u+0.004,v+0.194)]
            for i in range(n):
                if not subject:
                    break
                subject=clip(subject,poly[i],poly[(i+1)%n])
            if len(subject)>=3:
                start=len(verts)
                for uu,vv in subject:
                    # Subtle lower-edge lift suggests overlapping shingle courses.
                    lift=0.012+0.014*(1-(vv-v)/0.20)
                    verts.append(tuple(origin+e*uu+f*vv+normal*lift))
                faces.append(tuple(range(start,len(verts))))
                indices.append(rng.randrange(len(SHINGLES)))
            u+=0.67
        row+=1
        v+=0.20
    obj=mesh(name+' individual shingle courses',verts,faces,None)
    for mat in SHINGLES:
        obj.data.materials.append(mat)
    for face,index in zip(obj.data.polygons,indices):
        face.material_index=index


def fascia(name,a,b):
    beam(name,a,b,0.13,0.18,WHITE,COLS['06_Exterior_Trim'])


def hip_roof(name,x0,x1,y0,y1,z,pitch=0.44):
    # Longitudinal ridge; main house is slightly longer than it is wide.
    half=(x1-x0)/2
    xc=(x0+x1)/2
    inset=min(half,(y1-y0)/2)
    A=(x0,y0,z); B=(x1,y0,z); C=(x1,y1,z); D=(x0,y1,z)
    R=(xc,y0+inset,z+inset*pitch)
    T=(xc,y1-inset,z+inset*pitch)
    for label,pts in [('front',[A,B,R]),('east',[B,C,T,R]),
                      ('rear',[C,D,T]),('west',[D,A,R,T])]:
        roof_surface(name+' '+label,pts)
    for p,q in [(A,B),(B,C),(C,D),(D,A)]:
        fascia(name+' eave fascia',p,q)
    for p,q in [(A,R),(B,R),(C,T),(D,T),(R,T)]:
        if (Vector(p)-Vector(q)).length>0.001:
            beam(name+' ridge cap',Vector(p)+Vector((0,0,0.045)),
                 Vector(q)+Vector((0,0,0.045)),0.12,0.055,ROOF)


XMAX=P(1350,0)[0]
YMAIN=P(450,1860)[1]
YREAR=P(450,895)[1]
hip_roof('Main hipped shingle roof',-0.30,XMAX+0.30,
         YMAIN-0.30,YREAR+0.30,EAVE,0.44)
# Upper ceiling closes the model under the roof but is separately hideable.
rect('Upper ceiling',450,895,1350,1860,F1+H1,0.10,PLASTER)

# Garage front-facing gable, ridge running back toward the upper facade.
gx0=-0.28
gx1=P(980,0)[0]+0.28
gxc=(gx0+gx1)/2
gy0=-0.32
gy1=YMAIN+0.10
gz=F0+H0+0.10
grise=(gx1-gx0)*0.235
roof_surface('Garage gable west',[(gx0,gy0,gz),(gxc,gy0,gz+grise),
                                 (gxc,gy1,gz+grise),(gx0,gy1,gz)])
roof_surface('Garage gable east',[(gxc,gy0,gz+grise),(gx1,gy0,gz),
                                 (gx1,gy1,gz),(gxc,gy1,gz+grise)])
beam('Garage ridge cap',(gxc,gy0,gz+grise+0.05),(gxc,gy1,gz+grise+0.05),
     0.14,0.07,ROOF)
# Solid triangular gable infill with FH-1 board-and-batten detailing.
gable_y=-0.105
mesh('Garage triangular gable',[(gx0+0.2,gable_y,gz-0.04),
     (gx1-0.2,gable_y,gz-0.04),(gxc,gable_y,gz+grise-0.09)],[(0,1,2)],TAN)
ACTIVE = COLS['06_Exterior_Trim']
for i in range(1,int((gx1-gx0)/0.42)):
    x=gx0+i*0.42
    top=gz+grise*(1-abs(x-gxc)/((gx1-gx0)/2))-0.13
    if top>gz:
        box('Gable vertical batten',(x,gable_y-0.025,(gz+top)/2),
            (0.035,0.045,top-gz),WHITE)
for p,q in [((gx0,gy0,gz),(gxc,gy0,gz+grise)),
            ((gxc,gy0,gz+grise),(gx1,gy0,gz)),
            ((gx0,gy0,gz),(gx0,gy1,gz)),
            ((gx1,gy0,gz),(gx1,gy1,gz))]:
    fascia('Garage white rake / fascia',p,q)
box('Garage gable crossbeam',(gxc,-0.16,gz-0.075),(gx1-gx0,0.15,0.20),WHITE)
for x in (gx0+1.1,gxc,gx1-1.1):
    top=gz+grise*(1-abs(x-gxc)/((gx1-gx0)/2))-0.15
    box('FH1 brown gable bracket',(x,-0.22,top-0.13),(0.105,0.17,0.30),WOOD)

# Entry porch roof slopes up to the main facade beside the garage gable.
ACTIVE = COLS['07_Roofs']
px0=P(980,0)[0]-0.08
px1=XMAX+0.28
py0=P(450,1980)[1]-0.18
py1=YMAIN+0.12
pz0=gz-0.06
pz1=gz+0.53
roof_surface('Entry shed shingle roof',[(px0,py0,pz0),(px1,py0,pz0),
                                      (px1,py1,pz1),(px0,py1,pz1)])
fascia('Porch front fascia',(px0,py0,pz0),(px1,py0,pz0))
fascia('Porch right fascia',(px1,py0,pz0),(px1,py1,pz1))
rect('Porch soffit',982,1858,1354,1988,F0+H0-0.05,0.08,WHITE)
# Separate side-by-side square posts are visible in the floor plan.
ACTIVE=COLS['06_Exterior_Trim']
for x in (1310,1340):
    px,py=P(x,1970)
    box('Entry square column',(px,py,(F0+gz-0.15)/2),
        (0.145,0.145,gz-0.15-F0),WHITE)
    for z in (F0+0.09,gz-0.25):
        box('Entry column trim',(px,py,z),(0.20,0.20,0.15),WHITE)

# Rear covered lanai (standard, no optional extension or screen cage).
ACTIVE=COLS['07_Roofs']
lx0=-0.24; lx1=P(897,0)[0]+0.22
ly0=YREAR-0.06; ly1=P(450,655)[1]+0.22
roof_surface('Lanai shed roof',[(lx0,ly0,gz+0.72),(lx1,ly0,gz+0.72),
                               (lx1,ly1,gz),(lx0,ly1,gz)])
fascia('Lanai rear fascia',(lx0,ly1,gz),(lx1,ly1,gz))
fascia('Lanai west fascia',(lx0,ly0,gz+0.72),(lx0,ly1,gz))
fascia('Lanai east fascia',(lx1,ly0,gz+0.72),(lx1,ly1,gz))
rect('Lanai ceiling',450,655,897,895,F0+H0,0.08,WHITE)
ACTIVE=COLS['06_Exterior_Trim']
for x in (458,885):
    px,py=P(x,666)
    box('Lanai square pier',(px,py,F0+H0/2),(0.25,0.25,H0),STUCCO)
    box('Lanai pier cap',(px,py,F0+H0-0.07),(0.31,0.31,0.14),WHITE)
# White corner boards and continuous story band emphasize the FH-1 facade.
for x,y in ((450,1860),(1350,1860),(450,895),(1350,895)):
    px,py=P(x,y)
    box('Upper corner board X',(px,py,F1+H1/2),(0.15,0.235,H1),WHITE)
    box('Upper corner board Y',(px,py,F1+H1/2),(0.235,0.15,H1),WHITE)
for x,y in ((450,2435),(980,2435)):
    px,py=P(x,y)
    box('Garage corner trim',(px,py-0.025,F0+H0/2),(0.14,0.24,H0),WHITE)
box('Front upper frieze',(XMAX/2,YMAIN-0.115,F1+H1-0.065),
    (XMAX+0.08,0.08,0.15),WHITE)
box('Front story belt',(XMAX/2,YMAIN-0.12,F1+0.045),(XMAX,0.10,0.12),WHITE)

# Architectural model metadata, kept out of visible geometry.
root['reference'] = 'Honor brochure; C-1 base plan adapted to FH-1 elevation'
root['scale_note'] = 'Approximate brochure tracing; not construction documentation'
root['ground_ceiling_m'] = H0
root['upper_ceiling_m'] = H1
root['living_area_brochure_sqft'] = 2143
root['garage_area_brochure_sqft'] = 566
root['options'] = 'Standard 3-bedroom + loft; no optional bath, stair window or lanai extension'
for obj in root.all_objects:
    obj.select_set(False)
# Material colors are visible in Solid mode without needing a light rig.
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.shading.color_type = 'MATERIAL'
print('Honor FH-1 built: %d mesh objects. Hide 07_Roofs and upper collections to inspect interiors.'
      % len(root.all_objects))
