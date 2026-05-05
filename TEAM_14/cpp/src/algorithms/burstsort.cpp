#include "algorithms/burstsort.hpp"
#include <algorithm>
#include <array>
#include <cstring>
#include <memory>
#include <vector>

namespace cache_aware {

    static inline int char_at(const std::string& s, size_t d) {
        if (d < s.length()) return static_cast<unsigned char>(s[d]);
        return -1;
    }

    // ==========================================
    // STANDARD BURSTSORT 
    // ==========================================
    struct TrieNode {
        std::array<std::unique_ptr<TrieNode>, 256> children;
        std::vector<std::string> bucket;
        std::vector<std::string> eof_bucket;
    };

    static void burst(std::unique_ptr<TrieNode>& node, size_t depth, size_t threshold) {
        std::vector<std::string> to_distribute = std::move(node->bucket);
        node->bucket.clear();

        for (auto& s : to_distribute) {
            int c = char_at(s, depth);
            if (c == -1) {
                node->eof_bucket.push_back(std::move(s));
            } else {
                if (!node->children[c]) {
                    node->children[c] = std::make_unique<TrieNode>();
                }
                node->children[c]->bucket.push_back(std::move(s));
            }
        }

        for (int c = 0; c < 256; ++c) {
            if (node->children[c] && node->children[c]->bucket.size() > threshold) {
                burst(node->children[c], depth + 1, threshold);
            }
        }
    }

    static void collect(std::unique_ptr<TrieNode>& node, size_t depth, std::vector<std::string>& out) {
        if (!node) return;
        
        std::sort(node->eof_bucket.begin(), node->eof_bucket.end());
        for (auto& s : node->eof_bucket) {
            out.push_back(std::move(s));
        }

        if (!node->bucket.empty()) {
            std::sort(node->bucket.begin(), node->bucket.end());
            for (auto& s : node->bucket) {
                out.push_back(std::move(s));
            }
            return;
        }

        for (int c = 0; c < 256; ++c) {
            collect(node->children[c], depth + 1, out);
        }
    }

    void burstsort(std::vector<std::string>& strings, size_t threshold) {
        if (strings.empty()) return;

        auto root = std::make_unique<TrieNode>();
        for (auto& s : strings) {
            root->bucket.push_back(std::move(s));
        }
        
        if (root->bucket.size() > threshold) {
            burst(root, 0, threshold);
        }

        strings.clear();
        collect(root, 0, strings);
    }

    // ==========================================
    // OPTIMIZED C-BURSTSORT 
    // ==========================================

    // TWEAK 1: Store original_idx to avoid re-allocating memory at the end
    struct CRecord {
        uint32_t offset;
        uint32_t length;
        uint32_t original_idx; 
    };

    struct CArena {
        std::vector<char> data;

        void reserve(size_t bytes) {
            data.reserve(bytes);
        }

        CRecord add(const std::string& s, uint32_t idx) {
            uint32_t offset = static_cast<uint32_t>(data.size());
            data.insert(data.end(), s.begin(), s.end());
            return {offset, static_cast<uint32_t>(s.size()), idx};
        }
    };

    static inline int char_at(const CArena& arena, const CRecord& record, size_t depth) {
        if (depth >= record.length) return -1;
        return static_cast<unsigned char>(arena.data[record.offset + depth]);
    }

    // TWEAK 2: Add 'depth' to skip redundant prefix comparisons
    static inline bool record_less(const CArena& arena, const CRecord& left, const CRecord& right, size_t depth) {
        size_t min_len = std::min(left.length, right.length);
        
        if (depth >= min_len) return left.length < right.length;
        
        // Start memory comparison AFTER the shared prefix
        int cmp = std::memcmp(arena.data.data() + left.offset + depth, 
                              arena.data.data() + right.offset + depth, 
                              min_len - depth);
        if (cmp != 0) return cmp < 0;
        return left.length < right.length;
    }

    struct CTrieNode {
        std::array<std::unique_ptr<CTrieNode>, 256> children;
        std::vector<CRecord> bucket;
        std::vector<CRecord> eof_bucket;
    };

    static void burst(std::unique_ptr<CTrieNode>& node, const CArena& arena, size_t depth, size_t threshold) {
        std::vector<CRecord> to_distribute = std::move(node->bucket);
        node->bucket.clear();

        for (const auto& record : to_distribute) {
            int c = char_at(arena, record, depth);
            if (c == -1) {
                node->eof_bucket.push_back(record);
            } else {
                if (!node->children[c]) {
                    node->children[c] = std::make_unique<CTrieNode>();
                }
                node->children[c]->bucket.push_back(record);
            }
        }

        for (int c = 0; c < 256; ++c) {
            if (node->children[c] && node->children[c]->bucket.size() > threshold) {
                burst(node->children[c], arena, depth + 1, threshold);
            }
        }
    }

    // Pass depth down into collect to power our optimized comparison
    static void collect(std::unique_ptr<CTrieNode>& node, const CArena& arena, 
                        std::vector<std::string>& original_strings, 
                        std::vector<std::string>& out, size_t depth) {
        if (!node) return;

        std::sort(node->eof_bucket.begin(), node->eof_bucket.end(),
                  [&arena, depth](const CRecord& a, const CRecord& b) { return record_less(arena, a, b, depth); });
        
        // Move the existing string instead of allocating a new one
        for (const auto& record : node->eof_bucket) {
            out.push_back(std::move(original_strings[record.original_idx]));
        }

        if (!node->bucket.empty()) {
            std::sort(node->bucket.begin(), node->bucket.end(),
                      [&arena, depth](const CRecord& a, const CRecord& b) { return record_less(arena, a, b, depth); });
            
            // Move the existing string instead of allocating a new one
            for (const auto& record : node->bucket) {
                out.push_back(std::move(original_strings[record.original_idx]));
            }
            return;
        }

        for (int c = 0; c < 256; ++c) {
            collect(node->children[c], arena, original_strings, out, depth + 1);
        }
    }

    void c_burstsort(std::vector<std::string>& strings, size_t threshold) {
        if (strings.empty()) return;

        size_t input_count = strings.size();
        size_t total_bytes = 0;
        for (const auto& s : strings) {
            total_bytes += s.size();
        }

        CArena arena;
        arena.reserve(total_bytes);

        // Take ownership of original strings temporarily
        std::vector<std::string> original_strings = std::move(strings);
        strings.clear();
        strings.reserve(input_count);

        std::vector<CRecord> records;
        records.reserve(input_count);
        for (uint32_t i = 0; i < input_count; ++i) {
            records.push_back(arena.add(original_strings[i], i));
        }

        auto root = std::make_unique<CTrieNode>();
        root->bucket = std::move(records);

        if (root->bucket.size() > threshold) {
            burst(root, arena, 0, threshold);
        }

        // Start collecting back into 'strings' at depth 0
        collect(root, arena, original_strings, strings, 0);
    }
}