"""Unit tests for output models (WebAppSpec, VerificationReport, etc.).

Tests Pydantic model validation, serialization, and edge cases.
"""

from __future__ import annotations

import json
import pytest
from pydantic import ValidationError

from src.models import (
    WebAppSpec,
    GeneratedWebApp,
    VerificationReport,
    ConversionResult,
    GeneratedCode,
)

from tests.helpers import (
    get_webapp_spec_output,
    get_generated_webapp_output,
    get_test_evaluation_output,
)


class TestWebAppSpecModel:
    """Tests for WebAppSpec model."""

    def test_webapp_spec_minimal(self):
        """Test creating WebAppSpec with minimal required fields."""
        spec = WebAppSpec(
            app_name="테스트",
            app_description="테스트 앱",
        )
        assert spec.app_name == "테스트"
        assert spec.app_description == "테스트 앱"
        assert spec.input_fields == []
        assert spec.output_fields == []
        assert spec.korean_labels is True  # Default

    def test_webapp_spec_full(self):
        """Test creating WebAppSpec with all fields."""
        spec_dict = get_webapp_spec_output()
        spec = WebAppSpec(**spec_dict)

        assert spec.app_name == "테스트 앱"
        assert len(spec.input_fields) == 1
        assert len(spec.output_fields) == 1
        assert len(spec.calculations) == 1
        assert len(spec.expected_behaviors) == 2
        assert len(spec.boundary_conditions) == 1
        assert spec.korean_labels is True
        assert spec.print_layout["paper_size"] == "A4"

    def test_webapp_spec_input_field_structure(self):
        """Test input field structure in WebAppSpec."""
        spec_dict = get_webapp_spec_output()
        spec = WebAppSpec(**spec_dict)

        field = spec.input_fields[0]
        assert field["name"] == "salary"
        assert field["type"] == "number"
        assert field["label"] == "급여"
        assert field["source_cell"] == "B3"
        assert "validation" in field

    def test_webapp_spec_output_field_structure(self):
        """Test output field structure in WebAppSpec."""
        spec_dict = get_webapp_spec_output()
        spec = WebAppSpec(**spec_dict)

        field = spec.output_fields[0]
        assert field["name"] == "tax"
        assert field["format"] == "currency"
        assert field["label"] == "세금"
        assert field["source_cell"] == "B10"
        assert field["source_formula"] == "=B3*0.1"

    def test_webapp_spec_calculation_structure(self):
        """Test calculation structure in WebAppSpec."""
        spec_dict = get_webapp_spec_output()
        spec = WebAppSpec(**spec_dict)

        calc = spec.calculations[0]
        assert calc["name"] == "calculate_tax"
        assert "salary" in calc["inputs"]
        assert calc["output"] == "tax"
        assert calc["formula"] == "=B3*0.1"

    def test_webapp_spec_serialization(self):
        """Test WebAppSpec JSON serialization."""
        spec_dict = get_webapp_spec_output()
        spec = WebAppSpec(**spec_dict)

        # Serialize and deserialize
        json_str = spec.model_dump_json()
        restored = WebAppSpec.model_validate_json(json_str)

        assert restored.app_name == spec.app_name
        assert restored.input_fields == spec.input_fields

    def test_webapp_spec_empty_expected_behaviors(self):
        """Test WebAppSpec with empty expected_behaviors."""
        spec = WebAppSpec(
            app_name="테스트",
            app_description="테스트",
            expected_behaviors=[],
        )
        assert spec.expected_behaviors == []

    def test_webapp_spec_empty_boundary_conditions(self):
        """Test WebAppSpec with empty boundary_conditions."""
        spec = WebAppSpec(
            app_name="테스트",
            app_description="테스트",
            boundary_conditions=[],
        )
        assert spec.boundary_conditions == []


class TestVerificationReportModel:
    """Tests for VerificationReport model."""

    def test_verification_report_minimal(self):
        """Test creating VerificationReport with minimal fields."""
        report = VerificationReport(
            spec_name="테스트",
            total_requirements=5,
            verified_requirements=4,
            unverified_requirements=1,
            verification_rate=0.8,
        )
        assert report.spec_name == "테스트"
        assert report.verification_rate == 0.8

    def test_verification_report_full(self):
        """Test creating VerificationReport with all fields."""
        report = VerificationReport(
            spec_name="테스트 앱",
            total_requirements=10,
            verified_requirements=9,
            unverified_requirements=1,
            verification_rate=0.9,
            requirement_results=[
                {
                    "requirement": "Tax calculation",
                    "test_name": "test_tax",
                    "passed": True,
                    "details": "OK",
                }
            ],
            static_test_pass_rate=0.95,
            llm_evaluation_pass_rate=0.85,
            combined_pass_rate=0.91,
            blocking_issues=["Critical bug"],
            warnings=["Minor issue"],
        )
        assert len(report.requirement_results) == 1
        assert report.static_test_pass_rate == 0.95
        assert report.llm_evaluation_pass_rate == 0.85
        assert report.combined_pass_rate == 0.91
        assert len(report.blocking_issues) == 1
        assert len(report.warnings) == 1

    def test_verification_report_weighted_score(self):
        """Test that combined_pass_rate follows 60/40 weighting."""
        static_rate = 0.90
        llm_rate = 0.80
        expected_combined = static_rate * 0.6 + llm_rate * 0.4  # 0.86

        report = VerificationReport(
            spec_name="테스트",
            total_requirements=10,
            verified_requirements=8,
            unverified_requirements=2,
            verification_rate=0.8,
            static_test_pass_rate=static_rate,
            llm_evaluation_pass_rate=llm_rate,
            combined_pass_rate=expected_combined,
        )

        assert abs(report.combined_pass_rate - expected_combined) < 0.001

    def test_verification_report_serialization(self):
        """Test VerificationReport JSON serialization."""
        report = VerificationReport(
            spec_name="테스트",
            total_requirements=5,
            verified_requirements=5,
            unverified_requirements=0,
            verification_rate=1.0,
        )

        json_str = report.model_dump_json()
        restored = VerificationReport.model_validate_json(json_str)

        assert restored.spec_name == report.spec_name
        assert restored.verification_rate == report.verification_rate


class TestGeneratedWebAppModel:
    """Tests for GeneratedWebApp model."""

    def test_generated_webapp_minimal(self):
        """Test creating GeneratedWebApp with required fields."""
        webapp = GeneratedWebApp(
            app_name="테스트",
            source_excel="test.xlsx",
            html="<html></html>",
            css="body {}",
            js="function test() {}",
        )
        assert webapp.app_name == "테스트"
        assert webapp.html == "<html></html>"

    def test_generated_webapp_full(self):
        """Test creating GeneratedWebApp with all fields."""
        webapp_dict = get_generated_webapp_output()
        webapp = GeneratedWebApp(**webapp_dict)

        assert webapp.app_name == "테스트 앱"
        assert webapp.source_excel == "test.xlsx"
        assert "<!DOCTYPE html>" in webapp.html
        assert webapp.css is not None
        assert webapp.js is not None
        assert webapp.generation_iteration == 1

    def test_generated_webapp_html_contains_structure(self):
        """Test that generated HTML contains required structure."""
        webapp_dict = get_generated_webapp_output()
        webapp = GeneratedWebApp(**webapp_dict)

        assert "<html" in webapp.html
        assert "<head>" in webapp.html
        assert "<body>" in webapp.html
        assert "</html>" in webapp.html

    def test_generated_webapp_serialization(self):
        """Test GeneratedWebApp JSON serialization."""
        webapp_dict = get_generated_webapp_output()
        webapp = GeneratedWebApp(**webapp_dict)

        json_str = webapp.model_dump_json()
        restored = GeneratedWebApp.model_validate_json(json_str)

        assert restored.app_name == webapp.app_name
        assert restored.html == webapp.html


class TestConversionResultModel:
    """Tests for ConversionResult model."""

    def test_conversion_result_success(self):
        """Test creating successful ConversionResult."""
        webapp_dict = get_generated_webapp_output()
        webapp = GeneratedWebApp(**webapp_dict)

        result = ConversionResult(
            success=True,
            app=webapp,
            iterations_used=1,
            final_pass_rate=0.95,
            message="Conversion successful",
        )

        assert result.success is True
        assert result.app is not None
        assert result.iterations_used == 1

    def test_conversion_result_failure(self):
        """Test creating failed ConversionResult."""
        result = ConversionResult(
            success=False,
            app=None,
            iterations_used=3,
            final_pass_rate=0.5,
            message="Maximum iterations exceeded",
        )

        assert result.success is False
        assert result.app is None
        assert result.message == "Maximum iterations exceeded"

    def test_conversion_result_with_verification_report(self):
        """Test ConversionResult with VerificationReport."""
        webapp_dict = get_generated_webapp_output()
        webapp = GeneratedWebApp(**webapp_dict)

        report = VerificationReport(
            spec_name="테스트",
            total_requirements=5,
            verified_requirements=5,
            unverified_requirements=0,
            verification_rate=1.0,
        )

        result = ConversionResult(
            success=True,
            app=webapp,
            iterations_used=1,
            final_pass_rate=1.0,
            message="Success",
            verification_report=report,
        )

        assert result.verification_report is not None
        assert result.verification_report.verification_rate == 1.0


class TestModelValidation:
    """Tests for model validation and error handling."""

    def test_webapp_spec_requires_app_name(self):
        """Test that WebAppSpec requires app_name."""
        with pytest.raises(ValidationError):
            WebAppSpec(app_description="Missing name")

    def test_verification_report_requires_all_counts(self):
        """Test that VerificationReport requires all requirement counts."""
        with pytest.raises(ValidationError):
            VerificationReport(
                spec_name="테스트",
                total_requirements=5,
                # Missing verified_requirements, unverified_requirements
                verification_rate=0.8,
            )

    def test_generated_webapp_requires_html(self):
        """Test that GeneratedWebApp requires html field."""
        with pytest.raises(ValidationError):
            GeneratedWebApp(
                app_name="테스트",
                source_excel="test.xlsx",
                # Missing html, css, js
            )

    def test_model_extra_fields_ignored(self):
        """Test that extra fields are handled correctly."""
        spec_dict = get_webapp_spec_output()
        spec_dict["unknown_field"] = "should be ignored"

        # This should not raise an error (Pydantic default is to ignore extra)
        spec = WebAppSpec(**spec_dict)
        assert spec.app_name == "테스트 앱"


class TestModelEdgeCases:
    """Tests for model edge cases."""

    def test_webapp_spec_unicode_handling(self):
        """Test that models handle Unicode (Korean) correctly."""
        spec = WebAppSpec(
            app_name="한글 이름 테스트",
            app_description="설명도 한글로 작성",
            expected_behaviors=["급여 5000000원 → 세금 500000원"],
        )

        assert "한글" in spec.app_name
        assert "급여" in spec.expected_behaviors[0]

    def test_webapp_spec_large_expected_behaviors(self):
        """Test WebAppSpec with many expected behaviors."""
        behaviors = [f"Behavior {i}" for i in range(100)]
        spec = WebAppSpec(
            app_name="테스트",
            app_description="테스트",
            expected_behaviors=behaviors,
        )

        assert len(spec.expected_behaviors) == 100

    def test_verification_report_zero_requirements(self):
        """Test VerificationReport with zero requirements."""
        report = VerificationReport(
            spec_name="빈 스펙",
            total_requirements=0,
            verified_requirements=0,
            unverified_requirements=0,
            verification_rate=1.0,  # 0/0 = 100%
        )

        assert report.total_requirements == 0
        assert report.verification_rate == 1.0

    def test_generated_webapp_empty_css_js(self):
        """Test GeneratedWebApp with empty CSS and JS."""
        webapp = GeneratedWebApp(
            app_name="테스트",
            source_excel="test.xlsx",
            html="<html></html>",
            css="",
            js="",
        )

        assert webapp.css == ""
        assert webapp.js == ""


class TestGeneratedCodeModel:
    """Tests for GeneratedCode model."""

    def test_generated_code_creation(self):
        """Test creating GeneratedCode."""
        code = GeneratedCode(
            component_name="calculator",
            html="<div>Calculator</div>",
            css=".calc { color: blue; }",
            js="function calc() {}",
        )

        assert code.component_name == "calculator"
        assert code.html == "<div>Calculator</div>"
