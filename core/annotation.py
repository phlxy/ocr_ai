import os
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


class LayoutLMExporter:
    """
    คลาสสำหรับ Export ข้อมูล annotation ในรูปแบบที่ใช้กับ LayoutLMv3
    โดยข้อมูลที่ต้องใช้ประกอบด้วย:
      - current_document: dict ที่มี key 'pages' ซึ่งแต่ละหน้าเป็น dict
      - file_annotations: dict mapping image_path -> list of annotations (แต่ละ annotation เป็น dict ที่มี key 'coordinates' และ 'label')
      - doc_type_combo: widget (เช่น QComboBox) ที่มี method currentText() เพื่อให้ได้ประเภทเอกสาร
      - original_pixmap: QPixmap ของเอกสารต้นฉบับ (ใช้เพื่อดึง width และ height)
    """
    def __init__(self, current_document, file_annotations, doc_type_combo, original_pixmap):
        self.current_document = current_document
        self.file_annotations = file_annotations
        self.doc_type_combo = doc_type_combo
        self.original_pixmap = original_pixmap

    def export_layoutlm_format(self, directory) -> None:
        """Export ในรูปแบบที่ใช้กับ LayoutLMv3 โดยสร้างไฟล์ JSON สำหรับแต่ละหน้าที่มี annotations"""
        if self.current_document:
            for page in self.current_document['pages']:
                image_path = page['path']
                if image_path in self.file_annotations:
                    annotations = self.file_annotations[image_path]

                    # สร้างชื่อไฟล์
                    if page['type'] == 'pdf_page':
                        basename = f"{os.path.splitext(os.path.basename(page['original_path']))[0]}_page_{page['page']}"
                    else:
                        basename = os.path.splitext(os.path.basename(page['original_path']))[0]

                    json_name = f"{basename}_layoutlm.json"
                    save_path = os.path.join(directory, json_name)

                    # เตรียมข้อมูลสำหรับ LayoutLM
                    layoutlm_data = {
                        'image_path': image_path,
                        'original_path': page['original_path'],
                        'page_number': page.get('page', 1),
                        'document_type': self.doc_type_combo.currentText() if hasattr(self.doc_type_combo, "currentText") else "",
                        'width': self.original_pixmap.width() if self.original_pixmap else None,
                        'height': self.original_pixmap.height() if self.original_pixmap else None,
                        'layout': {
                            'bbox': [],        # [x1, y1, x2, y2] coordinates
                            'label': [],       # label ของแต่ละ bbox
                            'words': [],       # text ในแต่ละ box (สำหรับ OCR)
                            'segment_ids': [],  # group ID สำหรับ boxes ที่เกี่ยวข้องกัน
                            'confidence': []   # ค่าความเชื่อมั่น
                        }
                    }

                    # แปลง annotations เป็น format ของ LayoutLM
                    for ann in annotations:
                        coords = ann['coordinates']  # ควรเป็น dict ที่มี key: 'x1', 'y1', 'x2', 'y2'
                        bbox = [
                            coords['x1'],   # x1
                            coords['y1'],   # y1
                            coords['x2'],   # x2
                            coords['y2']    # y2
                        ]
                        layoutlm_data['layout']['bbox'].append(bbox)
                        layoutlm_data['layout']['label'].append(ann['label'])
                        layoutlm_data['layout']['words'].append("")  # เว้นว่างไว้สำหรับ OCR
                        layoutlm_data['layout']['segment_ids'].append(0)  # default group
                        layoutlm_data['layout']['confidence'].append(1.0)  # default confidence

                    # บันทึกไฟล์ JSON ลงใน directory ที่กำหนด
                    with open(save_path, 'w', encoding='utf-8') as f:
                        json.dump(layoutlm_data, f, ensure_ascii=False, indent=2)

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
    เช่น ตรวจสอบว่ามี annotation ซ้อนทับกันเกิน 80%
    """
    threshold = 0.8  # 80%
    n = len(annotations)
    for i in range(n):
        for j in range(i + 1, n):
            overlap = _calculate_overlap(annotations[i], annotations[j])
            if overlap > threshold:
                return (False, f"Annotations {i} and {j} overlap more than {threshold*100}%.")
    return (True, "Annotations are valid.")
