# project/gui/annotation_canvas.py

from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QSizePolicy
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPen, QColor
from PyQt6.QtGui import QPen, QColor, QWheelEvent

class AnnotationCanvas(QGraphicsView):
    def __init__(self, annotations, main_window=None, parent=None):
        super().__init__(parent)
        self.annotations = annotations  # List สำหรับเก็บ Annotation objects
        self.main_window = main_window  # เก็บอ้างอิงของ MainWindow
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
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
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
            # ใช้ default color ถ้า main_window.currentLabelColor ไม่ถูกกำหนด
            if self.main_window and hasattr(self.main_window, 'currentLabelColor') and self.main_window.currentLabelColor:
                pen_color = QColor(self.main_window.currentLabelColor)
            else:
                pen_color = QColor("red")
            pen = QPen(pen_color, 2)
            self.current_rect_item.setPen(pen)
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
            # ดึง label จาก MainWindow ถ้ามี
            label_text = ""
            if self.main_window and self.main_window.currentLabel:
                label_text = self.main_window.currentLabel
            # สมมุติว่าคุณมี Annotation object ที่รับ label และสามารถเก็บข้อมูลนี้ได้
            # (คุณอาจต้องแก้ไขคลาส Annotation ใน core/annotation.py ให้รับ color ด้วย)
            new_annotation = {"x": rect.x(), "y": rect.y(),
                              "width": rect.width(), "height": rect.height(),
                              "label": label_text,
                              "color": self.main_window.currentLabelColor if self.main_window else "#000000"}
            self.annotations.append(new_annotation)
            # วาดข้อความบนกล่อง annotation
            text_item = self.scene.addText(label_text)
            text_item.setDefaultTextColor(QColor(self.main_window.currentLabelColor if self.main_window else "#000000"))
            text_item.setPos(rect.x(), rect.y())
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
