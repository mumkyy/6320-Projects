import matplotlib.pyplot as plt
from matplotlib.transforms import Bbox
import csv
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

scalar_fl_axpy = []
auto_fl_axpy = []
native_fl_axpy = []

scalar_db_axpy = []
auto_db_axpy = []
native_db_axpy = []

scalar_fl_dp = []
auto_fl_dp = []
native_fl_dp = []

scalar_db_dp = []
auto_db_dp = []
native_db_dp = []

scalar_fl_em = []
auto_fl_em = []
native_fl_em = []

scalar_db_em = []
auto_db_em = []
native_db_em = []

with open('sweep.csv', mode='r', encoding='utf-8') as file:
  reader = csv.reader(file)
  
  # Optional: Skip the header row
  header = next(reader) 
  
  for row in reader:
    if row[0] == 'scalar':
      if row[1] == '0':
        scalar_fl_axpy.append((int(row[2]),float(row[3]) * 1e9 / int(row[2])))
      if row[1] == '1':
        scalar_db_axpy.append((int(row[2]),float(row[3]) * 1e9 / int(row[2])))
      if row[1] == '2':
        scalar_fl_dp.append((int(row[2]),float(row[3]) * 1e9  / int(row[2])))
      if row[1] == '3':
        scalar_db_dp.append((int(row[2]),float(row[3]) * 1e9  / int(row[2])))
      if row[1] == '4':
        scalar_fl_em.append((int(row[2]),float(row[3]) * 1e9  / int(row[2])))
      if row[1] == '5':
        scalar_db_em.append((int(row[2]),float(row[3]) * 1e9  / int(row[2])))
    if row[0] == 'auto':
      if row[1] == '0':
        auto_fl_axpy.append((int(row[2]),float(row[3]) * 1e9  / int(row[2])))
      if row[1] == '1':
        auto_db_axpy.append((int(row[2]),float(row[3]) * 1e9  / int(row[2])))
      if row[1] == '2':
        auto_fl_dp.append((int(row[2]),float(row[3]) * 1e9  / int(row[2])))
      if row[1] == '3':
        auto_db_dp.append((int(row[2]),float(row[3]) * 1e9  / int(row[2])))
      if row[1] == '4':
        auto_fl_em.append((int(row[2]),float(row[3]) * 1e9  / int(row[2])))
      if row[1] == '5':
        auto_db_em.append((int(row[2]),float(row[3]) * 1e9  / int(row[2])))
    if row[0] == 'native':
      if row[1] == '0':
        native_fl_axpy.append((int(row[2]),float(row[3]) * 1e9  / int(row[2])))
      if row[1] == '1':
        native_db_axpy.append((int(row[2]),float(row[3]) * 1e9  / int(row[2])))
      if row[1] == '2':
        native_fl_dp.append((int(row[2]),float(row[3]) * 1e9  / int(row[2])))
      if row[1] == '3':
        native_db_dp.append((int(row[2]),float(row[3]) * 1e9  / int(row[2])))
      if row[1] == '4':
        native_fl_em.append((int(row[2]),float(row[3]) * 1e9  / int(row[2])))
      if row[1] == '5':
        native_db_em.append((int(row[2]),float(row[3]) * 1e9  / int(row[2])))

# One entry per subplot: (title, scalar list, auto list, native list, bytes per element)
panels = [
    # top row: float
    ("AXPY float",  scalar_fl_axpy, auto_fl_axpy, native_fl_axpy, 8),
    ("Dot float",   scalar_fl_dp,   auto_fl_dp,   native_fl_dp,   8),
    ("Mul float",   scalar_fl_em,   auto_fl_em,   native_fl_em,   12),
    # bottom row: double
    ("AXPY double", scalar_db_axpy, auto_db_axpy, native_db_axpy, 16),
    ("Dot double",  scalar_db_dp,   auto_db_dp,   native_db_dp,   16),
    ("Mul double",  scalar_db_em,   auto_db_em,   native_db_em,   24),
]
plt.figure(figsize=(18, 10))

for i, (title, scalar, auto, native, bytes_per_elem) in enumerate(panels):
    plt.subplot(2, 3, i + 1)          # 2 rows, 3 columns, subplot number 1-6

    sizes, means, stds = mean_by_n(scalar)
    plt.errorbar(sizes, means, yerr=stds, marker="o", capsize=3, color="blue", label="Scalar")

    sizes, means, stds = mean_by_n(auto)
    plt.errorbar(sizes, means, yerr=stds, marker="o", capsize=3, color="red", label="Auto-Vectorized")

    sizes, means, stds = mean_by_n(native)
    plt.errorbar(sizes, means, yerr=stds, marker="o", capsize=3, color="green", label="Native")

    for size_bytes, name in [(32*1024, "L1"), (256*1024, "L2"), (3*1024*1024, "L3")]:
        n_boundary = size_bytes / bytes_per_elem
        plt.axvline(n_boundary, linestyle="--", color="purple", linewidth=2)
        bottom, top = plt.ylim()
        plt.text(n_boundary * 1.4, top - 0.03 * (top - bottom), name, ha="center", va="top")

    plt.xscale("log")
    plt.xlabel("Problem Size (N)", fontsize=12)
    plt.ylabel("Time per element (ns)", fontsize=12)
    plt.title(title, fontsize=14, fontweight="bold")
    plt.legend()

plt.tight_layout()          # stops the subplots from overlapping
plt.savefig("kernels.png", dpi=300, bbox_inches="tight")

# ---------------- Speedup: native and auto vs scalar ----------------
plt.figure(figsize=(18, 10))

for i, (title, scalar, auto, native, bytes_per_elem) in enumerate(panels):
    plt.subplot(2, 3, i + 1)

    sizes, sc_means, _ = mean_by_n(scalar)
    for vec, label, color in [(auto, "Auto-Vectorized", "red"), (native, "Native", "green")]:
        sizes, vec_means, _ = mean_by_n(vec)
        speedup = [s / v for s, v in zip(sc_means, vec_means)]
        plt.plot(sizes, speedup, marker="o", color=color, label=label)

    plt.axhline(1, color="black", linewidth=1)          # 1x = no speedup

    for size_bytes, name in [(32*1024, "L1"), (256*1024, "L2"), (3*1024*1024, "L3")]:
        n_boundary = size_bytes / bytes_per_elem
        plt.axvline(n_boundary, linestyle="--", color="purple", linewidth=2)
        bottom, top = plt.ylim()
        plt.text(n_boundary * 1.4, top - 0.03 * (top - bottom), name, ha="center", va="top")

    plt.xscale("log")
    plt.xlabel("Problem Size (N)", fontsize=12)
    plt.ylabel("Speedup over scalar (x)", fontsize=12)
    plt.title(title + " speedup", fontsize=14, fontweight="bold")
    plt.legend()

plt.tight_layout()
plt.savefig("speedup.png", dpi=300, bbox_inches="tight")
save_panels(["speedup_axpy_f32.png", "speedup_dot_f32.png", "speedup_mul_f32.png",
             "speedup_axpy_f64.png", "speedup_dot_f64.png", "speedup_mul_f64.png"])

# ---------------- Throughput: GFLOP/s ----------------
# GFLOP/s = FLOPs per element / ns per element
gflop_panels = [
    # (title, scalar, auto, native, bytes per element, FLOPs per element)
    ("AXPY float",  scalar_fl_axpy, auto_fl_axpy, native_fl_axpy, 8,  2),
    ("Dot float",   scalar_fl_dp,   auto_fl_dp,   native_fl_dp,   8,  2),
    ("Mul float",   scalar_fl_em,   auto_fl_em,   native_fl_em,   12, 1),
    ("AXPY double", scalar_db_axpy, auto_db_axpy, native_db_axpy, 16, 2),
    ("Dot double",  scalar_db_dp,   auto_db_dp,   native_db_dp,   16, 2),
    ("Mul double",  scalar_db_em,   auto_db_em,   native_db_em,   24, 1),
]

plt.figure(figsize=(18, 10))

for i, (title, scalar, auto, native, bytes_per_elem, flops) in enumerate(gflop_panels):
    plt.subplot(2, 3, i + 1)

    for data, label, color in [(scalar, "Scalar", "blue"), (auto, "Auto-Vectorized", "red"), (native, "Native", "green")]:
        sizes, means, _ = mean_by_n(data)
        gflops = [flops / ns for ns in means]
        plt.plot(sizes, gflops, marker="o", color=color, label=label)

    for size_bytes, name in [(32*1024, "L1"), (256*1024, "L2"), (3*1024*1024, "L3")]:
            n_boundary = size_bytes / bytes_per_elem
            plt.axvline(n_boundary, linestyle="--", color="purple", linewidth=2)
            bottom, top = plt.ylim()
            plt.text(n_boundary * 1.4, top - 0.03 * (top - bottom), name, ha="center", va="top")

    plt.xscale("log")
    plt.xlabel("Problem Size (N)", fontsize=12)
    plt.ylabel("GFLOP/s", fontsize=12)
    plt.title(title, fontsize=14, fontweight="bold")
    plt.legend()

plt.tight_layout()
plt.savefig("gflops.png", dpi=300, bbox_inches="tight")


# ---------------- Alignment, tail, stride (axpy float) ----------------
def read(filename):
    with open(filename) as file:
        reader = csv.reader(file)
        next(reader)                 # skip the header line
        return list(reader)

align = read('align.csv')     # build,n,offset,seconds
tail = read('tail.csv')       # build,n,seconds
stride = read('stride.csv')   # build,n,stride,seconds

plt.figure(figsize=(18, 5))

for build, color in [("scalar", "blue"), ("native", "green")]:

    # Panel 1: alignment at n = 4096 (fits in L1)
    points = []
    for r in align:
        if r[0] == build and r[1] == '4096':
            offset_bytes = int(r[2]) * 4                  # offset in floats x 4 bytes
            ns_per_elem = float(r[3]) * 1e9 / int(r[1])
            points.append((offset_bytes, ns_per_elem))
    sizes, means, stds = mean_by_n(points)
    first = means[0]                                      # aligned case
    means = [m / first for m in means]
    stds = [s / first for s in stds]
    plt.subplot(1, 3, 1)
    plt.errorbar(sizes, means, yerr=stds, marker="o", capsize=3, color=color, label=build)

    # Panel 2: tail, n = 1024..1040
    points = []
    for r in tail:
        if r[0] == build:
            n = int(r[1])
            ns_per_elem = float(r[2]) * 1e9 / n
            points.append((n, ns_per_elem))
    sizes, means, stds = mean_by_n(points)
    first = means[0]                                      # no-leftover case
    means = [m / first for m in means]
    stds = [s / first for s in stds]
    plt.subplot(1, 3, 2)
    plt.errorbar(sizes, means, yerr=stds, marker="o", capsize=3, color=color, label=build)

    # Panel 3: stride at n = 65536; each call processes n / stride elements
    points = []
    for r in stride:
        if r[0] == build and r[1] == '65536':
            s = int(r[2])
            ns_per_elem = float(r[3]) * 1e9 / (int(r[1]) // s)
            points.append((s, ns_per_elem))
    sizes, means, stds = mean_by_n(points)
    plt.subplot(1, 3, 3)
    plt.xscale("log", base=2)
    plt.xticks([1, 2, 4, 8, 16, 32], ["1", "2", "4", "8", "16", "32"])
    plt.errorbar(sizes, means, yerr=stds, marker="o", capsize=3, color=color, label=build)

titles = ["Alignment (N = 4096)", "Tail", "Stride (N = 65536)"]
xlabels = ["Offset (bytes)", "N", "Stride (elements)"]
ylabels = ["Time relative to aligned (x)", "Time relative to N = 1024 (x)", "Time per element (ns)"]
for i in range(3):
    plt.subplot(1, 3, i + 1)
    plt.title(titles[i], fontsize=14, fontweight="bold")
    plt.xlabel(xlabels[i], fontsize=12)
    plt.ylabel(ylabels[i], fontsize=12)
    plt.legend()

plt.subplot(1, 3, 1)
plt.axhline(1, color="black", linewidth=1)    # 1.0 = same speed as aligned
plt.subplot(1, 3, 2)
plt.axhline(1, color="black", linewidth=1)    # 1.0 = same speed as N = 1024
plt.subplot(1, 3, 3)
plt.ylim(bottom=0)

plt.tight_layout()
plt.savefig("access.png", dpi=300, bbox_inches="tight")
save_panels(["align.png", "tail.png", "stride.png"])


# ---------------- Roofline: AXPY float, n = 16M, fastest of 3 reps ----------------
big = 16777216
peak_s = min(float(r[1]) for r in read('peak.csv') if r[0] == 'native')
p_peak = 1000000 * 64 * 2 / peak_s / 1e9                  # GFLOP/s: 1M rounds x 64 floats x 2 FLOPs
mul_ns = min(t for n, t in native_fl_em if n == big)
bw = 16 / mul_ns                                          # GB/s: mul moves 16 B per element (incl. write-allocate)
ai = 2 / 12                                               # AXPY: 2 FLOPs per 12 bytes
scalar_gf = 2 / min(t for n, t in scalar_fl_axpy if n == big)
native_gf = 2 / min(t for n, t in native_fl_axpy if n == big)
print(f"roofline: peak {p_peak:.1f} GFLOP/s, bw {bw:.1f} GB/s, ridge {p_peak / bw:.2f}, "
      f"roof at AXPY {ai * bw:.2f}, scalar {scalar_gf:.2f}, native {native_gf:.2f} GFLOP/s")

intensities = [0.01 * 1.1 ** k for k in range(100)]       # 0.01 .. ~130 FLOP/byte
roof = [min(p_peak, i * bw) for i in intensities]

plt.figure(figsize=(8, 6))
plt.plot(intensities, roof, color="black", linewidth=2, label="Roofline")
plt.axvline(p_peak / bw, linestyle="--", color="purple")
plt.text(p_peak / bw * 1.1, p_peak * 0.6, f"ridge = {p_peak / bw:.1f} FLOP/B", color="purple", va="top")
plt.plot([ai], [scalar_gf], marker="o", markersize=9, linestyle="none", color="blue", label=f"Scalar AXPY ({scalar_gf:.2f} GFLOP/s)")
plt.plot([ai], [native_gf], marker="s", markersize=9, linestyle="none", color="green", label=f"Native AXPY ({native_gf:.2f} GFLOP/s)")
plt.xscale("log")
plt.yscale("log")
plt.ylim(0.2, p_peak * 2)
plt.xlabel("Arithmetic intensity (FLOP/byte)", fontsize=12)
plt.ylabel("GFLOP/s", fontsize=12)
plt.title(f"Roofline: peak {p_peak:.1f} GFLOP/s, memory {bw:.1f} GB/s", fontsize=14, fontweight="bold")
plt.legend(loc="lower right")
plt.savefig("roofline.png", dpi=200, bbox_inches="tight")
