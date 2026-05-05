#pragma once
#include <string>
#include <vector>

namespace cache_oblivious {
    // True K-way recursive funnelsort (cache-oblivious, I/O optimal)
    // I/O complexity: O((N/B) * log_{M/B}(N/B))
    void lazy_funnelsort(std::vector<std::string>& strings);

    // Standard 2-way merge sort (baseline comparison)
    // I/O complexity: O((N/B) * log_2(N/B))
    void merge_sort(std::vector<std::string>& strings);
}
