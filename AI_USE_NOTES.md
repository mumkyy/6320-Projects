# AI-Use Notes (all projects)

Tools: Claude (Anthropic), used as a chat assistant throughout; and, for the final stage, Claude Code (Claude in VS Code, with access to the project folders and a terminal). All code was compiled and run on my own machine (Intel i3-6100U laptop, SATA SSD); every measurement in the reports comes from my runs, not from the AI.

## 1. Understanding the assignment and background
- Asked for reading material and plain-language explanations of each project (SIMD, caches/latency/bandwidth, queueing, SSDs).
- AI pointed to: Algorithmica ("SIMD Parallelism", "RAM & CPU Caches" sections), Williams' roofline slides, LIKWID roofline tutorial, Intel MLC docs, fio docs, an HPC benchmarking lecture, Cornell CS 5220 notes on peak FLOPS, the STREAM site.
- Asked which of my lecture slides covered what, and what the slides did *not* cover.
- Asked conceptual questions: what flags do (`-fno-tree-vectorize`, `-march=native`, `-ffast-math`, `-mavx`), why GCC's flag says "tree", what objdump/perf/STREAM/MLC are, why timing needs repeats, why per-element time, write-allocate, Little's Law, TLB/huge pages, prefetching.

## 2. My code, and how the AI helped with it
- **I wrote the benchmark programs myself** (kernel functions, mode switch, function-pointer dispatch, argument layout). The AI found and explained bugs; I applied most fixes myself (sometimes via sed commands it suggested).
- Bugs it caught in my code: swapped `for` loop condition/increment, returning arrays from functions, stack arrays crashing at large sizes, wrong pointer types (float vs double, float used as an index), missing semicolons/braces/declarations, uninitialized variables, `free` inside timed kernels, out-of-bounds reads with stride/offset, a buffer overrun in an init call, missing/renamed functions, mode numbers that no longer matched the run script, a GFLOP/s plot loop using the wrong list.
- Design advice it gave that I used: time only the kernel (not setup), repeat runs and scale trials with size, use the result so the compiler can't delete the loop, non-zero varied init data, separate (non-aliased) arrays, 64-byte aligned allocation with an offset argument, fixed-footprint stride design, a peak-FLOP register-only kernel, a checksum mode for correctness, a pointer-chase kernel for latency (I simplified its chain builder myself).
- When the AI produced a larger "complete" harness, I **rejected it as too complicated** and kept my own structure with targeted fixes.

## 3. Run scripts
- AI drafted the bash run scripts (build variants, nested loops over sizes/strides/offsets/queue depths, CSV/JSON output, env capture, perf/MLC/fio commands).
- I **repeatedly asked for simpler versions**: no helper functions, no awk or bash string tricks, plain loops, plain seconds output (I do calculations later). Final scripts follow that style.
- I edited the scripts myself (renaming builds, adding sections, changing modes) and the AI reviewed my versions.
- In the final stage, Claude Code added the missing Project 2 MLC runs to the run script (100% write and 2:1 read/write mixes; random, 256 B and 1024 B stride bandwidth) after a gap check against the rubric; I ran them myself with sudo.

## 4. Plotting
- AI wrote initial plotting code; I restyled it to match my own approach (plain loops, my `mean_by_n` helper, explicit lists) and asked for rewrites when it used patterns I hadn't used (dictionary parsing, helper functions, tables).
- AI fixed issues in my plotting code: mixed float/double lists, unaveraged reps, linear vs log axes, missing legends/labels, unit conversion (s → ns), error bars (mean ± std), cache-boundary lines, label placement, normalizing alignment/tail to the aligned baseline.
- The AI tested plotting code on **sample/fake data in the expected formats** before I ran it on real data; I verified it on my real outputs.
- In the final stage, Claude Code edited the plotting scripts directly: added the new Project 2 MLC data (bandwidth per access pattern, all four read/write mixes), added error bars from the 3 reps to the Project 3 plots, and made every script also save each panel as its own image for the reports.

## 5. Analysis and interpretation
- AI explained what my measured plots/numbers showed (speedup compression past L3, alignment penalty, stride effects, roofline steps, cache-miss correlation, latency per level, prefetcher pitfall, knee and Little's Law, SSD read/write interference, periodic write spikes).
- I computed the roofline by hand from my CSVs with the AI checking the steps.
- AI suggested the write-allocate explanation for a kernel exceeding the memory roof. I first kept the original (12-byte) calculation and treated it as an anomaly; in the final stage I **decided to correct it to 16 bytes** (bandwidth 16.3 → 21.7 GB/s, native AXPY 131% → 98% of the roof).
- AI cross-checked my measured peak FLOP/s against the CPU's spec peak (73.1 measured vs 73.6 GFLOP/s theoretical).
- In the final stage, Claude Code recomputed summary numbers from my raw data (means, std, Little's Law, misses per element) and pointed out further anomalies: native slower than scalar at stride ≥ 16 in DRAM, LLC miss counts below the expected value (prefetching), huge pages cutting perf cycles far more than runtime (perf counts setup code), and the periodic SSD write bursts.

## 6. Tools and environment
- Help installing/running MLC, perf, fio; diagnosing perf permission settings, transparent huge pages, and why MLC couldn't disable prefetchers (kernel lockdown via Secure Boot). I chose to work around it (random access + prefetchers-on tests) rather than change BIOS settings.
- AI suggested which experiments MLC could cover vs. which needed my own loop kernels; I chose to use MLC wherever possible and keep my C code minimal.

## 7. Report and repository
- Claude Code reviewed each project against the assignment PDF and listed what was done and missing; I had it reduced to the minimum needed for full credit.
- It wrote the `.gitignore` files, short how-to-run READMEs, and report outlines: one section per rubric item, results filled in from my data, and placeholders for my analysis. At my request, the reports are formatted HTML pages with each result shown as its own graph rather than repeated in tables, and with marked boxes for my interpretation. It also added a roofline plot and per-panel images to the plotting scripts for this.
- I gave it my interpretation of each result as short notes, and it wrote them into the reports, keeping my wording where possible. It corrected statements that contradicted my data (e.g. which build reaches the memory roof, whether the stride speedup stays the same, whether reads or writes cost more) and told me about each correction so I could check it.
- For sections where I wasn't sure of the explanation (e.g. the Project 2 TLB and pitfall sections, the Project 3 knee, device-state and buffered-I/O sections), it wrote a short overview, which I reviewed.
- At my request, it replaced the per-report AI-use sections with a link to this shared note.
- It deleted files at my request: an old scratch folder (Project 1) and the 16 GB fio test file (Project 3).

## 8. Things the AI got wrong or I had to correct
- Initially guessed my machine was a VM (it's a laptop; corrected after `lscpu`).
- Gave Clang's flag (`-fno-vectorize`) when I'm using GCC; clarified after I asked.
- One muddled code snippet (normalizing error bars) that it then corrected.
- Its first harness and several scripts/plots were more complex than needed; simplified at my request.
- Added an explanation to my report outline (why scalar AXPY reached only 66% of the roof) that wasn't backed by a measurement; I had it removed.
- Interpretations of a few results (e.g., the 128K random-read dip, QD=1 tail latency) are hypotheses, not confirmed.

## 9. What I did independently
- Chose kernels and code structure; wrote and modified the C programs.
- Ran every experiment on my hardware; collected all data.
- Decided scope (minimal scripts, which builds/experiments to keep, MLC vs own code, skipping optional items, treating SSD temperature as not available).
- Supplied the per-core cache sizes from `/sys/devices/system/cpu/cpu0/cache/`, since `lscpu` reports totals across both cores.
- Verified outputs (sanity-checked numbers, correctness checksums, file counts) and caught mismatches (e.g., missing seconds lines, wrong modes).
- Gave the interpretation for each result (my notes are the basis of the report text), wrote my own hypotheses and their reasoning, and kept wording I chose where I didn't know the cause (e.g. calling the float/double dot-product difference "peculiar").
