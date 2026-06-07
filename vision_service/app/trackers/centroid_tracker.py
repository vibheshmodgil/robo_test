from app.interfaces.tracker_intefrace import TrackerInterface

class CentroidTracker(TrackerInterface):

    def track(self, detections):

        tracked = []

        for idx, detection in enumerate(detections):

            detection["id"] = idx

            tracked.append(detection)

        return tracked