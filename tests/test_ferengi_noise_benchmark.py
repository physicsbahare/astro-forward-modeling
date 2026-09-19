"""Regression test for the stochastic FERENGI target-detector extension."""

import numpy as np

from verification.ferengi_noise_benchmark import run_ferengi_noise_benchmark


def test_ferengi_noise_step_matches_target_detector_statistics():
    result = run_ferengi_noise_benchmark(realizations=600)

    assert result.target_pixels > 50
    assert result.source_total_mean_relative_bias < 0.003
    assert result.total_image_mean_relative_bias < 0.004

    # Sampling uncertainty of a variance estimate from 600 realizations is of
    # order sqrt(2/(N-1)) ~= 5.8%, so 15% is a broad regression bound rather
    # than a production tolerance.
    assert result.total_image_variance_relative_error < 0.15
    assert abs(result.center_source_variance_over_mean - 1.0) < 0.15

    # Shot noise is drawn independently per final detector pixel, and the
    # synthetic target background is also independent pixel-to-pixel here.
    assert np.isfinite(result.center_neighbor_source_correlation)
    assert abs(result.center_neighbor_source_correlation) < 0.12
    assert np.isfinite(result.center_neighbor_background_correlation)
    assert abs(result.center_neighbor_background_correlation) < 0.12
