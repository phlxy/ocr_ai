# project/api/api_handler.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import json
from core.annotation import Annotation, export_annotations, export_layoutlm_format, validate_annotations

app = FastAPI(title="Annotation API")

class AnnotationModel(BaseModel):
    x: float
    y: float
    width: float
    height: float
    label: str

# In-memory store สำหรับ Annotation
annotations_store: List[Annotation] = []

@app.get("/annotations", response_model=List[AnnotationModel])
def get_annotations():
    return [anno.to_dict() for anno in annotations_store]

@app.post("/annotations", response_model=AnnotationModel)
def create_annotation(anno: AnnotationModel):
    new_anno = Annotation(anno.x, anno.y, anno.width, anno.height, anno.label)
    annotations_store.append(new_anno)
    return new_anno.to_dict()

@app.get("/export/json")
def export_annotations_endpoint():
    try:
        json_data = export_annotations(annotations_store)
        return json.loads(json_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/export/layoutlm")
def export_layoutlm_endpoint():
    try:
        json_data = export_layoutlm_format(annotations_store)
        return json.loads(json_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/validate")
def validate_annotations_endpoint():
    valid, message = validate_annotations(annotations_store)
    return {"valid": valid, "message": message}
