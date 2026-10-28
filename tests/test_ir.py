import copy
import importlib.util
import json
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('yan_ir', ROOT / 'Plugins/YanMaterialBridge/Content/Python/yan_ir.py')
ir = importlib.util.module_from_spec(spec); spec.loader.exec_module(ir)
class ValidationTests(unittest.TestCase):
    def setUp(self): self.task = json.loads((ROOT / 'examples/blue_material.json').read_text())
    def test_example(self): ir.validate(self.task)
    def test_path_escape(self):
        self.task['asset_path'] = '/Game/ChatGPT/../Existing'
        with self.assertRaises(ValueError): ir.validate(self.task)
    def test_arbitrary_class(self):
        self.task['nodes'][0]['type'] = 'ExecutePython'
        with self.assertRaises(ValueError): ir.validate(self.task)
    def test_missing_reference(self):
        self.task['outputs']['BaseColor']['node'] = 'missing'
        with self.assertRaises(ValueError): ir.validate(self.task)
    def test_cycle(self):
        self.task['links'] = [{'from':'color','to':'rough'}, {'from':'rough','to':'color'}]
        with self.assertRaises(ValueError): ir.validate(self.task)
    def test_duplicate_pin(self):
        self.task['links'] = [{'from':'color','to':'rough','input':'A'}] * 2
        with self.assertRaises(ValueError): ir.validate(self.task)
if __name__ == '__main__': unittest.main()
