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
        pairs.append((start, end))
    if not pairs:
        return []
    pairs.sort()
    out = [list(pairs[0])]
    for start, end in pairs[1:]:
        if start <= out[-1][1]:
            if end > out[-1][1]:
                out[-1][1] = end
        else:
            out.append([start, end])
    return out
