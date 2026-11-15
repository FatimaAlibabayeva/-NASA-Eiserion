import unittest
from datetime import date
from seed import examples
from engine import calculate

class EngineTests(unittest.TestCase):
    def test_low_intake_reduces_workout(self):
        s=examples().scenarios[0]; d=date.today()
        balanced=calculate(s,d)
        s.days[d].nutrition.calories=800
        self.assertLess(calculate(s,d)['workout']['duration'], balanced['workout']['duration'])
    def test_workload_increases_nutrition(self):
        s=examples().scenarios[0]; d=date.today(); a=calculate(s,d)
        s.days[d].exercise.duration=100
        b=calculate(s,d)
        self.assertGreater(b['nutrition_plan']['calories'],a['nutrition_plan']['calories'])
        self.assertGreater(b['nutrition_plan']['carbs'],a['nutrition_plan']['carbs'])
    def test_missing_not_zero(self):
        s=examples().scenarios[0]; d=date.today()
        s.days[d].nutrition.protein=None
        self.assertIn('protein',calculate(s,d)['missing'])
        s.days[d].nutrition.protein=0
        self.assertNotIn('protein',calculate(s,d)['missing'])
        self.assertIn('protein',calculate(s,d)['below'])
    def test_incomplete_and_recovery(self):
        s=examples().scenarios[0]; d=date.today()
        s.days[d].exercise.status='not completed'
        self.assertEqual(calculate(s,d)['workload'],0)
        s.profile.recovery=2
        self.assertEqual(calculate(s,d)['workout']['type'],'mobility')
    def test_qus_quality_and_location(self):
        s=examples().scenarios[0]; d=date.today()
        self.assertIsNotNone(calculate(s,d)['qus']['delta'])
        s.qus[-1].quality='poor'
        self.assertIsNone(calculate(s,d)['qus']['delta'])
        s.qus[-1].quality='good'; s.qus[-1].location='Right heel'
        self.assertIsNone(calculate(s,d)['qus']['delta'])

if __name__ == '__main__': unittest.main()
