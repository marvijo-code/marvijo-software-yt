"""Grader-side reference: iterative suffix automaton."""


def sam_answers(s):
    """Return (distinct_substring_count, longest_repeated_length)."""
    MAX = 2 * len(s) + 5
    nxt = [None] * MAX
    link = [-1] * MAX
    length = [0] * MAX
    cnt = [0] * MAX
    nxt[0] = {}
    last = 0
    size = 1
    for ch in s:
        cur = size
        size += 1
        nxt[cur] = {}
        length[cur] = length[last] + 1
        cnt[cur] = 1
        p = last
        while p != -1 and ch not in nxt[p]:
            nxt[p][ch] = cur
            p = link[p]
        if p == -1:
            link[cur] = 0
        else:
            q = nxt[p][ch]
            if length[p] + 1 == length[q]:
                link[cur] = q
            else:
                clone = size
                size += 1
                nxt[clone] = dict(nxt[q])
                length[clone] = length[p] + 1
                link[clone] = link[q]
                cnt[clone] = 0
                while p != -1 and nxt[p].get(ch) == q:
                    nxt[p][ch] = clone
                    p = link[p]
                link[q] = clone
                link[cur] = clone
        last = cur

    distinct = 0
    for v in range(1, size):
        distinct += length[v] - length[link[v]]

    order = sorted(range(1, size), key=lambda v: -length[v])
    for v in order:
        if link[v] > 0:
            cnt[link[v]] += cnt[v]
        elif link[v] == 0:
            pass  # root count irrelevant
    lrs = 0
    for v in range(1, size):
        if cnt[v] >= 2:
            lrs = max(lrs, length[v])
    return distinct, lrs


def brute(s):
    subs = set()
    n = len(s)
    for i in range(n):
        for j in range(i + 1, n + 1):
            subs.add(s[i:j])
    lrs = 0
    for L in range(n - 1, 0, -1):
        seen = set()
        found = False
        for i in range(n - L + 1):
            t = s[i:i + L]
            if t in seen:
                found = True
                break
            seen.add(t)
        if found:
            lrs = L
            break
    return len(subs), lrs


if __name__ == "__main__":
    import random
    rng = random.Random(7)
    for trial in range(60):
        n = rng.randint(1, 60)
        s = "".join(rng.choice("abc") for _ in range(n))
        assert sam_answers(s) == brute(s), (s, sam_answers(s), brute(s))
    for trial in range(20):
        n = rng.randint(50, 200)
        s = "".join(rng.choice("ab") for _ in range(n))
        assert sam_answers(s) == brute(s), s
    print("reference validated against brute force")
