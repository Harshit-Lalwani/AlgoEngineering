# Setup

## 1. Build the C++ benchmark (one-time)

```sh
cd cpp/build  # in case the build directory do not exist do, mkdir cpp/build
cmake ..       
make
```

## 2. Download Wikipedia titles (one-time)

(in case u dont have data/dataset_wiki.txt)

```sh
python3 download_data.py
```

## 3. Run benchmarks
```sh
cd cpp/build
./benchmark
```

## 4. Update notebooks
```sh
python3 update_nbs.py
```

## 5. (Optional) Cache profiling
```sh
python3 run_profiler.py
```