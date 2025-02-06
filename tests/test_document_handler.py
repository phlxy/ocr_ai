import os
import pytest
from core.document_handler import DocumentHandler
from PIL import Image

# Fixture สร้างไฟล์ภาพตัวอย่างใน temporary directory
@pytest.fixture
def sample_image(tmp_path):
    from PIL import Image, ImageDraw
    file_path = tmp_path / "test_image.png"
    image = Image.new("RGB", (100, 100), color="white")
    draw = ImageDraw.Draw(image)
    draw.rectangle([20, 20, 80, 80], fill="blue")
    image.save(file_path)
    return str(file_path)

def test_load_image(sample_image):
    handler = DocumentHandler()
    document = handler.load_image(sample_image)
    info = handler.get_document_info()
    assert info["type"] == "image"
    assert "size" in info
    # ตรวจสอบขนาดภาพ (100, 100)
    assert info["size"] == (100, 100)
