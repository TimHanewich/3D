"""4690 Deer Creek Boulevard — photo-inspired landscape and site.
Run in Blender's Scripting workspace after house.py and pool.py.
Standalone procedural geometry; no downloads, assets or add-ons required.
Same meters/origin as both scripts: front = -Y, garage/driveway = -X.
Only E4690 and its generated objects are replaced on rerun.
House, dry pool, cage, cameras, lights, world and render settings are untouched.

REFERENCE NOTES
Front planting, curved pale driveway, curved entry walk, mulch, queen-like
palms and spreading shade trees follow the supplied photographs. The aerial
informs an open rear lawn and landscaped side strips. Lot limits, road,
tree positions and rear landscaping are visual estimates, NOT a survey.
The aerial is not an orthographic plan registered to the house floorplan.
Vegetation is procedural illustrative geometry, not botanical scans.
No added pool water, screen mesh, fence, furniture or neighboring buildings.
No automatic .blend save. Save your scene normally after running.

EDITING
SITE_BOUNDS and planting positions below are world meters. Plan anchors use
xy(), identical to house.py. Toggle tree crowns off for architectural review.
Surfaces stop below existing thresholds; terrain has a real opening beneath
the combined house/deck footprint so it cannot fill the dry swimming pool.
"""
import math
import random
import bpy
import bmesh
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

# -------------------------- editable settings --------------------------
PREFIX = 'E4690'
SCALE = 13.0 * .3048 / 207.0
SEED = 4690
SITE_BOUNDS = (-20.5, 17.0, -15.0, 31.0)  # xmin, xmax, front, rear
LAWN_Z = -.055
PAVING_Z = -.015
BED_Z = -.027
MAKE_STREET = True
MAKE_TREES = True
MAKE_TREE_CROWNS = True
MAKE_PALMS = True
MAKE_SMALL_PLANTS = True
MAKE_PATH_LIGHTS = True  # Geometry only, no actual Blender lights.
FOLIAGE_DENSITY = 1.0   # .5 for lighter geometry; 1.5 for fuller crowns.
rng = random.Random(SEED)


def xy(p):
    return ((p[0]-710)*SCALE, (1080-p[1])*SCALE)


if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
old = bpy.data.collections.get(PREFIX)
if old:
    # Remove owned objects only; do not purge unrelated scene datablocks.
    data_to_clean = []
    for ob in list(old.all_objects):
        if ob.data is not None:
            data_to_clean.append(ob.data)
        bpy.data.objects.remove(ob, do_unlink=True)
    def remove_collection(col):
        for child in list(col.children):
            remove_collection(child)
        bpy.data.collections.remove(col)
    remove_collection(old)
    for data in data_to_clean:
        if data.users == 0:
            if isinstance(data, bpy.types.Mesh):
                bpy.data.meshes.remove(data)
            elif isinstance(data, bpy.types.Curve):
                bpy.data.curves.remove(data)
root = bpy.data.collections.new(PREFIX)
bpy.context.scene.collection.children.link(root)
groups = {}
for name in ('Ground', 'Hardscape', 'Beds', 'Palms', 'Trees', 'Shrubs', 'Details'):
    col = bpy.data.collections.new(PREFIX+'_'+name)
    root.children.link(col)
    groups[name] = col


def material(name, low, high=None, scale=1, bump=0, roughness=.8):
    mat = bpy.data.materials.get(PREFIX+'_'+name)
    if mat is None:
        mat = bpy.data.materials.new(PREFIX+'_'+name)
    mat.diffuse_color = (*low, 1)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    out = nodes.new('ShaderNodeOutputMaterial')
    shader = nodes.new('ShaderNodeBsdfPrincipled')
    shader.inputs['Base Color'].default_value = (*low, 1)
    shader.inputs['Roughness'].default_value = roughness
    links.new(shader.outputs['BSDF'], out.inputs['Surface'])
    if high or bump:
        coord = nodes.new('ShaderNodeTexCoord')
        tex = nodes.new('ShaderNodeTexNoise')
        tex.inputs['Scale'].default_value = scale
        tex.inputs['Detail'].default_value = 3
        links.new(coord.outputs['Object'], tex.inputs['Vector'])
        if high:
            ramp = nodes.new('ShaderNodeValToRGB')
            ramp.color_ramp.elements[0].color = (*low, 1)
            ramp.color_ramp.elements[1].color = (*high, 1)
            links.new(tex.outputs['Fac'], ramp.inputs['Fac'])
            links.new(ramp.outputs['Color'], shader.inputs['Base Color'])
        if bump:
            normal = nodes.new('ShaderNodeBump')
            normal.inputs['Strength'].default_value = .28
            normal.inputs['Distance'].default_value = bump
            links.new(tex.outputs['Fac'], normal.inputs['Height'])
            links.new(normal.outputs['Normal'], shader.inputs['Normal'])
    return mat


grass = material('Living lawn', (.035,.095,.018), (.17,.29,.045), 25, .018)
soil = material('Earth sides', (.09,.052,.023), (.16,.09,.041), 35, .015)
concrete = material('Warm pale concrete', (.56,.55,.46), (.78,.76,.65), 6, .006)
mulch = material('Reddish brown bark mulch', (.065,.026,.013), (.21,.082,.035), 48, .026)
asphalt = material('Fine gray asphalt', (.13,.15,.15), (.25,.27,.26), 65, .009)
jointmat = material('Concrete control joints', (.18,.175,.145))
bark = material('Oak bark', (.095,.072,.04), (.25,.21,.13), 14, .022)
palmbark = material('Palm fibrous gray trunk', (.26,.24,.17), (.46,.43,.32), 24, .012)
bronze = material('Dark bronze landscape fixtures', (.055,.052,.035), roughness=.4)
stone = material('Landscape limestone', (.36,.32,.19), (.64,.57,.35), 9, .024)
foliage = [material('Leaf green %02d' % i, color, roughness=.72) for i,color in enumerate([
    (.035,.095,.019), (.06,.155,.028), (.10,.23,.038),
    (.18,.29,.055), (.25,.34,.085)])]
burgundy = [material('Ti leaf %02d' % i, color) for i,color in enumerate([
    (.13,.022,.036), (.27,.047,.072), (.34,.075,.10), (.17,.14,.033)])]
strapmats = [material('Liriope leaf %02d' % i, color) for i,color in enumerate([
    (.10,.22,.045), (.21,.32,.09), (.33,.39,.14)])]
flowers = [material('Small tropical flowers %02d' % i, color) for i,color in enumerate([
    (.62,.10,.07), (.76,.25,.13), (.80,.51,.12)])]


def mesh(name, verts, faces, mats, group, indices=None, smooth=False):
    data = bpy.data.meshes.new(PREFIX+'_'+name)
    data.from_pydata(verts, [], faces)
    data.update()
    ob = bpy.data.objects.new(PREFIX+'_'+name, data)
    groups[group].objects.link(ob)
    if mats:
        if not isinstance(mats, (list, tuple)):
            mats = [mats]
        for mat in mats:
            data.materials.append(mat)
    for i,face in enumerate(data.polygons):
        face.use_smooth = smooth
        if indices:
            face.material_index = indices[i]
    return ob


def prism(name, polygon, bottom, top, mat, group='Hardscape'):
    poly = [Vector((p[0],p[1],0)) for p in polygon]
    area = sum(p.x*poly[(i+1)%len(poly)].y-poly[(i+1)%len(poly)].x*p.y
               for i,p in enumerate(poly))
    if area < 0:
        poly.reverse()
    n = len(poly)
    verts = [(p.x,p.y,z) for z in (bottom,top) for p in poly]
    # Accept index triangles and vector triangles from different API builds.
    lookup = {(round(p.x,8),round(p.y,8)): i for i,p in enumerate(poly)}
    faces = []
    for tri in tessellate_polygon([poly]):
        ids = tuple(lookup[(round(p.x,8),round(p.y,8))]
                    if isinstance(p, Vector) else int(p) for p in tri)
        if len(ids) != 3 or any(i < 0 or i >= n for i in ids):
            raise ValueError('Invalid triangulation for '+name)
        a,b,c = (poly[i] for i in ids)
        winding = (b-a).cross(c-a).z
        if abs(winding) < 1e-12:
            continue
        if winding < 0:
            ids = tuple(reversed(ids))
        faces.extend([tuple(reversed(ids)),tuple(i+n for i in ids)])
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,verts,faces,mat,group)


def box(name, center, size, mat, group='Details'):
    x,y,z = center
    a,b,c = (v/2 for v in size)
    return prism(name,[(x-a,y-b),(x+a,y-b),(x+a,y+b),(x-a,y+b)],z-c,z+c,mat,group)


def tube(name, points, radius, mat, group='Details', sides=8):
    points = [Vector(p) for p in points]
    radii = radius if isinstance(radius,(list,tuple)) else [radius]*len(points)
    verts,faces = [],[]
    for i,p in enumerate(points):
        direction = (points[min(i+1,len(points)-1)]-points[max(0,i-1)]).normalized()
        ref = Vector((0,0,1)) if abs(direction.z)<.92 else Vector((1,0,0))
        u = direction.cross(ref).normalized()
        v = direction.cross(u).normalized()
        for j in range(sides):
            angle = math.tau*j/sides
            verts.append(tuple(p+radii[i]*(u*math.cos(angle)+v*math.sin(angle))))
    for i in range(len(points)-1):
        for j in range(sides):
            a = i*sides+j
            b = i*sides+(j+1)%sides
            faces.append((a,b,b+sides,a+sides))
    faces += [tuple(reversed(range(sides))),tuple(range((len(points)-1)*sides,len(points)*sides))]
    return mesh(name,verts,faces,mat,group,smooth=True)


def difference(ob, cutter):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    modifier = ob.modifiers.new('Clear house and dry pool footprint','BOOLEAN')
    modifier.operation = 'DIFFERENCE'
    modifier.solver = 'EXACT'
    modifier.object = cutter
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    data = cutter.data
    bpy.data.objects.remove(cutter,do_unlink=True)
    if data.users == 0:
        bpy.data.meshes.remove(data)


def bezier(a,b,c,d,steps=20):
    return [tuple((1-t)**3*a[k]+3*(1-t)**2*t*b[k]+3*(1-t)*t*t*c[k]+t**3*d[k]
                  for k in range(len(a))) for t in [i/steps for i in range(steps+1)]]


def smooth_loop(points, passes=3):
    # Chaikin subdivision: closed, convex-corner rounding, no spline overshoot.
    for _ in range(passes):
        result = []
        for a,b in zip(points,points[1:]+points[:1]):
            result += [tuple(.75*a[k]+.25*b[k] for k in range(2)),
                       tuple(.25*a[k]+.75*b[k] for k in range(2))]
        points = result
    return points


def ribbon(name, points, width, z=PAVING_Z, mat=concrete):
    left,right = [],[]
    for i,p in enumerate(points):
        a,b = Vector(points[max(0,i-1)]),Vector(points[min(i+1,len(points)-1)])
        d = (b-a).normalized()
        n = Vector((-d.y,d.x))*width/2
        left.append(tuple(Vector(p)+n))
        right.append(tuple(Vector(p)-n))
    return prism(name,left+list(reversed(right)),z-.085,z,mat)


def seam(name, a, b, z=PAVING_Z):
    # Thin inset-color ribbon instead of raised black rods.
    return ribbon(name,[a,b],.010,z+.0005,jointmat)


# -------------------------- ground and hardscape --------------------------
x0,x1,y0,y1 = SITE_BOUNDS
terrain = prism('Continuous yard with foundation void',[(x0,y0),(x1,y0),(x1,y1),(x0,y1)],
                -.32,LAWN_Z,grass,'Ground')
terrain.data.materials.append(soil)
for f in terrain.data.polygons:
    if f.normal.z < .5:
        f.material_index = 1
# Outer union of house + fixed pool deck, including optional pool bathroom.
# Deliberately use deck boundary, NOT the resized pool or roof bounds.
site_exclusion = [(160,216),(300,216),(300,84),(1257,84),(1257,740),
    (1280,740),(1280,956),(1255,956),(1255,1082),(1195,1082),
    (1195,1110),(1085,1110),(1085,1080),(524,1080),(524,1240),
    (186,1240),(186,1067),(160,1067)]
difference(terrain,prism('Temporary house deck exclusion',[xy(p) for p in site_exclusion],-4,1,None))

# Side-entry garage: double opening at plan (160,933), single at (186,1155).
# One continuous approach curves in from the front-left street edge.
drive = [(-19.4,y0),(-13.1,y0)]
drive += bezier((-13.1,y0),(-12.6,-11),(-11.0,-8.2),(-10.5,-6.4))[1:]
drive += bezier((-10.5,-6.4),(-10.0,-5.4),(-8.6,-4.9),(-8.7,-3.55))[1:]
drive += [(-10.15,-3.55),(-10.15,.20),(-10.65,.20),(-10.65,5.02),(-13.20,5.02)]
drive += bezier((-13.20,5.02),(-16.2,5.3),(-18.35,3.7),(-18.5,.3))[1:]
drive += bezier((-18.5,.3),(-18.6,-4.8),(-17.7,-10),(-19.4,y0))[1:-1]
prism('Sweeping side-entry driveway',drive,-.12,PAVING_Z,concrete)
# Small threshold strips meet the garage wall faces without entering rooms.
for label,center,width,x in [('Double',xy((160,933)),4.20,xy((160,933))[0]),
                             ('Single',xy((186,1155)),2.40,xy((186,1155))[0])]:
    yy = center[1]
    prism(label+' garage threshold apron',[(x-.22,yy-width/2),(x-.105,yy-width/2),
          (x-.105,yy+width/2),(x-.22,yy+width/2)],-.10,PAVING_Z,concrete)
for i,(a,b) in enumerate([
    ((-18.20,-11.1),(-12.75,-11.1)),((-18.02,-7.5),(-11.30,-7.5)),
    ((-18.38,-3.8),(-10.0,-3.8)),((-18.47,.0),(-10.16,.0)),
    ((-18.0,3.4),(-10.66,3.4)),((-14.65,-3.8),(-14.65,4.9))]):
    seam('Driveway control joint %02d'%i,a,b)

# Walk curls around the projecting garage wing, then turns into center gate.
gate_x,gate_y = xy(((684+845)/2,1068))
walk = bezier((-10.65,-5.7),(-7.8,-6.65),(-2.2,-5.3),(-.15,-3.30),28)
walk += bezier((-.15,-3.30),(1.25,-2.1),(gate_x,-.9),(gate_x,gate_y-.09),22)[1:]
ribbon('Curved front-door walk',walk,1.18)
for i in (6,14,22,30,38,46):
    p = Vector(walk[i]); d = (Vector(walk[i+1])-Vector(walk[i-1])).normalized()
    n = Vector((-d.y,d.x))*.585
    seam('Front walk joint %02d'%i,p-n,p+n)
# Gate paving remains house-owned; end only meets its front edge.

# Under/behind the vented equipment screen, keep service access understated.
prism('Equipment service pad',[(-13.5,5.04),(-10.65,5.04),(-10.65,7.8),(-13.5,7.8)],
      -.10,-.024,concrete)
# Side path connects the cage's east access door to the side yard.
side_door = xy((1257,350))
ribbon('East cage door landing',[(side_door[0]+.02,side_door[1]),
        (side_door[0]+1.55,side_door[1])],1.05)
# Rear access framed in pool.py at x=607..665, y=84.
rear_door = xy((636,84))
ribbon('Rear cage door landing',[(rear_door[0],rear_door[1]+.01),
        (rear_door[0],rear_door[1]+1.12)],1.05)

if MAKE_STREET:
    prism('Street context',[(x0-4,y0-7),(x1+4,y0-7),(x1+4,y0-.08),(x0-4,y0-.08)],
          -.25,-.095,asphalt)
    # Leave an actual dropped curb opening at the driveway mouth.
    for a,b in [(x0-4,-19.4),(-13.1,x1+4)]:
        prism('Street curb',[(a,y0-.32),(b,y0-.32),(b,y0),(a,y0)],-.17,.005,concrete)
    prism('Driveway dropped curb', [(-19.4,y0-.32),(-13.1,y0-.32),
          (-13.1,y0),(-19.4,y0)],-.17,PAVING_Z,concrete)

# -------------------------- sculpted mulch beds --------------------------
beds = {}
def bed(name, polygon):
    polygon = smooth_loop(polygon)
    beds[name] = polygon
    return prism(name,polygon,LAWN_Z-.012,BED_Z,mulch,'Beds')

bed('Garage front curved bed',[(-10.0,-3.4),(-3.7,-3.4),(-3.35,-4.5),
    (-5.0,-5.45),(-8.15,-5.55),(-9.9,-4.75)])
bed('Left entry palm bed',[(-3.30,-.15),(-.1,-.15),(-.15,-1.3),
    (-1.15,-3.2),(-3.1,-4.35),(-3.5,-3.35)])
bed('Right entry tropical bed',[(2.0,-.2),(6.05,-.2),(6.05,-.85),
    (9.6,-.9),(11.65,-1.0),(12.5,-2.5),(10.65,-3.25),
    (7.2,-2.4),(3.8,-2.7),(1.9,-1.6)])
bed('West driveway boundary planting',[(-20.35,-4.8),(-19.15,-4.3),(-19.05,2.8),
    (-17.2,5.75),(-14.3,6.0),(-14.1,9.7),(-18.2,10.7),(-20.35,8.5)])
bed('West bedroom border',[(-11.05,8.15),(-11.0,16.8),(-12.0,17.5),
    (-13.35,16.1),(-13.25,11.3),(-12.65,8.2)])
bed('East side border',[(11.55,.25),(12.8,.6),(13.6,5.5),(13.2,10.5),
    (12.9,12.55),(11.50,12.45),(11.35,8.0),(11.45,4.0)])
bed('East rear palm island',[(12.2,16.35),(15.9,16.2),(16.3,20.7),
    (13.7,23.0),(11.6,21.0),(11.55,18.2)])
bed('Rear west shade border',[(-18.6,18.5),(-13.6,18.0),(-10.9,20.2),
    (-7.8,22.1),(-9.4,25.5),(-15.5,26.7),(-19.5,24.1)])


def ellipse_bed(name,x,y,rx,ry):
    return bed(name,[(x+rx*math.cos(i*math.tau/24),y+ry*math.sin(i*math.tau/24))
                     for i in range(24)])
ellipse_bed('Front left oak mulch island',-9.8,-11.0,2.35,2.25)
ellipse_bed('Front right oak mulch island',12.6,-9.0,1.8,1.55)


def inside(p, polygon):
    x,y = p; odd = False
    for a,b in zip(polygon,polygon[1:]+polygon[:1]):
        if (a[1]>y)!=(b[1]>y) and x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:
            odd = not odd
    return odd


# -------------------------- procedural vegetation --------------------------
def leaf(verts,faces,indices,base,tip,width,mat_index=0):
    base,tip = Vector(base),Vector(tip)
    d = tip-base
    ref = Vector((0,0,1)) if abs(d.normalized().z)<.94 else Vector((1,0,0))
    side = d.cross(ref).normalized()*width
    center = base+d*.46
    ridge = center+Vector((0,0,width*.22))
    k = len(verts)
    verts.extend([tuple(base),tuple(center+side),tuple(tip),tuple(center-side),tuple(ridge)])
    faces.extend([(k,k+1,k+4),(k+1,k+2,k+4),(k+2,k+3,k+4),(k+3,k,k+4)])
    indices.extend([mat_index]*4)


def leaf_cloud(name,clusters,mats,group='Shrubs',density=150,size=.16):
    verts,faces,ids = [],[],[]
    for center,radii in clusters:
        center = Vector(center)
        for _ in range(max(12,int(density*FOLIAGE_DENSITY))):
            zz = rng.uniform(-1,1); theta = rng.random()*math.tau
            radial = rng.random()**(1/3)
            r = math.sqrt(1-zz*zz)
            p = center+Vector((r*math.cos(theta)*radii[0],r*math.sin(theta)*radii[1],zz*radii[2]))*radial
            theta = rng.random()*math.tau
            length = size*rng.uniform(.75,1.3)
            direction = Vector((math.cos(theta),math.sin(theta),rng.uniform(-.3,.65))).normalized()
            leaf(verts,faces,ids,p-direction*length/2,p+direction*length/2,
                 length*.25,rng.randrange(len(mats)))
    return mesh(name,verts,faces,mats,group,ids)


def shrub(name,x,y,r=.5,h=.7,flowering=False):
    clusters = [((x,y,BED_Z+h*.54),(r,r,h*.47)),
                ((x-r*.4,y+.1,BED_Z+h*.60),(r*.65,r*.7,h*.35)),
                ((x+r*.45,y-.1,BED_Z+h*.55),(r*.65,r*.7,h*.38))]
    leaf_cloud(name,clusters,foliage,density=max(100,int(260*r)),size=.17)
    if flowering:
        clusters = []
        for _ in range(9):
            a = rng.random()*math.tau
            clusters.append(((x+math.cos(a)*r*.72,y+math.sin(a)*r*.72,BED_Z+h*.85),(.09,.09,.07)))
        leaf_cloud(name+' flower clusters',clusters,flowers,density=12,size=.055)


def strap_plant(name,x,y,height=.50,radius=.43,mats=strapmats,blades=28):
    verts,faces,ids = [],[],[]
    for i in range(blades):
        a = rng.random()*math.tau
        length = radius*rng.uniform(.5,1.25)
        h = height*rng.uniform(.6,1.15)
        width = (.012 if mats is strapmats else .065)*rng.uniform(.7,1.4)
        direction = Vector((math.cos(a),math.sin(a),0))
        side = Vector((-math.sin(a),math.cos(a),0))
        base = Vector((x,y,BED_Z+.01))
        k = len(verts)
        for j in range(7):
            t = j/6
            p = base+direction*(length*t**1.4)+Vector((0,0,h*math.sin(t*2.15)))
            w = width*math.sin(math.pi*(.04+.96*t))
            verts.extend([tuple(p-side*w),tuple(p+Vector((0,0,w*.3))),tuple(p+side*w)])
        mi = rng.randrange(len(mats))
        for j in range(6):
            s = k+j*3
            faces.extend([(s,s+3,s+4,s+1),(s+1,s+4,s+5,s+2)])
            ids.extend([mi,mi])
    return mesh(name,verts,faces,mats,'Shrubs',ids)


def ti_plant(name,x,y,height=1.1):
    tube(name+' slender stems',[(x,y,BED_Z),(x+.07,y,height*.66)], [.035,.012],bark,'Shrubs')
    verts,faces,ids = [],[],[]
    for i in range(22):
        a = i*2.39996
        z = height*(.25+.65*i/22)
        base = Vector((x+.03,y,z))
        tip = base+Vector((math.cos(a)*height*.48,math.sin(a)*height*.48,height*(.6-i/34)))
        leaf(verts,faces,ids,base,tip,height*.075,rng.randrange(len(burgundy)))
    mesh(name+' upright colorful leaves',verts,faces,burgundy,'Shrubs',ids)


def palm(name,x,y,height=7.0,spread=2.5,lean=(.25,.05)):
    base = Vector((x,y,BED_Z))
    points = [base+Vector((lean[0]*t*t,lean[1]*t*t,height*t)) for t in [i/14 for i in range(15)]]
    tube(name+' tapered trunk',points,[.17*(1-.38*i/14) for i in range(15)],palmbark,'Palms',12)
    # Fine annular leaf scars are grouped into one mesh per trunk.
    verts,faces = [],[]
    for row in range(int(height/.19)):
        t = (row+.5)*.19/height
        p = base+Vector((lean[0]*t*t,lean[1]*t*t,height*t))
        r = .17*(1-.38*t)+.004
        k = len(verts)
        for dz in (-.008,.008):
            for j in range(12):
                a = math.tau*j/12
                verts.append(tuple(p+Vector((r*math.cos(a),r*math.sin(a),dz))))
        faces += [(k+j,k+(j+1)%12,k+(j+1)%12+12,k+j+12) for j in range(12)]
    mesh(name+' trunk rings',verts,faces,palmbark,'Palms',smooth=True)
    if not MAKE_TREE_CROWNS:
        return
    crown = points[-1]
    verts,faces,ids = [],[],[]
    for i in range(14):
        a = i*2.39996
        reach = spread*rng.uniform(.78,1.10)
        u = Vector((math.cos(a),math.sin(a),0))
        v = Vector((-math.sin(a),math.cos(a),0))
        rise = rng.uniform(.65,1.45)
        drop = rng.uniform(.45,1.15)
        def mid(t):
            return crown+u*(reach*t)+Vector((0,0,rise*math.sin(math.pi*t*.9)-drop*t*t))
        tube(name+' arching frond rachis',[mid(j/12) for j in range(13)],
             [.024*(1-j/14) for j in range(13)],foliage[2],'Palms',5)
        for j in range(1,25):
            t = j/25
            p = mid(t)
            length = reach*.30*math.sin(math.pi*t)**.7
            for side in (-1,1):
                tip = p+v*side*length+u*length*.28+Vector((0,0,-length*.40))
                leaf(verts,faces,ids,p,tip,.027*(1-t*.65),rng.randrange(len(foliage)))
    # Upright emerging spears at center, characteristic of a palm crown.
    for i in range(5):
        a = i*math.tau/5
        leaf(verts,faces,ids,crown,crown+Vector((.5*math.cos(a),.5*math.sin(a),1.5)),.10,3)
    mesh(name+' pinnate canopy',verts,faces,foliage,'Palms',ids)


def oak(name,x,y,height=9.5,spread=4.5):
    base = Vector((x,y,BED_Z))
    fork = base+Vector((.15,-.1,height*.39))
    tube(name+' broad trunk',[base,base+Vector((.04,.02,height*.18)),fork],
         [.43,.33,.24],bark,'Trees',12)
    clusters = []
    for i in range(7):
        a = i*2.39996
        u = Vector((math.cos(a),math.sin(a),0))
        end = base+u*spread*.67+Vector((0,0,height*rng.uniform(.63,.86)))
        elbow = fork+u*spread*.35+Vector((0,0,height*.14))
        tube(name+' spreading limb',[fork,elbow,end],[.19,.115,.045],bark,'Trees',9)
        for j in range(3):
            angle = a+(j-1)*.60
            tip = end+Vector((math.cos(angle)*spread*.34,math.sin(angle)*spread*.34,height*.12))
            tube(name+' crown branch',[elbow,end,tip],[.070,.045,.012],bark,'Trees',6)
            clusters.append((tuple(tip),(spread*.36,spread*.33,height*.15)))
    # Buttress roots remain within the tree's mulch ring.
    for i in range(5):
        a = i*math.tau/5
        tube(name+' root flare',[base+Vector((0,0,.38)),base+Vector((.8*math.cos(a),.8*math.sin(a),.025))],
             [.14,.025],bark,'Trees',7)
    if MAKE_TREE_CROWNS:
        leaf_cloud(name+' airy broadleaf crown',clusters,foliage,'Trees',density=650,size=.23)


if MAKE_PALMS:
    # Tall narrow front accents, with shorter palms on the right flank.
    for spec in [('Front left queen palm',-2.8,-1.4,7.0,2.2,(.10,.0)),
                 ('Front center queen palm',-.9,-1.1,8.0,2.2,(-.15,.08)),
                 ('Front right queen palm',3.0,-1.35,7.2,2.3,(.17,.06)),
                 ('Right low feather palm',7.9,-1.8,3.4,2.0,(.12,-.1)),
                 ('Right corner palm',11.5,-1.8,5.0,2.25,(.12,.0)),
                 ('Driveway outer palm',-18.65,5.4,6.1,2.6,(-.2,.1)),
                 ('West side palm',-12.2,13.5,5.1,2.1,(-.15,.1)),
                 ('Rear right palm',14.35,19.9,6.0,2.6,(.2,.15))]:
        palm(*spec)
if MAKE_TREES:
    oak('Front west shade oak',-9.8,-11.0,10.0,4.6)
    oak('Front east shade oak',12.6,-9.0,9.2,4.3)
    oak('Rear west shade oak',-14.7,22.5,10.5,4.9)

if MAKE_SMALL_PLANTS:
    # Low foundation shrubs, kept clear of the center gate and front path.
    for i,(x,y) in enumerate([(-9.15,-4.05),(-8.0,-4.15),(-6.8,-4.15),(-5.5,-4.0),
                             (-2.85,-2.4),(3.3,-1.4),(4.5,-1.35),(6.3,-1.55),
                             (9.7,-1.65),(11.8,-2.05)]):
        shrub('Front flowering shrub %02d'%i,x,y,.48,.68,flowering=True)
    for i,(x,y,h) in enumerate([(-9.0,-4.8,1.25),(-4.1,-4.0,1.0),(-2.6,-.6,1.1),
                               (4.8,-2.05,1.1),(8.9,-2.3,1.2),(11.85,-1.45,1.1),
                               (-18.9,7.4,1.15),(12.1,7.6,1.05),(14.6,18.3,1.3)]):
        ti_plant('Burgundy ti plant %02d'%i,x,y,h)
    # Liriope/society-garlic style border clumps follow the curved bed edges.
    for name,poly in beds.items():
        if 'oak mulch' in name:
            continue
        count = max(5,int(sum((Vector(a)-Vector(b)).length for a,b in zip(poly,poly[1:]+poly[:1]))/.9))
        # Arc-length sampling avoids clusters around heavily subdivided corners.
        lengths = [(Vector(b)-Vector(a)).length for a,b in zip(poly,poly[1:]+poly[:1])]
        total = sum(lengths)
        center = sum((Vector(p) for p in poly),Vector((0,0)))/len(poly)
        for i in range(count):
            dist = total*(i+.5)/count
            for j,length in enumerate(lengths):
                if dist <= length:
                    p = Vector(poly[j]).lerp(Vector(poly[(j+1)%len(poly)]),dist/max(length,1e-8))
                    p += (center-p).normalized()*.19
                    strap_plant(name+' border clump %02d'%i,p.x,p.y,.36,.32,blades=19)
                    break
                dist -= length
    # Informal side hedging rather than invented boundary walls/fences.
    for i,y in enumerate((8.9,10.1,11.3,12.5,14.7,15.8)):
        shrub('West side shrub %02d'%i,-11.85,y,.55,.9)
    for i,y in enumerate((1.5,3.0,4.5,6.0,8.8,10.3,11.6)):
        shrub('East side shrub %02d'%i,12.25,y,.56,.88)
    for i,(x,y) in enumerate([(-19.65,-2),(-19.65,.1),(-19.5,2.1),(-18.2,7.3),
                             (-16.8,8.2),(-15.1,8.5),(-18.0,22.0),(-16.5,24.2),
                             (-12.4,24.0),(-10.2,23.0),(13.3,20.9),(15.1,19.0)]):
        shrub('Informal perimeter shrub %02d'%i,x,y,.78,1.35)
    # Low fan-like accent plants beneath the shorter palms.
    for i,(x,y) in enumerate([(-7.2,-4.8),(-1.9,-2.0),(7.2,-1.45),(10.7,-2.3),(-17.6,6.9)]):
        strap_plant('Broad strap accent %02d'%i,x,y,.80,.85,foliage,24)

# -------------------------- small landscape details --------------------------
def rock(name,x,y,size):
    verts,faces = [],[]
    for row,z in enumerate((-.05,.15,.42)):
        for j in range(9):
            a = j*math.tau/9
            r = size*(.8 if row != 1 else 1)*rng.uniform(.85,1.1)
            verts.append((x+r*math.cos(a),y+r*.68*math.sin(a),BED_Z+z*size))
    faces = [tuple(reversed(range(9))),tuple(range(18,27))]
    for row in range(2):
        for j in range(9):
            faces.append((row*9+j,row*9+(j+1)%9,(row+1)*9+(j+1)%9,(row+1)*9+j))
    mesh(name,verts,faces,stone,'Details')
for i,(x,y,s) in enumerate([(-5.0,-4.9,.47),(-2.25,-3.0,.38),(5.4,-1.9,.32),
                           (11.7,-2.5,.38),(-16.0,7.0,.50),(13.1,20.7,.48)]):
    rock('Natural landscape stone %02d'%i,x,y,s)

if MAKE_PATH_LIGHTS:
    lens = material('Path light frosted lens',(.72,.66,.43),roughness=.4)
    for i in (13,28,41):
        p = Vector(walk[i]); d = (Vector(walk[i+1])-Vector(walk[i-1])).normalized()
        p += Vector((-d.y,d.x))*.87
        tube('Low path light post',[(p.x,p.y,LAWN_Z),(p.x,p.y,.40)],.022,bronze)
        tube('Low path light lens',[(p.x,p.y,.35),(p.x,p.y,.42)],.062,lens,sides=12)
        tube('Low path light cap',[(p.x,p.y,.425),(p.x,p.y,.46)], [.105,.025],bronze,sides=16)

# Reference-only metadata travels with the generated collection.
root['Coordinate system'] = 'Meters; same xy() origin as house.py and pool.py; front -Y'
root['Accuracy'] = 'Photo-inspired estimated site, not survey or construction geometry'
root['Site bounds meters'] = SITE_BOUNDS
root['Seed'] = SEED
root['Rear design'] = 'Open lawn retained; no invented rear fence or patio'
root['Ground opening'] = 'Combined fixed house/porch/deck boundary, open below dry pool'
root['Generated object count'] = len(root.all_objects)
print('E4690 environment created: %d objects. House and pool untouched.' % len(root.all_objects))
