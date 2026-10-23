import matplotlib.pyplot as plt
from matplotlib.transforms import Bbox
import statistics
import json

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

# One fio result file -> its job: job['read'] / job['write'] hold
#   'iops', 'bw' (KiB/s), 'lat_ns' {'mean'}, 'clat_ns' {'percentile': {'99.000000': ...}}
def load(filename):
    with open('json/' + filename) as file:
        return json.load(file)['jobs'][0]

PCTS = ['50.000000', '95.000000', '99.000000', '99.900000']   # fio's percentile keys

plt.figure(figsize=(20, 11))


# ---------------- 1. QD=1 baselines + pitfall: p50 / p95 / p99 latency ----------------
tests = [('qd1_randread_4k',  'read',  '4K rand\nread'),
         ('qd1_randwrite_4k', 'write', '4K rand\nwrite'),
         ('qd1_read_128k',    'read',  '128K seq\nread'),
         ('qd1_write_128k',   'write', '128K seq\nwrite'),
         ('buffered',         'read',  '4K rand read\nbuffered (pitfall)')]

plt.subplot(2, 3, 1)
for i, (pct, name, color) in enumerate([('50.000000', 'p50', 'blue'), ('95.000000', 'p95', 'orange'), ('99.000000', 'p99', 'red')]):
    values = []
    errs = []
    for test, side, label in tests:
        reps = []
        for rep in [1, 2, 3]:
            job = load(f'{test}_{rep}.json')
            reps.append(job[side]['clat_ns']['percentile'][pct] / 1000)    # ns -> us
        values.append(statistics.mean(reps))
        errs.append(statistics.stdev(reps))
    x = [t + i * 0.25 for t in range(len(tests))]
    plt.bar(x, values, yerr=errs, capsize=3, width=0.25, color=color, label=name)
plt.xticks([t + 0.25 for t in range(len(tests))], [label for test, side, label in tests], fontsize=9)
plt.yscale('log')
plt.ylabel('Latency (us)', fontsize=12)
plt.title('1. QD=1 latency (and buffered pitfall)', fontsize=14, fontweight='bold')
plt.legend()


# ---------------- 2. Block-size sweep: throughput and latency, same runs ----------------
sizes = [4, 16, 32, 64, 128, 256]
plt.subplot(2, 3, 2)
for rw, color in [('randread', 'blue'), ('read', 'green')]:
    mbs = []
    errs = []
    for bs in sizes:
        reps = []
        for rep in [1, 2, 3]:
            reps.append(load(f'bs_{rw}_{bs}k_{rep}.json')['read']['bw'] * 1024 / 1e6)   # KiB/s -> MB/s
        mbs.append(statistics.mean(reps))
        errs.append(statistics.stdev(reps))
    plt.errorbar(sizes, mbs, yerr=errs, capsize=3, marker='o', color=color, label=rw + ' (MB/s)')
plt.xscale('log', base=2)
plt.xticks(sizes, [f'{s}K' for s in sizes])
plt.xlabel('Block size', fontsize=12)
plt.ylabel('Throughput (MB/s)', fontsize=12)
plt.legend(loc='upper left')

plt.twinx()                                                   # latency on the right axis
for rw, color in [('randread', 'blue'), ('read', 'green')]:
    lats = []
    errs = []
    for bs in sizes:
        reps = []
        for rep in [1, 2, 3]:
            reps.append(load(f'bs_{rw}_{bs}k_{rep}.json')['read']['lat_ns']['mean'] / 1000)
        lats.append(statistics.mean(reps))
        errs.append(statistics.stdev(reps))
    plt.errorbar(sizes, lats, yerr=errs, capsize=3, marker='s', linestyle='--', color=color, label=rw + ' (latency)')
plt.ylabel('Mean latency (us), dashed', fontsize=12)
plt.legend(loc='lower right')
plt.title('2. Block size (QD=32)', fontsize=14, fontweight='bold')


# ---------------- 3. Read/write mix: read + write IOPS (stacked) ----------------
mixes = [100, 70, 50, 0]
read_iops = []
write_iops = []
read_errs = []
write_errs = []
for mix in mixes:
    r_reps = []
    w_reps = []
    for rep in [1, 2, 3]:
        job = load(f'mix_{mix}_{rep}.json')
        r_reps.append(job['read']['iops'] / 1000)
        w_reps.append(job['write']['iops'] / 1000)
    read_iops.append(statistics.mean(r_reps))
    write_iops.append(statistics.mean(w_reps))
    read_errs.append(statistics.stdev(r_reps))
    write_errs.append(statistics.stdev(w_reps))

plt.subplot(2, 3, 3)
labels = [f'{m}% read' for m in mixes]
plt.bar(labels, read_iops, yerr=read_errs, capsize=3, color='blue', label='reads')
plt.bar(labels, write_iops, bottom=read_iops, yerr=write_errs, capsize=3, color='red', label='writes')
plt.ylabel('IOPS (thousands)', fontsize=12)
plt.title('3. Read/write mix (4K random, QD=32)', fontsize=14, fontweight='bold')
plt.legend()


# ---------------- 4. Queue-depth sweep: latency vs throughput (knee) ----------------
qds = [1, 2, 4, 8, 16, 32, 64, 128, 256]
iops = []
lats = []
iops_errs = []
lat_errs = []
tails = {pct: [] for pct in PCTS}                             # for panel 5
tail_errs = {pct: [] for pct in PCTS}
for qd in qds:
    i_reps = []
    l_reps = []
    t_reps = {pct: [] for pct in PCTS}
    for rep in [1, 2, 3]:
        job = load(f'qd_{qd}_{rep}.json')['read']
        i_reps.append(job['iops'] / 1000)
        l_reps.append(job['lat_ns']['mean'] / 1000)
        for pct in PCTS:
            t_reps[pct].append(job['clat_ns']['percentile'][pct] / 1000)
    iops.append(statistics.mean(i_reps))
    lats.append(statistics.mean(l_reps))
    iops_errs.append(statistics.stdev(i_reps))
    lat_errs.append(statistics.stdev(l_reps))
    for pct in PCTS:
        tails[pct].append(statistics.mean(t_reps[pct]))
        tail_errs[pct].append(statistics.stdev(t_reps[pct]))

plt.subplot(2, 3, 4)
plt.errorbar(iops, lats, xerr=iops_errs, yerr=lat_errs, capsize=3, marker='o', color='blue')
for qd, x, y in zip(qds, iops, lats):
    plt.annotate(f'QD{qd}', (x, y), textcoords='offset points', xytext=(5, 5), fontsize=9)
plt.xlabel('IOPS (thousands)', fontsize=12)
plt.ylabel('Mean latency (us)', fontsize=12)
plt.title('4. Queue depth: latency vs IOPS (4K rand read)', fontsize=14, fontweight='bold')


# ---------------- 5. Tail latency vs queue depth ----------------
plt.subplot(2, 3, 5)
for pct, name, color in zip(PCTS, ['p50', 'p95', 'p99', 'p99.9'], ['blue', 'green', 'orange', 'red']):
    plt.errorbar(qds, tails[pct], yerr=tail_errs[pct], capsize=3, marker='o', color=color, label=name)
plt.xscale('log', base=2)
plt.yscale('log')
plt.xticks(qds, [str(q) for q in qds])
plt.xlabel('Queue depth', fontsize=12)
plt.ylabel('Latency (us)', fontsize=12)
plt.title('5. Tail latency vs queue depth', fontsize=14, fontweight='bold')
plt.legend()


# ---------------- 6. Long sequential write: burst vs steady state ----------------
# long_bw.1.log lines: time (ms), bandwidth (KiB/s), direction, block size, offset
times = []
bws = []
with open('json/long_bw.1.log') as file:
    for line in file:
        parts = line.split(',')
        times.append(int(parts[0]) / 1000)                   # ms -> s
        bws.append(int(parts[1]) * 1024 / 1e6)               # KiB/s -> MB/s

plt.subplot(2, 3, 6)
plt.plot(times, bws, color='blue', linewidth=1)
plt.xlabel('Time (s)', fontsize=12)
plt.ylabel('Write bandwidth (MB/s)', fontsize=12)
plt.ylim(bottom=0)
plt.title('6. 10-minute sequential write (128K, QD=32)', fontsize=14, fontweight='bold')


plt.tight_layout()
plt.savefig('project3.png', dpi=300, bbox_inches='tight')
save_panels(['fig1_qd1.png', 'fig2_block_size.png', 'fig3_rwmix.png',
             'fig4_qd_knee.png', 'fig5_tail.png', 'fig6_long_write.png'])
plt.show()
