#include "algorithms/baselines.hpp"
#include <algorithm>

namespace baselines {

    void std_sort(std::vector<std::string>& strings) {
        std::sort(strings.begin(), strings.end());
    }

    static inline int char_at(const std::string& s, size_t d) {
        if (d < s.length()) return static_cast<unsigned char>(s[d]);
        return -1;
    }

    static void mkqs(std::vector<std::string>& a, int lo, int hi, size_t d) {
        if (hi - lo <= 1) return;
        
        int pivot = char_at(a[lo + (hi - lo) / 2], d);
        int lt = lo, gt = hi - 1;
        int i = lo;
        
        while (i <= gt) {
            int current = char_at(a[i], d);
            if (current < pivot) {
                std::swap(a[lt++], a[i++]);
            } else if (current > pivot) {
                std::swap(a[i], a[gt--]);
            } else {
                i++;
            }
        }
        
        mkqs(a, lo, lt, d);
        if (pivot >= 0) mkqs(a, lt, gt + 1, d + 1);
        mkqs(a, gt + 1, hi, d);
    }

    void multikey_quicksort(std::vector<std::string>& strings) {
        if (strings.empty()) return;
        mkqs(strings, 0, strings.size(), 0);
    }
}
