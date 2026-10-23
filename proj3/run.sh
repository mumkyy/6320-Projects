#!/bin/bash
# Runs every Project 3 experiment with fio on a TEST FILE (never the raw disk).
#
# Every run writes one JSON file into json/ named after its settings.
# fio reports IOPS, bandwidth and latency percentiles (p50/p95/p99/p99.9) itself.
# Every setting runs 3 times (rep) for error bars, except the long write run.
#
# Drive: SATA SSD (sda). Interface limit ~550-600 MB/s, NCQ queue limit 32.

RT=15                                    # seconds per run (use 5 for a quick first pass)

# settings shared by every run:
#   direct=1       bypass the page cache, so we measure the SSD and not RAM
#   libaio         lets fio keep many requests in flight (needed for iodepth > 1)
#   refill_buffers fresh random data every write = incompressible (documented data pattern)
COMMON="--name=t --filename=testfile --size=16G --direct=1 --ioengine=libaio \
        --refill_buffers --time_based --runtime=$RT --ramp_time=2 \
        --percentile_list=50:95:99:99.9 --output-format=json"

mkdir -p json


# ---------------------------------------------------------------
# 0. Create the 16 GB test file and precondition: write all of it once
# ---------------------------------------------------------------
fio --name=fill --filename=testfile --size=16G --direct=1 --ioengine=libaio \
    --refill_buffers --rw=write --bs=1M --iodepth=32 --output-format=json --output=json/fill.json


# ---------------------------------------------------------------
# 1. QD=1 baselines: 4K random and 128K sequential, read and write
# ---------------------------------------------------------------
for rep in 1 2 3; do
  fio $COMMON --rw=randread  --bs=4k   --iodepth=1 --output=json/qd1_randread_4k_${rep}.json
  fio $COMMON --rw=randwrite --bs=4k   --iodepth=1 --output=json/qd1_randwrite_4k_${rep}.json
  fio $COMMON --rw=read      --bs=128k --iodepth=1 --output=json/qd1_read_128k_${rep}.json
  fio $COMMON --rw=write     --bs=128k --iodepth=1 --output=json/qd1_write_128k_${rep}.json
done


# ---------------------------------------------------------------
# 2. Block-size sweep: random and sequential reads at QD=32
# ---------------------------------------------------------------
for rep in 1 2 3; do
  for rw in randread read; do
    for bs in 4k 16k 32k 64k 128k 256k; do
      fio $COMMON --rw=$rw --bs=$bs --iodepth=32 --output=json/bs_${rw}_${bs}_${rep}.json
    done
  done
done


# ---------------------------------------------------------------
# 3. Read/write mix: 4K random, QD=32, 100/70/50/0 % reads
# ---------------------------------------------------------------
for rep in 1 2 3; do
  for mix in 100 70 50 0; do
    fio $COMMON --rw=randrw --rwmixread=$mix --bs=4k --iodepth=32 --output=json/mix_${mix}_${rep}.json
  done
done


# ---------------------------------------------------------------
# 4. Queue-depth sweep: 4K random reads, QD 1 -> 256
#    (also gives tail latency at mid and near-knee QD)
# ---------------------------------------------------------------
for rep in 1 2 3; do
  for qd in 1 2 4 8 16 32 64 128 256; do
    fio $COMMON --rw=randread --bs=4k --iodepth=$qd --output=json/qd_${qd}_${rep}.json
  done
done


# ---------------------------------------------------------------
# 5. Device state: 10-minute sequential write, bandwidth logged every second
#    burst (SLC cache) vs steady state
# ---------------------------------------------------------------
fio --name=long --filename=testfile --size=16G --direct=1 --ioengine=libaio \
    --refill_buffers --rw=write --bs=128k --iodepth=32 --time_based --runtime=600 \
    --write_bw_log=json/long --log_avg_msec=1000 --output-format=json --output=json/long.json


# ---------------------------------------------------------------
# 6. Pitfall: buffered I/O (no direct=1) measures the page cache, not the SSD
#    read the first 1 GB once to load it into RAM, then random-read it
# ---------------------------------------------------------------
fio --name=warm --filename=testfile --size=1G --rw=read --bs=1M --invalidate=0 --output=/dev/null
for rep in 1 2 3; do
  fio --name=t --filename=testfile --size=1G --invalidate=0 --ioengine=libaio \
      --rw=randread --bs=4k --iodepth=1 --time_based --runtime=$RT \
      --percentile_list=50:95:99:99.9 --output-format=json --output=json/buffered_${rep}.json
done


# ---------------------------------------------------------------
# 7. Machine and drive details for the methodology section
# ---------------------------------------------------------------
lsblk -d -o NAME,MODEL,SIZE,ROTA,TRAN > env.txt
echo "model / firmware:" >> env.txt
cat /sys/block/sda/device/model /sys/block/sda/device/rev >> env.txt
# optional, needs smartmontools: temperature and total writes
# sudo smartctl -i -A /dev/sda >> env.txt
df -hT . >> env.txt                              # filesystem type and free space
echo "I/O scheduler:" >> env.txt
cat /sys/block/sda/queue/scheduler >> env.txt
fio --version >> env.txt
uname -a >> env.txt
lscpu >> env.txt
free -h >> env.txt

# delete the 16 GB test file when you're done with all runs:
# rm testfile
