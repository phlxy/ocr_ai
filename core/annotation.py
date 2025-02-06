# project/core/annotation.py

import json

class Annotation:
    def __init__(self, x: float, y: float, width: float, height: float, label: str):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.label = label
    
    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "label": self.label
        }
    
    def __repr__(self):
        return f"Annotation({self.x}, {self.y}, {self.width}, {self.height}, {self.label})"

def export_annotations(annotations: list) -> str:
    """
    ส่งออก Annotation เป็น JSON string
    """
    return json.dumps([anno.to_dict() for anno in annotations], indent=4)

def export_layoutlm_format(annotations: list) -> str:
    """
    ส่งออก Annotation ในรูปแบบที่รองรับ LayoutLMv3
    """
    layoutlm_data = {
        "annotations": [anno.to_dict() for anno in annotations],
        "metadata": {
            "exported_format": "LayoutLMv3"
        }
    }
    return json.dumps(layoutlm_data, indent=4)

def _calculate_overlap(anno1: Annotation, anno2: Annotation) -> float:
    """
    คำนวณเปอร์เซ็นต์การซ้อนทับระหว่าง annotation 2 อัน
    คืนค่าเป็น float ระหว่าง 0.0 ถึง 1.0
    """
    x_left = max(anno1.x, anno2.x)
    y_top = max(anno1.y, anno2.y)
    x_right = min(anno1.x + anno1.width, anno2.x + anno2.width)
    y_bottom = min(anno1.y + anno1.height, anno2.y + anno2.height)
    
    if x_right < x_left or y_bottom < y_top:
        return 0.0
    overlap_area = (x_right - x_left) * (y_bottom - y_top)
    area1 = anno1.width * anno1.height
    area2 = anno2.width * anno2.height
    return overlap_area / min(area1, area2)

def validate_annotations(annotations: list) -> (bool, str):
    """
    ตรวจสอบความถูกต้องของ Annotation
    เช่น ตรวจสอบการซ้อนทับเกิน 80%
    """
    threshold = 0.8  # 80%
    n = len(annotations)
    for i in range(n):
        for j in range(i + 1, n):
            overlap = _calculate_overlap(annotations[i], annotations[j])
            if overlap > threshold:
                return (False, f"Annotations {i} and {j} overlap more than {threshold*100}%.")
    return (True, "Annotations are valid.")
