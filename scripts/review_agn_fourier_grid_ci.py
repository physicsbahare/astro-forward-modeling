#!/usr/bin/env python3
"""Reproduce the strict, read-only audit of C5k's actual GitHub artifacts."""
import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys

RUN=33788705952
COMMIT='7ad6e1ca1b6a78dcde83d6cdea9e3c1bc26bd33b'
ARTIFACTS={1:9908021400,4:9908228320}
DIGESTS={1:'bfd9a5b00c957c141fa135d7b03d52334593d2c4ea47887a2964df96508f220c',
         4:'a0946131448dcb86d68112b3ff4dcbc4d500fcb3e70ed63ceaaa460c5017b32c'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--worker',type=int,choices=(1,4))
    a=p.parse_args()
    import audit_agn_fourier_grid as audit
    import numpy as np
    e=audit.experiment.engine
    if a.worker:
        n=a.worker;root=a.root/f'n{n}'
        result=audit.audit(root,n)  # Historical exact assertions remain unchanged.
        assert result['config']['github_run_id']==str(RUN)
        assert result['config']['github_sha']==(root/'commit.txt').read_text().strip()==COMMIT
        assert result['config']['runtime_versions']==result['config']['pins']
        result.update(artifact_id=ARTIFACTS[n],zip_sha256=DIGESTS[n],
            audit_disabled_cpu_features=os.getenv('NPY_DISABLE_CPU_FEATURES',''))
        with contextlib.redirect_stdout(io.StringIO()) as captured:np.show_runtime()
        result['audit_numpy_runtime']=captured.getvalue()
        e.dump(a.output,result);return
    records=[]
    for n in (1,4):
        assert audit.experiment.parent.sha(a.root/f'{ARTIFACTS[n]}.zip')==DIGESTS[n]
        env=os.environ.copy();env.pop('NPY_DISABLE_CPU_FEATURES',None)
        if n==4:env['NPY_DISABLE_CPU_FEATURES']='X86_V4,AVX512_ICL'
        destination=a.root/f'confirmed_audit_n{n}.json'
        subprocess.run([sys.executable,__file__,'--root',str(a.root),'--worker',str(n),
                        '--output',str(destination)],env=env,check=True)
        records.append(e.read(destination))
    result=dict(run_id=RUN,commit=COMMIT,scope='Actual CI artifacts; strict read-only audit',
        github_confirmation=dict(status='completed',conclusion='success',
            updated_at='2026-09-03T18:56:30Z',
            url=f'https://github.com/physicsbahare/astro-forward-modeling/actions/runs/{RUN}',
            jobs=[dict(id=j,status='completed',conclusion='success') for j in (100759718795,100759719068)]),
        coordinate_portability=dict(original_default_n4_exact_audit='failed',
            mismatching_kx_elements=11,total_elements=260,max_absolute_difference=7.105427357601002e-15,
            resolution='Documented NumPy CPU dispatch restriction reproduces the saved coordinates exactly; no assertion or tolerance changed',
            scope='Audit arithmetic only; no CI image, fit, setting or record regenerated',
            source='https://numpy.org/doc/stable/reference/simd/build-options.html#runtime-dispatch'),
        artifacts=records)
    e.dump(a.output,result)
    print([(r['host_n'],r['counts'],len(r['warnings'])) for r in records])


if __name__=='__main__':main()
