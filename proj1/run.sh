#!/bin/bash
# Runs every Project 1 experiment using simd.c.
#
# simd.c arguments:  <n> <kernel> <offset> <stride> <trials>
#   kernel: 0 axpy float   1 axpy double
#           2 dot  float   3 dot  double
#           4 mul  float   5 mul  double
# simd.c prints seconds per call (lower = faster).
#
# trials = 200,000,000 / n  so every run is long enough to time.
# Every setting runs 3 times (rep) for error bars.


# ---------------------------------------------------------------
# Build the same code three ways
# ---------------------------------------------------------------
gcc -O3 -fno-tree-vectorize simd.c -o scalar   # no SIMD
gcc -O3                     simd.c -o auto     # default auto-vectorized (128-bit SSE)
gcc -O3 -march=native       simd.c -o native   # widest SIMD this CPU has


# ---------------------------------------------------------------
# 1. Main sweep: every build, every kernel, small -> large arrays
#    Answers: scalar vs SIMD, locality (cache -> DRAM),
#    float vs double, and the negative example (dot product).
# ---------------------------------------------------------------
echo "build,kernel,n,seconds" > sweep.csv
for rep in 1 2 3; do
  for build in scalar auto native; do
    for kernel in 0 1 2 3 4 5; do
      for n in 1024 4096 16384 65536 262144 1048576 4194304 16777216; do
        trials=$(( 200000000 / n + 5 ))
        echo "$build,$kernel,$n,$(taskset -c 2 ./$build $n $kernel 0 1 $trials)" >> sweep.csv
      done
    done
  done
done


# ---------------------------------------------------------------
# 2. Alignment: axpy float, arrays shifted 0-16 floats off a 64-byte boundary
# ---------------------------------------------------------------
echo "build,n,offset,seconds" > align.csv
for rep in 1 2 3; do
  for build in scalar native; do
    for n in 4096 16777216; do
      for offset in 0 1 2 4 8 16; do
        trials=$(( 200000000 / n + 5 ))
        echo "$build,$n,$offset,$(taskset -c 2 ./$build $n 0 $offset 1 $trials)" >> align.csv
      done
    done
  done
done


# ---------------------------------------------------------------
# 3. Tail: axpy float, sizes 1024-1040 (0-16 leftover elements)
# ---------------------------------------------------------------
echo "build,n,seconds" > tail.csv
for rep in 1 2 3; do
  for build in scalar native; do
    for n in $(seq 1024 1040); do
      trials=$(( 200000000 / n + 5 ))
      echo "$build,$n,$(taskset -c 2 ./$build $n 0 0 1 $trials)" >> tail.csv
    done
  done
done


# ---------------------------------------------------------------
# 4. Stride: axpy float, same array, use every 1st, 2nd ... 32nd element
# ---------------------------------------------------------------
echo "build,n,stride,seconds" > stride.csv
for rep in 1 2 3; do
  for build in scalar native; do
    for n in 65536 16777216; do
      for stride in 1 2 4 8 16 32; do
        trials=$(( 200000000 / n + 5 ))
        echo "$build,$n,$stride,$(taskset -c 2 ./$build $n 0 0 $stride $trials)" >> stride.csv
      done
    done
  done
done


# ---------------------------------------------------------------
# 5. Proof of SIMD
#    "ss" instructions = one number at a time
#    "ps" instructions on ymm/zmm registers = 8 or 16 numbers at a time
# ---------------------------------------------------------------
echo "== Compiler report: which loops were vectorized" > verify.txt
gcc -O3 -march=native -fopt-info-vec-optimized -c simd.c -o /dev/null 2>> verify.txt

echo "== axpy_32, scalar build (expect mulss/addss)" >> verify.txt
objdump -d scalar | grep -A40 "<axpy_32>:" | grep -m2 -E "mulss|addss" >> verify.txt

echo "== axpy_32, native build (expect vfmadd...ps on ymm)" >> verify.txt
objdump -d native | grep -A80 "<axpy_32>:" | grep -m2 "ps.*ymm" >> verify.txt

echo "== dp_32, native build (multiply is vmulps, but adds are vaddss = one at a time)" >> verify.txt
objdump -d native | grep -A80 "<dp_32>:" | grep -m3 -E "vmulps|vaddss" >> verify.txt


# ---------------------------------------------------------------
# 6. Machine details for the methodology section
# ---------------------------------------------------------------
lscpu > env.txt
uname -a >> env.txt
gcc --version >> env.txt
cat /sys/devices/system/cpu/cpu2/cpufreq/scaling_governor >> env.txt
cat /sys/devices/system/cpu/smt/active >> env.txt
grep . /sys/devices/system/cpu/cpu0/cache/index*/{level,type,size} >> env.txt   # per-core cache sizes


# 7. Peak Performance Estimation
echo "build,seconds" > peak.csv
for rep in 1 2 3; do
  for build in scalar native; do
    echo "$build,$(taskset -c 2 ./$build 1000000 6 0 1 50)" >> peak.csv
  done
done

# 8. Correctness: scalar output is the reference
echo "Correctness check: n = 4103, mode 7" > correctness.txt
for build in scalar auto native; do
  echo "== $build" >> correctness.txt
  ./$build 4103 7 0 1 1 >> correctness.txt
done
