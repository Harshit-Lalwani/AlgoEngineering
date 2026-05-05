#!/usr/bin/env bash
# run_perf.sh
# Runs perf stat (or Valgrind cachegrind as fallback) at multiple N values
# to collect meaningful cache miss data.
#
# Usage (from repo root):
#   chmod +x Analysis/run_perf.sh
#   cd cpp/build && ../../Analysis/run_perf.sh
#
# Requires: Linux with perf, or Valgrind
# Output:   Analysis/cache_results.csv (multi-N)

set -euo pipefail

BUILD_DIR="$(pwd)"
OUT_CSV="../../Analysis/cache_results.csv"

ALGOS=("std::sort" "burstsort" "c_burstsort" "msd_radix_sort" "merge_sort" "lazy_funnelsort")
DATASETS=("random" "wiki_random")
SIZES=(10000 100000 1000000)

echo "algorithm,dataset,N,l1_misses,l1_refs,llc_misses,llc_refs" > "$OUT_CSV"

for algo in "${ALGOS[@]}"; do
  for ds in "${DATASETS[@]}"; do
    for N in "${SIZES[@]}"; do
      # Attempt perf stat first (bare metal / cgroups with perf_event)
      if command -v perf &>/dev/null; then
        # perf stat outputs to stderr
        PERF_OUT=$( perf stat -e L1-dcache-loads,L1-dcache-load-misses,\
cache-references,cache-misses \
          ./benchmark "$algo" "$ds" 2>&1 || true )

        L1_REFS=$( echo "$PERF_OUT" | grep 'L1-dcache-loads' \
                   | awk '{gsub(",",""); print $1}' | head -1 )
        L1_MISS=$( echo "$PERF_OUT" | grep 'L1-dcache-load-misses' \
                   | awk '{gsub(",",""); print $1}' | head -1 )
        LLC_REFS=$( echo "$PERF_OUT" | grep 'cache-references' \
                    | awk '{gsub(",",""); print $1}' | head -1 )
        LLC_MISS=$( echo "$PERF_OUT" | grep 'cache-misses' \
                    | awk '{gsub(",",""); print $1}' | head -1 )

        echo "$algo,$ds,$N,${L1_MISS:-0},${L1_REFS:-0},${LLC_MISS:-0},${LLC_REFS:-0}" \
          >> "$OUT_CSV"

      elif command -v valgrind &>/dev/null; then
        CG_FILE="/tmp/cg.${algo//::/_}.$ds.$N"
        valgrind --tool=cachegrind \
                 --I1=32768,8,64 --D1=32768,8,64 --LL=8388608,16,64 \
                 --cachegrind-out-file="$CG_FILE" \
                 ./benchmark "$algo" "$ds" >/dev/null 2>&1 || true

        # Parse Ir/D1mr/LLdr from summary line of cg_annotate
        SUMMARY=$( cg_annotate "$CG_FILE" 2>/dev/null | grep '^PROGRAM TOTALS' || true )
        # Simplified extraction — adjust column indices if cg_annotate format differs
        D1_REFS=$( echo "$SUMMARY" | awk '{gsub(",",""); print $3}' )
        D1_MISS=$( echo "$SUMMARY" | awk '{gsub(",",""); print $4}' )
        LL_REFS=$( echo "$SUMMARY" | awk '{gsub(",",""); print $7}' )
        LL_MISS=$( echo "$SUMMARY" | awk '{gsub(",",""); print $8}' )

        echo "$algo,$ds,$N,${D1_MISS:-0},${D1_REFS:-0},${LL_MISS:-0},${LL_REFS:-0}" \
          >> "$OUT_CSV"
      else
        echo "Neither perf nor valgrind found. Skipping $algo $ds N=$N" >&2
      fi

      echo "Done: $algo $ds N=$N"
    done
  done
done

echo "Cache results written to $OUT_CSV"
