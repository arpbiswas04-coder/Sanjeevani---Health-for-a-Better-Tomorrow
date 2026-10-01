import copy
import json
from pathlib import Path
import unittest
from optimization.common.validation import ValidationError
from optimization.simulation.resilience import assess_resilience


class ResilienceTests(unittest.TestCase):
    def test_weighted_shortage_and_missing_weights(self):
        baseline = json.loads((Path(__file__).parents[1]/'simulation/comparison-example.json').read_text())['baseline']
        data = {'baseline': baseline, 'baseline_periods':[{'day':0,'demand':1500}],
                'scenarios':[{'scenario_id':'served','periods':[{'day':0,'demand':1500}]},
                             {'scenario_id':'shortage','periods':[{'day':0,'demand':3000}]}]}
        policy = {'version':'demo-v1','scenario_weights':{'served':1,'shortage':1}}
        self.assertEqual(assess_resilience(data, policy)['score_0_to_100'],75)
        with self.assertRaises(ValidationError): assess_resilience(data, {**policy,'scenario_weights':{'served':1}})
        data['scenarios'][0]['periods'][0]['demand']=0
        self.assertIsNone(assess_resilience(data, policy)['score_0_to_100'])
