"""Use Honor's Solid material swatches in Material Preview and renders.

RUN LAST: house, pool, environment, sign, then this script in Blender's Text Editor.
Rerun this script whenever you regenerate any of those models.

Flat-color mode: lighting, reflections, bumps and procedural color variation
are bypassed. Water becomes an opaque color swatch. The photo stays visible,
and the pool screen retains its procedural transparent weave.
This matches material swatches, NOT Solid's studio-light shadows/highlights.
Solid must use Color > Material for the comparison (not Object or Random).

Original shader nodes are retained. To undo, change MODE to 'RESTORE' and run.
Color management is scene-wide, so Standard also affects non-Honor objects.
Does not save the blend file. Source prepared, not executed in Blender here.
"""

import json
import bpy


MODE = 'APPLY'                  # 'APPLY' or 'RESTORE'
TAGS = ('honor_fh1_generated', 'honor_pool_generated',
        'honor_environment_generated', 'honor_sign_generated')
KEY = 'honor_flat_color_original_output'
NODE_TAG = 'honor_flat_color_node'
SCENE_KEY = 'honor_flat_color_original_display'


def owned(mat):
    return any(mat.get(tag) for tag in TAGS)


def new_node(nodes, kind, name):
    node = nodes.new(kind)
    node.name = name
    node.label = name
    node[NODE_TAG] = True
    return node


def remove_flat_nodes(mat):
    for node in list(mat.node_tree.nodes):
        if node.get(NODE_TAG):
            mat.node_tree.nodes.remove(node)


def restore_material(mat):
    original_name = mat.get(KEY)
    if original_name is None or not mat.use_nodes:
        return
    remove_flat_nodes(mat)
    original = mat.node_tree.nodes.get(original_name)
    if original is not None and original.type == 'OUTPUT_MATERIAL':
        original.is_active_output = True
    del mat[KEY]


if MODE not in ('APPLY', 'RESTORE'):
    raise ValueError("MODE must be 'APPLY' or 'RESTORE'.")

scene = bpy.context.scene
view = scene.view_settings

if MODE == 'RESTORE':
    for mat in bpy.data.materials:
        if owned(mat):
            restore_material(mat)
    saved = scene.get(SCENE_KEY)
    if saved:
        settings = json.loads(saved)
        scene.display_settings.display_device = settings['display_device']
        view.view_transform = settings['view_transform']
        view.look = settings['look']
        view.exposure = settings['exposure']
        view.gamma = settings['gamma']
        view.use_curve_mapping = settings['use_curve_mapping']
        if 'use_white_balance' in settings and hasattr(view, 'use_white_balance'):
            view.use_white_balance = settings['use_white_balance']
        del scene[SCENE_KEY]
    print('Honor: original shaders and saved color management restored.')
else:
    # Save display settings once, before modifying the scene.
    if SCENE_KEY not in scene:
        settings = {
            'display_device': scene.display_settings.display_device,
            'view_transform': view.view_transform,
            'look': view.look,
            'exposure': view.exposure,
            'gamma': view.gamma,
            'use_curve_mapping': view.use_curve_mapping,
        }
        if hasattr(view, 'use_white_balance'):
            settings['use_white_balance'] = view.use_white_balance
        scene[SCENE_KEY] = json.dumps(settings)

    scene.display_settings.display_device = 'sRGB'
    view.view_transform = 'Standard'
    view.look = 'None'
    view.exposure = 0.0
    view.gamma = 1.0
    view.use_curve_mapping = False
    if hasattr(view, 'use_white_balance'):
        view.use_white_balance = False

    count = 0
    for mat in bpy.data.materials:
        if not owned(mat) or not mat.use_nodes:
            continue
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        # On reruns, retrieve the original output, not our flat output.
        original = nodes.get(mat.get(KEY, ''))
        if original is None:
            original = next((node for node in nodes
                             if node.type == 'OUTPUT_MATERIAL'
                             and node.is_active_output and not node.get(NODE_TAG)), None)
        if original is None:
            print('Honor: skipped material without original output: ' + mat.name)
            continue
        mat[KEY] = original.name
        remove_flat_nodes(mat)

        emission = new_node(nodes, 'ShaderNodeEmission', 'Honor | flat swatch')
        # diffuse_color already contains scene-linear values. Do not convert twice.
        emission.inputs['Color'].default_value = tuple(mat.diffuse_color)
        emission.inputs['Strength'].default_value = 1.0
        emission.location = (400, -400)
        surface = emission.outputs[0]

        if mat.name.startswith('Sign | printed photograph'):
            texture = next((node for node in nodes
                            if node.type == 'TEX_IMAGE' and node.image is not None), None)
            if texture is not None:
                links.new(texture.outputs['Color'], emission.inputs['Color'])

        # Keep the screen's original weave mask and transparent branch;
        # replace only its lit dark strands with the viewport color.
        if mat.name.startswith('Pool | fine dark insect/barrier screen'):
            incoming = original.inputs['Surface'].links
            old_mix = incoming[0].from_node if incoming else None
            if old_mix is not None and old_mix.type == 'MIX_SHADER':
                mix = new_node(nodes, 'ShaderNodeMixShader', 'Honor | flat screen weave')
                mix.location = (620, -400)
                if old_mix.inputs[0].is_linked:
                    links.new(old_mix.inputs[0].links[0].from_socket, mix.inputs[0])
                else:
                    mix.inputs[0].default_value = old_mix.inputs[0].default_value
                transparent = new_node(nodes, 'ShaderNodeBsdfTransparent',
                                       'Honor | screen transparency')
                links.new(transparent.outputs[0], mix.inputs[1])
                links.new(emission.outputs[0], mix.inputs[2])
                surface = mix.outputs[0]

        output = new_node(nodes, 'ShaderNodeOutputMaterial', 'Honor | flat output')
        output.location = (850, -400)
        output.target = 'ALL'
        links.new(surface, output.inputs['Surface'])
        output.is_active_output = True
        count += 1

    print('Honor: flat viewport swatches applied to %d materials.' % count)
    print('Photo retained; screen weave retained; water is now opaque.')
    print('Use Material Preview. Set MODE to RESTORE to undo.')
    print('Rerun this companion after regenerating house/pool/environment/sign.')

bpy.context.view_layer.update()
