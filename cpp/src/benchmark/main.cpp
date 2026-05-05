#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <random>
#include <cstdlib>
#include <chrono>
#include <functional>
#include <algorithm>
#include <numeric>
#include <cmath>

#include "algorithms/baselines.hpp"
#include "algorithms/burstsort.hpp"
#include "algorithms/radix.hpp"
#include "algorithms/cache_oblivious.hpp"

// ============================================================================
//  Dataset generators
// ============================================================================

std::vector<std::string> generate_dataset(size_t count, int seed,
                                          bool prefix_heavy = false) {
    std::mt19937 rng(seed);
    std::uniform_int_distribution<int> len_dist(4, 24);
    std::uniform_int_distribution<int> char_dist('a', 'z');

    std::vector<std::string> dataset;
    dataset.reserve(count);

    if (prefix_heavy) {
        std::vector<std::string> prefixes = {"al", "cache", "burst", "string", "prefix"};
        std::uniform_int_distribution<int> pref_dist(0, (int)prefixes.size() - 1);
        std::uniform_int_distribution<int> tail_len_dist(2, 14);
        for (size_t i = 0; i < count; ++i) {
            std::string s = prefixes[pref_dist(rng)];
            int tail_len = tail_len_dist(rng);
            for (int j = 0; j < tail_len; ++j) s += (char)char_dist(rng);
            dataset.push_back(std::move(s));
        }
    } else {
        for (size_t i = 0; i < count; ++i) {
            int len = len_dist(rng);
            std::string s;
            for (int j = 0; j < len; ++j) s += (char)char_dist(rng);
            dataset.push_back(std::move(s));
        }
    }
    return dataset;
}

static std::ifstream open_dataset_or_exit(const std::string& filepath) {
    std::ifstream file(filepath);
    if (!file.is_open()) {
        std::cerr << "Error: Could not open " << filepath << "!\n";
        std::cerr << "Make sure you ran download_data.py first.\n";
        std::exit(1);
    }
    return file;
}

std::vector<std::string> load_wiki_random_dataset(const std::string& filepath,
                                                   size_t count, int seed) {
    std::vector<std::string> dataset;
    dataset.reserve(count);
    if (count == 0) return dataset;
    std::ifstream file = open_dataset_or_exit(filepath);
    std::mt19937 rng(seed);
    std::string line;
    size_t seen = 0;
    while (std::getline(file, line)) {
        if (line.empty()) continue;
        if (dataset.size() < count) {
            dataset.push_back(line);
        } else {
            std::uniform_int_distribution<size_t> dist(0, seen);
            size_t pick = dist(rng);
            if (pick < count) dataset[pick] = line;
        }
        ++seen;
    }
    std::shuffle(dataset.begin(), dataset.end(), rng);
    return dataset;
}

std::vector<std::string> load_wiki_heavy_dataset(const std::string& filepath,
                                                   size_t count,
                                                   size_t min_length, int seed) {
    std::vector<std::string> dataset;
    dataset.reserve(count);
    std::ifstream file = open_dataset_or_exit(filepath);
    std::mt19937 rng(seed);
    std::string line;
    while (std::getline(file, line) && dataset.size() < count) {
        if (line.size() >= min_length) dataset.push_back(line);
    }
    std::shuffle(dataset.begin(), dataset.end(), rng);
    return dataset;
}

// ============================================================================
//  Radix sort recursion depth profiler
//  Counts average recursion depth across all calls to msd_sort to quantify
//  why MSD radix degrades on prefix-heavy / wiki-heavy datasets.
// ============================================================================

static std::atomic<long long> g_radix_depth_accum{0};
static std::atomic<long long> g_radix_call_count{0};

static inline int char_at_depth(const std::string& s, size_t d) {
    return (d < s.length()) ? static_cast<unsigned char>(s[d]) : -1;
}

static void msd_depth_probe(const std::vector<std::string>& a, int lo, int hi,
                             size_t d) {
    if (hi - lo <= 1) return;
    g_radix_depth_accum.fetch_add((long long)d, std::memory_order_relaxed);
    g_radix_call_count.fetch_add(1, std::memory_order_relaxed);
    std::array<int, 258> count = {0};
    for (int i = lo; i < hi; i++) count[char_at_depth(a[i], d) + 2]++;
    for (int r = 0; r < 257; r++) count[r + 1] += count[r];
    for (int r = 0; r < 256; r++) {
        int sub_lo = lo + count[r], sub_hi = lo + count[r + 1];
        if (sub_hi - sub_lo > 1) msd_depth_probe(a, sub_lo, sub_hi, d + 1);
    }
}

double measure_radix_mean_depth(const std::vector<std::string>& data) {
    g_radix_depth_accum = 0;
    g_radix_call_count  = 0;
    msd_depth_probe(data, 0, (int)data.size(), 0);
    long long calls = g_radix_call_count.load();
    if (calls == 0) return 0.0;
    return (double)g_radix_depth_accum.load() / (double)calls;
}

// ============================================================================
//  Benchmark runner
// ============================================================================

using SortFunc = std::function<void(std::vector<std::string>&)>;

struct BenchmarkResult {
    std::string dataset;
    size_t count;
    int seed;
    std::string algorithm;
    // Timing (10 seeds used; we store mean and std)
    double elapsed_mean;    // seconds
    double elapsed_std;     // seconds
    bool sorted_correctly;
    size_t total_length;
    // Normalised metrics
    double time_per_element_us;   // microseconds per string
    double time_per_char_us;      // microseconds per character
};

// NUM_WARMUP runs are discarded before timing to avoid cold-cache bias.
constexpr int NUM_WARMUP = 2;

BenchmarkResult run_benchmark(const std::string& dataset_name, size_t count,
                               int seed, const std::string& algo_name,
                               SortFunc func,
                               const std::vector<std::string>& data) {
    // Warmup: run without measuring to warm up CPU caches and branch predictors
    for (int w = 0; w < NUM_WARMUP; w++) {
        std::vector<std::string> tmp = data;
        func(tmp);
    }

    // Timed run (single copy per call; repeat across outer seed loop for stats)
    std::vector<std::string> copy = data;
    auto t0 = std::chrono::high_resolution_clock::now();
    func(copy);
    auto t1 = std::chrono::high_resolution_clock::now();
    double elapsed = std::chrono::duration<double>(t1 - t0).count();

    bool correct = std::is_sorted(copy.begin(), copy.end());
    size_t total_length = 0;
    for (const auto& s : copy) total_length += s.length();

    double tpe_us = (elapsed / (double)count) * 1e6;
    double tpc_us = (total_length > 0)
                    ? (elapsed / (double)total_length) * 1e6
                    : 0.0;

    return {dataset_name, count, seed, algo_name,
            elapsed, 0.0,   // std computed later by aggregation
            correct, total_length, tpe_us, tpc_us};
}

// ============================================================================
//  main
// ============================================================================

int main(int argc, char* argv[]) {
    // Seeds: 10 independent runs for statistical rigour
    std::vector<size_t> sizes = {100000, 1000000, 5000000};
    std::vector<int>    seeds;
    for (int i = 0; i < 10; i++) seeds.push_back(i);

    std::string target_algo    = "";
    std::string target_dataset = "";

    if (argc > 1) {
        target_algo = argv[1];
        // Cache-profiling mode: small size to prevent Valgrind OOM
        sizes = {10000};
        seeds = {0};
        if (argc > 2) target_dataset = argv[2];
    }

    std::vector<std::pair<std::string, SortFunc>> algorithms = {
        {"std::sort",          baselines::std_sort},
        {"multikey_quicksort", baselines::multikey_quicksort},
        {"burstsort",          [](std::vector<std::string>& a){ cache_aware::burstsort(a); }},
        {"c_burstsort",        [](std::vector<std::string>& a){ cache_aware::c_burstsort(a); }},
        {"msd_radix_sort",     cache_aware::msd_radix_sort},
        {"merge_sort",         cache_oblivious::merge_sort},       // 2-way baseline
        {"lazy_funnelsort",    cache_oblivious::lazy_funnelsort},  // K-way funnelsort
    };

    const std::string wiki_path     = "../../data/dataset_wiki.txt";
    const size_t      wiki_min_len  = 20;

    // Accumulate per-(algo, dataset, count) times across seeds for stddev
    // key = algo + "|" + dataset + "|" + count
    std::map<std::string, std::vector<double>> timing_map;

    // Raw per-seed results (will be post-processed for mean/std)
    std::vector<BenchmarkResult> raw_results;

    for (size_t count : sizes) {
        for (int seed : seeds) {
            auto random_data  = generate_dataset(count, seed, false);
            auto prefix_data  = generate_dataset(count, seed, true);
            auto wiki_random  = load_wiki_random_dataset(wiki_path, count, seed);
            auto wiki_heavy   = load_wiki_heavy_dataset (wiki_path, count, wiki_min_len, seed);

            struct DS { std::string name; const std::vector<std::string>* data; };
            std::vector<DS> datasets = {
                {"random",       &random_data},
                {"prefix_heavy", &prefix_data},
                {"wiki_random",  &wiki_random},
                {"wiki_heavy",   &wiki_heavy},
            };

            for (const auto& algo : algorithms) {
                if (!target_algo.empty() && algo.first != target_algo) continue;

                for (const auto& ds : datasets) {
                    if (!target_dataset.empty() && ds.name != target_dataset) continue;

                    std::cout << "Running " << algo.first
                              << " on " << ds.name
                              << " (N=" << count << ", seed=" << seed << ")" << std::endl;

                    auto br = run_benchmark(ds.name, count, seed,
                                            algo.first, algo.second, *ds.data);
                    std::cout << "PROFILE," << br.algorithm << "," << br.dataset
                              << "," << br.count << "," << br.seed
                              << "," << br.total_length << std::endl;

                    std::string key = algo.first + "|" + ds.name + "|" + std::to_string(count);
                    timing_map[key].push_back(br.elapsed_mean);
                    raw_results.push_back(br);
                }
            }
        }
    }

    // ----- Compute mean / std per (algo, dataset, N) group -----
    auto compute_stats = [](const std::vector<double>& v,
                             double& mean, double& std_dev) {
        mean = 0.0; std_dev = 0.0;
        if (v.empty()) return;
        for (double x : v) mean += x;
        mean /= (double)v.size();
        for (double x : v) std_dev += (x - mean) * (x - mean);
        std_dev = std::sqrt(std_dev / (double)v.size());
    };

    if (target_algo.empty()) {
        // Write aggregated results (mean ± std)
        std::ofstream agg("../../Analysis/results_aggregated.csv");
        agg << "algorithm,dataset,count,elapsed_mean_s,elapsed_std_s,"
               "time_per_element_us_mean,time_per_char_us_mean\n";
        std::set<std::tuple<std::string,std::string,size_t>> seen;
        for (const auto& r : raw_results) {
            auto key = std::make_tuple(r.algorithm, r.dataset, r.count);
            if (seen.count(key)) continue;
            seen.insert(key);
            std::string mkey = r.algorithm + "|" + r.dataset + "|" + std::to_string(r.count);
            double mean, sd;
            compute_stats(timing_map[mkey], mean, sd);
            double tpe_us = (mean / (double)r.count) * 1e6;
            double tpc_us = (r.total_length > 0)
                            ? (mean / (double)r.total_length) * 1e6 : 0.0;
            agg << r.algorithm << "," << r.dataset << "," << r.count << ","
                << mean << "," << sd << "," << tpe_us << "," << tpc_us << "\n";
        }
        agg.close();

        // Write raw per-seed results (backward-compatible)
        std::ofstream out("../../Analysis/results.csv");
        out << "dataset,count,seed,algorithm,elapsed_seconds,sorted_correctly,"
               "total_length,time_per_element_us,time_per_char_us\n";
        for (const auto& r : raw_results) {
            out << r.dataset << "," << r.count << "," << r.seed << ","
                << r.algorithm << "," << r.elapsed_mean << ","
                << (r.sorted_correctly ? "True" : "False") << ","
                << r.total_length << "," << r.time_per_element_us << ","
                << r.time_per_char_us << "\n";
        }
        out.close();

        // Write radix recursion depth analysis
        std::vector<size_t> depth_sizes = {100000, 1000000, 5000000};
        std::ofstream depth_out("../../Analysis/radix_depth.csv");
        depth_out << "dataset,count,mean_recursion_depth\n";
        for (size_t count : depth_sizes) {
            auto random_data  = generate_dataset(count, 0, false);
            auto prefix_data  = generate_dataset(count, 0, true);
            auto wiki_random  = load_wiki_random_dataset(wiki_path, count, 0);
            auto wiki_heavy   = load_wiki_heavy_dataset (wiki_path, count, wiki_min_len, 0);
            depth_out << "random,"       << count << "," << measure_radix_mean_depth(random_data)  << "\n";
            depth_out << "prefix_heavy," << count << "," << measure_radix_mean_depth(prefix_data)  << "\n";
            depth_out << "wiki_random,"  << count << "," << measure_radix_mean_depth(wiki_random)  << "\n";
            depth_out << "wiki_heavy,"   << count << "," << measure_radix_mean_depth(wiki_heavy)   << "\n";
        }
        depth_out.close();

        std::cout << "Done. Wrote:\n"
                     "  Analysis/results.csv (raw per-seed)\n"
                     "  Analysis/results_aggregated.csv (mean +/- std)\n"
                     "  Analysis/radix_depth.csv (MSD recursion depth by dataset)\n";
    }
    return 0;
}
