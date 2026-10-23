# Project 2: Cache & Memory Performance Profiling

## Requirements
- Linux, Intel x86-64 CPU, sudo access
- gcc, taskset, `perf` (package `linux-tools-$(uname -r)`)
- Intel Memory Latency Checker v3.13 (not included, Intel license): download from
  https://www.intel.com/content/www/us/en/developer/articles/tool/intelr-memory-latency-checker.html
  and extract here so that `./mlc/Linux/mlc` exists
- Python 3 with matplotlib

## Run
```bash
./run.sh                 # asks for sudo (MLC, perf, huge-page switch)
python3 -m venv env && env/bin/pip install matplotlib
env/bin/python analyze.py
```

`run.sh` temporarily switches transparent huge pages to `never` / `always` for the TLB test
and sets it back to `madvise` at the end.

## Files
| File | Contents |
|---|---|
| `simd.c` | AXPY kernel and random pointer chase |
| `run.sh` | Runs every experiment |
| `analyze.py` | Makes `project2.png` |
| `mlc_sweep.txt` | Idle latency vs buffer size (L1 → DRAM) |
| `mlc_pattern.txt`, `mlc_stride.txt` | Idle latency: random vs sequential, strides 64/256/1024 B |
| `mlc_bw_random.txt`, `mlc_bw_stride256.txt`, `mlc_bw_stride1024.txt` | Max bandwidth for the same patterns |
| `mlc_rwmix.txt` | Peak bandwidth by read/write ratio |
| `mlc_loaded*.txt` | Loaded latency vs bandwidth: 100% read, 2:1 (`w2`), 1:1 (`w5`), 100% write (`w6`) |
| `perf_axpy.txt` | AXPY time + perf counters, 1K–16M elements, 3 reps |
| `perf_tlb.txt` | Pointer chase, 4 KB vs huge pages, 3 reps |
| `env.txt` | CPU, memory, kernel, gcc, MLC version, governor, SMT, THP |
| `project2.png` | All six plots; also saved one per file as `fig1_…png` – `fig6_…png` for the report |
| `report.html` | Report; open in a browser (needs the PNGs in this folder) |
