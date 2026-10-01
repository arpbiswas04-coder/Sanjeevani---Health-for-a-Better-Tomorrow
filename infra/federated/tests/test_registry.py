import copy
from pathlib import Path
import unittest
from federated.registry import load, validate


class RegistryTests(unittest.TestCase):
    def test_public_registry_and_cross_region_metadata(self):
        nodes = load(Path(__file__).parents[1]/'configs/regions.json')
        self.assertEqual(len(nodes),3)
        self.assertEqual(nodes['district-a']['country'],'IN')
        value = {'nodes':list(nodes.values())}
        value['nodes'][1]['country']='BD'
        self.assertEqual(validate(value)['district-b']['country'],'BD')
        for bad in ('unknown-data','patient_id'):
            changed=copy.deepcopy(value);changed['nodes'][0][bad]='private'
            with self.assertRaises(ValueError): validate(changed)
        value['nodes'].append(value['nodes'][0])
        with self.assertRaises(ValueError): validate(value)
