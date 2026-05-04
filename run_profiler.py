import subprocess
import re
import csv

algorithms = [
    "std::sort",
    "multikey_quicksort",
    "burstsort",
    "msd_radix_sort",
    "lazy_funnelsort"
]

results = []

for algo in algorithms:
    print(f"Profiling {algo}...")
    cmd = ["valgrind", "--tool=cachegrind", "--cache-sim=yes", "./benchmark", algo]
    
    res = subprocess.run(cmd, cwd="cpp/build", capture_output=True, text=True)
    output = res.stderr
    
    d_refs = re.search(r"D\s+refs:\s+([\d,]+)", output)
    d1_misses = re.search(r"D1\s+misses:\s+([\d,]+)", output)
    lld_misses = re.search(r"LLd\s+misses:\s+([\d,]+)", output)
    
    if d_refs and d1_misses and lld_misses:
        d_refs_val = int(d_refs.group(1).replace(",", ""))
        d1_miss_val = int(d1_misses.group(1).replace(",", ""))
        lld_miss_val = int(lld_misses.group(1).replace(",", ""))
        
        results.append({
            "algorithm": algo,
            "d_refs": d_refs_val,
            "d1_misses": d1_miss_val,
            "lld_misses": lld_miss_val,
            "d1_miss_rate": f"{(d1_miss_val / d_refs_val) * 100:.2f}%" if d_refs_val > 0 else "0%"
        })
    else:
        print(f"Failed to parse output for {algo}:\n{output[:500]}")

with open("Analysis/cache_profile.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["algorithm", "d_refs", "d1_misses", "lld_misses", "d1_miss_rate"])
    writer.writeheader()
    for row in results:
        writer.writerow(row)

print("Cache profiling complete! Results saved to Analysis/cache_profile.csv")
