# project/core/autosave.py

import os
import json
import time

class AutoSaveManager:
    def __init__(self, autosave_path="autosave.json"):
        self.autosave_path = autosave_path
    
    def auto_save(self, document_handler, annotations: list):
        """
        บันทึกสถานะปัจจุบันของเอกสารและ Annotation ลงไฟล์ autosave
        """
        data = {
            "timestamp": time.time(),
            "document": document_handler.filepath if hasattr(document_handler, 'filepath') else None,
            "annotations": [anno.to_dict() for anno in annotations]
        }
        try:
            with open(self.autosave_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            print(f"Auto-saved to {self.autosave_path}")
        except Exception as e:
            print(f"Error during auto-save: {e}")
    
    def check_for_autosave(self):
        """
        ตรวจสอบว่ามีไฟล์ autosave อยู่หรือไม่แล้วคืนข้อมูลออกมา
        """
        if os.path.exists(self.autosave_path):
            try:
                with open(self.autosave_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data
            except Exception as e:
                print(f"Error reading autosave file: {e}")
                return None
        return None
    
    def cleanup_old_autosaves(self, max_age_seconds=3600):
        """
        ลบไฟล์ autosave หากมีอายุเกิน max_age_seconds
        """
        if os.path.exists(self.autosave_path):
            try:
                file_time = os.path.getmtime(self.autosave_path)
                current_time = time.time()
                if current_time - file_time > max_age_seconds:
                    os.remove(self.autosave_path)
                    print("Old autosave file removed.")
            except Exception as e:
                print(f"Error cleaning up autosave file: {e}")
