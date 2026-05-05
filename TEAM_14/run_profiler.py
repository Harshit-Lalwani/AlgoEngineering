import subprocess
import re
import csv
import platform
import os

algorithms = [
    "std::sort",
    "multikey_quicksort",
    "burstsort",
    "c_burstsort",
    "msd_radix_sort",
    "lazy_funnelsort"
]

datasets = ["random", "prefix_heavy", "wiki_random", "wiki_heavy"]


def parse_size_str(s: str) -> int:
    s = s.strip()
    if s.endswith("K") or s.endswith("k"):
        return int(float(s[:-1]) * 1024)
    if s.endswith("M") or s.endswith("m"):
        return int(float(s[:-1]) * 1024 * 1024)
    try:
        return int(s)
    except ValueError:
        return 0


def detect_cache_params():
    system = platform.system()
    M = None
    B = None
    if system == "Darwin":
        try:
            M = int(subprocess.check_output(["sysctl", "-n", "hw.l3cachesize"]).strip())
        except Exception:
            M = None
        try:
            B = int(subprocess.check_output(["sysctl", "-n", "hw.cachelinesize"]).strip())
        except Exception:
            B = None
    else:
        # Linux / Codespaces
        try:
            idx3 = "/sys/devices/system/cpu/cpu0/cache/index3/size"
            if os.path.exists(idx3):
                with open(idx3, "r") as fh:
                    M = parse_size_str(fh.read().strip())
        except Exception:
            M = None
        try:
            cls = "/sys/devices/system/cpu/cpu0/cache/index0/coherency_line_size"
            # prefer index3 coherency_line_size if present
            cls_alt = "/sys/devices/system/cpu/cpu0/cache/index3/coherency_line_size"
            path = cls_alt if os.path.exists(cls_alt) else cls
            if os.path.exists(path):
                with open(path, "r") as fh:
                    B = int(fh.read().strip())
        except Exception:
            B = None

    return M, B


M_val, B_val = detect_cache_params()
print(f"Detected M={M_val} bytes, B={B_val} bytes")

results = []

for algo in algorithms:
    for ds in datasets:
        print(f"Profiling {algo} on dataset {ds}...")
        cmd = ["valgrind", "--tool=cachegrind", "--cache-sim=yes", "./benchmark", algo, ds]
        res = subprocess.run(cmd, cwd="cpp/build", capture_output=True, text=True)

        # parse valgrind/cachegrind summary from stderr
        stderr = res.stderr or ""
        stdout = res.stdout or ""

        d_refs = re.search(r"D\s+refs:\s+([\d,]+)", stderr)
        d1_misses = re.search(r"D1\s+misses:\s+([\d,]+)", stderr)
        lld_misses = re.search(r"(LLd|LLm)\s+misses:\s+([\d,]+)", stderr)

        d_refs_val = int(d_refs.group(1).replace(",", "")) if d_refs else 0
        d1_miss_val = int(d1_misses.group(1).replace(",", "")) if d1_misses else 0
        lld_miss_val = int(lld_misses.group(2).replace(",", "")) if lld_misses else 0

        # parse profile output printed by benchmark to get N and total_length
        # expecting lines like: PROFILE,<algorithm>,<dataset>,<count>,<seed>,<total_length>
        profile_lines = []
        for line in stdout.splitlines():
            if line.startswith("PROFILE,"):
                profile_lines.append(line.strip())

        if not profile_lines:
            print(f"No PROFILE lines found for {algo} {ds}; stdout snippet:\n{stdout[:400]}")

        for pl in profile_lines:
            parts = pl.split(",")
            if len(parts) >= 6:
                _, palgo, pdataset, pcount, pseed, ptotal = parts[:6]
                try:
                    pcount_i = int(pcount)
                    ptotal_i = int(ptotal)
                    avg_len = ptotal_i / pcount_i if pcount_i > 0 else 0
                except Exception:
                    pcount_i = 0
                    ptotal_i = 0
                    avg_len = 0

                results.append({
                    "algorithm": palgo,
                    "dataset": pdataset,
                    "count": pcount_i,
                    "seed": pseed,
                    "total_length": ptotal_i,
                    "avg_string_length": f"{avg_len:.3f}",
                    "d_refs": d_refs_val,
                    "d1_misses": d1_miss_val,
                    "lld_misses": lld_miss_val,
                    "M": M_val,
                    "B": B_val
                })

with open("Analysis/cache_results.csv", "w", newline="") as f:
    fieldnames = ["algorithm", "dataset", "count", "seed", "total_length", "avg_string_length", "d_refs", "d1_misses", "lld_misses", "M", "B"]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in results:
        writer.writerow(row)

print("Cache profiling complete! Results saved to Analysis/cache_results.csv")
