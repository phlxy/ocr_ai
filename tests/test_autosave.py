import os
import json
import time
import pytest
from core.autosave import AutoSaveManager
from core.document_handler import DocumentHandler
from core.annotation import Annotation

@pytest.fixture
def autosave_file(tmp_path):
    return tmp_path / "autosave.json"

@pytest.fixture
def sample_document_handler(tmp_path):
    handler = DocumentHandler()
    handler.filepath = str(tmp_path / "dummy.pdf")
    return handler

@pytest.fixture
def sample_annotations():
    return [Annotation(0, 0, 10, 10, "Test")]

def test_auto_save(tmp_path, sample_document_handler, sample_annotations):
    autosave_path = tmp_path / "autosave.json"
    manager = AutoSaveManager(str(autosave_path))
    manager.auto_save(sample_document_handler, sample_annotations)
    
    assert os.path.exists(autosave_path)
    with open(autosave_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["document"] == sample_document_handler.filepath
    assert "annotations" in data
    assert len(data["annotations"]) == 1

def test_check_for_autosave(tmp_path, sample_document_handler, sample_annotations):
    autosave_path = tmp_path / "autosave.json"
    manager = AutoSaveManager(str(autosave_path))
    manager.auto_save(sample_document_handler, sample_annotations)
    data = manager.check_for_autosave()
    assert data is not None
    assert data["document"] == sample_document_handler.filepath

def test_cleanup_old_autosaves(tmp_path, sample_document_handler, sample_annotations):
    autosave_path = tmp_path / "autosave.json"
    manager = AutoSaveManager(str(autosave_path))
    manager.auto_save(sample_document_handler, sample_annotations)
    
    # จำลองไฟล์ autosave ที่มีอายุเกินกำหนด (เช่น 2 ชั่วโมงเก่า)
    old_time = time.time() - 7200
    os.utime(autosave_path, (old_time, old_time))
    
    manager.cleanup_old_autosaves(max_age_seconds=3600)
    assert not os.path.exists(autosave_path)
