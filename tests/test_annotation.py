import pytest
import json
from core.annotation import (
    Annotation,
    export_annotations,
    export_layoutlm_format,
    validate_annotations,
    _calculate_overlap,
)

def test_annotation_to_dict():
    anno = Annotation(10, 20, 30, 40, "Test")
    d = anno.to_dict()
    assert d["x"] == 10
    assert d["y"] == 20
    assert d["width"] == 30
    assert d["height"] == 40
    assert d["label"] == "Test"

def test_export_annotations():
    annotations = [Annotation(0, 0, 10, 10, "A"), Annotation(10, 10, 20, 20, "B")]
    json_data = export_annotations(annotations)
    data = json.loads(json_data)
    assert isinstance(data, list)
    assert len(data) == 2

def test_export_layoutlm_format():
    annotations = [Annotation(0, 0, 10, 10, "A")]
    json_data = export_layoutlm_format(annotations)
    data = json.loads(json_data)
    assert "annotations" in data
    assert "metadata" in data
    assert data["metadata"]["exported_format"] == "LayoutLMv3"

def test_validate_annotations_valid():
    # สอง annotation ที่ไม่ซ้อนทับกัน
    annotations = [Annotation(0, 0, 10, 10, "A"), Annotation(20, 20, 10, 10, "B")]
    valid, message = validate_annotations(annotations)
    assert valid
    assert "valid" in message.lower()

def test_validate_annotations_invalid():
    # สอง annotation ที่ซ้อนทับกันเกิน 80%
    # Annotation A: (0, 0, 20, 20) -> พื้นที่ 400
    # Annotation B: (1, 1, 20, 20) -> พื้นที่ 400
    # พื้นที่ซ้อนทับ: จาก (1,1) ถึง (20,20) = 19x19 = 361, ratio = 361/400 = 0.9025 (90.25%)
    annotations = [Annotation(0, 0, 20, 20, "A"), Annotation(1, 1, 20, 20, "B")]
    valid, message = validate_annotations(annotations)
    assert not valid


def test_calculate_overlap():
    a1 = Annotation(0, 0, 10, 10, "A")
    a2 = Annotation(5, 5, 10, 10, "B")
    overlap = _calculate_overlap(a1, a2)
    # พื้นที่ซ้อนทับ: intersection จาก (5,5) ถึง (10,10) => พื้นที่ = 25; พื้นที่เล็กที่สุด = 100
    assert abs(overlap - 0.25) < 0.01
