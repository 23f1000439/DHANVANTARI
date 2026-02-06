"""
Pydantic Schemas for API Request/Response Validation
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


# ============================================================
# Enums
# ============================================================
class Priority(str, Enum):
    STAT = "STAT"
    URGENT = "URGENT"
    ROUTINE = "ROUTINE"

class Modality(str, Enum):
    XRAY = "X-Ray"
    CT = "CT"
    MRI = "MRI"
    MAMMOGRAPHY = "Mammography"
    ULTRASOUND = "Ultrasound"

class ClaimStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    DENIED = "denied"


# ============================================================
# Common Schemas
# ============================================================
class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime
    services: Dict[str, bool]


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================
# Patient Schemas
# ============================================================
class PatientCreate(BaseModel):
    mrn: str
    first_name: str
    last_name: str
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    allergies: Optional[List[str]] = []
    chronic_conditions: Optional[List[str]] = []
    current_medications: Optional[List[Dict]] = []


class PatientResponse(BaseModel):
    id: int
    mrn: str
    first_name: str
    last_name: str
    date_of_birth: Optional[datetime]
    gender: Optional[str]
    allergies: Optional[List[str]]
    chronic_conditions: Optional[List[str]]
    
    class Config:
        from_attributes = True


# ============================================================
# Triage Schemas
# ============================================================
class TriageRequest(BaseModel):
    chief_complaint: str
    vitals: Optional[Dict[str, Any]] = None
    clinical_history: Optional[str] = None


class TriageResponse(BaseModel):
    priority: Priority
    esi_level: Optional[int] = None
    matched_keywords: List[str] = []
    reasoning: str
    processing_time_ms: float


# ============================================================
# Clinical Schemas
# ============================================================
class SymptomAnalysisRequest(BaseModel):
    symptoms: List[str]
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    medical_history: Optional[List[str]] = []


class SymptomAnalysisResponse(BaseModel):
    differential_diagnoses: List[Dict[str, Any]]
    red_flags: List[str]
    recommended_workup: List[str]
    urgency: Priority
    model_used: str
    processing_time_ms: float


class PrescriptionValidateRequest(BaseModel):
    medications: List[Dict[str, str]]  # {drug, dose, frequency}
    patient_id: Optional[int] = None
    patient_allergies: Optional[List[str]] = []


class PrescriptionValidateResponse(BaseModel):
    safety_status: str  # PASS, REVIEW_REQUIRED, REJECT
    interactions: List[Dict[str, Any]]
    dosing_issues: List[Dict[str, Any]]
    recommendations: List[str]


class LabInterpretRequest(BaseModel):
    lab_results: Dict[str, Any]
    patient_id: Optional[int] = None
    clinical_context: Optional[str] = None


class LabInterpretResponse(BaseModel):
    abnormal_findings: List[Dict[str, Any]]
    clinical_significance: str
    follow_up_tests: List[str]
    overall_assessment: str


# ============================================================
# Imaging Schemas
# ============================================================
class ImagingAnalysisRequest(BaseModel):
    study_id: str
    modality: Modality
    referral_notes: str
    patient_id: Optional[int] = None
    clinical_history: Optional[str] = None
    image_data: Optional[str] = None  # Base64 encoded


class ImagingAnalysisResponse(BaseModel):
    study_id: str
    modality: str
    priority: Priority
    critical_alert: bool
    findings: List[Dict[str, Any]]
    scoring: Optional[Dict[str, Any]] = None
    report: Optional[Dict[str, Any]] = None
    processing_time_ms: float


class DermatologyRequest(BaseModel):
    patient_id: Optional[int] = None
    lesion_description: str
    patient_age: Optional[int] = None
    skin_type: Optional[str] = None
    sun_exposure: Optional[str] = None
    family_history_cancer: Optional[bool] = False
    image_data: Optional[str] = None  # Base64


class DermatologyResponse(BaseModel):
    priority: Priority
    classification: str
    detected_features: List[str]
    risk_cohort: Dict[str, Any]
    referral_recommendation: str
    processing_time_ms: float


# ============================================================
# Claims/RCM Schemas
# ============================================================
class ClaimCreateRequest(BaseModel):
    patient_id: int
    procedures: List[Dict[str, str]]  # {procedure, cpt_code}
    diagnosis_codes: List[str]
    total_charges: float
    payer: str
    pre_authorization: bool = False
    clinical_notes: Optional[str] = None


class ClaimAnalysisResponse(BaseModel):
    claim_id: Optional[int] = None
    denial_risk_score: float
    risk_factors: List[Dict[str, Any]]
    recommendations: List[str]
    coding_audit: Dict[str, Any]
    appeal_preview: Optional[str] = None


class ICD11CodingRequest(BaseModel):
    clinical_text: str
    extracted_entities: Optional[List[Dict]] = None


class ICD11CodingResponse(BaseModel):
    codes: List[Dict[str, Any]]
    primary_diagnosis: Dict[str, Any]
    secondary_diagnoses: List[Dict[str, Any]]
    confidence: float


# ============================================================
# Monitoring Schemas
# ============================================================
class RPMDataRequest(BaseModel):
    patient_id: int
    wearable_data: List[Dict[str, Any]]  # Time series
    device_type: Optional[str] = None


class RPMAnalysisResponse(BaseModel):
    patient_id: int
    status: str  # NORMAL, WARNING, CRITICAL
    anomalies: List[Dict[str, Any]]
    risk_persona: Dict[str, Any]
    health_nudge: Optional[str] = None
    teleconsult_recommended: bool


class EDTriageRequest(BaseModel):
    patient_id: Optional[str] = None
    vitals: Dict[str, Any]  # hr, bp_systolic, spo2, gcs
    chief_complaint: str
    arrival_mode: Optional[str] = None  # ambulance, walk-in


class EDTriageResponse(BaseModel):
    esi_level: int
    color_code: str
    disposition: str
    max_wait_time: str
    teams_to_alert: Optional[List[str]] = []
    critical_alert: bool


# ============================================================
# Search Schemas
# ============================================================
class GuidelineSearchRequest(BaseModel):
    query: str
    specialty: Optional[str] = None
    max_results: int = 5


class GuidelineSearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    sources: List[str]
    synthesis: str
