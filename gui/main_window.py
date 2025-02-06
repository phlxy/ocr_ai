# project/gui/main_window.py

import sys
from PyQt6.QtWidgets import QMainWindow, QApplication, QFileDialog, QMessageBox, QVBoxLayout, QWidget
from PyQt6.QtGui import QAction

from PyQt6.QtCore import QTimer
from core.document_handler import DocumentHandler
from core.autosave import AutoSaveManager
from core.annotation import export_annotations, validate_annotations, export_layoutlm_format
from gui.annotation_canvas import AnnotationCanvas

from concurrent.futures import ProcessPoolExecutor
from core.annotation import validate_annotations as core_validate_annotations

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Annotation Tool")
        
        # Initialize Core Components
        self.document_handler = DocumentHandler()
        self.annotations = []  # List สำหรับเก็บ Annotation objects
        self.autosave_manager = AutoSaveManager()
        
        # Set up GUI Components
        self.canvas = AnnotationCanvas(self.annotations)
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        self.create_menu()
        
        # ProcessPoolExecutor สำหรับงาน CPU-bound
        self.executor = ProcessPoolExecutor()
        
        # ตั้ง QTimer สำหรับ auto-save (เช่น ทุก 5 นาที)
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.perform_auto_save)
        self.autosave_timer.start(300000)  # 300,000 ms = 5 นาที
    
    def create_menu(self):
        menu_bar = self.menuBar()
        
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
        
        tools_menu = menu_bar.addMenu("Tools")
        validate_action = QAction("Validate Annotations", self)
        validate_action.triggered.connect(self.start_validation)
        tools_menu.addAction(validate_action)
    
    def open_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Images (*.png *.jpg *.bmp);;PDF Files (*.pdf)")
        if filepath:
            try:
                self.document_handler.load_image(filepath)
                # หลังจากโหลดไฟล์แล้ว สามารถแสดงเอกสารบน canvas (หรือแสดงข้อความแจ้ง)
                QMessageBox.information(self, "File Loaded", f"Loaded file: {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
    
    def export_annotations(self):
        json_data = export_annotations(self.annotations)
        QMessageBox.information(self, "Exported JSON", json_data)
    
    def export_layoutlm_format(self):
        json_data = export_layoutlm_format(self.annotations)
        QMessageBox.information(self, "Exported LayoutLM Format", json_data)
    
    def start_validation(self):
        # รัน validation ใน process แยก
        future = self.executor.submit(core_validate_annotations, self.annotations)
        future.add_done_callback(self.validation_callback)
    
    def validation_callback(self, future):
        # ใช้ QTimer.singleShot เพื่ออัปเดต UI บน main thread
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

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
