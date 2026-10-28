import json
import os
from pathlib import Path
import time
import traceback
import unreal
from yan_ir import validate, REGISTRY, OUTPUTS
_handle = None
_last = 0

def execute(task):
    validate(task)
    path = task['asset_path']
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        raise ValueError('Asset already exists; use a new asset path')
    folder, name = path.rsplit('/', 1)
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, unreal.Material, unreal.MaterialFactoryNew())
    if material is None: raise RuntimeError('Could not create material')
    try:
        nodes = {}
        for spec in task['nodes']:
            cls = getattr(unreal, REGISTRY[spec['type']][0])
            x, y = spec.get('position', [0, 0])
            node = unreal.MaterialEditingLibrary.create_material_expression(material, cls, x, y)
            if node is None: raise RuntimeError('Node creation failed')
            for key, value in spec.get('properties', {}).items():
                if isinstance(value, list): value = unreal.LinearColor(*value)
                node.set_editor_property(key, value)
            nodes[spec['id']] = node
        for link in task.get('links', []):
            if not unreal.MaterialEditingLibrary.connect_material_expressions(nodes[link['from']], link.get('output', ''), nodes[link['to']], link.get('input', '')):
                raise RuntimeError('Connection rejected: ' + str(link))
        for key, spec in task['outputs'].items():
            if not unreal.MaterialEditingLibrary.connect_material_property(nodes[spec['node']], spec.get('output', ''), getattr(unreal.MaterialProperty, OUTPUTS[key])):
                raise RuntimeError('Material output rejected: ' + key)
        unreal.MaterialEditingLibrary.recompile_material(material)
        if not unreal.EditorAssetLibrary.save_loaded_asset(material): raise RuntimeError('Asset save failed')
        return {'asset_path': path, 'nodes': len(nodes), 'compile_requested': True,
                'shader_validation': 'not_verified', 'saved': True}
    except Exception:
        unreal.EditorAssetLibrary.delete_asset(path)
        raise

def tick(delta):
    global _last
    if time.monotonic() - _last < 1: return
    _last = time.monotonic()
    root = Path(unreal.Paths.project_saved_dir()) / 'YanBridge'
    inbox, reports = root / 'inbox', root / 'reports'
    inbox.mkdir(parents=True, exist_ok=True); reports.mkdir(parents=True, exist_ok=True)
    for file in sorted(inbox.glob('*.json'))[:1]:
        report_file = reports / file.name
        if report_file.exists():
            file.unlink(); continue
        report = {'id': file.stem, 'status': 'failed'}
        try:
            task = json.loads(file.read_text(encoding='utf-8'))
            if task.get('id') != file.stem: raise ValueError('Filename/id mismatch')
            report.update(execute(task)); report['status'] = 'saved'
        except Exception:
            report['error'] = traceback.format_exc()
            unreal.log_error(report['error'])
        tmp = report_file.with_suffix('.tmp')
        tmp.write_text(json.dumps(report, indent=2), encoding='utf-8')
        os.replace(tmp, report_file)
        file.unlink()

def start():
    global _handle
    if _handle is None:
        _handle = unreal.register_slate_post_tick_callback(tick)
        unreal.log('YanBridge ready: Saved/YanBridge/inbox')

def stop():
    global _handle
    if _handle is not None:
        unreal.unregister_slate_post_tick_callback(_handle); _handle = None
