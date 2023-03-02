#! /bin/bash
PPAFM_DIR='../../ppafm/cmdline'

# ======= STEP 1 : Generate force-field grid
python ${PPAFM_DIR}/generateLJFF.py -i PTCDA.xyz
python ${PPAFM_DIR}/generateElFF_point_charges.py -i PTCDA.xyz --tip s

# ======= STEP 2 : Relax Probe Particle using that force-field grid
python ${PPAFM_DIR}/relaxed_scan.py -k 0.5 -q -0.10

# ======= STEP 3 : Plot the results
python ${PPAFM_DIR}/plot_results.py -k 0.5 -q -0.10 --arange 0.5 2.0 2 --df
