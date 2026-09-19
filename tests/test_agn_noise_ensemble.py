import sys
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from run_agn_noise_ensemble import SEEDS,block_seeds,background_field


def test_frozen_seed_partition():
    assert SEEDS==tuple(range(20261001,20261013))
    assert tuple(s for b in range(4) for s in block_seeds(b))==SEEDS
    assert not set(SEEDS)&{20260903,20260904,20260905}
    with pytest.raises(ValueError):
        block_seeds(4)


def test_noise_reproducibility():
    a=background_field((32,32),SEEDS[0])
    np.testing.assert_array_equal(a,background_field((32,32),SEEDS[0]))
    assert not np.array_equal(a,background_field((32,32),SEEDS[1]))
