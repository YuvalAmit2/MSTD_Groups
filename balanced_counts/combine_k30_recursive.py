#!/usr/bin/env python3
"""Verify and combine the recursively refined hybrid partition for k=30.

    python3 combine_k30_recursive.py [DATA_DIR]

See balanced_counts/README.md, section "How k = 30 was split up".
"""

import os
import re
import sys
from fractions import Fraction

K = 30
N0, N1, N2 = 20_000, 5_120_000, 1_310_720_000
PARENTS0 = {
    0, 1, 2, 54, 55, 7700, 7701, 7702, 7720, 7754,
    7755, 7773, 15010, 15400, 15401, 15402, 15420, 15454, 15455, 15473,
}
BASES1 = {0, 1, 2, 54, 1_720_054, 55, 27_720, 427_720, 567_720,
          27_773, 395_010, 395_454}
LINE = re.compile(
    r"k=\s*(\d+)\s+task\s+(\d+)/(\d+)\s+partial:\s*(.*?)\s*"
    r"emptyT=(\d+)\s+seconds=([\d.]+)"
)


def load_ids(path):
    if not os.path.exists(path):
        return None
    with open(path) as fh:
        return {int(line) for line in fh if line.strip()}


def read_result(path, expected_n):
    with open(path, errors="replace") as fh:
        found = [m for line in fh if (m := LINE.search(line))]
    if len(found) != 1:
        raise ValueError(f"{path}: expected exactly one result line")
    m = found[0]
    k, task, n = map(int, m.group(1, 2, 3))
    if (k, n) != (K, expected_n):
        raise ValueError(f"{path}: reports {k}/{n}; expected {K}/{expected_n}")
    values = [int(x) for x in m.group(4).split()]
    if len(values) != K:
        raise ValueError(f"{path}: wrong partial-count width")
    return task, values, int(m.group(5)), float(m.group(6))


def consume(directory, filename_re, n, expected, totals, ignored=frozenset()):
    seen, empty, seconds = set(), 0, 0.0
    for name in os.listdir(directory):
        if not re.fullmatch(filename_re, name):
            continue
        task, values, e, sec = read_result(os.path.join(directory, name), n)
        if task in ignored:
            continue
        if task not in expected:
            raise ValueError(f"{directory}/{name}: unexpected/overlapping task {task}")
        if task in seen:
            raise ValueError(f"{directory}: duplicate task {task}")
        seen.add(task)
        for t, value in enumerate(values, 1):
            totals[t] += value
        empty += e
        seconds += sec
    missing = expected - seen
    if missing:
        sys.exit(f"{directory}: {len(missing)} expected result(s) missing")
    return empty, seconds, len(seen)


def main():
    # Directory holding out_k30_n20000/, out_k30_sub256/, out_k30_sub2/,
    # out_k30_recursive/, out_k30_hier/ and recursive_state/.
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    state = os.path.join(root, "recursive_state")
    totals = [0] * (K + 1)
    empty = 0
    seconds = 0.0
    counts = []

    expected0 = set(range(N0)) - PARENTS0
    e, s, c = consume(os.path.join(root, "out_k30_n20000"), r"shard_\d+\.txt",
                      N0, expected0, totals, PARENTS0)
    empty += e; seconds += s; counts.append(("original", c))

    expected1_all = {p + q * N0 for p in PARENTS0 for q in range(256)}
    expected1 = expected1_all - BASES1
    e, s, c = consume(os.path.join(root, "out_k30_sub256"), r"sub_\d+_\d+\.txt",
                      N1, expected1, totals, BASES1)
    empty += e; seconds += s; counts.append(("level1", c))

    parents3 = load_ids(os.path.join(state, "parents_gen3.txt"))
    if parents3 is None:
        sys.exit("missing recursive_state/parents_gen3.txt")
    expected2_all = {b + q * N1 for b in BASES1 for q in range(256)}
    expected2 = expected2_all - parents3
    e, s, c = consume(os.path.join(root, "out_k30_sub2"), r"sub2_\d+_\d+\.txt",
                      N2, expected2, totals, parents3)
    empty += e; seconds += s; counts.append(("level2", c))

    gen, parent_n, parents = 3, N2, parents3
    while parents:
        if gen == 7:
            break
        if parent_n > (2**64 - 1) // 256:
            sys.exit("recursive modulus exceeds uint64")
        child_n = parent_n * 256
        expected_all = {p + q * parent_n for p in parents for q in range(256)}
        next_parents = load_ids(os.path.join(state, f"parents_gen{gen+1}.txt"))
        if next_parents is None:
            sys.exit(f"missing parents_gen{gen+1}.txt; controller has not finished generation {gen}")
        if not next_parents <= expected_all:
            sys.exit(f"parents_gen{gen+1}.txt contains tasks outside generation {gen}")
        expected = expected_all - next_parents
        directory = os.path.join(root, "out_k30_recursive", f"gen_{gen}")
        e, s, c = consume(directory, r"task_\d+\.txt", child_n, expected, totals,
                          next_parents)
        empty += e; seconds += s; counts.append((f"generation{gen}", c))
        parents, parent_n, gen = next_parents, child_n, gen + 1

    if gen != 7 or not parents:
        sys.exit(f"unexpected terminal recursive generation {gen}")
    hier_dir = os.path.join(root, "out_k30_hier")
    expected_pairs = {(parent, child) for parent in parents for child in range(256)}
    seen_pairs = set()
    for name in os.listdir(hier_dir):
        mname = re.fullmatch(r"parent_(\d+)_child_(\d+)\.txt", name)
        if not mname:
            continue
        pair = tuple(map(int, mname.groups()))
        if pair not in expected_pairs or pair in seen_pairs:
            raise ValueError(f"{hier_dir}/{name}: unexpected or duplicate hierarchy leaf")
        task, values, e, sec = read_result(os.path.join(hier_dir, name), 256)
        if task != pair[1]:
            raise ValueError(f"{hier_dir}/{name}: child task mismatch")
        seen_pairs.add(pair)
        for t, value in enumerate(values, 1):
            totals[t] += value
        empty += e
        seconds += sec
    missing_pairs = expected_pairs - seen_pairs
    if missing_pairs:
        sys.exit(f"{hier_dir}: {len(missing_pairs)} hierarchy leaf result(s) missing")
    counts.append(("hierarchical", len(seen_pairs)))

    answer = K * sum(Fraction(totals[t], t) for t in range(1, K + 1)) + empty
    if answer.denominator != 1:
        sys.exit("non-integral total: recursive hybrid partition is inconsistent")
    print(f"balanced subsets of D_{K} = {int(answer)}")
    print("  " + " ".join(f"{name}={count}" for name, count in counts))
    print(f"  measured core-seconds = {seconds:,.0f}")


if __name__ == "__main__":
    main()
