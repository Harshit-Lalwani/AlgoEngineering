#include "algorithms/radix.hpp"
#include <algorithm>
#include <array>

// MSD Radix Sort for strings
// Time complexity : O(N * D) where D = average distinguishing prefix length
// I/O complexity  : O(N * D / B) when alphabet_size < M/B (no bucket thrashing)
//                   degrades to O(N * D) cache misses when alphabet_size >= M/B
// Paper reference : Ng & Kakehi, "Cache Efficient Radix Sort for String Sorting" (2007)

namespace cache_aware {

    static inline int char_at(const std::string& s, size_t d) {
        if (d < s.length()) return static_cast<unsigned char>(s[d]);
        return -1;  // sentinel for end-of-string
    }

    // Invariant: aux must have the same size as `a` (the full array).
    // Indices lo/hi are absolute positions into both `a` and `aux`.
    // count[] is relative: count[r] is the number of elements before bucket r
    // within the slice [lo, hi), so the absolute write position for bucket r is
    // lo + count[r].
    static void msd_sort_impl(std::vector<std::string>& a, int lo, int hi,
                              size_t d, std::vector<std::string>& aux) {
        if (hi - lo <= 1) return;

        // --- Count frequencies ---
        std::array<int, 258> count = {0};
        for (int i = lo; i < hi; i++) {
            int c = char_at(a[i], d);
            count[c + 2]++;  // offset by 2: bucket -1 (EOF) lands at index 1
        }

        // --- Transform counts to starting indices (relative to lo) ---
        for (int r = 0; r < 257; r++) {
            count[r + 1] += count[r];
        }
        // After this, count[c+1] is the relative start of bucket c within [lo, hi).
        // Absolute start = lo + count[c+1].

        // --- Distribute into aux using ABSOLUTE indices ---
        for (int i = lo; i < hi; i++) {
            int c = char_at(a[i], d);
            // Write to lo + count[c+1] (absolute), then advance the pointer
            aux[lo + count[c + 1]++] = std::move(a[i]);
        }

        // --- Copy back (both sides use absolute indices, so no offset needed) ---
        for (int i = lo; i < hi; i++) {
            a[i] = std::move(aux[i]);
        }

        // --- Recursively sort each character bucket at depth d+1 ---
        for (int r = 0; r < 256; r++) {
            int sub_lo = lo + count[r];      // absolute start of bucket r
            int sub_hi = lo + count[r + 1];  // absolute end   of bucket r
            if (sub_hi - sub_lo > 1) {
                msd_sort_impl(a, sub_lo, sub_hi, d + 1, aux);
            }
        }
    }

    void msd_radix_sort(std::vector<std::string>& strings) {
        if (strings.empty()) return;
        // aux is allocated at the same size as strings so absolute indexing works
        std::vector<std::string> aux(strings.size());
        msd_sort_impl(strings, 0, (int)strings.size(), 0, aux);
    }

}  // namespace cache_aware
