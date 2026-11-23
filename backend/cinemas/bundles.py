"""Bundle booking logic for Feature 2.

Fewest bundles whose seats add up to exactly the group size.
Unbounded coin-change DP: O(group_size * number_of_sizes).
"""


def fewest_bundles(bundle_sizes, group_size):
    """Return a list of (size, count) pairs, largest size first, or None if impossible."""
    sizes = sorted(set(bundle_sizes), reverse=True)
    impossible = group_size + 1

    best = [0] + [impossible] * group_size
    last_pick = [0] * (group_size + 1)

    for total in range(1, group_size + 1):
        for size in sizes:
            if size <= total and best[total - size] + 1 < best[total]:
                best[total] = best[total - size] + 1
                last_pick[total] = size

    if best[group_size] >= impossible:
        return None

    counts = {}
    remaining = group_size
    while remaining > 0:
        size = last_pick[remaining]
        counts[size] = counts.get(size, 0) + 1
        remaining -= size

    return sorted(counts.items(), reverse=True)
