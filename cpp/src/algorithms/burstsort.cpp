#include "algorithms/burstsort.hpp"
#include <algorithm>
#include <memory>
#include <array>

namespace cache_aware {

    static inline int char_at(const std::string& s, size_t d) {
        if (d < s.length()) return static_cast<unsigned char>(s[d]);
        return -1;
    }

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
}
