# Made by gpt-6.1-sol on low reasoning

"""Honor / FH-1 brochure reconstruction. Run in Blender's Text Editor.
Units in the design below are feet; generated mesh coordinates are meters.
Front is -Y. Floor-plan drawing is labeled C-1: FH-1 facade is substituted.
Brochure is not construction documentation: wall thicknesses, roof pitches,
unshown side windows, doors and fittings are inferred. No optional extensions.
The strange rear 'Garage 11-4 x 13-1' label is retained as garage/storage.
Only meshes/materials/collections are generated. SAVE YOUR SCENE FIRST:
CLEAR_SCENE removes existing scene objects (including default camera/light).
"""
import bpy
import math
import random
from mathutils import Vector

CLEAR_SCENE = True
FT = 0.3048
W, FRONT, BACK = 32.0, 20.4, 55.0
GROUND, UPPER, EAVE = 0.35, 10.35, 19.35
H1, H2 = 9.333, 8.667
T = 0.5
random.seed(17)

if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
if CLEAR_SCENE:
    for obj in list(bpy.context.scene.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
else:
    old = bpy.data.collections.get('Honor FH-1')
    if old:
        for obj in list(old.all_objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(old)
root = bpy.data.collections.new('Honor FH-1')
bpy.context.scene.collection.children.link(root)
bpy.context.scene.unit_settings.system = 'METRIC'


def material(name, color, roughness=0.7, metallic=0.0):
    m = bpy.data.materials.new('Honor | ' + name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bs = m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (*color, 1)
    bs.inputs['Roughness'].default_value = roughness
    bs.inputs['Metallic'].default_value = metallic
    return m


mats = {
    'stucco': material('warm stucco', (0.65, 0.61, 0.50)),
    'siding': material('sand lap siding', (0.70, 0.65, 0.53)),
    'trim': material('ivory trim', (0.91, 0.89, 0.81)),
    'blue': material('navy shutters and entry', (0.075, 0.14, 0.19)),
    'wood': material('brown garage and brackets', (0.23, 0.14, 0.105)),
    'glass': material('dark window glazing', (0.07, 0.12, 0.15), 0.17, 0.3),
    'inside': material('interior plaster', (0.85, 0.82, 0.74)),
    'floor': material('warm floor', (0.49, 0.34, 0.22)),
    'tile': material('tile and slabs', (0.64, 0.62, 0.56)),
    'counter': material('countertops', (0.86, 0.84, 0.78)),
    'cabinet': material('cabinetry', (0.73, 0.69, 0.58)),
    'ceramic': material('bath fixtures', (0.93, 0.92, 0.88), 0.25),
    'metal': material('hardware', (0.25, 0.27, 0.28), 0.24, 0.8),
    'roof': material('shingle underlay', (0.19, 0.115, 0.085)),
}
for i in range(5):
    mats['shingle' + str(i)] = material('shingle variation ' + str(i),
                                      (0.24 + i*0.015, 0.155 + i*0.012, 0.11 + i*0.01))
# Batched disconnected solids, grouped by architectural assembly and material.
data = {}


def poly(group, mat, verts, faces):
    key = (group, mat)
    vs, fs = data.setdefault(key, ([], []))
    offset = len(vs)
    vs.extend(tuple(c*FT for c in v) for v in verts)
    fs.extend(tuple(i+offset for i in f) for f in faces)


def box(group, mat, x0, x1, y0, y1, z0, z1):
    if min(x1-x0, y1-y0, z1-z0) <= 0.00001:
        return
    poly(group, mat, [(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),
                     (x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)],
         [(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)])


def beam(group, mat, a, b, width):
    a, b = Vector(a), Vector(b)
    d = (b-a).normalized()
    ref = Vector((0,0,1)) if abs(d.z) < 0.9 else Vector((0,1,0))
    u = d.cross(ref).normalized()*width/2
    v = d.cross(u).normalized()*width/2
    verts = [tuple(p+s*u+t*v) for p in (a,b) for s,t in [(-1,-1),(1,-1),(1,1),(-1,1)]]
    poly(group, mat, verts, [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])


# Wall segment: local horizontal u and depth v, supports true openings.
def wall(name, a, b, z, h, openings=(), exterior=False, normal=-1):
    ax, ay = a
    bx, by = b
    horizontal = abs(by-ay) < 0.001
    lo, hi = sorted((ax,bx) if horizontal else (ay,by))
    fixed = ay if horizontal else ax
    def block(mat, u0,u1,v0,v1,z0,z1):
        if horizontal:
            box(name,mat,u0,u1,fixed+v0,fixed+v1,z0,z1)
        else:
            box(name,mat,fixed+v0,fixed+v1,u0,u1,z0,z1)
    cuts = sorted(set([lo,hi]+[max(lo,min(hi,c)) for o in openings for c in o[:2]]))
    for l,r in zip(cuts,cuts[1:]):
        holes = sorted((o[2],o[3]) for o in openings if o[0] <= (l+r)/2 <= o[1])
        low = 0
        for bottom,top in holes+[(h,h)]:
            block('stucco' if exterior else 'inside',l,r,-T/2,T/2,z+low,z+bottom)
            low = max(low,top)
    if exterior:
        # Each lap course is clipped at openings rather than covering glass.
        course = 0.48
        for j in range(math.ceil(h/course)):
            bottom, top = j*course, min(h,(j+1)*course-0.025)
            segments = [(lo,hi)]
            for o in openings:
                if bottom < o[3] and top > o[2]:
                    segments = [(p,q) for l,r in segments for p,q in
                                [(l,min(r,o[0])),(max(l,o[1]),r)] if q>p]
            v0,v1 = sorted((normal*(T/2+0.015), normal*(T/2+0.07)))
            for l,r in segments:
                block('siding',l,r,v0,v1,z+bottom,z+top)
    return block


def window(name, a, b, z, bottom, top, openings, shutters=False, normal=-1):
    # Return opening tuple; frames live on the outside of wall.
    l,r = openings
    horizontal = abs(a[1]-b[1]) < 0.001
    fixed = a[1] if horizontal else a[0]
    def part(mat,u0,u1,v0,v1,h0,h1):
        if horizontal:
            box(name,mat,u0,u1,fixed+v0,fixed+v1,z+h0,z+h1)
        else:
            box(name,mat,fixed+v0,fixed+v1,u0,u1,z+h0,z+h1)
    def face(mat,u0,u1,h0,h1,depth=0.1):
        v = normal*(T/2+0.11)
        part(mat,u0,u1,v-depth/2,v+depth/2,h0,h1)
    part('glass',l,r,-0.035,0.035,bottom,top)
    for u in (l,r):
        face('trim',u-0.12,u+0.12,bottom-0.12,top+0.12)
    for h in (bottom,top):
        face('trim',l-0.12,r+0.12,h-0.12,h+0.12)
    frame = 'wood' if shutters else 'trim'
    face(frame,l+0.06,l+0.14,bottom,top)
    face(frame,r-0.14,r-0.06,bottom,top)
    face(frame,(l+r)/2-0.025,(l+r)/2+0.025,bottom,top,0.06)
    for h in (bottom+(top-bottom)*0.5,bottom+(top-bottom)*0.75):
        face(frame,l,r,h-0.025,h+0.025,0.06)
    face('trim',l-0.2,r+0.2,bottom-0.18,bottom-0.06,0.25)
    if shutters:
        for s0,s1 in [(l-1.18,l-0.18),(r+0.18,r+1.18)]:
            face('blue',s0,s1,bottom,top,0.14)
            for k in range(5):
                face('blue',s0+k*0.2,s0+k*0.2+0.035,bottom,top,0.19)
            for h in (bottom+0.15,top-0.3):
                face('blue',s0-0.05,s1+0.05,h,h+0.18,0.23)
            # Visible diagonal barn-shutter brace.
            v = fixed+normal*0.48
            if horizontal:
                beam(name,'blue',(s0,v,bottom+z+0.35),(s1,v,top+z-0.35),0.13)
            else:
                beam(name,'blue',(v,s0,bottom+z+0.35),(v,s1,top+z-0.35),0.13)
    return (l,r,bottom,top)


def door(name, x, y, z, width=3, height=8, mat='blue'):
    box(name,mat,x-width/2,x+width/2,y-0.12,y+0.12,z,z+height)
    for xx in (x-width/2-0.09,x+width/2+0.09):
        box(name,'trim',xx-0.09,xx+0.09,y-0.30,y+0.2,z,z+height+0.14)
    box(name,'trim',x-width/2-0.18,x+width/2+0.18,y-0.3,y+0.2,z+height,z+height+0.18)
    for h0,h1 in [(0.6,1.9),(2.3,6.1),(6.5,7.5)]:
        # Raised rectangular panel border, not just a flat painted door.
        l,r=x-width/2+0.28,x+width/2-0.28
        for xx in (l,r):
            box(name,mat,xx,xx+0.06,y-0.17,y-0.12,z+h0,z+h1)
        for hh in (h0,h1):
            box(name,mat,l,r+0.06,y-0.17,y-0.12,z+hh,z+hh+0.06)
    box(name,'metal',x+width/2-0.4,x+width/2-0.3,y-0.25,y-0.16,z+3.1,z+3.6)


# Foundations: irregular ground footprint, full upstairs rectangle.
for rect in [(0,18.7,0,FRONT),(0,W,FRONT,BACK)]:
    box('Foundation','tile',*rect,0,GROUND)
box('Rear lanai','tile',0,16.333,BACK,BACK+8,0,GROUND)
box('Entry porch','tile',18.7,W,16.4,FRONT,0,GROUND)
box('Ground floor finishes','floor',11.7,W,FRONT,33.2,GROUND,GROUND+0.045)
box('Ground floor finishes','tile',0,W,33.2,BACK,GROUND,GROUND+0.045)
# Split upper floor around stairwell.
box('Upper floor slab','floor',0,28.7,FRONT,BACK,UPPER-0.5,UPPER)
box('Upper floor slab','floor',28.7,W,FRONT,24.8,UPPER-0.5,UPPER)
box('Upper floor slab','floor',28.7,W,39,BACK,UPPER-0.5,UPPER)

# Garage front with genuine 16-foot opening.
wall('Garage front',(0,0),(18.7,0),GROUND,H1,[(1.35,17.35,0,7.8)],True)
box('Garage door','wood',1.35,17.35,-0.02,0.12,GROUND,GROUND+7.8)
for row in range(4):
    for col in range(4):
        l=1.35+col*4+0.18; r=l+3.64
        b=GROUND+row*1.95+0.18; t=b+1.58
        box('Garage raised panels','wood',l,r,-0.075,-0.02,b,t)
        for xx in (l,r-0.055):
            box('Garage raised panels','wood',xx,xx+0.055,-0.105,-0.075,b,t)
        for zz in (b,t-0.055):
            box('Garage raised panels','wood',l,r,-0.105,-0.075,zz,zz+0.055)
for x in (1.2,17.5):
    box('Garage casing','trim',x-0.12,x+0.12,-0.4,0.1,GROUND,GROUND+8.1)
box('Garage casing','trim',1.05,17.65,-0.4,0.1,GROUND+7.85,GROUND+8.15)
wall('Garage left',(0,0),(0,FRONT),GROUND,H1,exterior=True)
wall('Garage right',(18.7,0),(18.7,FRONT),GROUND,H1,exterior=False)
front_windows=[window('Entry window',(18.7,FRONT),(W,FRONT),GROUND,2.2,7.8,(20.2,23),normal=-1)]
front_windows.append((24.3,27.3,0,8))
wall('Ground front',(18.7,FRONT),(W,FRONT),GROUND,H1,front_windows,True)
door('Blue front door',25.8,FRONT,GROUND)
# Rear wall with kitchen slider and great-room triple window.
rear=[window('Great room rear',(0,BACK),(W,BACK),GROUND,3,8,(19,28.7),normal=1),
      window('Kitchen sliding doors',(0,BACK),(W,BACK),GROUND,0,8,(3,12),normal=1)]
wall('Ground rear',(0,BACK),(W,BACK),GROUND,H1,rear,True,1)
for side,n in [(0,-1),(W,1)]:
    ops=[]
    if side==W:
        ops=[window('Great room side',(side,FRONT),(side,BACK),GROUND,3,8,(46,51),normal=n)]
    wall('Ground side '+str(side),(side,FRONT),(side,BACK),GROUND,H1,ops,True,n)
# Upstairs front: three tall windows with blue board-and-batten shutters.
uf=[]
for l,r in [(2,5),(18.5,21.5),(25.8,28.8)]:
    uf.append(window('FH-1 upper front',(0,FRONT),(W,FRONT),UPPER,2,7.8,(l,r),True))
wall('Upper front',(0,FRONT),(W,FRONT),UPPER,H2,uf,True)
uf=[]
for l,r,b,t in [(14,17,4.3,7.5),(19,22,2.4,7.6),(27,30,2.4,7.6)]:
    uf.append(window('Upper rear',(0,BACK),(W,BACK),UPPER,b,t,(l,r),normal=1))
wall('Upper rear',(0,BACK),(W,BACK),UPPER,H2,uf,True,1)
for side,n,ranges in [(0,-1,[(26,29),(38,41)]),(W,1,[(29.2,32.2),(45,49)])]:
    ops=[window('Upper side '+str(side),(side,FRONT),(side,BACK),UPPER,2.5,7.5,o,normal=n) for o in ranges]
    wall('Upper side '+str(side),(side,FRONT),(side,BACK),UPPER,H2,ops,True,n)
# Corner boards and floor belt.
for x,y,z,h in [(0,0,GROUND,H1),(18.7,0,GROUND,H1),(W,FRONT,GROUND,H1),
                 (0,FRONT,UPPER,H2),(W,FRONT,UPPER,H2),(0,BACK,GROUND,EAVE-GROUND),(W,BACK,GROUND,EAVE-GROUND)]:
    box('Exterior corner boards','trim',x-0.33,x+0.33,y-0.33,y+0.33,z,z+h)
for y in (FRONT,BACK):
    box('Floor belt trim','trim',-0.3,W+0.3,y-0.33,y+0.33,UPPER-0.35,UPPER-0.12)

# Partition network traced from the plan, including recessed garage/storage.
def partition(name,a,b,z,h,holes=()):
    wall(name,a,b,z,h,holes)

partition('Garage leisure separation',(11.7,FRONT),(11.7,33.2),GROUND,H1)
partition('Garage rear storage',(0,33.2),(11.7,33.2),GROUND,H1,[(2.3,5.1,0,7)])
partition('Cafe leisure separation',(11.7,33.2),(28.7,33.2),GROUND,H1,[(19.7,24.1,0,8)])
partition('Foyer leisure wall',(23.5,FRONT),(23.5,33.2),GROUND,H1,[(24.8,29.2,0,8)])
partition('Powder side',(28.7,FRONT),(28.7,28),GROUND,H1,[(22.8,25.5,0,7)])
partition('Powder back',(28.7,28),(W,28),GROUND,H1)
partition('Garage rear powder back',(0,39),(11.7,39),GROUND,H1,[(2.7,5.4,0,7)])
partition('Garage rear powder side',(6.1,33.2),(6.1,39),GROUND,H1,[(34.3,37,0,7)])
partition('Garage rear powder side',(11.7,33.2),(11.7,39),GROUND,H1)
# Upper: bedroom 2 left front, bedroom 3 left rear; master right rear.
partition('Upper bedrooms hall',(11.6,FRONT),(11.6,47),UPPER,H2,[(29.1,32,0,7),(34.7,37.6,0,7)])
partition('Bedroom 2 closets',(0,31.5),(11.6,31.5),UPPER,H2,[(1.5,5.4,0,7)])
partition('Bedroom 3 closets',(0,36.2),(8,36.2),UPPER,H2,[(1.5,5.4,0,7)])
partition('Bedroom closet divider',(0,33.85),(8,33.85),UPPER,H2)
partition('Closet end',(8,31.5),(8,36.2),UPPER,H2)
partition('Bedroom 3 bath back',(0,47),(18.3,47),UPPER,H2)
partition('Master west',(18.3,38.5),(18.3,BACK),UPPER,H2,[(38.7,41.6,0,7),(48.1,50.9,0,7)])
partition('Master closet front',(21.8,38.5),(W,38.5),UPPER,H2)
partition('Master closet back',(21.8,40.7),(W,40.7),UPPER,H2,[(24.8,29.8,0,7)])
partition('Master closet end',(21.8,38.5),(21.8,40.7),UPPER,H2)
partition('Master bath closet',(6.3,47),(6.3,BACK),UPPER,H2,[(47.5,50.3,0,7)])
partition('Master toilet wall',(12,44.6),(18.3,44.6),UPPER,H2)
partition('Master toilet side',(12,44.6),(12,48),UPPER,H2,[(45,47.5,0,7)])
partition('Utility left',(12,36.4),(12,44.6),UPPER,H2)
partition('Utility front',(12,36.4),(18.3,36.4),UPPER,H2,[(15,17.8,0,7)])
partition('HVAC front',(12,42.1),(18.3,42.1),UPPER,H2,[(15.1,17.7,0,7)])
partition('Bath 2 west',(11.6,FRONT),(11.6,31.5),UPPER,H2)
partition('Bath 2 east',(17.1,FRONT),(17.1,31.5),UPPER,H2)
partition('Bath 2 north',(11.6,31.5),(17.1,31.5),UPPER,H2,[(12.5,15.3,0,7)])
# Stair flight follows right edge; tread rise spans the actual floor levels.
N=17
start,end=24.8,39.0
for i in range(N):
    y0=start+i*(end-start)/N
    box('Stair treads','wood',28.8,31.7,y0,y0+(end-start)/N,GROUND,GROUND+(UPPER-GROUND)*(i+1)/N)
for i in range(N+1):
    y=start+i*(end-start)/N
    z=GROUND+(UPPER-GROUND)*i/N
    beam('Stair balusters','trim',(28.65,y,z),(28.65,y,z+3),0.075)
beam('Stair handrail','wood',(28.65,start,GROUND+3),(28.65,end,UPPER+3),0.17)
for x in [28.5,30,31.6]:
    beam('Upper landing balusters','trim',(x,39,UPPER),(x,39,UPPER+3),0.09)
beam('Upper landing rail','wood',(28.5,39,UPPER+3),(31.6,39,UPPER+3),0.17)

# Kitchen perimeter cabinetry and central island, as drawn.
box('Kitchen cabinets','cabinet',0.5,2.6,39.5,54.5,GROUND,GROUND+2.9)
box('Kitchen worktops','counter',0.4,2.7,39.4,54.6,GROUND+2.9,GROUND+3.05)
box('Kitchen island','cabinet',6.4,10.8,42.8,50.7,GROUND,GROUND+2.9)
box('Kitchen island','counter',6.2,11.0,42.6,50.9,GROUND+2.9,GROUND+3.08)
for y in [40,42,44,46,48,50,52]:
    box('Cabinet fronts','cabinet',2.6,2.67,y,y+1.8,GROUND+0.3,GROUND+2.7)
    box('Cabinet handles','metal',2.67,2.73,y+0.8,y+1.1,GROUND+2.3,GROUND+2.37)
box('Refrigerator','metal',0.6,3,39.5,42,GROUND,GROUND+6.5)
box('Cooktop','metal',0.6,2.55,47.5,49.7,GROUND+3.05,GROUND+3.1)
for x in [1.1,2]:
    for y in [48,49.1]:
        box('Burners','metal',x-0.25,x+0.25,y-0.25,y+0.25,GROUND+3.1,GROUND+3.14)
# Sink represented as rim and recessed dark basin insert.
def sink(name,x,y,z):
    box(name,'metal',x-0.7,x+0.7,y-0.8,y+0.8,z,z+0.04)
    box(name,'glass',x-0.55,x+0.55,y-0.65,y+0.65,z+0.04,z+0.05)
    beam(name,'metal',(x,y+0.9,z),(x,y+0.9,z+0.9),0.07)
    beam(name,'metal',(x,y+0.9,z+0.9),(x,y+0.3,z+0.9),0.07)
sink('Island sink',7.5,46.4,GROUND+3.08)


def bath(name,x,y,z,w=2.6,d=5):
    box(name,'ceramic',x,x+w,y,y+d,z,z+0.3)
    for l,r,b,t in [(x,x+0.18,y,y+d),(x+w-0.18,x+w,y,y+d),(x,x+w,y,y+0.18),(x,x+w,y+d-0.18,y+d)]:
        box(name,'ceramic',l,r,b,t,z+0.3,z+1.6)


def toilet(name,x,y,z):
    box(name,'ceramic',x-0.55,x+0.55,y-0.7,y+0.7,z,z+1.25)
    box(name,'ceramic',x-0.68,x+0.68,y-0.8,y+0.6,z+1.25,z+1.4)
    box(name,'ceramic',x-0.6,x+0.6,y+0.6,y+1.1,z,z+2.6)


def vanity(name,x0,x1,y0,y1,z,count=1):
    box(name,'cabinet',x0,x1,y0,y1,z,z+2.8)
    box(name,'counter',x0,x1,y0,y1,z+2.8,z+2.95)
    for i in range(count):
        sink(name,(x0+(i+0.5)*(x1-x0)/count),(y0+y1)/2,z+2.95)
vanity('Powder vanity',29.1,31.7,20.7,22.2,GROUND)
toilet('Powder toilet',30.3,26,GROUND)
vanity('Rear garage bath vanity',6.6,10.7,33.7,35.2,GROUND)
toilet('Rear garage bath toilet',3.5,37,GROUND)
vanity('Master double vanity',6.6,12.5,52.5,54.5,UPPER,2)
bath('Master shower tray',13,51.7,UPPER,4.8,2.8)
toilet('Master WC',16.4,46.3,UPPER)
vanity('Bath 2 vanity',15,16.8,25.6,29.9,UPPER)
toilet('Bath 2 WC',15.5,24,UPPER)
bath('Bath 2 tub',12,20.8,UPPER,4.7,2.7)
for y in (37,39.8):
    box('Laundry machines','ceramic',12.4,14.8,y,y+2.5,UPPER,UPPER+3.1)
    box('Laundry machine lid','metal',12.55,14.65,y+0.25,y+2.1,UPPER+3.1,UPPER+3.15)

# Roof meshes plus discrete shingle courses; no texture files required.
def roof_face(name, verts):
    poly(name,'roof',verts,[tuple(range(len(verts)))])
    # Tile small planar strips by scan-converting the face at each Y row.
    # All roof faces here are convex and planar.
    v0,v1,v2=map(Vector,verts[:3])
    n=(v1-v0).cross(v2-v0)
    if abs(n.z)<1e-8:
        return
    def height(x,y):
        return v0.z-(n.x*(x-v0.x)+n.y*(y-v0.y))/n.z+0.045
    def bounds(y):
        xs=[]
        for p,q in zip(verts,verts[1:]+verts[:1]):
            if abs(q[1]-p[1])>1e-8 and min(p[1],q[1])-1e-7<=y<=max(p[1],q[1])+1e-7:
                xs.append(p[0]+(q[0]-p[0])*(y-p[1])/(q[1]-p[1]))
        return (min(xs),max(xs)) if xs else None
    ymin=min(v[1] for v in verts); ymax=max(v[1] for v in verts)
    rows=math.ceil((ymax-ymin)/0.45)
    for j in range(rows):
        a=ymin+j*0.45+0.015; b=min(ymax-0.015,a+0.42)
        if b<=a: continue
        ba,bb=bounds(a),bounds(b)
        if not ba or not bb: continue
        l=max(ba[0],bb[0]); r=min(ba[1],bb[1])
        x=l
        while x<r-0.02:
            end=min(r,x+0.95)
            xx=x+0.015; ex=end-0.015
            if ex>xx:
                poly(name,'shingle'+str(random.randrange(5)),
                     [(xx,a,height(xx,a)),(ex,a,height(ex,a)),(ex,b,height(ex,b)),(xx,b,height(xx,b))],[(0,1,2,3)])
            x=end
    for a,b in zip(verts,verts[1:]+verts[:1]):
        beam(name+' edge caps','roof',a,b,0.13)


def hip(name,x0,x1,y0,y1,z,pitch=0.375):
    inset=min(x1-x0,y1-y0)/2
    # Rectangular hip, ridge along Y for this house's longer depth.
    ridge=(x0+x1)/2
    r0=(ridge,y0+inset,z+inset*pitch)
    r1=(ridge,y1-inset,z+inset*pitch)
    A=(x0,y0,z); B=(x1,y0,z); C=(x1,y1,z); D=(x0,y1,z)
    for face in [[A,B,r0],[B,C,r1,r0],[C,D,r1],[D,A,r0,r1]]:
        roof_face(name,face)
    beam(name+' ridge','roof',r0,r1,0.2)
    for a,b in [(A,B),(B,C),(C,D),(D,A)]:
        beam(name+' fascia','trim',(a[0],a[1],z-0.15),(b[0],b[1],z-0.15),0.3)
    box(name+' soffit','trim',x0,x1,y0,y1,z-0.23,z-0.18)

hip('Main hipped roof',-0.7,W+0.7,FRONT-0.7,BACK+0.7,EAVE+0.2,0.375)
# FH-1 garage GABLE, deliberately not the C-1 tiled hip.
x0,x1,y0,y1=-0.7,19.4,-0.7,FRONT+0.3
ze=GROUND+H1+0.35
xm=(x0+x1)/2; zr=ze+4.6
roof_face('Garage gable roof',[(x0,y0,ze),(xm,y0,zr),(xm,y1,zr),(x0,y1,ze)])
roof_face('Garage gable roof',[(xm,y0,zr),(x1,y0,ze),(x1,y1,ze),(xm,y1,zr)])
poly('Garage front gable','siding',[(0,-0.26,ze),(18.7,-0.26,ze),(xm,-0.26,zr-0.18)],[(0,1,2)])
# Vertical board-and-batten clipped to the front triangle.
for i in range(24):
    x=0.2+i*0.79
    top=ze+(zr-0.18-ze)*max(0,1-abs(x-xm)/(18.7/2))
    box('Gable battens','siding',x-0.045,x+0.045,-0.34,-0.27,ze,top)
for a,b in [((x0,y0,ze),(xm,y0,zr)),((xm,y0,zr),(x1,y0,ze))]:
    beam('Gable rake trim','trim',a,b,0.26)
beam('Garage ridge cap','roof',(xm,y0,zr),(xm,y1,zr),0.2)
box('Gable base trim','trim',-0.4,19.1,-0.48,-0.16,ze-0.3,ze+0.05)
for x in [3.1,xm,15.6]:
    top=ze+(zr-ze)*(1-abs(x-xm)/10.05)-0.35
    box('FH-1 gable brackets','wood',x-0.12,x+0.12,-0.6,-0.27,top-0.85,top)
# Lower porch roof slopes up to the upper front. Garage roof hides left joint.
roof_face('Porch shed roof',[(18.4,16,ze),(32.7,16,ze),(32.7,FRONT+0.1,ze+1.7),(18.4,FRONT+0.1,ze+1.7)])
box('Porch fascia','trim',18.4,32.7,15.85,16.15,ze-0.35,ze)
box('Porch ceiling','trim',18.7,W,16.3,FRONT,GROUND+H1-0.12,GROUND+H1)
for x in (30.4,31.7):
    box('FH-1 paired porch columns','trim',x-0.21,x+0.21,16.45,16.87,GROUND,ze-0.3)
    box('Porch column capitals','trim',x-0.3,x+0.3,16.36,16.96,ze-0.7,ze-0.4)
# Covered base lanai; no optional extension or screening.
hip('Lanai roof',-0.5,16.833,BACK-0.2,BACK+8.5,GROUND+H1+0.1,0.23)
for x in (0.25,16.08):
    box('Lanai columns','trim',x-0.23,x+0.23,BACK+7.5,BACK+8,GROUND,GROUND+H1)

# Final mesh assembly. Roof collection can be hidden for plan inspection.
collections={}
for (group,mat),(verts,faces) in data.items():
    if group not in collections:
        col=bpy.data.collections.new(group)
        root.children.link(col)
        collections[group]=col
    mesh=bpy.data.meshes.new(group+' | '+mat)
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    obj=bpy.data.objects.new(group+' | '+mat,mesh)
    collections[group].objects.link(obj)
    mesh.materials.append(mats[mat])
    obj['reference']='Honor brochure; FH-1 facade; C-1 floor plan'
root['notes']='Approximate brochure reconstruction. Front -Y; dimensions converted feet to meters.'
for obj in bpy.context.selected_objects:
    obj.select_set(False)
print('Honor FH-1 model complete: meshes only, no cameras, lights, landscaping or backdrop.')
