"""4690 — pool, deck, and photo-inspired raised spillover spa.
Run in Blender's Scripting workspace after house.py (or independently).
Uses exactly the house.py scale/origin: meters, front = negative world Y.
Only objects in P4690 are replaced on rerun; H4690 remains untouched.
No cameras, lighting, world changes, render settings, or automatic saves.

Pool outline traced from the supplied 1440px floorplan. Approximately
30 ft long by 14.3 ft wide, consistent with pool_dimensions.md estimates.
Depths, steps, spa dimensions and finishes are visual estimates, NOT survey
or construction dimensions. The raised spa is inferred from photographs;
its partition/location is not explicitly identified on the floorplan.
No screen enclosure, landscaping, furniture, equipment, or safety fencing.
The deck stops at the existing covered-lanai edge; no duplicate lanai slab.
Water appearance depends on the scene's existing lighting/render engine.
"""
import math
import bpy
import bmesh
from mathutils import Vector

# -------------------------- editable settings --------------------------
SCALE = 13.0 * 0.3048 / 207.0
PREFIX = 'P4690'
DECK_Z = .025
WATER_Z = -.13
SHALLOW_DEPTH = .95       # Below water, at the pool-bath end.
DEEP_DEPTH = 1.65         # Below water, at the master-suite end.
COPING_WIDTH = .28
MAKE_SPA = True
SPA_RIM_Z = .39
SPA_WATER_Z = .29

# Clockwise in image space, starting at the short topmost horizontal edge.
POOL = [(715,119),(810,119),(840,147),(1128,147),(1163,179),
        (1163,313),(1128,347),(929,347),(909,328),(746,328),
        (714,297),(714,250),(684,221),(684,147)]
# Deck follows the rear house setbacks, ending at the lanai's y=410 edge.
DECK = [(446,84),(1257,84),(1257,410),(607,410),(607,188),(446,188)]
SPA = [(715,119),(810,119),(838,147),(838,201),
       (810,228),(714,228),(684,201),(684,147)]


def xy(p):
    return Vector(((p[0]-710)*SCALE,(1080-p[1])*SCALE))


def world(points):
    return [xy(p) for p in points]


# Never clear unrelated scene objects or the generated house collection.
if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
old = bpy.data.collections.get(PREFIX)
if old:
    for obj in list(old.all_objects):
        bpy.data.objects.remove(obj,do_unlink=True)
    bpy.data.collections.remove(old)
root = bpy.data.collections.new(PREFIX)
bpy.context.scene.collection.children.link(root)


def material(name,color,roughness=.5,noise=0):
    mat = bpy.data.materials.get(PREFIX+'_'+name)
    if mat is None:
        mat = bpy.data.materials.new(PREFIX+'_'+name)
    mat.diffuse_color = (*color,1)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    shader = nodes.new('ShaderNodeBsdfPrincipled')
    shader.inputs['Base Color'].default_value = (*color,1)
    shader.inputs['Roughness'].default_value = roughness
    mat.node_tree.links.new(shader.outputs['BSDF'],output.inputs['Surface'])
    if noise:
        tex = nodes.new('ShaderNodeTexNoise')
        tex.inputs['Scale'].default_value = 75
        bump = nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = .22
        bump.inputs['Distance'].default_value = noise
        mat.node_tree.links.new(tex.outputs['Fac'],bump.inputs['Height'])
        mat.node_tree.links.new(bump.outputs['Normal'],shader.inputs['Normal'])
    return mat


deckmat = material('Warm pale textured deck',(.83,.81,.70),.75,.012)
coping = material('Ivory coping',(.91,.89,.79),.55,.004)
plaster = material('Pale aqua pool plaster',(.49,.74,.71),.55,.003)
grout = material('Blue gray grout',(.39,.57,.61),.65)
tiles = [material('Blue ceramic tile %02d' % i,color,.24) for i,color in enumerate([
    (.025,.18,.31),(.035,.26,.43),(.06,.34,.49),(.08,.29,.40)])]
water = material('Pool water',(.80,.96,.98),.075)
shader = water.node_tree.nodes.get('Principled BSDF')
shader.inputs['Transmission Weight'].default_value = 1
shader.inputs['IOR'].default_value = 1.333
absorption = water.node_tree.nodes.new('ShaderNodeVolumeAbsorption')
absorption.inputs['Color'].default_value = (.28,.78,.76,1)
absorption.inputs['Density'].default_value = .10
output = water.node_tree.nodes.get('Material Output')
water.node_tree.links.new(absorption.outputs['Volume'],output.inputs['Volume'])
ripple = water.node_tree.nodes.new('ShaderNodeTexNoise')
ripple.inputs['Scale'].default_value = 5.5
ripple.inputs['Detail'].default_value = 2
bump = water.node_tree.nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value = .14
bump.inputs['Distance'].default_value = .018
water.node_tree.links.new(ripple.outputs['Fac'],bump.inputs['Height'])
water.node_tree.links.new(bump.outputs['Normal'],shader.inputs['Normal'])


def mesh(name,verts,faces,mat):
    data = bpy.data.meshes.new(PREFIX+'_'+name)
    data.from_pydata(verts,[],faces)
    data.update()
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(data)
    bm.free()
    obj = bpy.data.objects.new(PREFIX+'_'+name,data)
    root.objects.link(obj)
    if mat:
        data.materials.append(mat)
    return obj


def prism(name,poly,bottom,top,mat):
    n = len(poly)
    verts = [(p.x,p.y,bottom) for p in poly]+[(p.x,p.y,top) for p in poly]
    faces = [tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,verts,faces,mat)


def difference(obj,cutter):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    mod = obj.modifiers.new('Pool opening','BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.solver = 'EXACT'
    mod.object = cutter
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter,do_unlink=True)


def offset(poly,distance):
    # Mitered parallel offset, including the pool's concave shoulder corners.
    area = sum(p.x*poly[(i+1)%len(poly)].y-poly[(i+1)%len(poly)].x*p.y
               for i,p in enumerate(poly))
    sign = 1 if area > 0 else -1
    result = []
    for i,p in enumerate(poly):
        before = (p-poly[i-1]).normalized()
        after = (poly[(i+1)%len(poly)]-p).normalized()
        n0 = Vector((before.y,-before.x))*sign
        n1 = Vector((after.y,-after.x))*sign
        bisector = n0+n1
        denominator = bisector.dot(n1)
        result.append(p+bisector*(distance/denominator))
    return result


def ring(name,inner,outer,bottom,top,mat):
    n = len(inner)
    verts = [(p.x,p.y,z) for z in (bottom,top) for loop in (inner,outer) for p in loop]
    faces = []
    for i in range(n):
        j = (i+1)%n
        faces += [(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),
                  (i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)]
    return mesh(name,verts,faces,mat)


pool = world(POOL)
spa = world(SPA)
min_x,max_x = min(p.x for p in pool),max(p.x for p in pool)


def floor_z(p):
    t = max(0,min(1,(p.x-min_x)/(max_x-min_x)))
    return WATER_Z-SHALLOW_DEPTH-(DEEP_DEPTH-SHALLOW_DEPTH)*t


# Deck has a genuine hole: no slab or fake blue plane across the basin.
deck = prism('Surrounding pool deck',world(DECK),-.18,DECK_Z,deckmat)
difference(deck,prism('Temporary pool void',pool,-3,1,None))
ring('Continuous pale pool coping',pool,offset(pool,COPING_WIDTH),
     DECK_Z-.025,DECK_Z+.015,coping)

# Closed basin shell with real depth and a gently sloping floor.
outer = offset(pool,.18)
n = len(pool)
verts = ([(p.x,p.y,floor_z(p)) for p in pool]+
         [(p.x,p.y,DECK_Z) for p in pool]+
         [(p.x,p.y,DECK_Z) for p in outer]+
         [(p.x,p.y,floor_z(p)-.18) for p in outer])
faces = [tuple(range(n)),tuple(reversed(range(3*n,4*n)))]
for i in range(n):
    j = (i+1)%n
    faces += [(i,j,n+j,n+i),(n+i,n+j,2*n+j,2*n+i),
              (2*n+i,2*n+j,3*n+j,3*n+i)]
mesh('Sloping plaster basin',verts,faces,plaster)

# Closed water volume, inset from the plaster to avoid coincident surfaces.
water_poly = offset(pool,-.008)
verts = ([(p.x,p.y,floor_z(p)+.01) for p in water_poly]+
         [(p.x,p.y,WATER_Z) for p in water_poly])
faces = [tuple(reversed(range(n))),tuple(range(n,2*n))]
faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
pool_water = mesh('Pool water volume',verts,faces,water)


def tile_band(name,poly,z0,z1,inward=True):
    # Individual small ceramic rectangles with visible grout gaps.
    surface = offset(poly,-.008 if inward else .008)
    verts,faces,indices = [],[],[]
    rows = max(1,round((z1-z0)/.10))
    for edge,a in enumerate(surface):
        b = surface[(edge+1)%len(surface)]
        count = max(1,math.ceil((b-a).length/.10))
        for col in range(count):
            p0 = a+(b-a)*((col+.025)/count)
            p1 = a+(b-a)*((col+.975)/count)
            for row in range(rows):
                low = z0+(z1-z0)*(row+.025)/rows
                high = z0+(z1-z0)*(row+.975)/rows
                k = len(verts)
                verts += [(p0.x,p0.y,low),(p1.x,p1.y,low),
                          (p1.x,p1.y,high),(p0.x,p0.y,high)]
                faces.append((k,k+1,k+2,k+3))
                indices.append((edge*7+col*3+row)%len(tiles))
    obj = mesh(name,verts,faces,None)
    for mat in tiles:
        obj.data.materials.append(mat)
    for polygon,index in zip(obj.data.polygons,indices):
        polygon.material_index = index


ring('Waterline grout backing',offset(pool,-.005),pool,-.25,DECK_Z,grout)
tile_band('Blue waterline ceramic tiles',pool,-.25,DECK_Z)

# Three broad entry treads traced at the lower-left corner of the plan.
# Nested solids put the shortest tread highest and the broadest deepest.
step_specs = [
    ([(714,280),(789,280),(840,328),(746,328),(714,297)],-.83),
    ([(714,296),(783,296),(816,328),(746,328),(714,297)],-.57),
    ([(730,312),(782,312),(794,328),(746,328)],-.31),
]
for i,(points,z) in enumerate(step_specs):
    step = prism('Entry step %d' % (3-i),world(points),-1.45,z,plaster)
    difference(pool_water,prism('Step water exclusion',world(points),-2,z+.001,None))
    # Small blue diamond accents on each visible tread.
    a,b = xy(points[0]),xy(points[1])
    for t in (.30,.65):
        p = a+(b-a)*t+Vector((0,-.10))
        s = .045
        mesh('Step tile diamond',[(p.x-s,p.y,z+.003),(p.x,p.y+s,z+.003),
                                  (p.x+s,p.y,z+.003),(p.x,p.y-s,z+.003)],
             [(0,1,2,3)],tiles[1])

# Submerged bench across the clipped corner at the opposite end.
bench = world([(1094,346),(1162,280),(1162,312),(1128,346)])
prism('Deep end corner bench',bench,-1.95,-.58,plaster)
difference(pool_water,prism('Bench water exclusion',bench,-3,-.579,None))

if MAKE_SPA:
    # Raised octagonal spa occupies the upper-left projection. Its wall
    # partitions the main pool; the remaining basin retains the plan outline.
    inner = offset(spa,-.22)
    spa_wall = ring('Raised spa tiled shell',inner,spa,-1.45,SPA_RIM_Z,grout)
    prism('Spa plaster floor',inner,-1.45,-.73,plaster)
    # Remove all pool water under the raised spa, including its interior.
    difference(pool_water,prism('Spa water exclusion',offset(spa,.004),-3,1,None))
    # Spillway on the spa's pool-facing short end, aimed toward positive X.
    sx,sy = xy((838,174))
    spill = [Vector((sx-.30,sy-.22)),Vector((sx+.10,sy-.22)),
             Vector((sx+.10,sy+.22)),Vector((sx-.30,sy+.22))]
    difference(spa_wall,prism('Spillway notch',spill,.25,.8,None))
    cap = ring('Spa pale rim',offset(inner,-.035),offset(spa,.035),
               SPA_RIM_Z,SPA_RIM_Z+.055,coping)
    difference(cap,prism('Rim spillway notch',spill,.25,.8,None))
    # Tile face strips are also cut at the spillway, not left over the opening.
    tile_band('Spa outer blue tiles',spa,DECK_Z,SPA_RIM_Z,False)
    tile_band('Spa inner blue tiles',inner,-.24,SPA_RIM_Z)
    for suffix in ('Spa outer blue tiles','Spa inner blue tiles'):
        obj = bpy.data.objects.get(PREFIX+'_'+suffix)
        # The notch crosses only the outer face's middle edge; remove tiles
        # by their centers to avoid boolean operations on open tile sheets.
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        remove = [f for f in bm.faces if
                  sx-.31 < f.calc_center_median().x < sx+.11 and
                  sy-.23 < f.calc_center_median().y < sy+.23 and
                  f.calc_center_median().z > .25]
        bmesh.ops.delete(bm,geom=remove,context='FACES')
        bm.to_mesh(obj.data)
        bm.free()
    # Seat ring inside the spa, with a deeper central footwell.
    seat_inner = offset(inner,-.30)
    ring('Spa submerged seating',seat_inner,inner,-.73,-.21,plaster)
    spa_water = prism('Spa water volume',offset(inner,-.006),-.72,SPA_WATER_Z,water)
    seat_cut = ring('Spa seat water exclusion',seat_inner,inner,-1,-.209,None)
    difference(spa_water,seat_cut)
    # Thin, gently leaning sheet joining the raised spa to pool water.
    prism('Spillway water lip',spill,.267,.29,water)
    sheet = [Vector((sx+.04,sy-.21)),Vector((sx+.065,sy-.21)),
             Vector((sx+.065,sy+.21)),Vector((sx+.04,sy+.21))]
    prism('Spa spillover water sheet',sheet,WATER_Z,.29,water)

# All geometry is contained in P4690 and uses the house's original origin.
print('P4690 pool created: approximately 30 x 14.3 ft; H4690 unchanged.')
