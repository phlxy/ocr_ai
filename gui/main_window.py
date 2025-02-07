from PyQt6.QtWidgets import (
    QMainWindow, QApplication, QFileDialog, QMessageBox, QVBoxLayout,
    QWidget, QMenu, QSplitter,QComboBox ,QToolBar
)
from PyQt6.QtGui import QAction, QPixmap
from PyQt6.QtCore import QTimer, Qt
from core.document_handler import DocumentHandler
from core.autosave import AutoSaveManager
from core.annotation import export_annotations, validate_annotations
from core.annotation import LayoutLMExporter
from gui.annotation_canvas import AnnotationCanvas
from gui.pdf_list_widget import PdfListWidget  # Widget สำหรับแสดง thumbnail ของ PDF
from core.pdf_utils import pdf_to_pixmap_list  # ฟังก์ชันแปลง PDF เป็น QPixmap list
from core.document_types import DOCUMENT_TYPES  # นำเข้าข้อมูลประเภทเอกสาร

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

        # เพิ่ม attribute สำหรับประเภทเอกสารและ Label
        self.currentDocType = None
        self.currentLabel = None
        self.currentLabelColor = None  # หรือกำหนดเป็นค่าสีเริ่มต้น เช่น "#000000"

        self.document_handler = DocumentHandler()
        self.annotations = []  # เก็บ Annotation objects ของ core
        self.autosave_manager = AutoSaveManager()
        
        # สร้าง AnnotationCanvas สำหรับแสดงภาพเพื่อทำ annotation
        self.canvas = AnnotationCanvas(self.annotations, main_window=self)
        
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
        self.create_document_dropdowns()  # สร้าง dropdown สำหรับ Document Type และ Label

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
        export_layoutlm_action.triggered.connect(self.export_layoutlm)  # เปลี่ยนที่นี่
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

    def create_document_dropdowns(self):
        """ สร้าง QToolBar พร้อม QComboBox สำหรับ Document Type และ Label """
        toolbar = QToolBar("Document Options", self)
        self.addToolBar(toolbar)

        # QComboBox สำหรับ Document Type
        self.combo_doc_type = QComboBox(self)
        self.combo_doc_type.addItems(DOCUMENT_TYPES.keys())
        self.combo_doc_type.currentIndexChanged.connect(self.on_doc_type_changed)
        toolbar.addWidget(self.combo_doc_type)

        # QComboBox สำหรับ Label
        self.combo_label = QComboBox(self)
        # อัปเดต label combo ตาม Document Type เริ่มต้น
        if DOCUMENT_TYPES:
            default_type = list(DOCUMENT_TYPES.keys())[0]
            self.combo_label.addItems(list(DOCUMENT_TYPES[default_type].keys()))
            # ตั้งค่าเริ่มต้นสำหรับ currentDocType, currentLabel, currentLabelColor
            self.currentDocType = default_type
            self.currentLabel = list(DOCUMENT_TYPES[default_type].keys())[0]
            self.currentLabelColor = DOCUMENT_TYPES[default_type][self.currentLabel]
        self.combo_label.currentIndexChanged.connect(self.on_label_changed)
        toolbar.addWidget(self.combo_label)
    
    def on_doc_type_changed(self, index):
        """ เมื่อเปลี่ยน Document Type ให้อัปเดต combo_label และ attribute """
        doc_type = self.combo_doc_type.currentText()
        self.currentDocType = doc_type
        self.update_label_combo()

    def update_label_combo(self):
        """ อัปเดต QComboBox ของ Labels ตาม Document Type ที่เลือก """
        self.combo_label.clear()
        if self.currentDocType in DOCUMENT_TYPES:
            labels = DOCUMENT_TYPES[self.currentDocType]
            self.combo_label.addItems(list(labels.keys()))
            # ตั้งค่าเริ่มต้นให้กับ Label และสี
            if labels:
                self.currentLabel = list(labels.keys())[0]
                self.currentLabelColor = labels[self.currentLabel]
                self.combo_label.setCurrentIndex(0)

    def on_label_changed(self, index):
        """ เมื่อเปลี่ยน Label ให้เก็บค่า Label และสี """
        label = self.combo_label.currentText()
        self.currentLabel = label
        if self.currentDocType in DOCUMENT_TYPES:
            self.currentLabelColor = DOCUMENT_TYPES[self.currentDocType].get(label, "#000000")
        # อัปเดตสถานะใน Status Bar (ถ้าต้องการ)
        self.statusBar().showMessage(f"Document Type: {self.currentDocType} | Label: {self.currentLabel} ({self.currentLabelColor}) - Zoom: {int(self.canvas._zoom_step ** self.canvas._zoom * 100)}%")


    def create_document_type_menu(self):
        """ สร้างเมนู Document Type และ Labels """
        menu_bar = self.menuBar()
        # สร้างเมนูสำหรับประเภทเอกสาร
        self.doc_type_menu = QMenu("Document Type", self)
        for doc_type in DOCUMENT_TYPES.keys():
            action = QAction(doc_type, self)
            action.triggered.connect(lambda checked, dt=doc_type: self.set_document_type(dt))
            self.doc_type_menu.addAction(action)
        menu_bar.addMenu(self.doc_type_menu)
        # สร้างเมนูสำหรับ Labels (จะอัปเดตตามประเภทเอกสาร)
        self.label_menu = QMenu("Labels", self)
        menu_bar.addMenu(self.label_menu)

    def set_document_type(self, doc_type):
        """ ตั้งค่า current document type และอัปเดตเมนู Labels """
        self.currentDocType = doc_type
        self.update_label_menu()

    def update_label_menu(self):
        """ อัปเดตเมนู Labels จาก DOCUMENT_TYPES """
        self.label_menu.clear()
        labels = DOCUMENT_TYPES.get(self.currentDocType, {})
        for label, color in labels.items():
            action = QAction(label, self)
            # เก็บค่าสีใน action.data
            action.setData(color)
            action.triggered.connect(lambda checked, l=label, c=color: self.set_current_label(l, c))
            self.label_menu.addAction(action)

    def set_current_label(self, label, color):
        """ ตั้งค่า Label ที่เลือกและสีที่เกี่ยวข้อง """
        self.currentLabel = label
        self.currentLabelColor = color
        self.statusBar().showMessage(f"Document Type: {self.currentDocType} | Label: {label} ({color}) - Zoom: {int(self.canvas._zoom_step ** self.canvas._zoom * 100)}%")

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

    def export_layoutlm(self):
        """Method สำหรับ Export ข้อมูลในรูปแบบ LayoutLMv3"""
        export_directory = QFileDialog.getExistingDirectory(self, "Select Export Directory")
        if not export_directory:
            return  # หากไม่เลือก directory ให้ยกเลิก

        # ตรวจสอบ attribute ที่จำเป็น (คุณต้องแน่ใจว่า current_document, file_annotations, doc_type_combo, original_pixmap ถูกเซ็ตไว้แล้ว)
        if not (hasattr(self, 'current_document') and hasattr(self, 'file_annotations')):
            QMessageBox.critical(self, "Error", "Document data is not available for export.")
            return

        from core.annotation import LayoutLMExporter  # นำเข้าคลาส LayoutLMExporter
        exporter = LayoutLMExporter(
            current_document=self.current_document,
            file_annotations=self.file_annotations,
            doc_type_combo=self.doc_type_combo,
            original_pixmap=self.original_pixmap
        )
        try:
            exporter.export_layoutlm_format(export_directory)
            QMessageBox.information(self, "Export", "Export for LayoutLMv3 completed.")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))


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
