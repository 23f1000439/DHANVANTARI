"""
Imaging Routes - Radiology, Dermatology
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import base64

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from app.infrastructure.persistence.models import get_db
from app.infrastructure.persistence.repository import DhanvantariRepository
from app.infrastructure.web.schemas import (
    ImagingAnalysisRequest, ImagingAnalysisResponse,
    DermatologyRequest, DermatologyResponse,
    Priority, Modality
)

router = APIRouter(prefix="/imaging", tags=["Imaging"])


@router.post("/radiology/analyze", response_model=ImagingAnalysisResponse)
async def analyze_radiology(request: ImagingAnalysisRequest, db: Session = Depends(get_db)):
    """
    Analyze radiological imaging study.
    Supports X-Ray, CT, MRI, Mammography, Ultrasound.
    """
    start_time = datetime.now()
    
    try:
        from app.application.services.radiology_pipeline import RadiologyPipeline
        from app.application.services.unified_ai_service import get_unified_ai_service
        
        pipeline = RadiologyPipeline()
        ai_service = get_unified_ai_service()
        
        # Decode image if provided
        image_data = None
        if request.image_data:
            image_data = base64.b64decode(request.image_data)
        
        # Run pipeline
        result = pipeline.run_pipeline(
            study_id=request.study_id,
            image_data=image_data,
            modality=request.modality.value,
            referral_notes=request.referral_notes,
            patient_info={"id": request.patient_id},
            ai_service=ai_service,
            clinical_history=request.clinical_history
        )
        
        # Log to database
        repo = DhanvantariRepository(db)
        
        # Create imaging study record
        repo.imaging_studies.create(
            patient_id=request.patient_id,
            study_id=request.study_id,
            modality=request.modality.value,
            referral_notes=request.referral_notes,
            ai_findings=result.get("analysis", {}).get("findings"),
            critical_alert=result.get("analysis", {}).get("critical_alert", False),
            scoring=result.get("scoring"),
            preliminary_report=str(result.get("report", {})),
            priority=result.get("triage", {}).get("priority", "ROUTINE")
        )
        
        # Create alert if critical
        if result.get("analysis", {}).get("critical_alert"):
            repo.alerts.create_alert(
                alert_type="CRITICAL_IMAGING_FINDING",
                severity="CRITICAL",
                message=f"Critical finding in {request.modality.value} study {request.study_id}",
                source_pipeline="RADIOLOGY",
                patient_id=request.patient_id,
                source_study_id=request.study_id
            )
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return ImagingAnalysisResponse(
            study_id=request.study_id,
            modality=request.modality.value,
            priority=Priority(result.get("triage", {}).get("priority", "ROUTINE")),
            critical_alert=result.get("analysis", {}).get("critical_alert", False),
            findings=result.get("analysis", {}).get("findings", []),
            scoring=result.get("scoring"),
            report=result.get("report"),
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dermatology/analyze", response_model=DermatologyResponse)
async def analyze_dermatology(request: DermatologyRequest, db: Session = Depends(get_db)):
    """
    Analyze skin lesion for dermatology assessment.
    """
    start_time = datetime.now()
    
    try:
        from app.application.services.dermatology_pipeline import DermatologyPipeline
        from app.application.services.unified_ai_service import get_unified_ai_service
        
        pipeline = DermatologyPipeline()
        ai_service = get_unified_ai_service()
        
        # Decode image if provided
        image_data = None
        if request.image_data:
            image_data = base64.b64decode(request.image_data)
        
        # Run individual stages
        # 1. Image quality check
        img_result = pipeline.cnn_image_processor(image_data)
        
        # 2. Text triage
        triage = pipeline.triage_text_nb(request.lesion_description)
        
        # 3. VLM analysis
        analysis = pipeline.analyze_lesion_medgemma(image_data, request.lesion_description)
        
        # 4. Risk clustering
        patient_profile = {
            "age": request.patient_age or 40,
            "skin_type": request.skin_type or "III",
            "sun_exposure": request.sun_exposure or "moderate",
            "family_history_cancer": request.family_history_cancer or False,
            "previous_lesions": 0
        }
        clustering = pipeline.cluster_patient_kmeans(patient_profile)
        
        # Determine referral recommendation
        if triage["priority"] == "HIGH" or analysis["classification"] == "Suspicious for Malignancy":
            referral = "URGENT referral to dermatologist recommended"
        elif triage["priority"] == "MODERATE" or analysis["classification"] == "Atypical Lesion":
            referral = "Routine referral to dermatologist recommended"
        else:
            referral = "Self-monitoring with photo documentation"
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return DermatologyResponse(
            priority=Priority(triage["priority"]),
            classification=analysis["classification"],
            detected_features=analysis.get("detected_features", []),
            risk_cohort=clustering,
            referral_recommendation=referral,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_imaging_study(
    study_id: str,
    modality: Modality,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload DICOM or image file for analysis.
    """
    contents = await file.read()
    
    # Save file
    upload_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "uploads", "imaging")
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, f"{study_id}_{file.filename}")
    with open(file_path, "wb") as f:
        f.write(contents)
    
    return {
        "study_id": study_id,
        "filename": file.filename,
        "size_bytes": len(contents),
        "path": file_path,
        "status": "uploaded"
    }
