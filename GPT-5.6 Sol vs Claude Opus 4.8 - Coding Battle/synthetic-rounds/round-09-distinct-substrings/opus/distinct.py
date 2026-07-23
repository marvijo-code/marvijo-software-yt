"""Exact distinct-substring counting and longest-repeated-substring length.

Both use a suffix automaton (SAM), giving O(n) construction and exact results
(no hashing / collision risk). n = len(s).

- Number of distinct substrings = sum over states of (len[v] - len[link[v]]).
- A state's endpos-set size = number of occurrences of its substrings; a
  substring occurs >= 2 times iff its state's endpos size >= 2. The longest
  repeated substring length = max len[v] over states with endpos size >= 2.
"""


def _analyze(s):
    """Build SAM once, return (distinct_count, longest_repeated_len)."""
    n = len(s)
    if n == 0:
        return 0, 0

    cap = 2 * n + 5
    sa_len = [0] * cap
    sa_link = [-1] * cap
    sa_next = [None] * cap
    sa_cnt = [0] * cap

    sa_next[0] = {}
    last = 0
    size = 1

    for ch in s:
        cur = size
        sa_len[cur] = sa_len[last] + 1
        sa_next[cur] = {}
        sa_cnt[cur] = 1
        size += 1

        p = last
        while p != -1 and ch not in sa_next[p]:
            sa_next[p][ch] = cur
            p = sa_link[p]

        if p == -1:
            sa_link[cur] = 0
        else:
            q = sa_next[p][ch]
            if sa_len[p] + 1 == sa_len[q]:
                sa_link[cur] = q
            else:
                clone = size
                sa_len[clone] = sa_len[p] + 1
                sa_next[clone] = sa_next[q].copy()
                sa_link[clone] = sa_link[q]
                sa_cnt[clone] = 0
                size += 1
                while p != -1 and sa_next[p].get(ch) == q:
                    sa_next[p][ch] = clone
                    p = sa_link[p]
                sa_link[q] = clone
                sa_link[cur] = clone
        last = cur

    # Distinct substrings.
    distinct = 0
    for v in range(1, size):
        distinct += sa_len[v] - sa_len[sa_link[v]]

    # Propagate endpos-set sizes up the suffix-link tree (children before
    # parents => process states in order of decreasing len).
    order = sorted(range(1, size), key=sa_len.__getitem__, reverse=True)
    for v in order:
        p = sa_link[v]
        if p:  # skip root (index 0)
            sa_cnt[p] += sa_cnt[v]

    longest = 0
    for v in range(1, size):
        if sa_cnt[v] >= 2 and sa_len[v] > longest:
            longest = sa_len[v]

    return distinct, longest


_last_key = None
_last_val = (0, 0)


def _get(s):
    global _last_key, _last_val
    if _last_key is not None and _last_key == s:
        return _last_val
    _last_val = _analyze(s)
    _last_key = s
    return _last_val


def count_distinct_substrings(s: str) -> int:
    return _get(s)[0]


def longest_repeated_substring(s: str) -> int:
    return _get(s)[1]
