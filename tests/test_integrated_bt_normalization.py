import sys
from pathlib import Path
import numpy as np
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from integrated_bt_normalization import integrated_component_amplitudes

class IntegratedBTTests(unittest.TestCase):
    def test_integrated_bt_survives_unequal_stamp_losses(self):
        total = np.array([7., 31.])
        amplitude = integrated_component_amplitudes(total, .63)
        integrated = amplitude * total
        self.assertAlmostEqual(integrated[1] / integrated.sum(), .63)
        finite = total * [.99, .70]
        old = np.array([.37, .63]) / finite * total
        self.assertGreater(abs(old[1] / old.sum() - .63), .05)

    def test_invalid_truth_is_explicit(self):
        for total, bt in [([0,1],.3),([1,np.nan],.3),([1,2],1.1),([1,2],np.nan),([1],.3)]:
            with self.subTest(total=total,bt=bt), self.assertRaises(ValueError):
                integrated_component_amplitudes(total, bt)

if __name__ == '__main__': unittest.main()
