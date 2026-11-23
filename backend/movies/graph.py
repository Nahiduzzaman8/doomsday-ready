"""Prerequisite graph logic for Feature 1.

The graph is a plain dict: movie_id -> list of prerequisite movie_ids.
No Django imports here so the logic can be tested on its own.
"""


def creates_cycle(graph, movie_id, new_prerequisites):
    """Return True if giving `movie_id` these prerequisites would form a cycle.

    A cycle appears only if `movie_id` can be reached by walking
    prerequisite links starting from one of its new prerequisites.
    """
    if movie_id in new_prerequisites:
        return True

    stack = list(new_prerequisites)
    seen = set()
    while stack:
        current = stack.pop()
        if current == movie_id:
            return True
        if current in seen:
            continue
        seen.add(current)
        stack.extend(graph.get(current, ()))
    return False


def rewatch_order(graph, target_id):
    """Return every movie needed before `target_id`, each once, prerequisites first.

    Iterative post-order DFS: a movie is added only after all of its
    prerequisites have been added. The target itself is not included.
    """
    order = []
    visited = {target_id}
    stack = [(target_id, iter(graph.get(target_id, ())))]
    done = object()

    while stack:
        node, children = stack[-1]
        child = next(children, done)
        if child is done:
            stack.pop()
            if node != target_id:
                order.append(node)
        elif child not in visited:
            visited.add(child)
            stack.append((child, iter(graph.get(child, ()))))

    return order
