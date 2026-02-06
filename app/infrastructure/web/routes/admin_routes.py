"""
Admin Routes - RCM, Claims, ICD Coding
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
import uuid

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from app.infrastructure.persistence.models import get_db
from app.infrastructure.persistence.repository import DhanvantariRepository
from app.infrastructure.web.schemas import (
    ClaimCreateRequest, ClaimAnalysisResponse,
    ICD11CodingRequest, ICD11CodingResponse
)

router = APIRouter(prefix="/admin", tags=["Admin/RCM"])


@router.post("/claims/analyze", response_model=ClaimAnalysisResponse)
async def analyze_claim(request: ClaimCreateRequest, db: Session = Depends(get_db)):
    """
    Analyze claim for denial risk before submission.
    Uses RCM pipeline for code extraction and validation.
    """
    try:
        from app.application.services.rcm_pipeline import RCMPipeline
        from app.application.services.unified_ai_service import get_unified_ai_service
        
        pipeline = RCMPipeline()
        ai_service = get_unified_ai_service()
        
        # Build claim object
        claim = {
            "procedures": request.procedures,
            "diagnosis_codes": request.diagnosis_codes,
            "total_charges": request.total_charges,
            "payer": request.payer,
            "pre_authorization": request.pre_authorization,
            "documentation": [request.clinical_notes] if request.clinical_notes else []
        }
        
        # Run audit
        audit_result = pipeline.isolation_forest_auditor(claim)
        
        # Run rules validation
        rules_result = pipeline.decision_tree_rules(claim)
        
        # Calculate risk score
        risk_score = 0.3  # Base
        if audit_result["status"] == "FLAGGED_FOR_REVIEW":
            risk_score += 0.3
        if rules_result["adjudication"] == "HOLD_FOR_REVIEW":
            risk_score += 0.3
        if not request.pre_authorization and any(p.get("cpt_code", "").startswith("27") for p in request.procedures):
            risk_score += 0.2  # High-cost procedures without pre-auth
        
        risk_score = min(risk_score, 1.0)
        
        # Get risk factors
        risk_factors = []
        for anomaly in audit_result.get("anomalies", []):
            risk_factors.append({
                "factor": anomaly["type"],
                "severity": anomaly.get("severity", "medium"),
                "details": anomaly.get("detail", "")
            })
        for violation in rules_result.get("violations", []):
            risk_factors.append({
                "factor": violation["rule"],
                "severity": "high",
                "details": violation.get("message", "")
            })
        
        # Generate recommendations
        recommendations = []
        if risk_score > 0.7:
            recommendations.append("HIGH RISK: Manual review strongly recommended before submission")
        if not request.pre_authorization:
            recommendations.append("Consider obtaining pre-authorization")
        if audit_result["status"] == "FLAGGED_FOR_REVIEW":
            recommendations.append("Verify charges against fee schedule")
        
        # Save claim to database
        repo = DhanvantariRepository(db)
        claim_number = f"CLM-{uuid.uuid4().hex[:8].upper()}"
        
        db_claim = repo.claims.create(
            patient_id=request.patient_id,
            claim_number=claim_number,
            procedures=request.procedures,
            diagnosis_codes=request.diagnosis_codes,
            total_charges=request.total_charges,
            payer=request.payer,
            pre_authorization=request.pre_authorization,
            denial_risk_score=risk_score,
            risk_factors=risk_factors
        )
        
        return ClaimAnalysisResponse(
            claim_id=db_claim.id,
            denial_risk_score=risk_score,
            risk_factors=risk_factors,
            recommendations=recommendations,
            coding_audit={
                "audit_status": audit_result["status"],
                "rules_status": rules_result["adjudication"]
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/claims/{claim_id}/submit")
async def submit_claim(claim_id: int, db: Session = Depends(get_db)):
    """
    Submit claim after analysis.
    """
    repo = DhanvantariRepository(db)
    claim = repo.claims.get(claim_id)
    
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Update status
    repo.claims.update(claim_id, status="submitted", submission_date=datetime.utcnow())
    
    return {"claim_id": claim_id, "status": "submitted", "message": "Claim submitted successfully"}


@router.get("/claims/high-risk")
async def get_high_risk_claims(threshold: float = 0.7, db: Session = Depends(get_db)):
    """
    Get all claims with high denial risk.
    """
    repo = DhanvantariRepository(db)
    claims = repo.claims.get_high_risk_claims(threshold)
    
    return {
        "count": len(claims),
        "threshold": threshold,
        "claims": [
            {
                "id": c.id,
                "claim_number": c.claim_number,
                "patient_id": c.patient_id,
                "denial_risk_score": c.denial_risk_score,
                "status": c.status
            }
            for c in claims
        ]
    }


@router.post("/claims/{claim_id}/appeal")
async def generate_appeal(claim_id: int, clinical_evidence: str, db: Session = Depends(get_db)):
    """
    Generate appeal letter for denied claim.
    """
    repo = DhanvantariRepository(db)
    claim = repo.claims.get(claim_id)
    
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    from app.application.services.unified_ai_service import get_unified_ai_service
    ai_service = get_unified_ai_service()
    
    denial_info = {
        "claim_number": claim.claim_number,
        "denial_reason": claim.denial_reason or "Not specified",
        "procedures": claim.procedures,
        "payer": claim.payer
    }
    
    result = ai_service.draft_appeal_letter(denial_info, clinical_evidence)
    
    # Save appeal letter
    repo.claims.update(claim_id, appeal_letter=result.get("text", ""), status="appealed")
    
    return {
        "claim_id": claim_id,
        "appeal_letter": result.get("text", ""),
        "status": "appeal_generated"
    }


@router.post("/coding/icd11", response_model=ICD11CodingResponse)
async def generate_icd11_codes(request: ICD11CodingRequest, db: Session = Depends(get_db)):
    """
    Generate ICD-11 codes from clinical text.
    """
    from app.application.services.unified_ai_service import get_unified_ai_service
    ai_service = get_unified_ai_service()
    
    result = ai_service.generate_icd_codes(request.clinical_text, request.extracted_entities)
    
    # Parse response
    try:
        import json
        parsed = json.loads(result.get("text", "{}"))
    except:
        parsed = {"codes": [], "primary": {}, "secondary": []}
    
    return ICD11CodingResponse(
        codes=parsed.get("codes", []),
        primary_diagnosis=parsed.get("primary", {}),
        secondary_diagnoses=parsed.get("secondary", []),
        confidence=parsed.get("confidence", 0.0)
    )
