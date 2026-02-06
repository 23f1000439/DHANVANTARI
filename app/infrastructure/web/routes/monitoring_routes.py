"""
Monitoring Routes - RPM, ED Triage, Alerts
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
    RPMDataRequest, RPMAnalysisResponse,
    EDTriageRequest, EDTriageResponse
)

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.post("/rpm/analyze", response_model=RPMAnalysisResponse)
async def analyze_rpm_data(request: RPMDataRequest, db: Session = Depends(get_db)):
    """
    Analyze Remote Patient Monitoring (RPM) wearable data.
    Detects anomalies and provides health nudges.
    """
    try:
        from app.application.services.chronic_disease_pipeline import ChronicDiseasePipeline
        from app.application.services.unified_ai_service import get_unified_ai_service
        
        pipeline = ChronicDiseasePipeline()
        ai_service = get_unified_ai_service()
        
        # Run LSTM anomaly detection
        lstm_result = pipeline.lstm_wearable_monitor(request.wearable_data)
        
        # Get patient profile for risk persona
        repo = DhanvantariRepository(db)
        patient = repo.patients.get(request.patient_id)
        
        patient_profile = {
            "age": 50,  # Default, should come from patient
            "disease_duration_years": 5,
            "hba1c": 7.0,
            "comorbidities": patient.chronic_conditions if patient else [],
            "medication_adherence": 0.8,
            "recent_hospitalizations": 0
        }
        
        # Get risk persona
        risk_persona = pipeline.kmeans_risk_persona(patient_profile)
        
        # Determine if teleconsult needed
        teleconsult_recommended = False
        if lstm_result.get("status") == "ALERT_CRITICAL":
            teleconsult_recommended = True
        elif risk_persona.get("persona_id") == 2:  # High Alert
            teleconsult_recommended = True
        
        # Generate health nudge
        health_nudge = None
        if lstm_result.get("anomalies"):
            anomaly_types = [a["type"] for a in lstm_result["anomalies"]]
            if "HYPERGLYCEMIA_TREND" in anomaly_types:
                health_nudge = "Your glucose levels have been elevated. Consider reviewing your diet and medication timing."
            elif "RISING_HEART_RATE" in anomaly_types:
                health_nudge = "Your heart rate has been trending upward. If symptoms persist, please contact your care team."
        
        # Create alert if critical
        if lstm_result.get("status") == "ALERT_CRITICAL":
            repo.alerts.create_alert(
                alert_type="RPM_CRITICAL_ANOMALY",
                severity="CRITICAL",
                message=f"Critical RPM anomaly detected for patient {request.patient_id}",
                source_pipeline="CHRONIC_DISEASE",
                patient_id=request.patient_id
            )
        
        return RPMAnalysisResponse(
            patient_id=request.patient_id,
            status=lstm_result.get("status", "NORMAL"),
            anomalies=lstm_result.get("anomalies", []),
            risk_persona=risk_persona,
            health_nudge=health_nudge,
            teleconsult_recommended=teleconsult_recommended
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ed/triage", response_model=EDTriageResponse)
async def ed_triage(request: EDTriageRequest, db: Session = Depends(get_db)):
    """
    Emergency Department ESI triage assignment.
    Critical for high-volume ED environments.
    """
    try:
        from app.application.services.ed_triage_pipeline import EDTriagePipeline
        
        pipeline = EDTriagePipeline()
        
        # Run ESI assignment
        esi_result = pipeline.naive_bayes_esi(request.vitals, request.chief_complaint)
        
        # Determine teams to alert
        teams_to_alert = []
        if esi_result["esi_level"] == 1:
            teams_to_alert = ["Trauma", "Critical Care", "Attending"]
        elif esi_result["esi_level"] == 2:
            if "chest" in request.chief_complaint.lower():
                teams_to_alert = ["Cardiology"]
            if "stroke" in request.chief_complaint.lower():
                teams_to_alert = ["Neurology", "Stroke Team"]
        
        # Log to database
        repo = DhanvantariRepository(db)
        repo.audit_logs.log_action(
            action="ed_triage",
            pipeline="ED_TRIAGE",
            request_type="ESI_ASSIGNMENT",
            request_payload={
                "vitals": request.vitals,
                "chief_complaint": request.chief_complaint
            },
            response_summary={
                "esi_level": esi_result["esi_level"],
                "teams_alerted": teams_to_alert
            }
        )
        
        # Create alert if critical
        if esi_result["esi_level"] <= 2:
            repo.alerts.create_alert(
                alert_type="ED_CRITICAL_TRIAGE",
                severity="CRITICAL" if esi_result["esi_level"] == 1 else "HIGH",
                message=f"ESI Level {esi_result['esi_level']} patient: {request.chief_complaint[:50]}",
                source_pipeline="ED_TRIAGE",
                patient_id=None  # Anonymous until registered
            )
        
        return EDTriageResponse(
            esi_level=esi_result["esi_level"],
            color_code=esi_result["color_code"],
            disposition=esi_result.get("esi_name", "Unknown"),
            max_wait_time=esi_result.get("max_wait_time", "Unknown"),
            teams_to_alert=teams_to_alert,
            critical_alert=esi_result["esi_level"] <= 2
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/unacknowledged")
async def get_unacknowledged_alerts(db: Session = Depends(get_db)):
    """
    Get all unacknowledged alerts.
    """
    repo = DhanvantariRepository(db)
    alerts = repo.alerts.get_unacknowledged()
    
    return {
        "count": len(alerts),
        "alerts": [
            {
                "id": a.id,
                "alert_type": a.alert_type,
                "severity": a.severity,
                "message": a.message,
                "source_pipeline": a.source_pipeline,
                "patient_id": a.patient_id,
                "created_at": a.created_at.isoformat()
            }
            for a in alerts
        ]
    }


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int, user: str, db: Session = Depends(get_db)):
    """
    Acknowledge an alert.
    """
    repo = DhanvantariRepository(db)
    alert = repo.alerts.acknowledge(alert_id, user)
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"alert_id": alert_id, "acknowledged": True, "acknowledged_by": user}


@router.get("/dashboard")
async def get_monitoring_dashboard(db: Session = Depends(get_db)):
    """
    Get monitoring dashboard summary.
    """
    repo = DhanvantariRepository(db)
    
    unack_alerts = repo.alerts.get_unacknowledged()
    recent_audits = repo.audit_logs.get_recent(hours=24)
    active_encounters = repo.encounters.get_active_encounters()
    critical_imaging = repo.imaging_studies.get_critical_alerts()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "summary": {
            "unacknowledged_alerts": len(unack_alerts),
            "active_encounters": len(active_encounters),
            "critical_imaging_studies": len(critical_imaging),
            "api_calls_24h": len(recent_audits)
        },
        "alerts_by_severity": {
            "critical": len([a for a in unack_alerts if a.severity == "CRITICAL"]),
            "high": len([a for a in unack_alerts if a.severity == "HIGH"]),
            "medium": len([a for a in unack_alerts if a.severity == "medium"]),
        }
    }
