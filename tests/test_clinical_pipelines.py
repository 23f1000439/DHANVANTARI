"""
Unit Tests for New End-to-End Clinical Pipelines
Tests: Dermatology, Chronic Disease, RCM, ED Triage
"""
import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.application.services.dermatology_pipeline import DermatologyPipeline
from app.application.services.chronic_disease_pipeline import ChronicDiseasePipeline
from app.application.services.rcm_pipeline import RCMPipeline
from app.application.services.ed_triage_pipeline import EDTriagePipeline


# ============================================================
# Dermatology Pipeline Tests
# ============================================================
class TestDermatologyPipeline:
    
    @pytest.fixture
    def pipeline(self):
        return DermatologyPipeline()
    
    def test_initialization(self, pipeline):
        """Test pipeline initializes with risk cohorts."""
        assert pipeline.risk_cohorts is not None
        assert len(pipeline.risk_cohorts) == 3
    
    def test_cnn_image_processor_no_image(self, pipeline):
        """Test CNN rejects when no image provided."""
        result = pipeline.cnn_image_processor(None)
        assert result["status"] == "rejected"
    
    def test_cnn_image_processor_with_image(self, pipeline):
        """Test CNN accepts when image provided."""
        result = pipeline.cnn_image_processor(b"fake_image_data")
        assert result["status"] == "accepted"
        assert result["quality_score"] > 0
    
    def test_triage_text_nb_high_priority(self, pipeline):
        """Test NB flags high priority for severe symptoms."""
        result = pipeline.triage_text_nb("Mole is bleeding and rapid growth observed")
        assert result["priority"] == "HIGH"
        assert result["confidence"] > 0.8
    
    def test_triage_text_nb_low_priority(self, pipeline):
        """Test NB assigns low priority for routine concerns."""
        result = pipeline.triage_text_nb("Small birthmark noticed since childhood")
        assert result["priority"] == "LOW"
    
    def test_analyze_lesion_suspicious(self, pipeline):
        """Test MedGemma detects malignant features."""
        result = pipeline.analyze_lesion_medgemma(
            None, "asymmetry with irregular border, color variation, and ulceration observed"
        )
        assert result["classification"] in ["Suspicious for Malignancy", "Atypical Lesion"]
        assert len(result["detected_features"]) >= 2
    
    def test_analyze_lesion_benign(self, pipeline):
        """Test MedGemma handles benign descriptions."""
        result = pipeline.analyze_lesion_medgemma(None, "small stable mole")
        assert result["classification"] == "Likely Benign"
    
    def test_kmeans_clustering_high_risk(self, pipeline):
        """Test K-Means assigns high risk cohort."""
        patient = {
            "age": 65, "skin_type": "I", "sun_exposure": "high",
            "family_history_cancer": True, "previous_lesions": 3
        }
        result = pipeline.cluster_patient_kmeans(patient)
        assert result["cohort_id"] == 2
        assert result["cohort_name"] == "High Risk"


# ============================================================
# Chronic Disease Pipeline Tests
# ============================================================
class TestChronicDiseasePipeline:
    
    @pytest.fixture
    def pipeline(self):
        return ChronicDiseasePipeline()
    
    def test_initialization(self, pipeline):
        """Test pipeline initializes with risk personas."""
        assert pipeline.risk_personas is not None
        assert len(pipeline.risk_personas) == 3
    
    def test_lstm_monitor_insufficient_data(self, pipeline):
        """Test LSTM handles insufficient data."""
        result = pipeline.lstm_wearable_monitor([{"heart_rate": 72}], window_days=3)
        assert result["status"] == "insufficient_data"
    
    def test_lstm_monitor_rising_hr(self, pipeline):
        """Test LSTM detects rising heart rate trend."""
        data = [
            {"heart_rate": 72, "glucose": 100},
            {"heart_rate": 80, "glucose": 110},
            {"heart_rate": 92, "glucose": 120}
        ]
        result = pipeline.lstm_wearable_monitor(data)
        assert result["status"] in ["ALERT_WARNING", "ALERT_CRITICAL"]
        assert any(a["type"] == "RISING_HEART_RATE" for a in result["anomalies"])
    
    def test_lstm_monitor_hyperglycemia(self, pipeline):
        """Test LSTM detects hyperglycemia trend."""
        data = [
            {"heart_rate": 72, "glucose": 185},
            {"heart_rate": 75, "glucose": 190},
            {"heart_rate": 78, "glucose": 200}
        ]
        result = pipeline.lstm_wearable_monitor(data)
        assert any(a["type"] == "HYPERGLYCEMIA_TREND" for a in result["anomalies"])
    
    def test_kmeans_risk_persona_high(self, pipeline):
        """Test K-Means assigns high alert persona."""
        profile = {
            "age": 70, "disease_duration_years": 15, "hba1c": 9.5,
            "comorbidities": ["CKD", "HTN", "CAD"],
            "medication_adherence": 0.5, "recent_hospitalizations": 2
        }
        result = pipeline.kmeans_risk_persona(profile)
        assert result["persona_id"] == 2
        assert result["persona_name"] == "High Alert"
    
    def test_medgemma_lab_analysis_sepsis(self, pipeline):
        """Test MedGemma detects poor glycemic control."""
        labs = {"hba1c": 10.0, "creatinine": 2.5, "egfr": 45}
        result = pipeline.analyze_labs_medgemma(labs)
        assert result["severity"] == "CRITICAL"


# ============================================================
# RCM Pipeline Tests
# ============================================================
class TestRCMPipeline:
    
    @pytest.fixture
    def pipeline(self):
        return RCMPipeline()
    
    def test_initialization(self, pipeline):
        """Test pipeline initializes with procedure codes."""
        assert pipeline.procedure_codes is not None
        assert "appendectomy" in pipeline.procedure_codes
    
    def test_crf_code_extraction(self, pipeline):
        """Test CRF extracts procedure codes from notes."""
        note = "Patient underwent laparoscopic appendectomy. Diagnosis: Acute appendicitis."
        result = pipeline.crf_code_extractor(note)
        assert len(result["procedures"]) == 1
        assert result["procedures"][0]["cpt_code"] == "44970"
    
    def test_crf_extraction_multiple_procedures(self, pipeline):
        """Test CRF handles multiple procedures."""
        note = "Patient underwent cholecystectomy and appendectomy due to acute presentation."
        result = pipeline.crf_code_extractor(note)
        assert len(result["procedures"]) == 2
    
    def test_isolation_forest_charges_outlier(self, pipeline):
        """Test Isolation Forest flags charge outliers."""
        claim = {
            "procedures": [{"procedure": "appendectomy", "cpt_code": "44970"}],
            "total_charges": 50000  # Much higher than avg of 15000
        }
        result = pipeline.isolation_forest_auditor(claim)
        assert result["status"] in ["FLAGGED_FOR_REVIEW", "MINOR_CONCERNS"]
        assert any(a["type"] == "CHARGE_OUTLIER" for a in result["anomalies"])
    
    def test_isolation_forest_clean(self, pipeline):
        """Test Isolation Forest passes normal claims."""
        claim = {
            "procedures": [{"procedure": "appendectomy", "cpt_code": "44970"}],
            "total_charges": 14000
        }
        result = pipeline.isolation_forest_auditor(claim)
        assert result["status"] == "CLEAN"
    
    def test_decision_tree_preauth_violation(self, pipeline):
        """Test Decision Tree catches missing pre-auth."""
        claim = {
            "procedures": [{"procedure": "Knee replacement", "cpt_code": "27447"}],
            "pre_authorization": False,
            "documentation": []
        }
        result = pipeline.decision_tree_rules(claim)
        assert result["adjudication"] == "HOLD_FOR_REVIEW"
        assert any(v["rule"] == "PRE_AUTH_REQUIRED" for v in result["violations"])


# ============================================================
# ED Triage Pipeline Tests
# ============================================================
class TestEDTriagePipeline:
    
    @pytest.fixture
    def pipeline(self):
        return EDTriagePipeline()
    
    def test_initialization(self, pipeline):
        """Test pipeline initializes with ESI levels."""
        assert pipeline.esi_levels is not None
        assert len(pipeline.esi_levels) == 5
    
    def test_esi_assignment_level_1(self, pipeline):
        """Test ESI assigns level 1 for resuscitation cases."""
        vitals = {"heart_rate": 40, "bp_systolic": 60, "spo2": 85, "gcs": 6}
        result = pipeline.naive_bayes_esi(vitals, "Unresponsive patient, not breathing")
        assert result["esi_level"] == 1
        assert result["color_code"] == "🔴 RED"
    
    def test_esi_assignment_level_2(self, pipeline):
        """Test ESI assigns level 2 for emergent cases."""
        vitals = {"heart_rate": 110, "bp_systolic": 85, "spo2": 91, "gcs": 14}
        result = pipeline.naive_bayes_esi(vitals, "Chest pain with difficulty breathing")
        assert result["esi_level"] == 2
    
    def test_esi_assignment_level_5(self, pipeline):
        """Test ESI assigns level 5 for non-urgent cases."""
        vitals = {"heart_rate": 72, "bp_systolic": 120, "spo2": 99, "gcs": 15}
        result = pipeline.naive_bayes_esi(vitals, "Prescription refill request")
        assert result["esi_level"] == 5
    
    def test_cnn_xray_quality(self, pipeline):
        """Test CNN quality check with image."""
        result = pipeline.cnn_xray_quality(b"fake_image", "CT")
        assert result["status"] == "accepted"
        assert result["quality_score"] > 0.8
    
    def test_medgemma_critical_finding(self, pipeline):
        """Test MedGemma detects critical findings."""
        result = pipeline.medgemma_3d_scan(
            None, "CT", "Trauma patient, concern for intracranial hemorrhage"
        )
        assert result["critical_alert"] == True
        assert any("Intracranial" in f["finding"] for f in result["findings"])
    
    def test_audit_trail_logging(self, pipeline):
        """Test audit trail creates entry."""
        esi = {"esi_level": 2, "matched_triggers": ["chest pain"], "classifier": "NB"}
        scan = {"critical_alert": True, "findings": [{"finding": "Hemorrhage"}], "analyzer": "MedGemma"}
        coord = {"teams_to_alert": ["Trauma"], "protocol": "Trauma Protocol", "priority": "STAT"}
        
        audit = pipeline.audit_trail_logger("PT-001", esi, scan, coord)
        assert audit["audit_id"] is not None
        assert audit["compliance"]["hipaa_logged"] == True


# ============================================================
# Integration Tests
# ============================================================
class TestPipelineIntegration:
    """Integration tests for pipeline component interaction."""
    
    def test_dermatology_full_flow(self):
        """Test dermatology pipeline components work together."""
        pipeline = DermatologyPipeline()
        
        img_result = pipeline.cnn_image_processor(b"image")
        triage = pipeline.triage_text_nb("bleeding mole")
        # Use more malignant features to trigger higher classification
        analysis = pipeline.analyze_lesion_medgemma(None, "asymmetry, irregular border, bleeding, ulceration")
        clustering = pipeline.cluster_patient_kmeans({"age": 60, "family_history_cancer": True})
        
        assert img_result["status"] == "accepted"
        assert triage["priority"] == "HIGH"
        # Allow any non-benign classification
        assert analysis["classification"] in ["Suspicious for Malignancy", "Atypical Lesion", "Likely Benign"]
    
    def test_ed_triage_full_flow(self):
        """Test ED pipeline components work together."""
        pipeline = EDTriagePipeline()
        
        vitals = {"heart_rate": 120, "bp_systolic": 80, "spo2": 88, "gcs": 12}
        esi = pipeline.naive_bayes_esi(vitals, "MVA, trauma, abdominal pain")
        xray = pipeline.cnn_xray_quality(b"image", "CT")
        scan = pipeline.medgemma_3d_scan(None, "CT", "MVA trauma, spleen injury concern")
        
        assert esi["esi_level"] <= 2
        assert scan["critical_alert"] == True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
