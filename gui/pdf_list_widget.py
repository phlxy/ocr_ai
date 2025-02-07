from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QWidget, QVBoxLayout
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize, pyqtSignal, Qt

class PdfListWidget(QWidget):
    # ประกาศ signal ที่ส่งค่า index ของหน้าที่เลือก
    pageSelected = pyqtSignal(int)

    def __init__(self, pixmap_list, parent=None):
        super().__init__(parent)
        # pixmap_list นี้ควรเป็นรายชื่อ QPixmap แบบ full resolution
        self.pixmap_list = pixmap_list  
        self.list_widget = QListWidget()
        self.init_ui()

    def init_ui(self):
        # กำหนดขนาดของ icon สำหรับ thumbnail
        self.list_widget.setIconSize(QSize(100, 100))
        for i, pixmap in enumerate(self.pixmap_list):
            # สร้าง thumbnail โดย scaling QPixmap ลง
            thumbnail = pixmap.scaled(QSize(100, 100), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            item = QListWidgetItem(QIcon(thumbnail), f"Page {i+1}")
            self.list_widget.addItem(item)

        layout = QVBoxLayout()
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

        # เมื่อมีการเปลี่ยนแถวที่เลือก ส่งค่า index ผ่าน signal pageSelected
        self.list_widget.currentRowChanged.connect(self.pageSelected.emit)
