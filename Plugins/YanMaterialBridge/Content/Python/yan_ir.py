"""Dependency-free validator. No task-provided Python or class names are executed."""
import re
REGISTRY = {
    'Constant': ('MaterialExpressionConstant', {'r'}),
    'Constant3Vector': ('MaterialExpressionConstant3Vector', {'constant'}),
    'ScalarParameter': ('MaterialExpressionScalarParameter', {'parameter_name', 'default_value'}),
    'VectorParameter': ('MaterialExpressionVectorParameter', {'parameter_name', 'default_value'}),
    'TextureCoordinate': ('MaterialExpressionTextureCoordinate', {'coordinate_index', 'u_tiling', 'v_tiling'}),
    'Time': ('MaterialExpressionTime', set()),
    'Add': ('MaterialExpressionAdd', {'const_a', 'const_b'}),
    'Multiply': ('MaterialExpressionMultiply', {'const_a', 'const_b'}),
    'Lerp': ('MaterialExpressionLinearInterpolate', {'const_a', 'const_b', 'const_alpha'}),
    'Sine': ('MaterialExpressionSine', {'period'}),
    'OneMinus': ('MaterialExpressionOneMinus', set()),
    'Clamp': ('MaterialExpressionClamp', {'min_default', 'max_default'}),
}
OUTPUTS = {'BaseColor': 'MP_BASE_COLOR', 'Roughness': 'MP_ROUGHNESS',
           'Metallic': 'MP_METALLIC', 'EmissiveColor': 'MP_EMISSIVE_COLOR'}
def validate(task):
    if task.get('version') != 1 or task.get('operation') != 'create_material':
        raise ValueError('Expected version 1 create_material')
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', task.get('id', '')):
        raise ValueError('Invalid task id')
    if not re.fullmatch(r'/Game/ChatGPT/(?:[A-Za-z0-9_]+/)*[A-Za-z0-9_]+', task.get('asset_path', '')):
        raise ValueError('asset_path must be under /Game/ChatGPT/')
    nodes = task.get('nodes', [])
    if not isinstance(nodes, list) or not 1 <= len(nodes) <= 128:
        raise ValueError('Expected 1..128 nodes')
    ids = set()
    for n in nodes:
        if not isinstance(n.get('id'), str) or n['id'] in ids:
            raise ValueError('Duplicate or invalid node id')
        ids.add(n['id'])
        if n.get('type') not in REGISTRY:
            raise ValueError('Unsupported node type')
        props = n.get('properties', {})
        if not isinstance(props, dict) or set(props) - REGISTRY[n['type']][1]:
            raise ValueError('Unsupported node property')
        for key, value in props.items():
            if key in ('constant',) or (key == 'default_value' and n['type'] == 'VectorParameter'):
                if not isinstance(value, list) or len(value) != 4 or any(type(x) not in (int, float) for x in value):
                    raise ValueError('Color requires four numbers')
            elif key == 'parameter_name':
                if not isinstance(value, str) or not value: raise ValueError('Invalid parameter name')
            elif type(value) not in (int, float): raise ValueError('Expected numeric property')
        pos = n.get('position', [0, 0])
        if not isinstance(pos, list) or len(pos) != 2 or any(type(x) is not int for x in pos):
            raise ValueError('Expected integer node position')
    links = task.get('links', [])
    if not isinstance(links, list) or len(links) > 512: raise ValueError('Too many links')
    edges = {i: [] for i in ids}
    inputs = set()
    for link in links:
        if link['from'] not in ids or link['to'] not in ids: raise ValueError('Unknown node reference')
        pin = (link['to'], link.get('input', ''))
        if pin in inputs: raise ValueError('Duplicate destination pin')
        inputs.add(pin)
        edges[link['from']].append(link['to'])
    visiting, done = set(), set()
    def visit(i):
        if i in visiting: raise ValueError('Graph contains cycle')
        if i in done: return
        visiting.add(i)
        for j in edges[i]: visit(j)
        visiting.remove(i); done.add(i)
    for i in ids: visit(i)
    outputs = task.get('outputs', {})
    if not outputs or set(outputs) - OUTPUTS.keys(): raise ValueError('Unsupported material output')
    for output in outputs.values():
        if output['node'] not in ids: raise ValueError('Unknown output node')
    return task
