# Cache-Aware and Cache-Oblivious Algorithms for String Sorting

## Overview

This report surveys popular cache-aware and cache-oblivious algorithms for string sorting, focusing on their algorithmic ideas, cache analyses, and reference results that can be replicated experimentally. It emphasizes algorithms specifically designed or engineered for hierarchical memory (CPU caches and external memory), rather than generic RAM-model string sorters.[^1][^2]

## Background: String Sorting and Cache Models

String sorting deals with lexicographically ordering a set of variable-length strings, typically over an alphabet of size \(\sigma\), with total length \(N\) and number of strings \(K\). The cost of comparing strings is dominated by character inspections, and the access pattern over the underlying memory strongly affects performance via cache misses.[^3][^4]

Two main models for hierarchical memory are used in the analysis of string sorting:

- **External Memory / I/O model**: A main memory of size \(M\) and a disk; data moves in blocks of size \(B\). Complexity is measured in number of block transfers (I/Os).[^5]
- **Cache-oblivious model**: The algorithm is written without parameters \(M\) and \(B\), but is analyzed against an ideal cache that transfers blocks of size \(B\) between a cache of size \(M\) and an arbitrarily large main memory.[^5]

String-specific measures such as the total sum of longest common prefixes (\(\sum \mathrm{LCP}\)) and the distinguishing prefix length \(D\) (total number of characters that must be inspected to determine the order) are commonly used to obtain more refined bounds.[^6][^3]

## Popular Cache-Aware String Sorting Algorithms

### CRadix: Cache-Efficient MSD Radix Sort for Strings

CRadix is a cache-aware variant of MSD (most-significant-digit first) radix sort for strings proposed by Ng and Kakehi. It improves cache behavior by associating a small key buffer with each string key and copying a prefix of each key into its buffer, so that subsequent radix passes access these key segments contiguously.[^7][^8][^9]

Key properties:
- Based on classical MSD radix sort, but starts at the most significant character and refines partitions recursively.[^10]
- Uses per-key buffers to reduce random accesses to scattered string storage and to improve TLB and cache locality.[^9][^7]
- Evaluated against MSD radix sort and other string sorters, showing fewer cache misses and lower running time on large string collections.[^8][^9]

### Burstsort and Cache-Efficient Variants (Burstsort, C-burstsort, CP-burstsort)

Burstsort is a cache-conscious string sorting algorithm that builds a dynamic trie over prefixes and stores suffixes in buckets, which are then sorted using an in-cache sorter (often multikey quicksort). It was engineered specifically to reduce out-of-cache references for large sets of strings.[^11][^4]

Key ideas:
- Construct a compact trie whose leaves contain buckets of pointers (or copied suffixes) to strings that share a common prefix.[^4]
- When a bucket exceeds a threshold, it "bursts" into a subtree, redistributing its strings into smaller buckets; this keeps buckets small enough to fit in cache.[^11][^4]
- During bucket sorting, string suffixes can be copied into contiguous buffers (C-burstsort) to further improve spatial locality, or both suffixes and record pointers can be copied (CP-burstsort) to obtain stability at the cost of more memory.[^12][^13]

Empirical findings:
- For large sets of strings derived from real-world data (web lexicons, genomic strings), burstsort and its copy-based variants are typically up to four or five times faster than multikey quicksort and prior radix-based methods, primarily due to lower cache-miss rates.[^4][^12]
- C-burstsort reduces cache misses further by copying unexamined tails into contiguous buffers, leading to about a factor of two speedup over the original burstsort.[^13][^12]

### Other Cache-Aware Engineering of String Sorters

Beyond CRadix and burstsort, there are additional cache-aware engineering efforts:

- **Parallel optimized MSD radix sort implementations** that incorporate loop fission, "super alphabet" grouping of characters, and reduced copying to improve cache and TLB performance; these are often based on CRadix-like ideas and demonstrate substantial speedups over std::sort in practice.[^14]
- General cache-aware adaptive sorting frameworks, such as cache-aware GenericSort and GreedySort, which achieve I/O-optimal bounds for integer keys with few inversions; these frameworks can be adapted to string keys when comparisons are lexicographic, though they are not string-specific.[^15]

## Popular Cache-Oblivious String Sorting Algorithms

### External String Sorting: Faster and Cache-Oblivious (Fagerberg–Pagh–Pagh)

Fagerberg, Anna Pagh, and Rasmus Pagh present a randomized algorithm for sorting strings in external memory that is also cache-oblivious under the tall cache assumption \(M = \Omega(B^{1+\varepsilon})\).[^16][^17][^18]

Main characteristics:
- Input: \(K\) binary strings of total length \(N\) words; output: sorted order and the LCP array of the strings.[^17][^16]
- I/O complexity: \(O\big(\tfrac{K}{B} \log_{M/B}(K/M) \log(N/K) + \tfrac{N}{B}\big)\), which is never worse than \(O\big(\tfrac{K}{B} \log_{M/B}(K/M) \log \log_{M/B}(K/M) + \tfrac{N}{B}\big)\).[^19][^17]
- Algorithm type: Monte Carlo randomized, with error probability that can be made \(O(N^{-c})\) for any constant \(c > 0\).[^17]
- The method uses a signature technique: construct a reduced set of "signature" strings that preserve the trie structure of the originals, enabling efficient rank computation and LCP construction in external or cache-oblivious memory.[^19]

### Cache-Oblivious Randomized String Sorting via Signatures (Surveyed by Angrish & Garg)

Angrish and Garg survey efficient string sorting algorithms and describe a cache-oblivious randomized algorithm that uses the signature technique introduced in external string sorting work.[^20][^1][^19]

Highlights:
- Classifies algorithms into cache-aware (CRadix, burstsort) and cache-oblivious (randomized signature-based algorithm) categories.[^20]
- For the cache-oblivious algorithm, they report the same asymptotic I/O bound \(O(\tfrac{K}{B} \log_{M/B}(K/M) \log(N/K) + \tfrac{N}{B})\) under the cache-oblivious model.[^19]
- Emphasizes that practical cache-oblivious string sorting was, at the time, mostly a theoretical concept compared to cache-aware implementations that dominated experimental results.[^21][^1]

### Burstsort as a Cache-Oblivious Algorithm (in Practice)

Burstsort and its variants are often described as cache-oriented or cache-efficient rather than strictly cache-oblivious; however, some applied works in sequence compression refer to burstsort-based pipelines as cache-oblivious in the sense that they exploit locality without explicit tuning to cache sizes.[^22][^11]

Characteristics:
- The trie plus small bucket design leads to access patterns that perform well across different cache sizes because buckets fit in cache and traversal is mostly sequential.[^11][^4]
- There is no formal cache-oblivious I/O analysis analogous to funnelsort, but empirical cache-simulator studies show dramatically lower cache miss rates than multikey quicksort and conventional radix sort.[^12][^4]

### General Cache-Oblivious Sorting Applied to Strings

Cache-oblivious comparison-based sorting algorithms such as funnelsort and variants of merge sort can be used to sort pointers to strings using lexicographic comparisons. While not string-specific, their cache-oblivious I/O optimality for comparison sorting extends to string sorting in the comparison model, with the cost of comparisons reflecting string-access patterns.[^23][^24]

Important points:
- Funnelsort achieves work \(\Theta(N \log N)\) and I/O complexity \(O((N/B) \log_{M} N)\) under a tall cache assumption, which is optimal for comparison sorting.[^25][^23]
- Engineering studies of Lazy Funnelsort show that careful implementation can outperform tuned Quicksort and even some cache-aware merge-based sorters on in-RAM data, confirming the practical benefits of cache-oblivious design.[^26][^27]

## Analysis Results for String-Specific Cache-Aware Algorithms

### CRadix Analysis and Experimental Results

Ng and Kakehi analyze CRadix primarily experimentally, using running time and hardware performance counters (cache and TLB misses) on large string sets.[^8][^9]

Reported findings:
- CRadix reduces L1/L2 data cache and TLB misses compared to standard MSD radix sort by buffering key prefixes.[^7][^9]
- On typical workloads (e.g., tens of millions of strings of varied lengths), CRadix is significantly faster than MSD radix and competitive with or faster than high-quality comparison-based string sorters.[^9][^8]

To replicate:
- Generate large synthetic or real-world string datasets with controlled length and alphabet distributions (e.g., web URLs, dictionary words).[^8]
- Implement both baseline MSD radix sort and CRadix with per-key buffers and run them under a profiler that collects cache and TLB miss statistics.
- Measure wall-clock time and cache-miss counts as a function of number of strings, average length, and alphabet size.

### Burstsort and C-burstsort: Cache-Simulator Studies

Sinha and Zobel, and later Sinha, Zobel, and Ring, perform detailed empirical analyses of burstsort variants using both real hardware and cache simulators.[^28][^4][^12]

Key observations:
- Original burstsort is up to twice as fast as the best prior string sorting algorithms (multikey quicksort, radix-based methods) for large in-memory data sets due to reduced out-of-cache references.[^4]
- C-burstsort, which copies suffixes into contiguous buckets, is typically twice as fast as original burstsort and four to five times faster than multikey quicksort and earlier radix sort implementations.[^13][^12]
- Cache-simulator experiments show that most of the performance improvement is attributable to lower L1/L2 cache miss rates and better spatial locality in bucket accesses.[^12][^4]

Experimental setup details:
- Data sets include large lexicons, web crawl-derived word lists, and genomic sequences of varying length and redundancy.[^4]
- Algorithms compared: burstsort, C-burstsort (and CP-burstsort), multikey quicksort, radix sort variants, and library sorts.[^12][^4]
- Metrics: running time, number of memory accesses, cache-miss rates, memory usage (peak working set), and sensitivity to bucket thresholds.

## Analysis Results for Cache-Oblivious String Sorting

### External String Sorting Algorithm (Fagerberg–Pagh–Pagh)

The main theoretical result is an I/O bound expressed in terms of \(K\), \(N\), \(M\), and \(B\), showing an improvement over earlier deterministic external string sorting algorithms.[^16][^17]

Analytical contributions:
- Proves that the randomized algorithm achieves \(O(\tfrac{K}{B} \log_{M/B}(K/M) \log(N/K) + \tfrac{N}{B})\) I/Os in expectation, under the tall cache assumption.[^17][^19]
- Demonstrates that the error probability that the algorithm outputs an incorrect order can be made polynomially small in \(N\).[^17]
- Shows how to construct both the sorted permutation and the LCP array within the same asymptotic I/O cost, by performing an Euler tour and list ranking on the trie representing the signature set.[^16]

Replication guidance:
- Implement the randomized signature construction, rank computation, and LCP-array construction described in the paper, targeting an external memory framework (e.g., using file-backed arrays or an I/O library).
- Choose realistic parameters \(M\) and \(B\) based on a specific machine, and instrument the code to count block transfers via explicit buffering or an I/O simulator.
- Compare the observed number of I/Os and running time to those of a baseline external merge sort on pointer arrays, as well as the earlier algorithm by Arge et al. if implemented.

### Cache-Oblivious Randomized Signature-Based Algorithm (Surveyed)

The survey by Angrish and Garg reiterates the I/O complexity of the signature-based cache-oblivious algorithm and compares it conceptually to cache-aware approaches.[^1][^20][^19]

Key analytical points:
- The signature technique reduces input size while preserving trie structure, thereby ensuring that sorting the signatures yields the same lexicographic order as sorting the original strings.[^19]
- The algorithm is Monte Carlo; it may occasionally produce incorrect orderings, but error probability can be made negligible at the cost of larger constants in running time.[^17][^19]
- Even though asymptotically efficient, cache-oblivious string sorting remained mostly theoretical compared to cache-aware implementations like CRadix and burstsort, which dominated practical benchmarks at the time of writing.[^21][^1]

### General Cache-Oblivious Sorting (Lazy Funnelsort) and its Empirical Evaluation

While not string-specific, Lazy Funnelsort provides a key example of a cache-oblivious sorting algorithm whose implementation has been carefully engineered and empirically evaluated against cache-aware and cache-agnostic competitors.[^27][^26]

Findings from the engineering study:
- With appropriate parameter choices and implementation optimizations, Lazy Funnelsort can be faster than the best Quicksort implementation tested, even on problems that fit entirely in RAM.[^26]
- It also matches or exceeds the performance of several cache-aware sorting algorithms included in the study, while simultaneously providing asymptotically optimal I/O behavior in the cache-oblivious model.[^27][^26]
- On disk-based workloads, it is significantly faster than Quicksort but somewhat slower than carefully engineered multiway mergesort implementations, which are tuned for known \(M\) and \(B\).[^26]

Replication outline:
- Implement Lazy Funnelsort according to the paper, paying attention to recursion structure and buffer management.[^26]
- Compare against high-quality library Quicksort (e.g., std::sort) and a cache-aware multiway mergesort, measuring wall-clock time and profiling cache behavior.
- Although the algorithm is comparison-based, replacing scalar keys by pointers to strings and lexicographic comparison allows reuse of the implementation in a string-sorting context; however, the cost of comparisons may dominate for long strings.

## Summary Table of Key Algorithms

| Algorithm / Paper | Type | Model / Analysis | Main ideas | Reported advantages |
|-------------------|------|------------------|------------|----------------------|
| CRadix (Cache Efficient Radix Sort for String Sorting) | Cache-aware | Experimental cache/TLB analysis for MSD radix sort | Per-key buffers storing prefixes, MSD radix with improved locality | Fewer cache and TLB misses than MSD radix; faster for large string sets than baseline radix and some string sorters[^7][^8][^9] |
| Burstsort | Cache-aware / cache-efficient | Empirical, cache-simulator analysis | Dynamic trie, buckets for common prefixes, in-cache bucket sorting | Up to 2× faster than previous string sorters due to reduced out-of-cache references[^4][^11] |
| C-burstsort / CP-burstsort | Cache-aware / cache-efficient | Empirical, cache-simulator analysis | Copy suffixes (and optionally record pointers) into contiguous buckets | Typically 2× faster than burstsort and 4–5× faster than multikey quicksort and previous radix sorts[^12][^13] |
| External String Sorting: Faster and Cache-Oblivious | Cache-oblivious (external) | I/O bound \(O(\tfrac{K}{B} \log_{M/B}(K/M) \log(N/K) + \tfrac{N}{B})\) | Randomized signatures preserving trie structure; construct sorted order and LCP array | Improves on earlier external string sorting bounds; works in cache-oblivious model under tall cache assumption[^17][^16][^18] |
| Randomized signature-based cache-oblivious string sorter (surveyed) | Cache-oblivious | Same I/O bound as above | Uses signature reduction to sort strings cache-obliviously | Theoretically efficient; classified alongside CRadix and burstsort in surveys[^1][^19][^20] |
| Lazy Funnelsort | Cache-oblivious (comparison-based) | Optimal comparison and I/O bounds for sorting | Recursive funnels and mergers; oblivious to \(M, B\) | Engineered implementation can outperform Quicksort and compete with cache-aware sorters on in-RAM data[^26][^27] |

## How to Replicate Analyses: Practical Checklist

To reproduce and extend existing analyses for cache-aware and cache-oblivious string sorting algorithms:

1. **Select representative algorithms**:
   - Cache-aware: CRadix, burstsort, C-burstsort (or a high-quality burstsort implementation).[^8][^4][^12]
   - Cache-oblivious: external string sorting algorithm of Fagerberg–Pagh–Pagh (for I/O), Lazy Funnelsort (for in-RAM) with string keys via pointer indirection, and, if available, an implementation of the signature-based string sorter.[^26][^19][^17]

2. **Prepare datasets**:
   - Synthetic: random strings over varying alphabets and length distributions; collections with shared prefixes to stress trie-based methods.[^3][^4]
   - Real-world: web crawl-derived lexicons, dictionaries, and genomic sequences, similar to those used in burstsort and C-burstsort papers.[^4][^12]

3. **Define metrics**:
   - Runtime: wall-clock time as a function of \(K\) and \(N\).
   - Cache behavior: L1/L2 cache misses and TLB misses via hardware counters or cache simulators, following the methodology of burstsort and CRadix studies.[^7][^12][^4]
   - I/O behavior: number of block transfers \(B\) for external-memory algorithms, measured via explicit buffering or simulator.[^16][^17]
   - Memory usage: peak heap usage, especially important for copy-based methods like C-burstsort and CP-burstsort.[^12]

4. **Re-implement or obtain reference implementations**:
   - Use existing reference code where available, such as open-source parallel MSD radix sort tuned with CRadix techniques.[^14]
   - Implement algorithms directly from the papers, ensuring adherence to described buffering, bursting thresholds, and recursion strategies.

5. **Compare against baselines**:
   - Include multikey quicksort and standard library sort (e.g., std::sort) as RAM-model baselines.[^26][^4]
   - For external-memory experiments, include external merge sort and earlier external string sorting algorithms.[^17]

6. **Analyze and report**:
   - Plot runtime and cache-miss counts versus dataset size and characteristics.
   - Check whether empirical trends match the theoretical I/O and cache complexity predictions (e.g., near-linear growth in \(N/B\) for external algorithms, reduction in cache misses for cache-aware methods).[^4][^17][^26]

Following these steps will allow replication of most of the key analyses in the literature and provide a basis for evaluating new cache-aware or cache-oblivious string sorting algorithms.

---

## References

1. [Efficient String Sorting Algorithms: Cache-aware and Cache-Oblivious](https://www.semanticscholar.org/paper/Efficient-String-Sorting-Algorithms:-Cache-aware-Angrish-Garg/f90dd090606fa19400f4f3eb5fda59142d40a640) - Various algorithms that aim at minimizing the number of cache misses so that the I/O bottleneck prob...

2. [CACHE-AWARE AND CACHE-OBLIVIOUS ALGORITHMS](https://tudr.thapar.edu/server/api/core/bitstreams/e8a698c9-9e31-4c38-b0f9-42df1405560b/content)

3. [Radix Sort Lcp-Comparisons](https://www.cs.helsinki.fi/u/tpkarkka/teach/15-16/SPA/lecture03-2x4.pdf)

4. [Cache-Conscious Sorting of Large Sets of Strings with ...](https://courses.grainger.illinois.edu/cs232/fa2010/section/p1-sinha.pdf)

5. [Cache-oblivious algorithm - Wikipedia](https://en.wikipedia.org/wiki/Cache-oblivious_algorithm) - Optimal cache-oblivious algorithms are known for matrix multiplication, matrix transposition, sortin...

6. [[2006.02219] LCP-Aware Parallel String Sorting - arXiv](https://arxiv.org/abs/2006.02219) - We propose a framework yielding a D-aware modification of any existing PRAM string sorter. The deriv...

7. [Engineering Radix Sort for Strings - ACM Digital Library](https://dl.acm.org/doi/10.1007/978-3-540-89097-3_3) - Cache Efficient Radix Sort for String Sorting. In this paper, we propose CRadix sort, a new string s...

8. [Cache efficient radix sort for string sorting - Waseda University](https://waseda.elsevierpure.com/en/publications/cache-efficient-radix-sort-for-string-sorting/) - ... MSD radix sort. CRadix sort causes fewer cache misses than MSD radix ... Dive into the research ...

9. [Cache Efficient Radix Sort for String Sorting - ACM Digital Library](https://dl.acm.org/doi/10.5555/1226834.1226858) - In this paper, we propose CRadix sort, a new string sorting algorithm based on MSD ... Cache Efficie...

10. [MSD( Most Significant Digit ) Radix Sort - GeeksforGeeks](https://www.geeksforgeeks.org/dsa/msd-most-significant-digit-radix-sort/) - MSD can be used to sort strings of variable length, unlike LSD. LSD has to be stable in order to wor...

11. [Burstsort - Wikipedia](https://en.wikipedia.org/wiki/Burstsort)

12. [Cache-efficient string sorting using copying](https://www.academia.edu/8385516/Cache_efficient_string_sorting_using_copying) - Burstsort is a cache-oriented sorting technique that uses a dynamic trie to efficiently divide large...

13. [Cache-Efficient String Sorting Using Copying](https://docslib.org/download/5551403/cache-efficient-string-sorting-using-copying)

14. [A parallelized implementation of optimized MSD radix sort for strings](https://github.com/iwiwi/parallel-string-radix-sort) - MSD Radix Sort. Waihong Ng and Katsuhiko Kakehi. 2007. Cache Efficient Radix Sort for String Sorting...

15. [[PDF] Cache-Aware and Cache-Oblivious Adaptive Sorting](https://cs.au.dk/~gerth/papers/icalp05.pdf) - Two new adaptive sorting algorithms are introduced which perform an optimal number of comparisons wi...

16. [External String Sorting: Faster and Cache-oblivious](https://www.imada.sdu.dk/u/rolf/Edu/DM823/E10/STACS2006Slides.pdf)

17. [External string sorting | Proceedings of the 23rd Annual conference ...](https://dl.acm.org/doi/10.1007/11672142_4) - External string sorting: faster and cache-oblivious. Authors: Rolf ... External string sorting: fast...

18. [[PDF] External String Sorting: Faster and Cache-oblivious - IMADA](https://imada.sdu.dk/~rolf/Edu/DM823/E10/STACS2006Slides.pdf) - Rolf Fagerberg. Universiy of Southern Denmark. Anna Pagh. IT University of Copenhagen. Rasmus Pagh. ...

19. [International Journal of Soft Computing and Engineering (IJSCE)](https://gdeepak.com/pubs/Efficient%20String%20Sorting%20AlgorithmsCache-aware%20and%20Cache-Oblivious.pdf)

20. [Efficient String Sorting Algorithms:Cache-aware and Cache-Oblivious](https://www.academia.edu/1975734/Efficient_String_Sorting_Algorithms_Cache_aware_and_Cache_Oblivious) - Pagh, ―External string sorting: Faster and cache-oblivious‖. [14] M ... Pagh, -External string sorti...

21. [[PDF] CACHE-AWARE AND CACHE-OBLIVIOUS ALGORITHMS](https://gdeepak.com/thesisme/Cache-Aware%20And%20Cache%20Oblivious%20Algorithms.pdf)

22. [SRComp: Short Read Sequence Compression Using Burstsort and ...](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0081414) - Burstsort is a cache-oblivious string-sorting algorithm, as it takes advantage of the cache system o...

23. [Funnelsort - Wikipedia](https://en.wikipedia.org/wiki/Funnelsort)

24. [[PDF] Cache-Oblivious Sorting (1999; Frigo, Leiserson, Prokop ...](https://cs.au.dk/~gerth/papers/encyclopedia08.pdf) - The theorem shows cache-oblivious comparison based sorting without a tall cache assumption cannot ma...

25. [Dark Blue with Orange](https://cglab.ca/~dana/funnelsort/funnelsort.pdf)

26. [[PDF] Engineering a Cache-Oblivious Sorting Algorithm](https://cs.au.dk/~gerth/papers/alcomft-tr-03-101.pdf)

27. [Engineering a cache-oblivious sorting algorithm - ACM Digital Library](https://dl.acm.org/doi/10.1145/1227161.1227164) - Fagerberg, R., Pagh, A., and Pagh, R. 2006. External string sorting: Faster and cache-oblivious. In ...

28. [2.5](https://www.cs.amherst.edu/~ccmcgeoch/cs34/papers/a2_5-sinha.pdf)

