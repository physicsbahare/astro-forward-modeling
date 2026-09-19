#!/usr/bin/env python3
"""Run unchanged refinement algebra audit under the separate C5n protocol."""
from run_agn_imfit_bounded import experiment_scope
from audit_agn_imfit_refinement import main

if __name__=='__main__':
    with experiment_scope():main()
