"""Fast 2D rectangle point-counting (borders inclusive).

Offline sweep on x with a Fenwick tree over compressed y-coordinates.
For each rect [x1,x2] x [y1,y2] the answer is decomposed via 2D prefix
counts A(X,Y) = #points with px<=X and py<=Y:

    count = A(x2, y2) - A(x1-1, y2) - A(x2, y1-1) + A(x1-1, y1-1)
"""

from bisect import bisect_right, bisect_left


def count_points_in_rects(points, rects):
    n = len(points)
    m = len(rects)
    out = [0] * m
    if n == 0 or m == 0:
        return out

    # Compress point y-coordinates.
    ys = sorted({p[1] for p in points})
    ysize = len(ys)

    # Fenwick tree (1-indexed) over compressed y.
    tree = [0] * (ysize + 1)

    def fen_add(i):
        i += 1
        while i <= ysize:
            tree[i] += 1
            i += i & (-i)

    def fen_sum(i):
        # prefix sum of ranks [0, i) i.e. first i entries; i in [0, ysize]
        s = 0
        while i > 0:
            s += tree[i]
            i -= i & (-i)
        return s

    # Points sorted by x, precompute compressed y-rank.
    pts = sorted(points)  # sorts by x then y
    pxs = [p[0] for p in pts]
    pranks = [bisect_left(ys, p[1]) for p in pts]

    # Build corner queries: (X, Y, rect_index, sign)
    # A(X,Y): count points with px<=X and py<=Y.
    # Y bound converted to a fenwick prefix length = bisect_right(ys, Y).
    queries = []
    for ri, (x1, y1, x2, y2) in enumerate(rects):
        # prefix lengths for y bounds
        yhi = bisect_right(ys, y2)      # py <= y2
        ylo = bisect_right(ys, y1 - 1)  # py <= y1-1
        # x bounds
        queries.append((x2, yhi, ri, 1))
        queries.append((x2, ylo, ri, -1))
        queries.append((x1 - 1, yhi, ri, -1))
        queries.append((x1 - 1, ylo, ri, 1))

    # Sort queries by X so we can sweep alongside sorted points.
    queries.sort(key=lambda q: q[0])

    pi = 0
    for X, ylen, ri, sign in queries:
        if X < 0:
            continue  # A(X,*) = 0 when no point has px <= X
        # Insert all points with px <= X.
        while pi < n and pxs[pi] <= X:
            fen_add(pranks[pi])
            pi += 1
        if ylen > 0:
            out[ri] += sign * fen_sum(ylen)

    return out
