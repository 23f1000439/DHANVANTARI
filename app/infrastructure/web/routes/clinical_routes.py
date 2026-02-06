"""
Clinical Routes - RAG, Prescription, Triage, Labs
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from app.infrastructure.persistence.models import get_db
from app.infrastructure.persistence.repository import DhanvantariRepository
from app.infrastructure.web.schemas import (
    TriageRequest, TriageResponse, Priority,
    SymptomAnalysisRequest, SymptomAnalysisResponse,
    PrescriptionValidateRequest, PrescriptionValidateResponse,
    LabInterpretRequest, LabInterpretResponse,
    GuidelineSearchRequest, GuidelineSearchResponse
)
from app.application.services.unified_ai_service import get_unified_ai_service

router = APIRouter(prefix="/clinical", tags=["Clinical"])


@router.post("/triage", response_model=TriageResponse)
async def triage_patient(request: TriageRequest, db: Session = Depends(get_db)):
    """
    Quick triage classification from chief complaint.
    Returns priority level and ESI score.
    """
    start_time = datetime.now()
    ai_service = get_unified_ai_service()
    
    # Combine inputs
    text = request.chief_complaint
    if request.clinical_history:
        text += f" History: {request.clinical_history}"
    
    # Get triage result
    result = ai_service.triage_text(text)
    
    # Parse response
    try:
        import json
        parsed = json.loads(result.get("text", "{}"))
    except:
        parsed = {"priority": "ROUTINE", "esi_level": 4, "keywords": [], "reasoning": "Unable to parse"}
    
    # Log to audit
    repo = DhanvantariRepository(db)
    repo.audit_logs.log_action(
        action="triage",
        pipeline="clinical",
        request_type="TRIAGE",
        request_payload={"chief_complaint": request.chief_complaint},
        response_summary={"priority": parsed.get("priority")},
        ai_model=result.get("model_used")
    )
    
    processing_time = (datetime.now() - start_time).total_seconds() * 1000
    
    return TriageResponse(
        priority=Priority(parsed.get("priority", "ROUTINE")),
        esi_level=parsed.get("esi_level", 4),
        matched_keywords=parsed.get("keywords", []),
        reasoning=parsed.get("reasoning", ""),
        processing_time_ms=processing_time
    )


@router.post("/symptoms/analyze", response_model=SymptomAnalysisResponse)
async def analyze_symptoms(request: SymptomAnalysisRequest, db: Session = Depends(get_db)):
    """
    Analyze symptoms and provide differential diagnosis.
    Uses MedGemma locally when available.
    """
    start_time = datetime.now()
    ai_service = get_unified_ai_service()
    
    patient_info = {
        "age": request.patient_age,
        "gender": request.patient_gender
    }
    
    result = ai_service.analyze_symptoms(request.symptoms, patient_info)
    
    # Parse response
    try:
        import json
        parsed = json.loads(result.get("text", "{}"))
    except:
        parsed = {
            "differential_diagnoses": [],
            "red_flags": [],
            "recommended_workup": [],
            "urgency": "ROUTINE"
        }
    
    processing_time = (datetime.now() - start_time).total_seconds() * 1000
    
    return SymptomAnalysisResponse(
        differential_diagnoses=parsed.get("differential_diagnoses", []),
        red_flags=parsed.get("red_flags", []),
        recommended_workup=parsed.get("recommended_workup", []),
        urgency=Priority(parsed.get("urgency", "ROUTINE")),
        model_used=result.get("model_used", "unknown"),
        processing_time_ms=processing_time
    )


@router.post("/prescription/validate", response_model=PrescriptionValidateResponse)
async def validate_prescription(request: PrescriptionValidateRequest, db: Session = Depends(get_db)):
    """
    Validate prescription for drug interactions and dosing.
    Uses local MedGemma for privacy.
    """
    ai_service = get_unified_ai_service()
    
    result = ai_service.validate_prescription(request.medications)
    
    # Parse response
    try:
        import json
        parsed = json.loads(result.get("text", "{}"))
    except:
        parsed = {
            "safety_status": "REVIEW_REQUIRED",
            "interactions": [],
            "dosing_issues": [],
            "recommendations": ["Manual review recommended"]
        }
    
    return PrescriptionValidateResponse(
        safety_status=parsed.get("safety_status", "REVIEW_REQUIRED"),
        interactions=parsed.get("interactions", []),
        dosing_issues=parsed.get("dosing_issues", []),
        recommendations=parsed.get("recommendations", [])
    )


@router.post("/labs/interpret", response_model=LabInterpretResponse)
async def interpret_labs(request: LabInterpretRequest, db: Session = Depends(get_db)):
    """
    Interpret laboratory results.
    """
    ai_service = get_unified_ai_service()
    
    result = ai_service.interpret_labs(request.lab_results)
    
    # Parse response
    try:
        import json
        parsed = json.loads(result.get("text", "{}"))
    except:
        parsed = {
            "abnormal_findings": [],
            "clinical_significance": "Unable to interpret",
            "follow_up_tests": [],
            "overall_assessment": "Review required"
        }
    
    return LabInterpretResponse(
        abnormal_findings=parsed.get("abnormal_findings", []),
        clinical_significance=parsed.get("clinical_significance", ""),
        follow_up_tests=parsed.get("follow_up_tests", []),
        overall_assessment=parsed.get("overall_assessment", "")
    )


@router.post("/guidelines/search", response_model=GuidelineSearchResponse)
async def search_guidelines(request: GuidelineSearchRequest, db: Session = Depends(get_db)):
    """
    Search clinical guidelines using RAG pipeline.
    """
    try:
        from app.application.services.central_orchestrator import DhanvantariCentralOrchestrator
        
        orchestrator = DhanvantariCentralOrchestrator()
        result = orchestrator.route_request("GUIDELINE_SEARCH", {
            "query": request.query,
            "specialty": request.specialty
        })
        
        return GuidelineSearchResponse(
            results=result.get("response", {}).get("results", []),
            sources=result.get("response", {}).get("sources", []),
            synthesis=result.get("response", {}).get("synthesis", "")
        )
    except Exception as e:
        return GuidelineSearchResponse(
            results=[],
            sources=[],
            synthesis=f"Search error: {str(e)}"
        )
