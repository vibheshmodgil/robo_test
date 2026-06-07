class MovementAnalyzer:

    def __init__(self):

        self.previous_positions = {}

    def analyze(self, detections):
        moved_objects = []
        for detection in detections:
            label = detection["label"]
            x1, y1, x2, y2 = detection["bbox"]
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            current_position = (
                center_x,
                center_y
            )
            if label in self.previous_positions:
                old_x, old_y = self.previous_positions[label]
                distance = abs(center_x - old_x) + abs(center_y - old_y)
                if distance > 5:
                    moved_objects.append(label)

            self.previous_positions[label] = \
                current_position

        return moved_objects