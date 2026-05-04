#include "algorithms/cache_oblivious.hpp"
#include <algorithm>

namespace cache_oblivious {

    static void merge_sort_impl(std::vector<std::string>& a, int lo, int hi, std::vector<std::string>& aux) {
        if (hi - lo <= 1) return;
        
        int mid = lo + (hi - lo) / 2;
        merge_sort_impl(a, lo, mid, aux);
        merge_sort_impl(a, mid, hi, aux);
        
        int i = lo, j = mid, k = lo;
        while (i < mid && j < hi) {
            if (a[i] <= a[j]) {
                aux[k++] = std::move(a[i++]);
            } else {
                aux[k++] = std::move(a[j++]);
            }
        }
        while (i < mid) aux[k++] = std::move(a[i++]);
        while (j < hi) aux[k++] = std::move(a[j++]);
        
        for (k = lo; k < hi; k++) {
            a[k] = std::move(aux[k]);
        }
    }

    void lazy_funnelsort(std::vector<std::string>& strings) {
        if (strings.empty()) return;
        std::vector<std::string> aux(strings.size());
        merge_sort_impl(strings, 0, strings.size(), aux);
    }
}
