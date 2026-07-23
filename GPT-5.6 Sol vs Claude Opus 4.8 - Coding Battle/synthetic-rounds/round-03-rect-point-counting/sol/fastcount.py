"""Fast offline rectangle point counting."""

from bisect import bisect_right


def count_points_in_rects(points, rects):
    """Count points in each inclusive axis-aligned rectangle.

    A rectangle count is expressed as four 2-D prefix counts.  Those prefix
    queries are answered together by sweeping from left to right and storing
    the swept points' y coordinates in a Fenwick tree.
    """
    rect_count = len(rects)
    if rect_count == 0:
        return []
    if not points:
        return [0] * rect_count

    sorted_points = sorted(points)
    ys = sorted({y for _, y in sorted_points})
    y_index = {y: i + 1 for i, y in enumerate(ys)}

    # (maximum x, maximum y, output index, coefficient)
    events = []
    append_event = events.append
    for i, (x1, y1, x2, y2) in enumerate(rects):
        append_event((x2, y2, i, 1))
        append_event((x1 - 1, y2, i, -1))
        append_event((x2, y1 - 1, i, -1))
        append_event((x1 - 1, y1 - 1, i, 1))
    events.sort()

    bit = [0] * (len(ys) + 1)
    answers = [0] * rect_count
    point_pos = 0
    point_count = len(sorted_points)
    bit_size = len(bit)
    br = bisect_right

    for max_x, max_y, output_index, coefficient in events:
        while point_pos < point_count and sorted_points[point_pos][0] <= max_x:
            y_pos = y_index[sorted_points[point_pos][1]]
            while y_pos < bit_size:
                bit[y_pos] += 1
                y_pos += y_pos & -y_pos
            point_pos += 1

        y_pos = br(ys, max_y)
        prefix_count = 0
        while y_pos:
            prefix_count += bit[y_pos]
            y_pos -= y_pos & -y_pos
        answers[output_index] += coefficient * prefix_count

    return answers
