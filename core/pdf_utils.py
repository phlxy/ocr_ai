import fitz  # PyMuPDF
from PyQt6.QtGui import QImage, QPixmap

def pdf_to_pixmap_list(filepath: str) -> list:
    """
    เปิดไฟล์ PDF และแปลงแต่ละหน้าเป็น QPixmap แบบ full resolution
    """
    pixmap_list = []
    doc = fitz.open(filepath)
    # กำหนด zoom factor สูงขึ้นเพื่อให้ได้ความละเอียดที่ดี
    zoom = 3.0  # ปรับค่าได้ตามต้องการ
    mat = fitz.Matrix(zoom, zoom)
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("ppm")
        image = QImage.fromData(img_data)
        full_pixmap = QPixmap.fromImage(image)
        pixmap_list.append(full_pixmap)
    return pixmap_list
