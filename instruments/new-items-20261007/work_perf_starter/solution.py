def merge(intervals):
    if not isinstance(intervals, list):
        raise ValueError("intervals must be a list")
    pairs = []
    for item in intervals:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise ValueError("each interval must be a pair")
        start, end = item
        for value in (start, end):
            if not isinstance(value, int) or isinstance(value, bool):
                raise ValueError("bounds must be ints")
        if start > end:
            raise ValueError("start must not exceed end")
        pairs.append([start, end])
    # correct, but quadratic: every new interval is compared with every one already merged
    merged = []
    for pair in pairs:
        hit = False
        for existing in merged:
            if pair[0] <= existing[1] and existing[0] <= pair[1]:
                existing[0] = min(existing[0], pair[0])
                existing[1] = max(existing[1], pair[1])
                hit = True
                break
        if not hit:
            merged.append(pair)
    # overlapping chains can still be separate after the single pass; fix them up quadratically
    changed = True
    while changed:
        changed = False
        for index, pair in enumerate(merged):
            for other in merged[index + 1:]:
                if pair[0] <= other[1] and other[0] <= pair[1]:
                    pair[0] = min(pair[0], other[0])
                    pair[1] = max(pair[1], other[1])
                    other[0] = pair[0]
                    other[1] = pair[1]
                    changed = True
    unique = sorted({(p[0], p[1]) for p in merged})
    final = []
    for start, end in unique:
        if final and start <= final[-1][1]:
            if end > final[-1][1]:
                final[-1][1] = end
        else:
            final.append([start, end])
    return final
