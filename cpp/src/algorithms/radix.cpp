#include "algorithms/radix.hpp"
#include <algorithm>
#include <array>

namespace cache_aware {

    static inline int char_at(const std::string& s, size_t d) {
        if (d < s.length()) return static_cast<unsigned char>(s[d]);
        return -1;
    }

    static void msd_sort_impl(std::vector<std::string>& a, int lo, int hi, size_t d, std::vector<std::string>& aux) {
        if (hi - lo <= 1) return;

        // Count frequencies
        std::array<int, 258> count = {0};
        for (int i = lo; i < hi; i++) {
            int c = char_at(a[i], d);
            count[c + 2]++;
        }

        // Transform counts to indices
        for (int r = 0; r < 257; r++) {
            count[r + 1] += count[r];
        }

        // Distribute
        for (int i = lo; i < hi; i++) {
            int c = char_at(a[i], d);
            aux[count[c + 1]++] = std::move(a[i]);
        }

        // Copy back
        for (int i = lo; i < hi; i++) {
            a[i] = std::move(aux[i - lo]);
        }

        // Recursively sort for each character
        for (int r = 0; r < 256; r++) {
            int sub_lo = lo + count[r];
            int sub_hi = lo + count[r + 1];
            if (sub_hi - sub_lo > 1) {
                msd_sort_impl(a, sub_lo, sub_hi, d + 1, aux);
            }
        }
    }

    void msd_radix_sort(std::vector<std::string>& strings) {
        if (strings.empty()) return;
        std::vector<std::string> aux(strings.size());
        msd_sort_impl(strings, 0, strings.size(), 0, aux);
    }
}
