import pytest
from PyQt6.QtCore import Qt
from gui.annotation_canvas import AnnotationCanvas

# ใช้ fixture qtbot (จาก pytest-qt) เพื่อควบคุม widget
@pytest.fixture
def canvas(qtbot):
    annotations = []
    widget = AnnotationCanvas(annotations)
    qtbot.addWidget(widget)
    widget.show()
    return widget, annotations

def test_annotation_drawing(qtbot, canvas):
    widget, annotations = canvas
    # สมมุติให้วาดสี่เหลี่ยมจาก (10,10) ถึง (50,50) ใน Scene coordinates
    start_pos = widget.mapFromScene(10, 10)
    mid_pos = widget.mapFromScene(30, 30)
    end_pos = widget.mapFromScene(50, 50)
    
    qtbot.mousePress(widget.viewport(), Qt.MouseButton.LeftButton, pos=start_pos)
    qtbot.mouseMove(widget.viewport(), pos=mid_pos)
    qtbot.mouseMove(widget.viewport(), pos=end_pos)
    qtbot.mouseRelease(widget.viewport(), Qt.MouseButton.LeftButton, pos=end_pos)
    
    # ตรวจสอบว่า annotation ถูกเพิ่มเข้าไปใน list
    assert len(annotations) == 1
    anno = annotations[0]
    # ตรวจสอบตำแหน่งและขนาด (ค่าอาจมีความคลาดเคลื่อนเล็กน้อย)
    assert anno.x == pytest.approx(10, abs=1)
    assert anno.y == pytest.approx(10, abs=1)
    assert anno.width == pytest.approx(40, abs=1)
    assert anno.height == pytest.approx(40, abs=1)
