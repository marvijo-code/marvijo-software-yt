"""Exact, linear-time substring statistics.

The implementation uses a suffix automaton.  Every non-root state represents
all substring lengths in ``(length[link[state]], length[state]]``.
"""

from array import array


_cached_string: str | None = None
_cached_result: tuple[int, int] | None = None


def _analyze(s: str) -> tuple[int, int]:
    global _cached_string, _cached_result

    # The two public functions are commonly called consecutively for the same
    # (potentially very large) string.  Strings are immutable, so an identity
    # cache safely avoids constructing the automaton twice.
    if s is _cached_string and _cached_result is not None:
        return _cached_result

    n = len(s)
    if n == 0:
        result = (0, 0)
        _cached_string, _cached_result = s, result
        return result

    lengths = array("i", [0])
    links = array("i", [-1])
    occurrences = array("I", [0])
    transitions: list[dict[str, int]] = [{}]

    last = 0
    distinct = 0

    for ch in s:
        current = len(transitions)
        current_length = lengths[last] + 1
        lengths.append(current_length)
        links.append(0)
        occurrences.append(1)
        transitions.append({})

        p = last
        while p != -1 and ch not in transitions[p]:
            transitions[p][ch] = current
            p = links[p]

        if p == -1:
            current_link = 0
        else:
            q = transitions[p][ch]
            if lengths[p] + 1 == lengths[q]:
                current_link = q
            else:
                clone = len(transitions)
                clone_length = lengths[p] + 1
                lengths.append(clone_length)
                links.append(links[q])
                occurrences.append(0)
                transitions.append(transitions[q].copy())

                while p != -1 and transitions[p].get(ch) == q:
                    transitions[p][ch] = clone
                    p = links[p]

                links[q] = clone
                current_link = clone

        links[current] = current_link
        # Clone creation changes how existing state intervals are partitioned,
        # but not their total size.  This is exactly the new interval.
        distinct += current_length - lengths[current_link]
        last = current

    # Counting-sort states by maximum length, then propagate terminal-path
    # counts through suffix links from longer states to shorter states.
    state_count = len(transitions)
    counts = array("I", [0]) * (n + 1)
    for state_length in lengths:
        counts[state_length] += 1
    for i in range(1, n + 1):
        counts[i] += counts[i - 1]

    order = array("I", [0]) * state_count
    for state in range(state_count - 1, -1, -1):
        state_length = lengths[state]
        counts[state_length] -= 1
        order[counts[state_length]] = state

    longest_repeated = 0
    for i in range(state_count - 1, 0, -1):
        state = order[i]
        count = occurrences[state]
        if count >= 2 and lengths[state] > longest_repeated:
            longest_repeated = lengths[state]
        parent = links[state]
        occurrences[parent] += count

    result = (distinct, longest_repeated)
    _cached_string, _cached_result = s, result
    return result


def count_distinct_substrings(s: str) -> int:
    """Return the exact number of distinct non-empty substrings of *s*."""

    return _analyze(s)[0]


def longest_repeated_substring(s: str) -> int:
    """Return the longest substring length having at least two occurrences."""

    return _analyze(s)[1]

