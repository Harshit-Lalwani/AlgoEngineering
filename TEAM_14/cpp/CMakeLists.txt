cmake_minimum_required(VERSION 3.10)
project(StringSortingBenchmarks)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Optimization flags for accurate benchmarking
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3 -march=native -Wall -Wextra")

# Include directories
include_directories(src)

# Collect source files for algorithms
file(GLOB ALGORITHM_SOURCES "src/algorithms/*.cpp")

# Main benchmark executable
add_executable(benchmark src/benchmark/main.cpp ${ALGORITHM_SOURCES})
