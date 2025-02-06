import os
import pytest
from core.document_handler import DocumentHandler
from core.annotation import Annotation, validate_annotations
from core.autosave import AutoSaveManager
from gui.annotation_canvas import AnnotationCanvas
from PyQt6.QtCore import Qt
from pytestqt.qtbot import QtBot

def test_integration_core_and_gui(qtbot, tmp_path):
    # เตรียม core components
    handler = DocumentHandler()
    handler.filepath = "dummy_image.png"  # กำหนด filepath จำลอง
    
    annotations = []
    
    # สร้าง GUI component สำหรับวาด Annotation
    canvas = AnnotationCanvas(annotations)
    qtbot.addWidget(canvas)
    canvas.show()
    
    # จำลองการวาด annotation จาก (10,10) ถึง (50,50)
    start = canvas.mapFromScene(10, 10)
    end = canvas.mapFromScene(50, 50)
    qtbot.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, pos=start)
    qtbot.mouseMove(canvas.viewport(), pos=end)
    qtbot.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, pos=end)
    
    # ตรวจสอบว่ามี annotation หนึ่งอันใน list
    assert len(annotations) == 1
    
    # ใช้ core validate annotations
    valid, message = validate_annotations(annotations)
    assert valid
    
    # ทดสอบ auto-save integration
    autosave_path = tmp_path / "autosave.json"
    autosave_manager = AutoSaveManager(str(autosave_path))
    autosave_manager.auto_save(handler, annotations)
    assert os.path.exists(autosave_path)
