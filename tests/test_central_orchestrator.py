"""
Unit Tests for Central Orchestrator and Pipelines
Tests: RAG, Digitalizer, Risk Stratification, Central Orchestrator Routing
"""
import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.application.services.rag_pipeline import HybridSearchRAG
from app.application.services.digitalizer_pipeline import ClinicalSlipDigitalizer
from app.application.services.risk_stratification_pipeline import BedsideRiskStratifier


# ============================================================
# Pipeline 1: HybridSearchRAG Tests
# ============================================================
class TestHybridSearchRAG:
    
    @pytest.fixture
    def rag(self):
        return HybridSearchRAG()
    
    def test_initialization(self, rag):
        """Test RAG pipeline initializes with document store."""
        assert rag.document_store is not None
        assert len(rag.document_store) > 0
    
    def test_hybrid_search_returns_results(self, rag):
        """Test hybrid search returns relevant results for sepsis query."""
        results = rag.hybrid_search_rag("sepsis management")
        assert len(results) > 0
        assert any("sepsis" in r['title'].lower() for r in results)
    
    def test_hybrid_search_prioritizes_recent(self, rag):
        """Test that more recent documents get higher scores."""
        results = rag.hybrid_search_rag("sepsis")
        if len(results) > 1:
            # First result should be most recent due to recency boost
            years = [r['year'] for r in results]
            assert years[0] >= max(years) - 1  # Within 1 year of most recent
    
    def test_validate_protocol_currency(self, rag):
        """Test MedGemma validation prioritizes recent protocols."""
        snippets = [
            {"id": "OLD", "year": 2020, "content": "Old protocol"},
            {"id": "NEW", "year": 2025, "content": "New protocol"}
        ]
        result = rag.validate_protocol_currency(snippets)
        assert result['status'] == 'validated'
        assert result['preferred_doc']['year'] == 2025
    
    def test_validate_empty_snippets(self, rag):
        """Test validation handles empty results gracefully."""
        result = rag.validate_protocol_currency([])
        assert result['status'] == 'no_results'


# ============================================================
# Pipeline 2: ClinicalSlipDigitalizer Tests
# ============================================================
class TestClinicalSlipDigitalizer:
    
    @pytest.fixture
    def digitalizer(self):
        return ClinicalSlipDigitalizer()
    
    def test_initialization(self, digitalizer):
        """Test digitalizer initializes with drug catalog."""
        assert digitalizer.drug_catalog is not None
        assert "amoxicillin" in digitalizer.drug_catalog
    
    def test_ocr_extraction(self, digitalizer):
        """Test OCR extracts prescription items."""
        result = digitalizer.extract_text_ocr("Rx: Amox 500mg TID")
        assert result['raw_text'] is not None
        assert len(result['extracted_items']) > 0
    
    def test_drug_catalog_matching(self, digitalizer):
        """Test drug matching normalizes to RxNorm."""
        items = [{"drug_raw": "amox", "dose_raw": "500mg", "frequency_raw": "TID"}]
        matched = digitalizer.match_drug_catalog(items)
        assert len(matched) == 1
        assert matched[0]['normalized_drug'] == "Amoxicillin"
        assert matched[0]['rxnorm_code'] == "723"
    
    def test_unknown_drug_handling(self, digitalizer):
        """Test unknown drugs are flagged appropriately."""
        items = [{"drug_raw": "unknowndrug123", "dose_raw": "100mg"}]
        matched = digitalizer.match_drug_catalog(items)
        assert matched[0]['rxnorm_code'] == "UNKNOWN"
        assert 'warning' in matched[0]
    
    def test_prescription_validation(self, digitalizer):
        """Test MedGemma validation checks dose forms."""
        items = [
            {"normalized_drug": "Amoxicillin", "dose_raw": "500mg", "valid_forms": ["250mg", "500mg", "875mg"]}
        ]
        result = digitalizer.validate_prescription(items)
        assert result['validation_status'] == "PASSED"
    
    def test_validation_fails_invalid_dose(self, digitalizer):
        """Test validation flags invalid doses."""
        items = [
            {"normalized_drug": "Amoxicillin", "dose_raw": "999mg", "valid_forms": ["250mg", "500mg"]}
        ]
        result = digitalizer.validate_prescription(items)
        assert result['validation_status'] == "REVIEW_REQUIRED"


# ============================================================
# Pipeline 3: BedsideRiskStratifier Tests
# ============================================================
class TestBedsideRiskStratifier:
    
    @pytest.fixture
    def stratifier(self):
        return BedsideRiskStratifier()
    
    def test_initialization(self, stratifier):
        """Test stratifier initializes with thresholds."""
        assert stratifier.sepsis_threshold > 0
    
    def test_triage_gate_emergency(self, stratifier):
        """Test triage gate detects emergency keywords."""
        result = stratifier.triage_gate_nb("Patient has chest pain and difficulty breathing")
        assert result['status'] == "EMERGENCY"
        assert result['confidence'] > 0.9
    
    def test_triage_gate_urgent(self, stratifier):
        """Test triage gate detects urgent keywords."""
        result = stratifier.triage_gate_nb("Patient has high fever and vomiting blood")
        assert result['status'] == "URGENT"
    
    def test_triage_gate_routine(self, stratifier):
        """Test triage gate handles routine cases."""
        result = stratifier.triage_gate_nb("Annual checkup, no complaints")
        assert result['status'] == "ROUTINE"
    
    def test_vitals_critical_case(self, stratifier):
        """Test vitals analysis flags critical case."""
        vitals = {
            "heart_rate": 130,
            "bp_systolic": 80,
            "spo2": 85,
            "temperature": 39.5,
            "respiratory_rate": 30
        }
        result = stratifier.vitals_anomaly_forest(vitals)
        assert result['alert_level'] == "CRITICAL"
        assert result['risk_score'] >= 0.7
    
    def test_vitals_stable_case(self, stratifier):
        """Test vitals analysis for stable patient."""
        vitals = {
            "heart_rate": 72,
            "bp_systolic": 120,
            "bp_diastolic": 80,
            "spo2": 98,
            "temperature": 37.0,
            "respiratory_rate": 16
        }
        result = stratifier.vitals_anomaly_forest(vitals)
        assert result['alert_level'] == "STABLE"
        assert result['risk_score'] < 0.4
    
    def test_lab_analysis_sepsis_markers(self, stratifier):
        """Test lab analysis detects sepsis markers."""
        labs = {"lactate": 5.0, "wbc": 15.0, "bands_percent": 12}
        result = stratifier.analyze_lab_pdf(labs)
        assert result['severity'] == "CRITICAL"
        assert result['sepsis_markers'] == True
    
    def test_lab_analysis_normal(self, stratifier):
        """Test lab analysis for normal values."""
        labs = {"lactate": 1.0, "wbc": 7.0, "bands_percent": 3, "creatinine": 1.0}
        result = stratifier.analyze_lab_pdf(labs)
        assert result['severity'] == "NORMAL"


# ============================================================
# Central Orchestrator Routing Tests
# ============================================================
class TestCentralOrchestratorRouting:
    """Tests for Central Orchestrator without live API calls."""
    
    @pytest.fixture
    def rag(self):
        return HybridSearchRAG()
    
    @pytest.fixture
    def digitalizer(self):
        return ClinicalSlipDigitalizer()
    
    @pytest.fixture
    def stratifier(self):
        return BedsideRiskStratifier()
    
    def test_rag_pipeline_integration(self, rag):
        """Test RAG pipeline components work together."""
        # Search
        results = rag.hybrid_search_rag("diabetes management")
        # Validate
        validated = rag.validate_protocol_currency(results)
        assert validated['status'] in ['validated', 'no_results']
    
    def test_digitalizer_pipeline_integration(self, digitalizer):
        """Test digitalizer pipeline components work together."""
        # OCR
        ocr = digitalizer.extract_text_ocr("Metformin 500mg BD")
        # Match
        matched = digitalizer.match_drug_catalog(ocr['extracted_items'])
        # Validate
        validated = digitalizer.validate_prescription(matched)
        assert validated['validation_status'] in ['PASSED', 'REVIEW_REQUIRED']
    
    def test_risk_pipeline_integration(self, stratifier):
        """Test risk stratification pipeline components work together."""
        # Triage
        triage = stratifier.triage_gate_nb("Sepsis suspected, fever and confusion")
        # Vitals
        vitals_result = stratifier.vitals_anomaly_forest({
            "heart_rate": 110, "bp_systolic": 90, "spo2": 91, "temperature": 38.5
        })
        # Labs
        labs_result = stratifier.analyze_lab_pdf({"lactate": 3.0, "wbc": 12.0})
        
        assert triage['status'] == "EMERGENCY"
        assert vitals_result['alert_level'] in ["CRITICAL", "WARNING"]


# ============================================================
# Run Tests
# ============================================================
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
