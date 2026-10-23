# Project 3: SSD Performance Profiling

## Requirements
- Linux, fio with libaio
- About 17 GB free on the SSD under test
- Python 3 with matplotlib

## Run
```bash
./run.sh                 # creates ./testfile (16 GB) and runs every fio job into json/
python3 -m venv env && env/bin/pip install matplotlib
env/bin/python analyze.py
rm testfile              # delete the test file when done
```

All tests run on a 16 GB file (`testfile`) in this folder, never on the raw device, so no
existing data is touched. Run from a folder on the SSD you want to measure.
Every fio job except the buffered pitfall uses direct I/O (`--direct=1`). Every job except
the preconditioning fill and the 10-minute write runs 3 times.

## Files
| File | Contents |
|---|---|
| `run.sh` | All fio commands (the configs are the command lines) |
| `analyze.py` | Makes `project3.png` |
| `json/fill.json` | Preconditioning write of the whole file |
| `json/qd1_*` | QD=1 baselines: 4K random and 128K sequential, read and write |
| `json/bs_*` | Block-size sweep 4K–256K, random and sequential read, QD=32 |
| `json/mix_*` | 4K random, QD=32, 100/70/50/0 % reads |
| `json/qd_*` | 4K random read, QD 1–256 |
| `json/long.json`, `json/long_bw.1.log` | 10-minute sequential write, bandwidth per second |
| `json/buffered_*` | Buffered (page-cache) reads, the pitfall case |
| `env.txt` | Drive model, filesystem, scheduler, fio version, kernel, CPU, memory |
| `project3.png` | All six plots; also saved one per file as `fig1_…png` – `fig6_…png` for the report |
| `report.html` | Report; open in a browser (needs the PNGs in this folder) |
