#!/bin/bash
# Runs every Project 2 experiment.
#   Intel MLC (v3.13) does: latency per level, working-set sweep, sequential vs random,
#                           stride, read/write mix, loaded latency (knee), prefetcher pitfall.
#   simd.c does only what needs our own loop kernels:
#                           cache-miss and TLB-miss counts vs runtime (perf), huge pages.
#
# simd.c arguments:  <n> <mode> <offset> <stride> <trials>
#   mode 0 = axpy (y = a*x + y), mode 1 = random pointer chase
#   n = number of 4-byte elements; simd.c prints seconds per call.
#
# Needs sudo: MLC (to control prefetchers), perf counters, huge-page switch.

MLC=./mlc/Linux/mlc

gcc -O3 -march=native simd.c -o native

# ---------------------------------------------------------------
# 1. Working-set sweep: random-access latency from L1 to DRAM (MLC)
#    -b = buffer size in KiB, -r = random access
#    L1 32 KiB, L2 256 KiB, L3 3 MiB
# ---------------------------------------------------------------
echo "" > mlc_sweep.txt
for kb in 8 16 32 64 128 256 512 1024 2048 4096 8192 32768 100000; do
  echo "== buffer ${kb} KiB" >> mlc_sweep.txt
  sudo $MLC --idle_latency -b$kb -r >> mlc_sweep.txt
done

# ---------------------------------------------------------------
# 2. Sequential vs random + pitfall (MLC, DRAM-sized buffer)
#    MLC can't disable prefetchers here (kernel lockdown), so:
#    -r = random (true latency), -e = sequential with prefetchers ON (looks fast)
# ---------------------------------------------------------------
echo "== random" > mlc_pattern.txt
sudo $MLC --idle_latency -b100000 -r >> mlc_pattern.txt
echo "== sequential, prefetchers ON" >> mlc_pattern.txt
sudo $MLC --idle_latency -b100000 -e >> mlc_pattern.txt

# --------------------------------------------------------------- 
# 3. Stride / granularity: 64, 256, 1024 B, prefetchers ON (MLC)
# ---------------------------------------------------------------
echo "" > mlc_stride.txt
for l in 64 256 1024; do
  echo "== stride ${l} B" >> mlc_stride.txt
  sudo $MLC --idle_latency -b100000 -e -l$l >> mlc_stride.txt
done

# Bandwidth for the same patterns, max load only (-d0 = no injection delay)
#   -U = random access for the bandwidth threads, -l = stride
#   (sequential 64 B bandwidth is the delay-0 row of mlc_loaded.txt)
sudo $MLC --loaded_latency -d0 -U     > mlc_bw_random.txt
sudo $MLC --loaded_latency -d0 -l256  > mlc_bw_stride256.txt
sudo $MLC --loaded_latency -d0 -l1024 > mlc_bw_stride1024.txt

# ---------------------------------------------------------------
# 4. Read/write mix: all reads, 3:1, 2:1, 1:1 (MLC)
# ---------------------------------------------------------------
sudo $MLC --peak_injection_bandwidth > mlc_rwmix.txt


# ---------------------------------------------------------------
# 5. Intensity sweep: latency vs bandwidth as load rises -> knee (MLC)
#    all reads, and 1:1 read/write (-W5)
# ---------------------------------------------------------------
sudo $MLC --loaded_latency > mlc_loaded.txt
sudo $MLC --loaded_latency -W5 > mlc_loaded_w5.txt
sudo $MLC --loaded_latency -W2 > mlc_loaded_w2.txt   # 2:1 = 67/33, closest MLC mix to 70/30
sudo $MLC --loaded_latency -W6 > mlc_loaded_w6.txt   # 100% write (non-temporal)


# ---------------------------------------------------------------
# 6. Cache-miss impact: axpy from L1 to DRAM, time + perf counters (simd.c)
#    one block per size in perf_axpy.txt; seconds per call on the first line
# ---------------------------------------------------------------
echo "" > perf_axpy.txt
for rep in 1 2 3; do
  for n in 1024 4096 16384 65536 262144 1048576 4194304 16777216; do
    trials=$(( 50000000 / n + 2 ))
    echo "== rep=$rep n=$n" >> perf_axpy.txt
    sudo perf stat -x, -e cycles,instructions,cache-misses,LLC-load-misses,dTLB-load-misses \
        -o perf_tmp.txt taskset -c 2 ./native $n 0 0 1 $trials >> perf_axpy.txt
    cat perf_tmp.txt >> perf_axpy.txt
  done
done


# ---------------------------------------------------------------
# 7. TLB-miss impact: random chase in DRAM, 4 KB pages vs huge pages (simd.c)
#    switches transparent huge pages, then puts it back to madvise
# ---------------------------------------------------------------
echo "" > perf_tlb.txt
for rep in 1 2 3; do
  for pages in never always; do
    echo $pages | sudo tee /sys/kernel/mm/transparent_hugepage/enabled > /dev/null
    for n in 4194304 33554432; do
      trials=$(( 50000000 / n + 2 ))
      echo "== rep=$rep pages=$pages n=$n" >> perf_tlb.txt
      sudo perf stat -x, -e cycles,dTLB-load-misses,LLC-load-misses \
          -o perf_tmp.txt taskset -c 2 ./native $n 1 0 1 $trials >> perf_tlb.txt
      cat perf_tmp.txt >> perf_tlb.txt
    done
  done
done
echo madvise | sudo tee /sys/kernel/mm/transparent_hugepage/enabled > /dev/null
rm -f perf_tmp.txt


# ---------------------------------------------------------------
# 8. Machine details for the methodology section
# ---------------------------------------------------------------
lscpu > env.txt
uname -a >> env.txt
gcc --version >> env.txt
free -h >> env.txt
sudo $MLC --help 2>/dev/null | head -1 >> env.txt
echo "governor:" >> env.txt
cat /sys/devices/system/cpu/cpu2/cpufreq/scaling_governor >> env.txt
echo "SMT active:" >> env.txt
cat /sys/devices/system/cpu/smt/active >> env.txt
echo "transparent huge pages:" >> env.txt
cat /sys/kernel/mm/transparent_hugepage/enabled >> env.txt
echo "perf_event_paranoid:" >> env.txt
cat /proc/sys/kernel/perf_event_paranoid >> env.txt
