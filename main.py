# main.py

import sys
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow

def main():
    # สร้าง QApplication instance
    app = QApplication(sys.argv)
    
    # สร้างหน้าต่างหลักของโปรแกรม
    window = MainWindow()
    window.show()
    
    # เริ่ม event loop ของโปรแกรม
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
