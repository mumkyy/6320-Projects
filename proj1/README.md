# Project 1: SIMD Advantage Profiling

## Requirements
- Linux, x86-64 CPU with AVX2/FMA
- gcc, taskset, objdump
- Python 3 with matplotlib

## Run
```bash
./run.sh                 # builds scalar/auto/native, runs all experiments
python3 -m venv env && env/bin/pip install matplotlib
env/bin/python analyze.py
```

`run.sh` pins every run to core 2 (`taskset -c 2`) and repeats each setting 3 times.

## Files
| File | Contents |
|---|---|
| `simd.c` | Kernels (AXPY, dot, multiply; float/double), peak-FLOP test, correctness check |
| `run.sh` | Builds the 3 versions and runs every experiment |
| `analyze.py` | Makes all plots from the CSVs |
| `sweep.csv` | All kernels × builds × sizes 1K–16M |
| `align.csv`, `tail.csv`, `stride.csv` | Alignment, tail and stride studies (AXPY float) |
| `peak.csv` | Register-only FMA loop for peak GFLOP/s |
| `correctness.txt` | Results of every kernel in every build, n = 4103 |
| `verify.txt` | Compiler vectorization report and key disassembly |
| `env.txt` | CPU, kernel, gcc, governor, SMT state, per-core cache sizes |
| `kernels.png`, `speedup.png`, `gflops.png`, `access.png` | Plots (also split per panel for the report: `speedup_*.png`, `align.png`, `tail.png`, `stride.png`) |
| `roofline.png` | Roofline for AXPY float from measured peak and bandwidth |
| `report.html` | Report; open in a browser (needs the PNGs in this folder) |
