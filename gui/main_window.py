from PyQt6.QtWidgets import (
    QMainWindow, QApplication, QFileDialog, QMessageBox, QVBoxLayout,
    QWidget, QMenu, QSplitter
)
from PyQt6.QtGui import QAction, QPixmap
from PyQt6.QtCore import QTimer, Qt
from core.document_handler import DocumentHandler
from core.autosave import AutoSaveManager
from core.annotation import export_annotations, validate_annotations, export_layoutlm_format
from gui.annotation_canvas import AnnotationCanvas
from gui.pdf_list_widget import PdfListWidget  # Widget สำหรับแสดง thumbnail ของ PDF
from core.pdf_utils import pdf_to_pixmap_list  # ฟังก์ชันแปลง PDF เป็น QPixmap list

from concurrent.futures import ProcessPoolExecutor
from core.annotation import validate_annotations as core_validate_annotations

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Annotation Tool")
        # Attribute สำหรับติดตามไฟล์ปัจจุบัน
        self.currentFile = None
        # Flag สำหรับติดตามงานที่ยังไม่ได้บันทึก
        self.unsavedChanges = False
        self.document_handler = DocumentHandler()
        self.annotations = []  # เก็บ Annotation objects ของ core
        self.autosave_manager = AutoSaveManager()
        
        # สร้าง AnnotationCanvas สำหรับแสดงภาพเพื่อทำ annotation
        self.canvas = AnnotationCanvas(self.annotations)
        
        # QSplitter แบ่งพื้นที่เป็น 2 ส่วน (แนวนอน)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.canvas)  # ด้านขวา: AnnotationCanvas
        # ด้านซ้ายสำหรับ PdfListWidget จะถูกเพิ่มเมื่อเปิดไฟล์ PDF
        
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.splitter)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        # Status Bar สำหรับแสดงค่า Zoom
        self.statusBar().showMessage("Zoom: 100%")
        
        self.create_menu()
        
        self.executor = ProcessPoolExecutor()
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.perform_auto_save)
        self.autosave_timer.start(300000)  # ทุก 5 นาที

    def create_menu(self):
        menu_bar = self.menuBar()
        
        # File Menu
        file_menu = menu_bar.addMenu("File")
        open_action = QAction("Open", self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        export_action = QAction("Export Annotations (JSON)", self)
        export_action.triggered.connect(self.export_annotations)
        file_menu.addAction(export_action)
        
        export_layoutlm_action = QAction("Export for LayoutLMv3", self)
        export_layoutlm_action.triggered.connect(self.export_layoutlm_format)
        file_menu.addAction(export_layoutlm_action)
        
        # Edit Menu (สำหรับ Undo)
        edit_menu = menu_bar.addMenu("Edit")
        undo_action = QAction("Undo", self)
        undo_action.triggered.connect(self.undo_annotation)
        edit_menu.addAction(undo_action)
        
        # View Menu สำหรับ Zoom In/Out
        view_menu = menu_bar.addMenu("View")
        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)
        
        # Tools Menu สำหรับ Validate
        tools_menu = menu_bar.addMenu("Tools")
        validate_action = QAction("Validate Annotations", self)
        validate_action.triggered.connect(self.start_validation)
        tools_menu.addAction(validate_action)

    def update_zoom_status(self):
        zoom_factor = self.canvas._zoom_step ** self.canvas._zoom
        percentage = int(zoom_factor * 100)
        self.statusBar().showMessage(f"Zoom: {percentage}%")

    def on_pdf_page_selected(self, index: int):
        """
        เมื่อผู้ใช้เลือกหน้าจาก PdfListWidget
        ให้ดึง QPixmap แบบเต็มความละเอียดจาก self.pdf_pixmap_list ตาม index แล้วแสดงใน AnnotationCanvas
        """
        try:
            if index < 0 or index >= len(self.pdf_pixmap_list):
                return
            full_pixmap = self.pdf_pixmap_list[index]
            self.canvas.setImage(full_pixmap)
            self.canvas.resetTransform()
            self.canvas._zoom = 0
            self.update_zoom_status()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def zoom_in(self):
        if self.canvas._zoom < self.canvas._max_zoom:
            self.canvas.scale(self.canvas._zoom_step, self.canvas._zoom_step)
            self.canvas._zoom += 1
            self.update_zoom_status()

    def zoom_out(self):
        if self.canvas._zoom > self.canvas._min_zoom:
            self.canvas.scale(1 / self.canvas._zoom_step, 1 / self.canvas._zoom_step)
            self.canvas._zoom -= 1
            self.update_zoom_status()

    def undo_annotation(self):
        self.canvas.undoLastAnnotation()

    def export_annotations(self):
        json_data = export_annotations(self.annotations)
        QMessageBox.information(self, "Exported JSON", json_data)

    def export_layoutlm_format(self):
        json_data = export_layoutlm_format(self.annotations)
        QMessageBox.information(self, "Exported LayoutLM Format", json_data)

    def start_validation(self):
        future = self.executor.submit(core_validate_annotations, self.annotations)
        future.add_done_callback(self.validation_callback)

    def validation_callback(self, future):
        result = future.result()
        QTimer.singleShot(0, lambda: self.show_validation_result(result))

    def show_validation_result(self, result):
        valid, message = result
        if valid:
            QMessageBox.information(self, "Validation", "All annotations are valid.")
        else:
            QMessageBox.warning(self, "Validation Error", message)

    def perform_auto_save(self):
        self.autosave_manager.auto_save(self.document_handler, self.annotations)

    def prompt_save_changes(self):
        """
        แสดง dialog ถามผู้ใช้ว่าต้องการบันทึกงานที่ยังไม่ได้บันทึกหรือไม่
        คืนค่าตัวเลือกของผู้ใช้:
          - QMessageBox.StandardButton.Yes: บันทึก
          - QMessageBox.StandardButton.No: ไม่บันทึก
          - QMessageBox.StandardButton.Cancel: ยกเลิก
        """
        msgBox = QMessageBox(self)
        msgBox.setIcon(QMessageBox.Icon.Warning)
        msgBox.setWindowTitle("บันทึกงาน")
        msgBox.setText("คุณมีงานที่ยังไม่ได้บันทึก\nต้องการบันทึกหรือไม่?")
        msgBox.setStandardButtons(
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No |
            QMessageBox.StandardButton.Cancel
        )
        msgBox.setDefaultButton(QMessageBox.StandardButton.Yes)
        return msgBox.exec()
    
    def save_current_file(self):
        """
        ฟังก์ชันสำหรับบันทึกงานปัจจุบัน
        (ปรับปรุงได้ตามรูปแบบที่ต้องการ)
        """
        filepath, _ = QFileDialog.getSaveFileName(self, "Save File", "", "JSON Files (*.json)")
        if filepath:
            json_data = export_annotations(self.annotations)
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(json_data)
                self.unsavedChanges = False
                self.currentFile = filepath
                return True
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving file: {e}")
                return False
        return False

    def clear_ui(self):
        """
        เคลียร์เฉพาะข้อมูล annotation ใน AnnotationCanvas และ annotation list
        (ไม่ลบโครงสร้าง UI เช่น panel thumbnail)
        """
        self.annotations.clear()
        self.canvas.scene.clear()
        self.currentFile = None
        self.unsavedChanges = False

    def open_file(self):
        """
        เมื่อผู้ใช้เปิดไฟล์ใหม่ ให้ตรวจสอบงานที่ยังไม่ได้บันทึกก่อน
        หากมีงานที่ยังไม่ได้บันทึก:
          - ถ้าเลือก Yes: บันทึกก่อนเปิดไฟล์ใหม่ (หากบันทึกล้มเหลวให้หยุด)
          - ถ้าเลือก No: เคลียร์เฉพาะข้อมูล annotation แล้วดำเนินการเปิดไฟล์ใหม่
          - ถ้าเลือก Cancel: ยกเลิกการเปิดไฟล์ใหม่
        จากนั้นโหลดไฟล์ใหม่ (PDF หรือรูปภาพ) โดยยังคงมี panel thumbnail (สำหรับ PDF) และ canvas สำหรับ annotate อยู่ใน UI เดิม
        """
        if self.unsavedChanges:
            result = self.prompt_save_changes()
            if result == QMessageBox.StandardButton.Yes:
                if not self.save_current_file():
                    return  # หากบันทึกไม่สำเร็จ
            elif result == QMessageBox.StandardButton.Cancel:
                return  # ยกเลิกเปิดไฟล์ใหม่
            # หากเลือก No ให้เคลียร์เฉพาะข้อมูล annotation
            self.annotations.clear()
            self.canvas.scene.clear()
        
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", "Images (*.png *.jpg *.bmp);;PDF Files (*.pdf)"
        )
        if filepath:
            try:
                ext = filepath.split('.')[-1].lower()
                if ext == "pdf":
                    # แปลง PDF เป็น QPixmap แบบ full resolution แล้วเก็บไว้ใน attribute
                    self.pdf_pixmap_list = pdf_to_pixmap_list(filepath)
                    if not self.pdf_pixmap_list:
                        raise Exception("ไม่พบหน้าที่สามารถแปลงเป็นภาพได้")
                    # สร้าง PdfListWidget สำหรับแสดง thumbnail
                    pdf_list_widget = PdfListWidget(self.pdf_pixmap_list)
                    pdf_list_widget.setFixedWidth(200)
                    pdf_list_widget.pageSelected.connect(self.on_pdf_page_selected)
                    if self.splitter.count() == 1:
                        self.splitter.insertWidget(0, pdf_list_widget)
                    else:
                        self.splitter.widget(0).deleteLater()
                        self.splitter.insertWidget(0, pdf_list_widget)
                    self.splitter.setStretchFactor(0, 0)
                    self.splitter.setStretchFactor(1, 1)
                    # แสดงหน้ากระดาษแรกใน AnnotationCanvas
                    self.canvas.setImage(self.pdf_pixmap_list[0])
                else:
                    # กรณีเปิดไฟล์รูปภาพ
                    self.document_handler.load_image(filepath)
                    pixmap = QPixmap(filepath)
                    self.canvas.setImage(pixmap)
                self.canvas.resetTransform()
                self.canvas._zoom = 0
                self.update_zoom_status()
                self.currentFile = filepath
                self.unsavedChanges = True
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))


def main():
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
