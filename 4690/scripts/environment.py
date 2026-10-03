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
SITE_BOUNDS = (-25.0, 17.0, -15.0, 31.0)  # Widened west edge; xmin, xmax, front, rear
LAWN_Z = -.055
PAVING_Z = -.015
BED_Z = -.027
MAKE_STREET = True
MAKE_TREES = True
MAKE_TREE_CROWNS = True
MAKE_PALMS = True
MAKE_SMALL_PLANTS = True
MAKE_PATH_LIGHTS = True  # Geometry only, no actual Blender lights.
MAKE_BASKETBALL_HOOP = True
HOOP_POSITION = (-17.55, 1.25)  # Planted west edge, facing into driveway (+X).
HOOP_RIM_HEIGHT = 3.05          # Visual reconstruction, not measured equipment.
MAKE_PLANTING_MOUND = True
PLANTING_MOUND_HEIGHT = .34    # Raised tree/shrub island ONLY; driveway stays flat.
FRONT_LEFT_TREE_POSITION = (-3.5, -11.0)  # Estimated from marked viewport.
FRONT_RIGHT_TREE_POSITION = (5.8, -10.5)
PLANTING_MOUND_CENTER = FRONT_LEFT_TREE_POSITION  # Move the planted bank too.
PLANTING_MOUND_RADII = (2.10, 2.65)    # Local planted bank, not the approach.
MAKE_STOP_SIGN = True
STOP_SIGN_POSITION = (-19.95, -14.35)  # Opposite (west) verge of driveway entrance.
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
ellipse_bed('Front left oak mulch island',*FRONT_LEFT_TREE_POSITION,2.35,2.25)
ellipse_bed('Front right oak mulch island',*FRONT_RIGHT_TREE_POSITION,1.8,1.55)


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
    oak('Front west shade oak',*FRONT_LEFT_TREE_POSITION,10.0,4.6)
    oak('Front east shade oak',*FRONT_RIGHT_TREE_POSITION,9.2,4.3)
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

# -------------------------- reference touch-ups --------------------------
def planting_rise(x,y):
    # Compact bank beneath the existing street-end tree/shrub island ONLY.
    # No displacement within the driveway, or outside this small ellipse.
    if not MAKE_PLANTING_MOUND:
        return 0.0
    cx,cy = PLANTING_MOUND_CENTER
    rx,ry = PLANTING_MOUND_RADII
    r2 = ((x-cx)/rx)**2+((y-cy)/ry)**2
    if r2 >= 1 or inside((x,y),drive):
        return 0.0
    # Fade out before the paving edge, even if the mound settings are edited.
    point = Vector((x,y))
    clearance = float('inf')
    for a,b in zip(drive,drive[1:]+drive[:1]):
        av,bv = Vector(a),Vector(b)
        delta = bv-av
        t = max(0,min(1,(point-av).dot(delta)/max(delta.length_squared,1e-12)))
        clearance = min(clearance,(point-av-delta*t).length)
    edge = max(0,min(1,(clearance-.15)/.40))
    return PLANTING_MOUND_HEIGHT*(1-r2)**2*edge*edge*(3-2*edge)


def shape_front_planting():
    if not MAKE_PLANTING_MOUND:
        return
    cx,cy = PLANTING_MOUND_CENTER
    rx,ry = PLANTING_MOUND_RADII
    lower,upper = cy-ry,cy+ry
    left,right = cx-rx,cx+rx
    # Hardscape is intentionally excluded: driveway, joints, aprons, walk,
    # street and curb retain their ORIGINAL, FLAT geometry on every rerun.
    for group in ('Ground','Beds'):
        for ob in list(groups[group].objects):
            if ob.type != 'MESH':
                continue
            coords = [v.co for v in ob.data.vertices]
            if not coords or max(p.y for p in coords) <= lower or min(p.y for p in coords) >= upper:
                continue
            if max(p.x for p in coords) <= left or min(p.x for p in coords) >= right:
                continue
            bm = bmesh.new()
            bm.from_mesh(ob.data)
            try:
                for axis,start,end,spacing in ((1,lower,upper,.18),
                                               (0,left,right,.18)):
                    count = max(1,math.ceil((end-start)/spacing))
                    for i in range(count+1):
                        value = start+(end-start)*i/count
                        co = [0.0,0.0,0.0]; co[axis] = value
                        normal = [0.0,0.0,0.0]; normal[axis] = 1.0
                        bmesh.ops.bisect_plane(bm,
                            geom=list(bm.verts)+list(bm.edges)+list(bm.faces),
                            dist=.000001,plane_co=Vector(co),plane_no=Vector(normal),
                            clear_inner=False,clear_outer=False)
                bmesh.ops.triangulate(bm,faces=list(bm.faces))
                for vertex in bm.verts:
                    vertex.co.z += planting_rise(vertex.co.x,vertex.co.y)
                bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
                bm.to_mesh(ob.data)
                ob.data.update()
            finally:
                bm.free()
    # Move the existing oak as one rigid assembly onto its planted bank.
    for ob in groups['Trees'].objects:
        if ob.name.startswith(PREFIX+'_Front west shade oak'):
            ob.location.z += planting_rise(*FRONT_LEFT_TREE_POSITION)
    # Understory shrubbery on this specific island, as shown in the photo.
    # Each complete plant is seated at its own ground height, not distorted.
    if MAKE_SMALL_PLANTS:
        for i,(x,y) in enumerate([(-10.75,-11.45),(-9.75,-12.15),
                                  (-8.75,-11.65),(-8.65,-10.6),(-10.0,-9.8)]):
            # Preserve the original shrub offsets within the moved tree island.
            x += FRONT_LEFT_TREE_POSITION[0]-(-9.8)
            y += FRONT_LEFT_TREE_POSITION[1]-(-11.0)
            before = set(groups['Shrubs'].objects)
            shrub('Raised street-end island shrub %02d'%i,x,y,.58,.95)
            for ob in set(groups['Shrubs'].objects)-before:
                ob.location.z += planting_rise(x,y)
    root['Planting island rise meters'] = PLANTING_MOUND_HEIGHT
    root['Driveway grade'] = 'Flat; raised terrain confined to street-end tree/shrub island'


shape_front_planting()


def portable_basketball_hoop():
    hx,hy = HOOP_POSITION
    ground = PAVING_Z  # The driveway and hoop base remain flat.
    black = material('Hoop charcoal molded base',(.022,.027,.030),roughness=.62)
    steel = material('Hoop black painted steel',(.035,.045,.047),roughness=.36)
    orange = material('Hoop orange rim',(.72,.13,.018),roughness=.40)
    white = material('Hoop white net and target',(.89,.88,.81),roughness=.75)
    clear = material('Hoop clear backboard',(.88,.96,.95),roughness=.10)
    shader = clear.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Transmission Weight'].default_value = 1.0
    shader.inputs['IOR'].default_value = 1.46
    # Local u = along board (+Y); v = into playing area (+X).
    def q(u,v,z):
        return Vector((hx+v,hy+u,ground+z))
    def member(label,a,b,radius=.025,mat=steel):
        return tube('Basketball '+label,[q(*a),q(*b)],radius,mat,'Details',10)
    base = box('Basketball portable weighted base',q(0,-.22,.115),
               (1.12,.83,.20),black)
    bevel = base.modifiers.new('Rounded molded base corners','BEVEL')
    bevel.width = .075
    bevel.segments = 3
    # Raised molding, fill cap, axle and two small transport wheels.
    box('Basketball base molded inset',q(0,-.23,.224),(.69,.54,.018),steel)
    member('base filling plug',(0,-.54,.23),(0,-.54,.246),.055,black)
    member('wheel axle',(-.46,-.65,.09),(.46,-.65,.09),.025)
    for side in (-1,1):
        member('transport wheel',(side*.36,-.65,.095),(side*.47,-.65,.095),.095,black)
    member('main upright',(0,.0,.19),(0,-.15,2.48),.061)
    member('telescoping upper pole',(0,-.15,1.65),(0,-.16,2.76),.047)
    for side in (-1,1):
        member('base diagonal brace',(side*.32,-.52,.20),(0,-.03,1.12),.023)
        member('upper angled support',(side*.12,-.16,2.47),(side*.30,.39,3.27),.024)
        member('lower board support',(side*.08,-.15,2.15),(side*.32,.39,3.02),.024)
    member('height adjustment pin',(-.105,-.095,1.80),(.105,-.095,1.80),.017)
    box('Basketball pole orange label',q(-.062,-.04,1.88),(.11,.006,.22),orange)
    rim_z = HOOP_RIM_HEIGHT
    bottom,top = rim_z-.08,rim_z+.80
    board_v = .42
    board = box('Basketball transparent rectangular backboard',
                q(0,board_v,(bottom+top)/2),(.022,1.28,top-bottom),clear)
    # Borders and white target are actual modeled strips, not textures.
    corners = [(-.64,board_v+.018,bottom),(.64,board_v+.018,bottom),
               (.64,board_v+.018,top),(-.64,board_v+.018,top)]
    for a,b in zip(corners,corners[1:]+corners[:1]):
        member('backboard perimeter',a,b,.022)
    target = [(-.245,board_v+.033,rim_z+.015),(.245,board_v+.033,rim_z+.015),
              (.245,board_v+.033,rim_z+.365),(-.245,board_v+.033,rim_z+.365)]
    for a,b in zip(target,target[1:]+target[:1]):
        member('white target rectangle',a,b,.010,white)
    box('Basketball rim mounting plate',q(0,board_v+.055,rim_z-.035),(.055,.16,.16),orange)
    member('rim mounting arm',(0,board_v+.05,rim_z),(0,board_v+.11,rim_z),.022,orange)
    center_v = board_v+.10+.23
    # Closed tube ring with evenly spaced points, no external assets.
    ring = [q(.23*math.cos(a),center_v+.23*math.sin(a),rim_z)
            for a in [math.tau*i/64 for i in range(65)]]
    tube('Basketball orange steel rim',ring,.0095,orange,'Details',8)
    # Counter-wound cord strands create an open diamond net, not a cone.
    for i in range(12):
        start = i*math.tau/12
        for direction in (-1,1):
            points = []
            for j in range(17):
                t = j/16
                angle = start+direction*t*math.tau/6
                radius = .23-(.23-.135)*min(1,t*1.5)
                points.append(q(radius*math.cos(angle),center_v+radius*math.sin(angle),rim_z-.012-.43*t))
            tube('Basketball woven net strand',points,.0027,white,'Details',5)
    root['Basketball reference'] = 'Portable dark base, clear board, orange rim, open white net; photo-estimated'


if MAKE_BASKETBALL_HOOP:
    portable_basketball_hoop()


def street_stop_sign():
    sx,sy = STOP_SIGN_POSITION
    base_z = LAWN_Z+planting_rise(sx,sy)
    metal = material('Stop sign aluminum back',(.43,.46,.45),roughness=.40)
    red = material('Stop sign red face',(.62,.018,.020),roughness=.43)
    white = material('Stop sign white border and letters',(.95,.94,.87),roughness=.45)
    postmat = material('Street sign dark painted post',(.035,.045,.039),roughness=.5)
    # Turned 180 degrees: STOP now faces east, opposite its former direction.
    # Local u runs +Y, outward depth runs +X, Z is vertical.
    def q(u,depth,z):
        return Vector((sx+depth,sy+u,base_z+z))
    def member(label,a,b,r=.03,mat=postmat):
        return tube('Street sign '+label,[q(*a),q(*b)],r,mat,'Details',10)
    member('round dark post',(0,-.07,0),(0,-.07,3.16),.037)
    member('post foot collar',(0,-.07,0),(0,-.07,.16),.072)
    member('top finial',(0,-.07,3.16),(0,-.07,3.23),[.065,.008])
    center_z = 2.39
    def octagon(label,radius,depth0,depth1,mat):
        outline = [(radius*math.cos(math.pi/8+i*math.tau/8),
                    center_z+radius*math.sin(math.pi/8+i*math.tau/8)) for i in range(8)]
        verts = [tuple(q(u,depth,z)) for depth in (depth0,depth1) for u,z in outline]
        faces = [tuple(reversed(range(8))),tuple(range(8,16))]
        faces += [(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)]
        return mesh('Street sign '+label,verts,faces,mat,'Details')
    # Layered solid plate leaves a narrow white octagonal border.
    octagon('octagonal metal backing',.43,-.012,0,metal)
    octagon('white octagonal border',.424,.001,.004,white)
    octagon('red inset face',.394,.005,.007,red)
    for z in (center_z-.29,center_z+.29):
        member('mounting bolt',(0,.008,z),(0,.014,z),.012,metal)
    text = bpy.data.curves.new(PREFIX+'_STOP lettering',type='FONT')
    text.body = 'STOP'
    text.align_x = 'CENTER'
    text.align_y = 'CENTER'
    text.size = .225
    text.extrude = .0007
    text.resolution_u = 6
    ob = bpy.data.objects.new(PREFIX+'_Street sign STOP',text)
    groups['Details'].objects.link(ob)
    ob.location = q(0,.010,center_z)
    ob.rotation_euler = (math.pi/2,0,math.pi/2)
    text.materials.append(white)
    # Slim street-name blade above, as visible in the reference. No invented
    # second street name; lettering is on both sides of this one blade.
    blade = box('Street sign road-name blade',q(0,-.07,2.98),(.023,1.10,.16),postmat)
    for front in (True,False):
        label = bpy.data.curves.new(PREFIX+'_Street name text',type='FONT')
        label.body = 'DEER CREEK BLVD'
        label.align_x = 'CENTER'
        label.align_y = 'CENTER'
        label.size = .070
        label.extrude = .0003
        obj = bpy.data.objects.new(PREFIX+'_Street name lettering',label)
        groups['Details'].objects.link(obj)
        obj.location = q(0,-.055 if front else -.085,2.98)
        obj.rotation_euler = (math.pi/2,0,math.pi/2 if front else -math.pi/2)
        label.materials.append(white)
    root['Street sign reference'] = 'Estimated verge location; decorative model, not traffic engineering'


if MAKE_STREET and MAKE_STOP_SIGN:
    street_stop_sign()

# -------------------------- NET NEW left roadside oak island --------------------------
# LEFT means west / negative world X when viewing the house from the road.
# This is a fourth large tree, NOT either of the repositioned front-yard oaks.
# Its mound is a new mesh: no displacement, replacement or relocation of the
# existing ground, trees, driveway, sign, curb, hoop or planting islands.
MAKE_NEW_LEFT_ROADSIDE_ISLAND = True
NEW_LEFT_ISLAND_CENTER = (-21.3, -10.3)
NEW_LEFT_ISLAND_RADII = (2.50, 3.10)
NEW_LEFT_ISLAND_HEIGHT = .40
# The lot now extends west to x=-25.0 for its FULL depth, encompassing this
# mound with a continuous lawn strip to the street and up the driveway side.
# The existing skirt feathers into that lawn; its buried perimeter has no
# exposed island edge. Street and curb lengths follow SITE_BOUNDS automatically.
# Tree, mound, sign and driveway positions are deliberately unchanged.


def add_left_roadside_oak_island():
    if not MAKE_NEW_LEFT_ROADSIDE_ISLAND:
        return
    prior_objects = set(root.all_objects)
    state = rng.getstate()
    rng.seed(SEED+714)
    group = 'New left roadside island'
    col = bpy.data.collections.new(PREFIX+'_New_left_roadside_island')
    root.children.link(col)
    groups[group] = col
    cx,cy = NEW_LEFT_ISLAND_CENTER
    rx,ry = NEW_LEFT_ISLAND_RADII
    label = 'NEW left-of-driveway island '

    def edge_shape(a):
        return 1+.022*math.sin(3*a)+.016*math.cos(5*a)

    def ground_at(x,y):
        xx,yy = (x-cx)/rx,(y-cy)/ry
        a = math.atan2(yy,xx)
        r = math.hypot(xx,yy)/edge_shape(a)
        # Outer edge is embedded a few millimeters into the original lawn;
        # the raised top replaces no original vertices or faces.
        return LAWN_Z-.004+NEW_LEFT_ISLAND_HEIGHT*max(0,1-r*r)**2

    def branch(name,points,radii,sides=10):
        return tube(label+name,points,radii,bark,group,sides)

    def core(name,center,radii,mat):
        # Irregular, shaded inner foliage mass, dressed with detailed leaves.
        # Avoids a sparse see-through hedge without using external assets.
        verts,faces = [],[]
        rows,segments = 9,16
        for row in range(rows):
            phi = -math.pi/2+.045+(math.pi-.09)*row/(rows-1)
            for j in range(segments):
                a = math.tau*j/segments
                uneven = 1+.05*math.sin(3*a+row*.6)+.025*math.cos(5*a-row)
                verts.append((center[0]+radii[0]*math.cos(phi)*math.cos(a)*uneven,
                              center[1]+radii[1]*math.cos(phi)*math.sin(a)*uneven,
                              center[2]+radii[2]*math.sin(phi)))
        for row in range(rows-1):
            for j in range(segments):
                a = row*segments+j; b = row*segments+(j+1)%segments
                faces.append((a,b,b+segments,a+segments))
        faces += [tuple(reversed(range(segments))),
                  tuple(range((rows-1)*segments,rows*segments))]
        return mesh(label+name,verts,faces,mat,group,smooth=True)

    try:
        # Build a closed, smoothly sampled mound with a reddish mulch center
        # and grass skirt, entirely LEFT of the actual driveway polygon.
        rings,segments = 30,96
        verts = [(cx,cy,ground_at(cx,cy))]
        faces,ids = [],[]
        for row in range(1,rings+1):
            r = row/rings
            for j in range(segments):
                a = math.tau*j/segments
                x = cx+rx*r*edge_shape(a)*math.cos(a)
                y = cy+ry*r*edge_shape(a)*math.sin(a)
                if inside((x,y),drive) or y <= SITE_BOUNDS[2]:
                    raise ValueError('New left island must remain off driveway and street.')
                verts.append((x,y,ground_at(x,y)))
        for j in range(segments):
            faces.append((0,1+j,1+(j+1)%segments)); ids.append(0)
        for row in range(rings-1):
            a0 = 1+row*segments
            b0 = a0+segments
            for j in range(segments):
                k = (j+1)%segments
                faces.append((a0+j,b0+j,b0+k,a0+k))
                ids.append(0 if (row+2)/rings <= .80 else 1)
        # Close the earthen sides and bottom. The widened continuous lawn
        # now surrounds the entire skirt and conceals its perimeter sides.
        outer = 1+(rings-1)*segments
        bottom = len(verts)
        verts.extend([(verts[outer+j][0],verts[outer+j][1],-.31)
                      for j in range(segments)])
        for j in range(segments):
            k = (j+1)%segments
            faces.append((outer+j,bottom+j,bottom+k,outer+k)); ids.append(2)
        faces.append(tuple(reversed(range(bottom,bottom+segments)))); ids.append(2)
        mound = mesh(label+'raised mulch bank and grass skirt',verts,faces,
                     [mulch,grass,soil],group,ids,smooth=True)
        mound['Net new addition'] = True
        mound['Position'] = 'West / left of driveway when facing house from road'

        if MAKE_TREES:
            # Thick, early-forking oak with substantial spreading boughs.
            # The new trunk stands well outside the driveway edge and the
            # overhead crown can spread naturally across the entrance.
            base = Vector((cx,cy,ground_at(cx,cy)))
            def p(x,y,z):
                return base+Vector((x,y,z))
            branch('mature oak broad trunk',
                   [p(0,0,-.03),p(.03,.02,.35),p(.09,.06,1.25),
                    p(.02,.12,2.15),p(-.10,.15,2.90)],
                   [.79,.66,.56,.50,.42],18)
            for i in range(8):
                a = i*math.tau/8+.1
                length = 1.0+.13*math.sin(i*1.5)
                ex,ey = cx+length*math.cos(a),cy+length*math.sin(a)
                branch('oak buttress root',
                       [p(.12*math.cos(a),.12*math.sin(a),.44),
                        p(.50*math.cos(a),.50*math.sin(a),.13),
                        Vector((ex,ey,ground_at(ex,ey)+.018))],
                       [.22,.13,.023],9)
            fork = p(-.08,.14,2.65)
            clusters = []
            for i in range(8):
                a = i*math.tau/8+.18
                u = Vector((math.cos(a),math.sin(a),0))
                side = Vector((-u.y,u.x,0))
                reach = 4.0+rng.random()*.7
                end = base+u*reach+Vector((0,0,5.5+rng.uniform(-.30,.70)))
                elbow = fork+u*1.6+side*rng.uniform(-.25,.25)+Vector((0,0,1.15))
                points = bezier(tuple(fork),tuple(fork+u*.6+Vector((0,0,.8))),
                                tuple(elbow),tuple(end),16)
                branch('oak spreading scaffold %02d'%i,points,
                       [.32*(1-j/20)**1.30+.018 for j in range(17)],12)
                for j in range(4):
                    aa = a+(j-1.5)*.36
                    direction = Vector((math.cos(aa),math.sin(aa),0))
                    start = Vector(points[9+j])
                    tip = end+direction*rng.uniform(1.1,1.85)+Vector((0,0,rng.uniform(.6,1.5)))
                    middle = start.lerp(tip,.60)+Vector((0,0,.38))
                    branch('oak secondary bough',
                           bezier(tuple(start),tuple(start+direction*.55),
                                  tuple(middle),tuple(tip),10),
                           [.095*(1-k/12)+.008 for k in range(11)],8)
                    for sign in (-1,1):
                        branch('oak fine branching',
                               [middle,tip,tip+side*sign*.60+Vector((0,0,.30))],
                               [.033,.019,.005],5)
                    clusters.append((tuple(tip),(1.40,1.30,1.05)))
                clusters.append((tuple(base+u*2.5+Vector((0,0,7.15+rng.uniform(-.2,.5)))),
                                 (1.85,1.65,1.12)))
            branch('oak central leader',[fork,p(.38,.22,4.0),p(.23,.38,6.0),p(.55,.4,7.5)],
                   [.27,.20,.11,.024],12)
            if MAKE_TREE_CROWNS:
                leaf_cloud(label+'mature oak broad canopy',clusters,
                           foliage,group,density=1300,size=.22)

        if MAKE_SMALL_PLANTS:
            shaded = material('New left island shaded hedge',(.027,.069,.018),
                              (.07,.125,.03),12,.009)
            # Overlapping tall, leafy shrubs rather than a few small clumps.
            # Leave the street-side sign at its original position and height.
            specs = [(-1.02,-.95,.65,1.65),(-.25,-1.40,.76,1.85),
                     (.55,-1.16,.73,1.95),(1.12,-.53,.62,1.80),
                     (1.15,.30,.62,1.90),(.65,1.10,.75,2.02),
                     (-.10,1.42,.73,1.95),(-.95,.99,.67,1.80),
                     (-1.20,.12,.64,1.72)]
            for i,(dx,dy,r,h) in enumerate(specs):
                x,y = cx+dx,cy+dy
                z = ground_at(x,y)
                clusters = [((x,y,z+h*.54),(r,r*.88,h*.47)),
                            ((x+r*.35,y-.1,z+h*.61),(r*.70,r*.69,h*.33)),
                            ((x-r*.32,y+.16,z+h*.60),(r*.68,r*.72,h*.35))]
                for k,(center,radii) in enumerate(clusters):
                    core('dense shrub %02d shaded interior %d'%(i,k),
                         center,tuple(v*.82 for v in radii),shaded)
                leaf_cloud(label+'dense shrub %02d leaves'%i,clusters,
                           foliage[:4],group,density=650,size=.15)
                branch('shrub woody stem',[(x,y,z),(x+.04,y,z+h*.65)],
                       [.032,.008],7)
            # Low pale-green strap leaves along the mulch/grass transition.
            for i in range(30):
                a = math.tau*i/30
                x = cx+rx*.72*math.cos(a)
                y = cy+ry*.72*math.sin(a)
                ob = strap_plant(label+'low border clump %02d'%i,x,y,
                                 .35+.08*rng.random(),.27,strapmats,26)
                ob.location.z += ground_at(x,y)-BED_Z

        # Collect ONLY newly created objects into the independent addition.
        # Existing tree groups and every original object remain as generated.
        for ob in set(root.all_objects)-prior_objects:
            if col not in list(ob.users_collection):
                col.objects.link(ob)
            for owner in list(ob.users_collection):
                if owner != col:
                    owner.objects.unlink(ob)
        col['Net new'] = True
        col['Mound center meters'] = NEW_LEFT_ISLAND_CENTER
        col['Mound height meters'] = NEW_LEFT_ISLAND_HEIGHT
        col['Reference'] = 'Circled roadside oak and dense hedge; left looking from road toward house'
        col['Existing scene geometry'] = 'Unmodified; additive bank and vegetation only'
    finally:
        rng.setstate(state)


add_left_roadside_oak_island()

# Reference-only metadata travels with the generated collection.
root['Coordinate system'] = 'Meters; same xy() origin as house.py and pool.py; front -Y'
root['Accuracy'] = 'Photo-inspired estimated site, not survey or construction geometry'
root['Site bounds meters'] = SITE_BOUNDS
root['Seed'] = SEED
root['Rear design'] = 'Open lawn retained; no invented rear fence or patio'
root['Ground opening'] = 'Combined fixed house/porch/deck boundary, open below dry pool'
root['Generated object count'] = len(root.all_objects)
print('E4690 environment created: %d objects. House and pool untouched.' % len(root.all_objects))
