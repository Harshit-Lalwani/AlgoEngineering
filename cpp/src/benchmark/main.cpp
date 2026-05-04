#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <random>
#include <chrono>
#include <functional>
#include <algorithm>

#include "algorithms/baselines.hpp"
#include "algorithms/burstsort.hpp"
#include "algorithms/radix.hpp"
#include "algorithms/cache_oblivious.hpp"

std::vector<std::string> generate_dataset(size_t count, int seed, bool prefix_heavy = false) {
    std::mt19937 rng(seed);
    std::uniform_int_distribution<int> len_dist(4, 24);
    std::uniform_int_distribution<int> char_dist('a', 'z');
    
    std::vector<std::string> dataset;
    dataset.reserve(count);
    
    if (prefix_heavy) {
        std::vector<std::string> prefixes = {"al", "cache", "burst", "string", "prefix"};
        std::uniform_int_distribution<int> pref_dist(0, prefixes.size() - 1);
        std::uniform_int_distribution<int> tail_len_dist(2, 14);
        
        for (size_t i = 0; i < count; ++i) {
            std::string s = prefixes[pref_dist(rng)];
            int tail_len = tail_len_dist(rng);
            for (int j = 0; j < tail_len; ++j) {
                s += (char)char_dist(rng);
            }
            dataset.push_back(s);
        }
    } else {
        for (size_t i = 0; i < count; ++i) {
            int len = len_dist(rng);
            std::string s;
            for (int j = 0; j < len; ++j) {
                s += (char)char_dist(rng);
            }
            dataset.push_back(s);
        }
    }
    return dataset;
}

using SortFunc = std::function<void(std::vector<std::string>&)>;

struct BenchmarkResult {
    std::string dataset;
    size_t count;
    int seed;
    std::string algorithm;
    double elapsed_seconds;
    bool sorted_correctly;
    size_t total_length;
};

BenchmarkResult run_benchmark(const std::string& dataset_name, size_t count, int seed, const std::string& algo_name, SortFunc func, const std::vector<std::string>& data) {
    std::vector<std::string> copy = data;
    
    auto start = std::chrono::high_resolution_clock::now();
    func(copy);
    auto end = std::chrono::high_resolution_clock::now();
    
    std::chrono::duration<double> elapsed = end - start;
    
    bool correct = std::is_sorted(copy.begin(), copy.end());
    size_t total_length = 0;
    for (const auto& s : copy) total_length += s.length();
    
    return {dataset_name, count, seed, algo_name, elapsed.count(), correct, total_length};
}

int main(int argc, char* argv[]) {
    std::vector<BenchmarkResult> results;
    std::vector<size_t> sizes = {10000, 50000, 100000};
    std::vector<int> seeds = {0, 1, 2};
    
    std::string target_algo = "";
    if (argc > 1) {
        target_algo = argv[1];
        sizes = {10000}; // Reduced size to prevent valgrind OOM
        seeds = {0};      // Only one seed for cache profiling
    }

    std::vector<std::pair<std::string, SortFunc>> algorithms = {
        {"std::sort", baselines::std_sort},
        {"multikey_quicksort", baselines::multikey_quicksort},
        {"burstsort", [](std::vector<std::string>& a) { cache_aware::burstsort(a); }},
        {"msd_radix_sort", cache_aware::msd_radix_sort},
        {"lazy_funnelsort", cache_oblivious::lazy_funnelsort}
    };
    
    for (size_t count : sizes) {
        for (int seed : seeds) {
            auto random_data = generate_dataset(count, seed, false);
            auto prefix_data = generate_dataset(count, seed, true);
            
            for (const auto& algo : algorithms) {
                if (!target_algo.empty() && algo.first != target_algo) continue;
                
                std::cout << "Running " << algo.first << " on random dataset (size=" << count << ")" << std::endl;
                results.push_back(run_benchmark("random", count, seed, algo.first, algo.second, random_data));
                
                std::cout << "Running " << algo.first << " on prefix_heavy dataset (size=" << count << ")" << std::endl;
                results.push_back(run_benchmark("prefix_heavy", count, seed, algo.first, algo.second, prefix_data));
            }
        }
    }
    
    if (target_algo.empty()) {
        std::ofstream out("../Analysis/results.csv");
        out << "dataset,count,seed,algorithm,elapsed_seconds,sorted_correctly,total_length\n";
        for (const auto& r : results) {
            out << r.dataset << "," << r.count << "," << r.seed << "," << r.algorithm << "," 
                << r.elapsed_seconds << "," << (r.sorted_correctly ? "True" : "False") << "," << r.total_length << "\n";
        }
        out.close();
        std::cout << "Benchmarks completed. Results written to Analysis/results.csv" << std::endl;
    }
    return 0;
}
