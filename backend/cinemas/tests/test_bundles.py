from itertools import product
from unittest import TestCase

from cinemas.bundles import fewest_bundles


def brute_force_fewest(sizes, group_size):
    best = None
    ranges = [range(group_size // size + 1) for size in sizes]
    for counts in product(*ranges):
        if sum(s * c for s, c in zip(sizes, counts)) == group_size:
            total = sum(counts)
            if best is None or total < best:
                best = total
    return best


class FewestBundlesTests(TestCase):
    def test_examples_from_brief(self):
        self.assertEqual(fewest_bundles([1, 3, 4], 6), [(3, 2)])
        self.assertEqual(fewest_bundles([2, 5], 11), [(5, 1), (2, 3)])
        self.assertEqual(fewest_bundles([6, 9, 20], 44), [(20, 1), (9, 2), (6, 1)])
        self.assertIsNone(fewest_bundles([4, 6], 7))

    def test_greedy_would_fail(self):
        # greedy takes 9 + 1 + 1 (3 bundles); best is 6 + 5 (2 bundles)
        self.assertEqual(fewest_bundles([1, 5, 6, 9], 11), [(6, 1), (5, 1)])

    def test_single_bundle(self):
        self.assertEqual(fewest_bundles([7], 7), [(7, 1)])

    def test_group_smaller_than_every_bundle(self):
        self.assertIsNone(fewest_bundles([5, 10], 3))

    def test_matches_brute_force_on_small_inputs(self):
        for sizes in ([1, 3, 4], [2, 5], [6, 9, 20], [4, 6], [3, 7, 11]):
            for group_size in range(1, 61):
                result = fewest_bundles(sizes, group_size)
                expected = brute_force_fewest(sizes, group_size)
                if expected is None:
                    self.assertIsNone(result)
                else:
                    self.assertEqual(sum(size * count for size, count in result), group_size)
                    self.assertEqual(sum(count for _, count in result), expected)

    def test_largest_input_is_fast(self):
        result = fewest_bundles([7, 13, 97, 233, 389, 401, 433, 457, 487, 499], 10000)
        self.assertEqual(sum(size * count for size, count in result), 10000)
