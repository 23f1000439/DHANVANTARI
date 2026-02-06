"""
Unit Tests for Radiology Pipeline
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.application.services.radiology_pipeline import RadiologyPipeline


class TestRadiologyPipeline:
    
    @pytest.fixture
    def pipeline(self):
        return RadiologyPipeline()
    
    def test_initialization(self, pipeline):
        """Test pipeline initializes with modality configs."""
        assert pipeline.modality_configs is not None
        assert "X-Ray" in pipeline.modality_configs
        assert "CT" in pipeline.modality_configs
        assert "MRI" in pipeline.modality_configs
    
    def test_cnn_quality_no_image(self, pipeline):
        """Test CNN rejects when no image provided."""
        result = pipeline.cnn_image_quality_check(None, "CT")
        assert result["status"] == "rejected"
        assert result["ready_for_analysis"] == False
    
    def test_cnn_quality_with_image(self, pipeline):
        """Test CNN accepts when image provided."""
        result = pipeline.cnn_image_quality_check(b"fake_dicom", "CT")
        assert result["status"] == "accepted"
        assert result["quality_score"] > 0.8
        assert result["ready_for_analysis"] == True
    
    def test_triage_stat_priority(self, pipeline):
        """Test NB assigns STAT priority for urgent cases."""
        result = pipeline.triage_referral_nb("STAT CT head, r/o stroke, acute symptoms")
        assert result["priority"] == "STAT"
        assert result["max_report_time"] == "1 hour"
    
    def test_triage_routine_priority(self, pipeline):
        """Test NB assigns ROUTINE priority for screening."""
        result = pipeline.triage_referral_nb("Routine follow-up chest X-ray, annual screening")
        assert result["priority"] == "ROUTINE"
    
    def test_medgemma_critical_finding(self, pipeline):
        """Test MedGemma detects critical findings."""
        result = pipeline.analyze_imaging_medgemma(
            b"fake_ct", "CT", "r/o pulmonary embolism, acute chest pain"
        )
        assert result["critical_alert"] == True
        assert any("embolism" in f["finding"].lower() for f in result["findings"])
    
    def test_medgemma_ct_appendicitis(self, pipeline):
        """Test MedGemma detects appendicitis in CT."""
        result = pipeline.analyze_imaging_medgemma(
            b"fake_ct", "CT", "RLQ pain, r/o appendicitis"
        )
        assert any("appendicitis" in f["finding"].lower() for f in result["findings"])
    
    def test_medgemma_mri_disc_herniation(self, pipeline):
        """Test MedGemma detects disc herniation in MRI."""
        result = pipeline.analyze_imaging_medgemma(
            b"fake_mri", "MRI", "Lower back pain, r/o disc herniation"
        )
        assert any("disc" in f["finding"].lower() or "herniation" in f["finding"].lower() 
                   for f in result["findings"])
    
    def test_medgemma_normal_findings(self, pipeline):
        """Test MedGemma handles normal exams."""
        result = pipeline.analyze_imaging_medgemma(
            b"fake_xray", "X-Ray", "routine chest xray, no symptoms"
        )
        assert result["critical_alert"] == False
        assert any("no acute" in f["finding"].lower() for f in result["findings"])
    
    def test_birads_scoring_mammography(self, pipeline):
        """Test BIRADS scoring for mammography."""
        findings = [{"finding": "Mass", "severity": "MODERATE"}]
        result = pipeline.compute_standardized_score(findings, "Mammography")
        assert result["scoring_applicable"] == True
        assert result["scoring_system"] == "BIRADS"
    
    def test_lungrads_scoring_ct(self, pipeline):
        """Test Lung-RADS scoring for CT."""
        findings = [{"finding": "Pulmonary Nodule", "severity": "MODERATE"}]
        result = pipeline.compute_standardized_score(findings, "CT")
        assert result["scoring_applicable"] == True
        assert result["scoring_system"] == "LungRADS"
    
    def test_audit_trail_logging(self, pipeline):
        """Test audit trail creates entry."""
        result = {
            "analysis": {"modality": "CT", "critical_alert": True, "finding_count": 2},
            "triage": {"priority": "STAT"},
            "scoring": {"scoring_system": "LungRADS"}
        }
        audit = pipeline.log_audit_trail("STUDY-001", result)
        assert audit["study_id"] == "STUDY-001"
        assert audit["compliance"]["hipaa_logged"] == True


class TestRadiologyIntegration:
    """Integration tests for radiology pipeline flow."""
    
    def test_stat_ct_flow(self):
        """Test STAT CT full flow."""
        pipeline = RadiologyPipeline()
        
        quality = pipeline.cnn_image_quality_check(b"image", "CT")
        triage = pipeline.triage_referral_nb("STAT CT abdomen, acute abdominal pain, r/o appendicitis")
        analysis = pipeline.analyze_imaging_medgemma(b"image", "CT", "acute abdominal pain, r/o appendicitis")
        scoring = pipeline.compute_standardized_score(analysis["findings"], "CT")
        
        assert quality["ready_for_analysis"] == True
        assert triage["priority"] == "STAT"
        assert any("appendicitis" in str(f).lower() for f in analysis["findings"])
    
    def test_routine_xray_flow(self):
        """Test routine X-Ray flow."""
        pipeline = RadiologyPipeline()
        
        quality = pipeline.cnn_image_quality_check(b"image", "X-Ray")
        triage = pipeline.triage_referral_nb("Routine chest X-ray, annual physical")
        analysis = pipeline.analyze_imaging_medgemma(b"image", "X-Ray", "routine screening")
        
        assert quality["ready_for_analysis"] == True
        assert triage["priority"] == "ROUTINE"
        assert analysis["critical_alert"] == False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
