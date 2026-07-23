"""Reference (correct but slow) implementation. Spec source of truth."""


def count_points_in_rects(points, rects):
    """points: list of (x, y) int tuples. rects: list of (x1, y1, x2, y2)
    with x1 <= x2, y1 <= y2. Returns list of ints: for each rect, the number
    of points with x1 <= x <= x2 and y1 <= y <= y2 (borders inclusive).
    """
    out = []
    for x1, y1, x2, y2 in rects:
        c = 0
        for x, y in points:
            if x1 <= x <= x2 and y1 <= y <= y2:
                c += 1
        out.append(c)
    return out
