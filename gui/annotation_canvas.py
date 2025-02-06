# project/gui/annotation_canvas.py

from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPen, QColor

class AnnotationCanvas(QGraphicsView):
    def __init__(self, annotations, parent=None):
        super().__init__(parent)
        self.annotations = annotations  # List สำหรับเก็บ Annotation objects
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # สำหรับวาด Annotation ใหม่
        self.current_rect_item = None
        self.start_pos = None
        self.pen = QPen(QColor(255, 0, 0), 2)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = self.mapToScene(event.position().toPoint())
            self.current_rect_item = QGraphicsRectItem(QRectF(self.start_pos, self.start_pos))
            self.current_rect_item.setPen(self.pen)
            self.scene.addItem(self.current_rect_item)
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if self.current_rect_item is not None:
            current_pos = self.mapToScene(event.position().toPoint())
            rect = QRectF(self.start_pos, current_pos).normalized()
            self.current_rect_item.setRect(rect)
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        if self.current_rect_item is not None:
            rect = self.current_rect_item.rect()
            from core.annotation import Annotation  # import ณ จุดนี้เพื่อหลีกเลี่ยง circular dependency
            new_annotation = Annotation(rect.x(), rect.y(), rect.width(), rect.height(), label="")
            self.annotations.append(new_annotation)
            self.current_rect_item = None
        super().mouseReleaseEvent(event)
