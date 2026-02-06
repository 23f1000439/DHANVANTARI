"""
Database Models for Dhanvantr.ai
SQLAlchemy ORM models for persistence layer.
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum
import os

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dhanvantari.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ============================================================
# Enums
# ============================================================
class Gender(enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

class EncounterType(enum.Enum):
    OUTPATIENT = "outpatient"
    INPATIENT = "inpatient"
    EMERGENCY = "emergency"
    TELECONSULT = "teleconsult"

class TriagePriority(enum.Enum):
    STAT = "stat"
    URGENT = "urgent"
    ROUTINE = "routine"

class ClaimStatus(enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    DENIED = "denied"
    APPEALED = "appealed"


# ============================================================
# Core Models
# ============================================================
class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    mrn = Column(String(50), unique=True, index=True)  # Medical Record Number
    first_name = Column(String(100))
    last_name = Column(String(100))
    date_of_birth = Column(DateTime)
    gender = Column(String(20))
    phone = Column(String(20))
    email = Column(String(100))
    address = Column(Text)
    
    # Medical info
    blood_type = Column(String(10))
    allergies = Column(JSON)  # List of allergies
    chronic_conditions = Column(JSON)  # List of conditions
    current_medications = Column(JSON)  # List of medications
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    encounters = relationship("Encounter", back_populates="patient")
    prescriptions = relationship("Prescription", back_populates="patient")
    claims = relationship("Claim", back_populates="patient")
    imaging_studies = relationship("ImagingStudy", back_populates="patient")


class Encounter(Base):
    __tablename__ = "encounters"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), index=True)
    encounter_type = Column(String(50))
    
    # Clinical data
    chief_complaint = Column(Text)
    vitals = Column(JSON)  # {hr, bp, temp, spo2, rr}
    clinical_notes = Column(Text)
    diagnosis_codes = Column(JSON)  # ICD-11 codes
    procedure_codes = Column(JSON)  # CPT codes
    
    # Triage
    triage_priority = Column(String(20))
    esi_level = Column(Integer)
    
    # Timestamps
    admission_time = Column(DateTime)
    discharge_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="encounters")
    clinical_notes_records = relationship("ClinicalNote", back_populates="encounter")


class ClinicalNote(Base):
    __tablename__ = "clinical_notes"
    
    id = Column(Integer, primary_key=True, index=True)
    encounter_id = Column(Integer, ForeignKey("encounters.id"), index=True)
    
    note_type = Column(String(50))  # progress, discharge, procedure, etc.
    content = Column(Text)
    author = Column(String(100))
    
    # AI-extracted entities
    extracted_entities = Column(JSON)
    icd_codes = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    encounter = relationship("Encounter", back_populates="clinical_notes_records")


class Prescription(Base):
    __tablename__ = "prescriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), index=True)
    
    # Prescription details
    medications = Column(JSON)  # List of {drug, dose, frequency, duration}
    prescriber = Column(String(100))
    prescription_date = Column(DateTime)
    
    # OCR/Digitization
    original_image_path = Column(String(500))
    ocr_text = Column(Text)
    fhir_bundle = Column(JSON)
    
    # Validation
    validation_status = Column(String(50))
    validation_notes = Column(Text)
    drug_interactions = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="prescriptions")


class Claim(Base):
    __tablename__ = "claims"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), index=True)
    claim_number = Column(String(50), unique=True, index=True)
    
    # Claim details
    procedures = Column(JSON)
    diagnosis_codes = Column(JSON)
    total_charges = Column(Float)
    
    # Insurance
    payer = Column(String(100))
    pre_authorization = Column(Boolean, default=False)
    
    # Status
    status = Column(String(50), default="draft")
    submission_date = Column(DateTime)
    decision_date = Column(DateTime)
    
    # ML predictions
    denial_risk_score = Column(Float)
    risk_factors = Column(JSON)
    
    # Appeal
    denial_reason = Column(Text)
    appeal_letter = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="claims")


class ImagingStudy(Base):
    __tablename__ = "imaging_studies"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), index=True)
    study_id = Column(String(50), unique=True, index=True)
    
    # Study info
    modality = Column(String(50))  # X-Ray, CT, MRI, etc.
    body_part = Column(String(100))
    referral_notes = Column(Text)
    
    # AI Analysis
    ai_findings = Column(JSON)
    critical_alert = Column(Boolean, default=False)
    scoring = Column(JSON)  # BIRADS, TIRADS, etc.
    
    # Report
    preliminary_report = Column(Text)
    final_report = Column(Text)
    reporting_radiologist = Column(String(100))
    
    # Priority
    priority = Column(String(20))
    
    study_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="imaging_studies")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Action details
    action = Column(String(100))
    pipeline = Column(String(100))
    request_type = Column(String(100))
    
    # Actor
    user_id = Column(String(100))
    user_role = Column(String(50))
    
    # Data
    request_payload = Column(JSON)
    response_summary = Column(JSON)
    
    # AI decisions
    thinking_level = Column(String(20))
    ai_model_used = Column(String(100))
    
    # Compliance
    hipaa_compliant = Column(Boolean, default=True)
    
    timestamp = Column(DateTime, default=datetime.utcnow)


class AlertHistory(Base):
    __tablename__ = "alert_history"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), index=True, nullable=True)
    
    # Alert details
    alert_type = Column(String(100))
    severity = Column(String(20))
    message = Column(Text)
    
    # Source
    source_pipeline = Column(String(100))
    source_study_id = Column(String(50))
    
    # Status
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(100))
    acknowledged_at = Column(DateTime)
    
    # Actions taken
    actions = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================
# Database Initialization
# ============================================================
def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)
    print("[DB] All tables created successfully.")

def get_db():
    """Dependency for FastAPI to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
