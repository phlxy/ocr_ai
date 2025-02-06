# project/core/document_handler.py

import os
from PIL import Image
import fitz  # ใช้สำหรับเปิด PDF (PyMuPDF)

class DocumentHandler:
    def __init__(self):
        self.document = None
        self.filepath = None
        self.document_type = None  # 'pdf' หรือ 'image'
    
    def load_image(self, filepath: str):
        """
        โหลดเอกสาร (PDF หรือรูปภาพ) โดยพิจารณาจากส่วนขยายไฟล์
        """
        self.filepath = filepath
        ext = os.path.splitext(filepath)[1].lower()
        if ext == '.pdf':
            try:
                self.document = fitz.open(filepath)
                self.document_type = 'pdf'
            except Exception as e:
                raise Exception(f"Error loading PDF file: {e}")
        elif ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif']:
            try:
                self.document = Image.open(filepath)
                self.document_type = 'image'
            except Exception as e:
                raise Exception(f"Error loading image file: {e}")
        else:
            raise Exception("Unsupported file type")
        return self.document
    
    def get_document_info(self):
        """
        คืนค่าข้อมูลพื้นฐานของเอกสาร
        """
        if self.document_type == 'pdf':
            return {"type": "pdf", "pages": self.document.page_count}
        elif self.document_type == 'image':
            return {"type": "image", "size": self.document.size}
        else:
            return {}
