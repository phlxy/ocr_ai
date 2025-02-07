# project/gui/annotation_canvas.py

from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPen, QColor
from PyQt6.QtGui import QPen, QColor, QWheelEvent

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

        # กำหนดค่าเริ่มต้นสำหรับ zoom factor
        self._zoom = 0
        self._zoom_step = 1.25  # ปัจจัยเพิ่ม/ลดการ zoom
        self._max_zoom = 10
        self._min_zoom = -10

        # เก็บรายการ QGraphicsRectItem ที่ถูกวาดเสร็จแล้ว
        self.annotation_items = []
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    def setImage(self, pixmap):
        self.scene.clear()  # ล้าง scene ก่อน (ถ้าต้องการ)
        self.scene.addPixmap(pixmap)
        from PyQt6.QtCore import QRectF
        self.setSceneRect(QRectF(pixmap.rect()))
        # รีเซ็ต transform และ zoom เมื่อโหลดภาพใหม่
        self.resetTransform()
        self._zoom = 1  # กำหนดค่า zoom เริ่มต้น
        # ล้าง annotation_items เมื่อโหลดภาพใหม่
        self.annotation_items.clear()

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
            from core.annotation import Annotation  # Import ณ จุดนี้เพื่อหลีกเลี่ยง circular dependency
            new_annotation = Annotation(rect.x(), rect.y(), rect.width(), rect.height(), label="")
            self.annotations.append(new_annotation)
            # บันทึก item ที่วาดเสร็จแล้วลงใน annotation_items
            self.annotation_items.append(self.current_rect_item)
            self.current_rect_item = None
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event: QWheelEvent):
        # ตรวจสอบว่าผู้ใช้หมุนเมาส์เพื่อ zoom เข้า/ออก
        angle = event.angleDelta().y()
        if angle > 0 and self._zoom < self._max_zoom:
            factor = self._zoom_step
            self._zoom += 1
        elif angle < 0 and self._zoom > self._min_zoom:
            factor = 1 / self._zoom_step
            self._zoom -= 1
        else:
            # หากถึงขีดจำกัดแล้ว ไม่ทำการ zoom
            return
        self.scale(factor, factor)

    def undoLastAnnotation(self):
        """
        ลบ Annotation ล่าสุดออกจาก scene และ list
        """
        if self.annotation_items:
            # ลบ QGraphicsRectItem ล่าสุดจาก scene
            last_item = self.annotation_items.pop()
            self.scene.removeItem(last_item)
            # ลบ Annotation object ล่าสุดจาก list
            if self.annotations:
                self.annotations.pop()
