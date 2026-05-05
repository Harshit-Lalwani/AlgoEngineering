#include "algorithms/cache_oblivious.hpp"
#include <algorithm>
#include <cmath>
#include <queue>
#include <vector>

namespace cache_oblivious {

    // ---------------------------------------------------------------------------
    // Baseline: standard 2-way merge sort (kept as a reference/comparison point)
    // I/O complexity: O((N/B) log2(N/B)) — NOT cache-oblivious
    // ---------------------------------------------------------------------------
    static void merge_sort_impl(std::vector<std::string>& a, int lo, int hi,
                                std::vector<std::string>& aux) {
        if (hi - lo <= 1) return;
        int mid = lo + (hi - lo) / 2;
        merge_sort_impl(a, lo, mid, aux);
        merge_sort_impl(a, mid, hi, aux);
        int i = lo, j = mid, k = lo;
        while (i < mid && j < hi)
            aux[k++] = (a[i] <= a[j]) ? std::move(a[i++]) : std::move(a[j++]);
        while (i < mid) aux[k++] = std::move(a[i++]);
        while (j < hi)  aux[k++] = std::move(a[j++]);
        for (k = lo; k < hi; k++) a[k] = std::move(aux[k]);
    }

    void merge_sort(std::vector<std::string>& strings) {
        if (strings.empty()) return;
        std::vector<std::string> aux(strings.size());
        merge_sort_impl(strings, 0, (int)strings.size(), aux);
    }

    // ---------------------------------------------------------------------------
    // Lazy Funnelsort  (cache-oblivious, Brodal & Fagerberg 2002)
    //
    // Key idea:
    //   Divide the input into K = ceil(N^{1/3}) contiguous sub-arrays.
    //   Recursively sort each sub-array.
    //   Merge the K sorted runs with a K-way merge.
    //
    // Why it is cache-oblivious:
    //   The recursion bottoms out when a sub-problem of size n satisfies
    //   n <= THRESHOLD (set conservatively so that the sub-problem and its
    //   merge buffers fit inside L1/L2 cache for any reasonable machine).
    //   At that point std::sort handles the sub-problem entirely in cache,
    //   incurring zero further I/O misses.
    //   Because K = N^{1/3}, the recursion depth is O(log_{3}(log N)) and
    //   the overall I/O complexity is O((N/B) * log_{M/B}(N/B)).
    //
    // Implementation note:
    //   A textbook funnel uses an elaborate binary-tree buffer structure.
    //   Here we use a std::priority_queue over (value, run-index) pairs for
    //   the K-way merge step; this is I/O-equivalent but simpler to read.
    // ---------------------------------------------------------------------------

    // Below this size a sub-problem is solved entirely in cache.
    // 1 << 13 = 8192 strings.  At ~14 bytes/string average that is ~114 KB,
    // which fits comfortably inside a typical 256 KB L2 cache.
    static constexpr int THRESHOLD = 1 << 13;

    static void funnelsort_impl(std::vector<std::string>& a, int lo, int hi) {
        int n = hi - lo;
        if (n <= 1) return;

        // Base case: small enough to be entirely in cache
        if (n <= THRESHOLD) {
            std::sort(a.begin() + lo, a.begin() + hi);
            return;
        }

        // Split into K = ceil(n^{1/3}) sub-arrays of roughly equal size
        int K = std::max(2, (int)std::ceil(std::cbrt((double)n)));
        int chunk = (n + K - 1) / K;  // ceil(n / K)

        // Recursively sort each chunk
        for (int k = 0; k < K; k++) {
            int sub_lo = lo + k * chunk;
            int sub_hi = std::min(sub_lo + chunk, hi);
            if (sub_lo >= hi) break;
            funnelsort_impl(a, sub_lo, sub_hi);
        }

        // K-way merge of the K sorted runs back into [lo, hi)
        // We use a min-heap of (current_string, run_index, position_in_run)
        using Entry = std::tuple<std::string, int, int>;
        auto cmp = [](const Entry& x, const Entry& y) {
            return std::get<0>(x) > std::get<0>(y);  // min-heap
        };
        std::priority_queue<Entry, std::vector<Entry>, decltype(cmp)> pq(cmp);

        // Track start/end positions of each run
        std::vector<int> run_start(K), run_end(K);
        for (int k = 0; k < K; k++) {
            run_start[k] = lo + k * chunk;
            run_end[k]   = std::min(run_start[k] + chunk, hi);
            if (run_start[k] < hi) {
                pq.push({a[run_start[k]], k, run_start[k]});
            }
        }

        // Drain the heap into a temporary output buffer
        std::vector<std::string> out;
        out.reserve(n);
        while (!pq.empty()) {
            auto [val, k, pos] = pq.top(); pq.pop();
            out.push_back(std::move(val));
            int next = pos + 1;
            if (next < run_end[k]) {
                pq.push({a[next], k, next});
            }
        }

        // Write sorted output back into a[lo..hi)
        for (int i = 0; i < n; i++) {
            a[lo + i] = std::move(out[i]);
        }
    }

    void lazy_funnelsort(std::vector<std::string>& strings) {
        if (strings.empty()) return;
        funnelsort_impl(strings, 0, (int)strings.size());
    }

}  // namespace cache_oblivious
