#!/usr/bin/env python3
"""C5n: separately frozen 8/10 experiment; preserve incomplete C5m8/16."""
from contextlib import contextmanager
from pathlib import Path
import run_agn_imfit_refinement as m

PROTOCOL=m.h.ROOT/'benchmarks/zhuang_shen_2024/C5N_PROTOCOL.md'


def fft_allocation_bytes(s):
    p=824*s+3
    return 3*p*p*8+3*p*(p//2+1)*16


@contextmanager
def experiment_scope():
    samples,protocol,config,filename=m.SAMPLES,m.PROTOCOL,m.configuration,m.__file__
    def configuration(n):
        result=config(n)
        result.update(stage='C5n resource-bounded Imfit sampling refinement',
            reused_adapter_sha256=m.h.sha(Path(filename)),
            failed_local_predecessor='C5m8/16; not dispatched, not passed',
            fft_allocation_bytes={str(s):fft_allocation_bytes(s) for s in (8,10,16)})
        return result
    try:
        m.SAMPLES=(8,10);m.PROTOCOL=PROTOCOL;m.configuration=configuration;m.__file__=__file__
        yield
    finally:m.SAMPLES,m.PROTOCOL,m.configuration,m.__file__=samples,protocol,config,filename


if __name__=='__main__':
    with experiment_scope():m.main()
