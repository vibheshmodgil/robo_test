# app/trackers/target_tracker.py

import time


def _iou(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)
    iw = max(0, ix2 - ix1)
    ih = max(0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)
    return inter / float(area_a + area_b - inter)


def _center(b):
    return ((b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0)


def _center_dist(a, b):
    ca, cb = _center(a), _center(b)
    return ((ca[0] - cb[0]) ** 2 + (ca[1] - cb[1]) ** 2) ** 0.5


def _diag(b):
    return ((b[2] - b[0]) ** 2 + (b[3] - b[1]) ** 2) ** 0.5


class Track:
    def __init__(self, track_id, bbox):
        self.id = track_id
        self.bbox = bbox
        self.last_seen = time.time()
        self.hits = 1

    def update(self, bbox):
        self.bbox = bbox
        self.last_seen = time.time()
        self.hits += 1

    def area(self):
        x1, y1, x2, y2 = self.bbox
        return (x2 - x1) * (y2 - y1)


class TargetTracker:
    """Stable IDs for faces + locks the gimbal onto exactly ONE of them."""

    def __init__(self, iou_threshold=0.3, max_age=0.8, min_hits=3, max_shift=1.4):
        self.tracks = {}
        self.next_id = 0
        self.iou_threshold = iou_threshold
        self.max_age = max_age      # seconds a lost face stays alive (re-acquire window)
        self.min_hits = min_hits    # frames before a face can become the target
        self.max_shift = max_shift  # allowed centre jump as a multiple of face diagonal;
                                    # lower it if IDs swap between two nearby faces
        self.locked_id = None

    def _best_match(self, tr, boxes, unmatched):
        # On a moving gimbal a pan/tilt slews EVERY face across the frame between
        # frames, so plain IOU often drops below threshold and the lock is lost.
        # Accept a detection if it overlaps (IOU) OR its centre is within a
        # size-scaled radius of where the track was -> the lock survives motion.
        gate = self.max_shift * _diag(tr.bbox)
        best_j, best_iou, best_dist = -1, 0.0, float("inf")
        for j in unmatched:
            iou = _iou(tr.bbox, boxes[j])
            dist = _center_dist(tr.bbox, boxes[j])
            if iou < self.iou_threshold and dist > gate:
                continue
            # prefer stronger overlap; among non-overlapping, prefer the nearest
            if iou > best_iou or (iou == best_iou and dist < best_dist):
                best_j, best_iou, best_dist = j, iou, dist
        return best_j

    def update(self, detections):
        now = time.time()
        boxes = [d["bbox"] for d in detections]
        assigned = [None] * len(boxes)      # detection index -> track id
        unmatched = set(range(len(boxes)))

        # locked track gets first pick so it stays sticky through clutter
        order = sorted(self.tracks, key=lambda t: t != self.locked_id)

        for tid in order:
            tr = self.tracks[tid]
            best_j = self._best_match(tr, boxes, unmatched)
            if best_j >= 0:
                tr.update(boxes[best_j])
                assigned[best_j] = tid
                unmatched.discard(best_j)

        for j in unmatched:
            tid = self.next_id
            self.tracks[tid] = Track(tid, boxes[j])
            assigned[j] = tid
            self.next_id += 1

        for tid in list(self.tracks):
            if now - self.tracks[tid].last_seen > self.max_age:
                del self.tracks[tid]

        # re-lock only if our target is gone
        if self.locked_id not in self.tracks:
            self.locked_id = self._acquire()

        # tag detections in place so the drawer (and anything downstream) has an id
        for det, tid in zip(detections, assigned):
            det["id"] = tid
            det["locked"] = (tid == self.locked_id)

        return self.tracks, self.locked_id

    def _acquire(self):
        # biggest confirmed face = nearest / most prominent person
        candidates = [t for t in self.tracks.values() if t.hits >= self.min_hits]
        if not candidates:
            return None
        return max(candidates, key=lambda t: t.area()).id

    # manual override if you ever want it
    def lock(self, track_id):
        if track_id in self.tracks:
            self.locked_id = track_id

    def unlock(self):
        self.locked_id = None