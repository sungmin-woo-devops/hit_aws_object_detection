import cv2
import numpy as np
from typing import List, Dict

def draw_detections(image: np.ndarray, detections: Dict, class_names: List[str],
                    thickness: int = 2) -> np.ndarray:
    """Draw detection boxes and labels in image"""

    image_copy = image.copy()

    for box, score, class_id in zip(detections['boxes'], detections['scores'], detections['class_ids']):
        x1, y1, x2, y2 = map(int, box)
        
        class_name = class_names[int(class_id)] if int(class_id) < len(class_names) else f'Class_{int(class_id)}'
        
        color = get_class_color(class_name)

        cv2.rectangle(image_copy, (x1, y1), (x2, y2), color, thickness)

        label = f'{class_name}: {score: .2f}'
        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]

        cv2.rectangle(image_copy, (x1, y1 - label_size[1] - 10), (x1 + label_size[0], y1), color, -1)

        cv2.putText(image_copy, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    return image_copy


def get_class_color(class_id: int) -> tuple:
    """Get color for specific class"""
    colors = [
        (255, 0, 0),    # Red
        (0, 255, 0),    # Green
        (0, 0, 255),    # Blue
        (255, 255, 0),  # Yellow
        (255, 0, 255),  # Magenta
        (0, 255, 255),  # Cyan
        (128, 0, 128),  # Purple
        (255, 165, 0),  # Orange
        (128, 128, 128), # Gray
        (255, 192, 203), # Pink
    ]
    
    return colors[class_id % len(colors)]
