"""
Repository Pattern for Database Access
Provides CRUD operations for all models.
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from .models import (
    Patient, Encounter, ClinicalNote, Prescription, 
    Claim, ImagingStudy, AuditLog, AlertHistory
)


class BaseRepository:
    """Base repository with common CRUD operations."""
    
    def __init__(self, db: Session, model):
        self.db = db
        self.model = model
    
    def get(self, id: int):
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def get_all(self, skip: int = 0, limit: int = 100):
        return self.db.query(self.model).offset(skip).limit(limit).all()
    
    def create(self, **kwargs):
        obj = self.model(**kwargs)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj
    
    def update(self, id: int, **kwargs):
        obj = self.get(id)
        if obj:
            for key, value in kwargs.items():
                setattr(obj, key, value)
            self.db.commit()
            self.db.refresh(obj)
        return obj
    
    def delete(self, id: int):
        obj = self.get(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
            return True
        return False


class PatientRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db, Patient)
    
    def get_by_mrn(self, mrn: str) -> Optional[Patient]:
        return self.db.query(Patient).filter(Patient.mrn == mrn).first()
    
    def search(self, name: str) -> List[Patient]:
        return self.db.query(Patient).filter(
            (Patient.first_name.ilike(f"%{name}%")) | 
            (Patient.last_name.ilike(f"%{name}%"))
        ).all()


class EncounterRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db, Encounter)
    
    def get_by_patient(self, patient_id: int) -> List[Encounter]:
        return self.db.query(Encounter).filter(Encounter.patient_id == patient_id).all()
    
    def get_active_encounters(self) -> List[Encounter]:
        return self.db.query(Encounter).filter(Encounter.discharge_time == None).all()
    
    def get_by_priority(self, priority: str) -> List[Encounter]:
        return self.db.query(Encounter).filter(Encounter.triage_priority == priority).all()


class ClinicalNoteRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db, ClinicalNote)
    
    def get_by_encounter(self, encounter_id: int) -> List[ClinicalNote]:
        return self.db.query(ClinicalNote).filter(ClinicalNote.encounter_id == encounter_id).all()


class PrescriptionRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db, Prescription)
    
    def get_by_patient(self, patient_id: int) -> List[Prescription]:
        return self.db.query(Prescription).filter(Prescription.patient_id == patient_id).all()
    
    def get_pending_validation(self) -> List[Prescription]:
        return self.db.query(Prescription).filter(Prescription.validation_status == "pending").all()


class ClaimRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db, Claim)
    
    def get_by_patient(self, patient_id: int) -> List[Claim]:
        return self.db.query(Claim).filter(Claim.patient_id == patient_id).all()
    
    def get_by_status(self, status: str) -> List[Claim]:
        return self.db.query(Claim).filter(Claim.status == status).all()
    
    def get_by_claim_number(self, claim_number: str) -> Optional[Claim]:
        return self.db.query(Claim).filter(Claim.claim_number == claim_number).first()
    
    def get_high_risk_claims(self, threshold: float = 0.7) -> List[Claim]:
        return self.db.query(Claim).filter(Claim.denial_risk_score >= threshold).all()


class ImagingStudyRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db, ImagingStudy)
    
    def get_by_patient(self, patient_id: int) -> List[ImagingStudy]:
        return self.db.query(ImagingStudy).filter(ImagingStudy.patient_id == patient_id).all()
    
    def get_by_study_id(self, study_id: str) -> Optional[ImagingStudy]:
        return self.db.query(ImagingStudy).filter(ImagingStudy.study_id == study_id).first()
    
    def get_critical_alerts(self) -> List[ImagingStudy]:
        return self.db.query(ImagingStudy).filter(ImagingStudy.critical_alert == True).all()
    
    def get_by_modality(self, modality: str) -> List[ImagingStudy]:
        return self.db.query(ImagingStudy).filter(ImagingStudy.modality == modality).all()


class AuditLogRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db, AuditLog)
    
    def log_action(self, action: str, pipeline: str, request_type: str,
                   user_id: str = "system", request_payload: Dict = None,
                   response_summary: Dict = None, thinking_level: str = "LOW",
                   ai_model: str = "gemini-3") -> AuditLog:
        return self.create(
            action=action,
            pipeline=pipeline,
            request_type=request_type,
            user_id=user_id,
            request_payload=request_payload,
            response_summary=response_summary,
            thinking_level=thinking_level,
            ai_model_used=ai_model
        )
    
    def get_by_pipeline(self, pipeline: str) -> List[AuditLog]:
        return self.db.query(AuditLog).filter(AuditLog.pipeline == pipeline).all()
    
    def get_recent(self, hours: int = 24) -> List[AuditLog]:
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return self.db.query(AuditLog).filter(AuditLog.timestamp >= cutoff).all()


class AlertHistoryRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db, AlertHistory)
    
    def create_alert(self, alert_type: str, severity: str, message: str,
                     source_pipeline: str, patient_id: int = None,
                     source_study_id: str = None) -> AlertHistory:
        return self.create(
            patient_id=patient_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            source_pipeline=source_pipeline,
            source_study_id=source_study_id
        )
    
    def get_unacknowledged(self) -> List[AlertHistory]:
        return self.db.query(AlertHistory).filter(AlertHistory.acknowledged == False).all()
    
    def acknowledge(self, alert_id: int, user: str) -> AlertHistory:
        return self.update(
            alert_id,
            acknowledged=True,
            acknowledged_by=user,
            acknowledged_at=datetime.utcnow()
        )


# ============================================================
# Unified Repository Access
# ============================================================
class DhanvantariRepository:
    """
    Unified access to all repositories.
    """
    def __init__(self, db: Session):
        self.db = db
        self.patients = PatientRepository(db)
        self.encounters = EncounterRepository(db)
        self.clinical_notes = ClinicalNoteRepository(db)
        self.prescriptions = PrescriptionRepository(db)
        self.claims = ClaimRepository(db)
        self.imaging_studies = ImagingStudyRepository(db)
        self.audit_logs = AuditLogRepository(db)
        self.alerts = AlertHistoryRepository(db)
