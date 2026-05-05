import gzip
import os
import random
import urllib.request


def download_wiki_titles(
    output_file: str = "data/dataset_wiki.txt",
    max_lines: int = 5_000_000,
    dump_file: str = "enwiki-latest-all-titles-in-ns0.gz",
    seed: int = 0,
) -> None:
    url = "https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-all-titles-in-ns0.gz"
    print(f"Downloading Wikipedia titles from {url}...")
    print("This might take a while depending on your internet speed...")

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

    try:
        with urllib.request.urlopen(req) as response:
            with open(dump_file, "wb") as out_f:
                out_f.write(response.read())

        print("Download complete. Reading all titles into memory...")

        titles: list[str] = []
        with gzip.open(dump_file, "rb") as uncompressed:
            for line in uncompressed:
                title = line.decode("utf-8").strip()
                if title:
                    titles.append(title)

        print(f"Loaded {len(titles):,} titles. Shuffling...")
        rng = random.Random(seed)
        rng.shuffle(titles)

        write_count = min(max_lines, len(titles))
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as out_f:
            for title in titles[:write_count]:
                out_f.write(title + "\n")

        print(f"Success! Wrote {write_count:,} real-world strings to {output_file}")
    except Exception as exc:
        print(f"An error occurred: {exc}")
    finally:
        if os.path.exists(dump_file):
            os.remove(dump_file)


if __name__ == "__main__":
    download_wiki_titles()
