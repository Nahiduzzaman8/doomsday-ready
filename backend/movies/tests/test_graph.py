from unittest import TestCase

from movies.graph import creates_cycle, rewatch_order

IRON_MAN, FIRST_AVENGER, AVENGERS, CIVIL_WAR = 1, 2, 3, 4
RAGNAROK, INFINITY_WAR, ENDGAME, DOOMSDAY = 5, 6, 7, 8

SAMPLE = {
    IRON_MAN: [],
    FIRST_AVENGER: [],
    AVENGERS: [IRON_MAN, FIRST_AVENGER],
    CIVIL_WAR: [AVENGERS],
    RAGNAROK: [],
    INFINITY_WAR: [CIVIL_WAR, RAGNAROK],
    ENDGAME: [INFINITY_WAR],
    DOOMSDAY: [ENDGAME],
}


def assert_valid_order(test, graph, order):
    position = {movie: i for i, movie in enumerate(order)}
    for movie in order:
        for prereq in graph[movie]:
            test.assertLess(position[prereq], position[movie])


class RewatchOrderTests(TestCase):
    def test_doomsday_needs_all_seven_others(self):
        order = rewatch_order(SAMPLE, DOOMSDAY)
        self.assertEqual(sorted(order), [1, 2, 3, 4, 5, 6, 7])
        self.assertEqual(len(order), len(set(order)))
        assert_valid_order(self, SAMPLE, order)

    def test_civil_war(self):
        order = rewatch_order(SAMPLE, CIVIL_WAR)
        self.assertEqual(set(order[:2]), {IRON_MAN, FIRST_AVENGER})
        self.assertEqual(order[2:], [AVENGERS])

    def test_ragnarok_is_empty(self):
        self.assertEqual(rewatch_order(SAMPLE, RAGNAROK), [])

    def test_shared_prerequisite_appears_once(self):
        graph = {1: [], 2: [1], 3: [1], 4: [2, 3]}
        order = rewatch_order(graph, 4)
        self.assertEqual(order.count(1), 1)
        assert_valid_order(self, graph, order)

    def test_long_chain_does_not_hit_recursion_limit(self):
        graph = {i: [i - 1] for i in range(1, 5000)}
        graph[0] = []
        self.assertEqual(rewatch_order(graph, 4999), list(range(4999)))


class CreatesCycleTests(TestCase):
    def test_endgame_as_prerequisite_of_iron_man(self):
        self.assertTrue(creates_cycle(SAMPLE, IRON_MAN, [ENDGAME]))

    def test_self_dependency(self):
        self.assertTrue(creates_cycle(SAMPLE, RAGNAROK, [RAGNAROK]))

    def test_valid_new_link(self):
        self.assertFalse(creates_cycle(SAMPLE, RAGNAROK, [IRON_MAN]))

    def test_new_movie_cannot_cycle(self):
        self.assertFalse(creates_cycle(SAMPLE, 99, [DOOMSDAY, IRON_MAN]))
