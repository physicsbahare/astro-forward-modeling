#!/usr/bin/env python3
"""Read-only audit for C7 chromatic source-SED mismatch output."""
import argparse, json
from pathlib import Path
import numpy as np

CONTROL_ATOL = 1e-10


def audit(root: Path):
    cfg=json.loads((root/'config.json').read_text())
    summary=json.loads((root/'summary.json').read_text())
    assert cfg==summary['config']
    rows={r['case']:r for r in summary['results']}
    assert set(rows)=={'color_gradient','same_sed_control','achromatic_psf_control'}
    with np.load(root/'arrays.npz') as a:
        assert len(a.files)==12
        for name in rows:
            for key in ('correct','shortcut','global_psf','intrinsic_band'):
                x=a[f'{name}__{key}']
                assert x.shape==(161,161) and np.isfinite(x).all()
            assert abs(a[f'{name}__global_psf'].sum()-1.0) < 1e-12
    for name in ('same_sed_control','achromatic_psf_control'):
        r=rows[name]
        assert r['normalized_l1_difference'] <= CONTROL_ATOL
        assert r['second_moment_relative_difference'] <= CONTROL_ATOL
    cg=rows['color_gradient']
    assert cg['normalized_l1_difference'] > CONTROL_ATOL
    assert abs(cg['disk_effective_psf_sigma']-cg['bulge_effective_psf_sigma']) > 0
    result={'stage':'C7','status':'controls close; source-SED mismatch remains measurable','control_atol':CONTROL_ATOL,'color_gradient_l1':cg['normalized_l1_difference'],'color_gradient_size_bias':cg['second_moment_relative_difference']}
    (root/'audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    return result


def main():
    p=argparse.ArgumentParser(); p.add_argument('--source',type=Path,required=True); a=p.parse_args(); print(audit(a.source))
if __name__=='__main__': main()
