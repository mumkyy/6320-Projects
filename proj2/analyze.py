import matplotlib.pyplot as plt
from matplotlib.transforms import Bbox
import statistics

# Save each subplot of the current figure (with any twin axes) as its own PNG, for the report
def save_panels(names):
  fig = plt.gcf()
  renderer = fig.canvas.get_renderer()
  groups = {}
  for ax in fig.axes:
      groups.setdefault(ax.get_position().bounds, []).append(ax)
  for name, axes in zip(names, groups.values()):
      box = Bbox.union([ax.get_tightbbox(renderer) for ax in axes])
      box = box.transformed(fig.dpi_scale_trans.inverted()).padded(0.1)
      fig.savefig(name, dpi=200, bbox_inches=box)

def mean_by_n(points):
  groups = {}
  for n, t in points:
      groups.setdefault(n, []).append(t)
  sizes = sorted(groups)
  means = [statistics.mean(groups[n]) for n in sizes]
  stds  = [statistics.stdev(groups[n]) for n in sizes]
  return sizes, means, stds

def read(filename):
    with open(filename) as file:
        return file.read().splitlines()      # list of lines

# mlc --loaded_latency output: rows of 3 numbers   delay   latency (ns)   bandwidth (MB/s)
def loaded_rows(filename):
    lats = []
    bws = []
    for r in read(filename):
        parts = r.split()
        if len(parts) == 3 and parts[0].isdigit():
            lats.append(float(parts[1]))
            bws.append(float(parts[2]) / 1000)          # MB/s -> GB/s
    return lats, bws

GHZ = 2.3                                    # i3-6100U clock, for ns -> cycles

plt.figure(figsize=(20, 11))


# ---------------- 1. Latency per level / working-set sweep (MLC) ----------------
# mlc_sweep.txt: "== buffer 128 KiB", then "Each iteration took ... ( 4.8  ns)"
sizes = []
latencies = []
for r in read('mlc_sweep.txt'):
    if r.startswith('=='):
        kb = int(r.split()[2])                          # "== buffer 128 KiB" -> 128
    if 'Each iteration took' in r:
        sizes.append(kb)
        latencies.append(float(r.split('(')[1].split()[0]))

plt.subplot(2, 3, 1)
plt.plot(sizes, latencies, marker="o", color="blue")
plt.xscale("log")
plt.yscale("log")
for size_kb, name in [(32, "L1"), (256, "L2"), (3072, "L3")]:
    plt.axvline(size_kb, linestyle="--", color="purple", linewidth=2)
    bottom, top = plt.ylim()
    plt.text(size_kb * 1.1, top - 0.03 * (top - bottom), name, ha="left", va="top")
plt.gca().secondary_yaxis("right", functions=(lambda ns: ns * GHZ, lambda c: c / GHZ)).set_ylabel("Cycles (2.3 GHz)")
plt.xlabel("Buffer size (KiB)", fontsize=12)
plt.ylabel("Latency (ns)", fontsize=12)
plt.title("1. Idle latency vs working set (random)", fontsize=14, fontweight="bold")


# ---------------- 2. Sequential vs random, stride, pitfall (MLC) ----------------
# mlc_pattern.txt and mlc_stride.txt: "== label", then "Each iteration took ... ( 111.4  ns)"
labels = []
values = []
for filename in ['mlc_pattern.txt', 'mlc_stride.txt']:
    for r in read(filename):
        if r.startswith('=='):
            label = r[2:].strip().replace(", ", "\n")
        if 'Each iteration took' in r:
            labels.append(label)
            values.append(float(r.split('(')[1].split()[0]))

# bandwidth for the same patterns, max load (delay 0 row); same order as labels
# sequential and stride 64 B are the same pattern: delay-0 row of mlc_loaded.txt
bw_files = ['mlc_bw_random.txt', 'mlc_loaded.txt', 'mlc_loaded.txt',
            'mlc_bw_stride256.txt', 'mlc_bw_stride1024.txt']
bws = [loaded_rows(f)[1][0] for f in bw_files]

x = range(len(labels))
plt.subplot(2, 3, 2)
plt.bar([i - 0.2 for i in x], values, width=0.4, color="blue", label="Idle latency")
plt.xticks(x, labels, fontsize=9)
plt.ylabel("Idle latency (ns)", fontsize=12, color="blue")
plt.legend(loc="upper left")
plt.twinx()                                             # bandwidth on the right axis
plt.bar([i + 0.2 for i in x], bws, width=0.4, color="red", label="Max bandwidth")
plt.ylabel("Bandwidth (GB/s)", fontsize=12, color="red")
plt.legend(loc="upper right")
plt.title("2. Access pattern and stride (DRAM)", fontsize=14, fontweight="bold")


# ---------------- 3. Read/write mix (MLC) ----------------
# mlc_rwmix.txt: lines like "3:1 Reads-Writes :   23076.5"  (MB/s)
labels = []
values = []
for r in read('mlc_rwmix.txt'):
    if 'Reads' in r or 'triad' in r:
        name, value = r.rsplit(':', 1)
        labels.append(name.strip())
        values.append(float(value) / 1000)              # MB/s -> GB/s

plt.subplot(2, 3, 3)
plt.bar(labels, values, color="blue")
plt.xticks(fontsize=9, rotation=20)
plt.ylabel("Bandwidth (GB/s)", fontsize=12)
plt.title("3. Peak bandwidth by read/write mix", fontsize=14, fontweight="bold")


# ---------------- 4. Intensity sweep: loaded latency (MLC) ----------------
# mlc_loaded*.txt: rows of 3 numbers   delay   latency (ns)   bandwidth (MB/s)
plt.subplot(2, 3, 4)
for filename, label, color in [('mlc_loaded.txt',    "100% read",        "blue"),
                                ('mlc_loaded_w2.txt', "2:1 read/write",   "orange"),
                                ('mlc_loaded_w5.txt', "1:1 read/write",   "red"),
                                ('mlc_loaded_w6.txt', "100% write (NT)",  "green")]:
    lats, bws = loaded_rows(filename)
    plt.plot(bws, lats, marker="o", color=color, label=label)
plt.xlabel("Bandwidth (GB/s)", fontsize=12)
plt.ylabel("Latency (ns)", fontsize=12)
plt.xscale("log")
plt.title("4. Loaded latency vs bandwidth by R/W mix", fontsize=14, fontweight="bold")
plt.legend()


# ---------------- 5. Cache misses vs runtime: axpy (perf) ----------------
# perf_axpy.txt blocks: "== rep=1 n=1024", then seconds, then "value,,event,..." lines
time_points = []
miss_points = []
for r in read('perf_axpy.txt'):
    if r.startswith('=='):
        n = int(r.split('n=')[1])                       # "== rep=1 n=1024" -> 1024
        trials = 50000000 // n + 2                      # same as run.sh
        kb = 2 * n * 4 / 1024                           # axpy touches x and y: 8 bytes per element
    elif r[:1].isdigit() and ',' not in r:              # seconds per call
        time_points.append((kb, float(r) / n * 1e9))
    elif 'LLC-load-misses' in r:
        miss_points.append((kb, float(r.split(',')[0]) / (n * trials)))

plt.subplot(2, 3, 5)
sizes, means, stds = mean_by_n(time_points)
plt.errorbar(sizes, means, yerr=stds, marker="o", capsize=3, color="blue")
plt.xscale("log")
for size_kb, name in [(32, "L1"), (256, "L2"), (3072, "L3")]:
    plt.axvline(size_kb, linestyle="--", color="purple", linewidth=2)
    bottom, top = plt.ylim()
    plt.text(size_kb * 1.1, top - 0.03 * (top - bottom), name, ha="left", va="top")
plt.xlabel("Working set (KiB)", fontsize=12)
plt.ylabel("Time per element (ns)", fontsize=12, color="blue")
plt.title("5. AXPY time and LLC misses", fontsize=14, fontweight="bold")

plt.twinx()                                             # second y-axis on the right
sizes, means, stds = mean_by_n(miss_points)
plt.errorbar(sizes, means, yerr=stds, marker="s", capsize=3, color="red")
plt.ylabel("LLC misses per element", fontsize=12, color="red")


# ---------------- 6. TLB: 4 KB pages vs huge pages (perf) ----------------
# perf_tlb.txt blocks: "== rep=1 pages=never n=4194304", then seconds, then perf lines
points = []                                             # ((n, pages), ns per access)
for r in read('perf_tlb.txt'):
    if r.startswith('=='):
        pages = r.split('pages=')[1].split()[0]         # "never" or "always"
        n = int(r.split('n=')[1])
    elif r[:1].isdigit() and ',' not in r:
        points.append(((n, pages), float(r) / n * 1e9))

labels = []
values = []
for n in [4194304, 33554432]:
    for pages in ['never', 'always']:
        ns = [t for key, t in points if key == (n, pages)]
        labels.append(f"{n * 4 // 1048576} MB\n{'4 KB pages' if pages == 'never' else 'huge pages'}")
        values.append(statistics.mean(ns))

plt.subplot(2, 3, 6)
plt.bar(labels, values, color=["blue", "green", "blue", "green"])
plt.ylabel("Latency per access (ns)", fontsize=12)
plt.title("6. Random chase: 4 KB vs huge pages", fontsize=14, fontweight="bold")


plt.tight_layout()
plt.savefig("project2.png", dpi=300, bbox_inches="tight")
save_panels(["fig1_working_set.png", "fig2_pattern.png", "fig3_rwmix_bw.png",
             "fig4_loaded_latency.png", "fig5_axpy_misses.png", "fig6_tlb.png"])
plt.show()
