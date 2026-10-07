"""Suggest an axis rectangle from long neutral-coloured rules in a chart.

Suggestions are never automatically accepted as calibration.
"""
import numpy as np


def detect_plot_box(image, allow_open_axes=False):
    rgb = np.asarray(image.convert('RGB'), dtype=np.int16)
    h, w = rgb.shape[:2]
    # Exclude coloured fans and decorative blue borders, and pale backgrounds.
    neutral = (rgb.max(axis=2)-rgb.min(axis=2) <= 24) & (rgb.mean(axis=2) < 225)
    horizontal = neutral.copy()
    horizontal[1:] |= neutral[:-1]
    horizontal[:-1] |= neutral[1:]
    rows = []
    for y in range(round(.10*h), round(.96*h)):
        row = horizontal[y]
        edges = np.diff(np.r_[False, row, False].astype(np.int8))
        starts, ends = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)
        if not len(starts):
            continue
        # Bridge tiny gaps where a coloured curve crosses an axis rule.
        merged = []
        for start, end in zip(starts, ends):
            if merged and start-merged[-1][1] <= 5:
                merged[-1][1] = end
            else:
                merged.append([start, end])
        starts, ends = np.array(merged).T
        index = np.argmax(ends-starts)
        if ends[index]-starts[index] >= .50*w:
            rows.append((y, int(starts[index]), int(ends[index]-1)))
    # Collapse anti-aliased/thick horizontal rules to a single centre row.
    groups = []
    for row in rows:
        if groups and row[0] <= groups[-1][-1][0]+1:
            groups[-1].append(row)
        else:
            groups.append([row])
    rules = [tuple(np.median(group, axis=0).astype(int)) for group in groups]
    best = None
    for top_index, (top, left1, right1) in enumerate(rules):
        for bottom, left2, right2 in rules[top_index+1:]:
            if bottom-top < .20*h:
                continue
            if abs(left1-left2) > .08*w or abs(right1-right2) > .08*w:
                continue
            sides = []
            for target in ((left1+left2)/2, (right1+right2)/2):
                low=max(0,round(target-.045*w));high=min(w,round(target+.045*w)+1)
                scores=neutral[top:bottom+1,low:high].mean(axis=0)
                maximum=float(scores.max())
                candidates=np.flatnonzero(scores >= maximum-.005)+low
                x=float(np.median(candidates))
                sides.append((x,maximum))
            (left, ls), (right, rs)=sides
            if min(ls,rs)<.55 or right-left<.50*w:
                continue
            # The largest supported rectangle excludes interior grid lines.
            score=(right-left)*(bottom-top)*min(ls,rs)
            if best is None or score>best[0]:
                best=(score,[left,float(top),right,float(bottom)])
    if best is not None:
        return best[1]
    if not allow_open_axes:
        return None
    # Some central banks draw only a left axis and a bottom baseline. Infer
    # the other two sides from the axis endpoints; acceptance remains manual.
    candidates = []
    for bottom, left_hint, right in rules:
        if bottom < .35*h:
            continue
        for x in range(max(0,left_hint-round(.04*w)), min(w,left_hint+round(.06*w))):
            column=neutral[:bottom+1,x]
            changes=np.diff(np.r_[False,column,False].astype(np.int8))
            starts,ends=np.flatnonzero(changes==1),np.flatnonzero(changes==-1)
            for top,end in zip(starts,ends):
                if end >= bottom-2 and bottom-top >= .20*h and right-x >= .50*w:
                    candidates.append(((right-x)*(bottom-top),x,int(top),right,bottom))
    if not candidates:
        return None
    best=max(candidates)
    # Centre a multi-pixel vertical rule rather than choosing its outer edge.
    _,x,top,right,bottom=best
    matching=[c[1] for c in candidates if abs(c[1]-x)<=8 and c[2:]==best[2:]]
    return [float(np.median(matching)),float(top),float(right),float(bottom)]
