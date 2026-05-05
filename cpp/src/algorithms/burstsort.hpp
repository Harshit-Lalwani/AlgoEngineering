#pragma once

#include <vector>
#include <string>

namespace cache_aware {
    void burstsort(std::vector<std::string>& strings, size_t threshold = 8192);
    void c_burstsort(std::vector<std::string>& strings, size_t threshold = 8192);
}
