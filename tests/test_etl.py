"""
Unit tests for ETL transform utilities.
Tests: date normalization, ISO3 mapping, monotonicity fixes, data validation.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import date
import sys
from pathlib import Path

# Add etl dir to path
sys.path.insert(0, str(Path(__file__).parent.parent / "etl"))

from transform_utils import (
    normalize_date,
    get_iso3_code,
    fix_monotonicity,
    long_format_timeseries,
    validate_data
)


class TestDateNormalization:
    """Test date normalization across formats."""
    
    def test_normalize_iso_format(self):
        result = normalize_date("2020-01-23")
        assert result.year == 2020
        assert result.month == 1
        assert result.day == 23
    
    def test_normalize_us_format(self):
        result = normalize_date("1/23/20")
        assert result.year == 2020
        assert result.month == 1
        assert result.day == 23
    
    def test_normalize_invalid_date(self):
        result = normalize_date("invalid")
        assert result is None
    
    def test_normalize_empty_string(self):
        result = normalize_date("")
        assert result is None
    
    def test_normalize_nan(self):
        result = normalize_date(np.nan)
        assert result is None


class TestISO3Mapping:
    """Test country name to ISO3 code mapping."""
    
    def test_direct_lookup_us(self):
        assert get_iso3_code("US") == "USA"
        assert get_iso3_code("USA") == "USA"
        assert get_iso3_code("United States") == "USA"
    
    def test_direct_lookup_uk(self):
        assert get_iso3_code("UK") == "GBR"
        assert get_iso3_code("United Kingdom") == "GBR"
    
    def test_case_insensitive_lookup(self):
        assert get_iso3_code("china") == "CHN"
        assert get_iso3_code("INDIA") == "IND"
    
    def test_unmapped_country(self):
        result = get_iso3_code("Atlantis")
        assert result is None
    
    def test_nan_input(self):
        result = get_iso3_code(np.nan)
        assert result is None


class TestMonotonicity:
    """Test monotonicity fixing for cumulative data."""
    
    def test_already_monotonic(self):
        series = pd.Series([0, 10, 20, 30, 40])
        result = fix_monotonicity(series)
        expected = pd.Series([0, 10, 20, 30, 40])
        pd.testing.assert_series_equal(result, expected, check_dtype=False)
    
    def test_with_nan_values(self):
        series = pd.Series([0, 10, np.nan, 30, 40])
        result = fix_monotonicity(series)
        assert result[0] == 0
        assert pd.notna(result[2]) or result[2] >= result[1]  # Fixed or forward-filled
    
    def test_decreasing_values_fixed(self):
        series = pd.Series([0, 10, 20, 15, 25])  # 15 is a decrease
        result = fix_monotonicity(series)
        assert result[0] == 0
        assert result[1] == 10
        assert result[2] == 20
        assert result[3] >= 20  # Should be fixed to >= previous
    
    def test_empty_series(self):
        series = pd.Series([], dtype=float)
        result = fix_monotonicity(series)
        assert len(result) == 0


class TestLongFormatConversion:
    """Test wide-to-long format conversion for timeseries."""
    
    def test_basic_conversion(self):
        df = pd.DataFrame({
            "date": ["2020-01-23", "2020-01-24"],
            "US": [1, 2],
            "China": [100, 101],
            "Japan": [0, 1]
        })
        result = long_format_timeseries(df, metric_col="confirmed_cases")
        
        assert len(result) == 6  # 2 dates × 3 countries
        assert "iso3" in result.columns
        assert "date" in result.columns
        assert "country" in result.columns
        assert "confirmed_cases" in result.columns
        assert result["iso3"].isin(["USA", "CHN", "JPN"]).all()
    
    def test_negative_values_filtered(self):
        df = pd.DataFrame({
            "date": ["2020-01-23"],
            "US": [-5],
            "China": [100]
        })
        result = long_format_timeseries(df, metric_col="test_metric")
        
        # Negative value should be NaN
        us_row = result[result["country"] == "US"]
        assert us_row["test_metric"].isna().all()


class TestDataValidation:
    """Test data quality validation."""
    
    def test_valid_data(self):
        df = pd.DataFrame({
            "date": [date(2020, 1, 23), date(2020, 1, 24)],
            "iso3": ["USA", "GBR"],
            "country": ["United States", "United Kingdom"],
            "confirmed_cases": [1, 2]
        })
        assert validate_data(df) is True
    
    def test_empty_dataframe(self):
        df = pd.DataFrame()
        assert validate_data(df) is False
    
    def test_missing_required_columns(self):
        df = pd.DataFrame({
            "date": [date(2020, 1, 23)],
            "country": ["US"]
            # Missing iso3
        })
        assert validate_data(df) is False


class TestIntegration:
    """Integration tests for full pipelines."""
    
    def test_end_to_end_transform(self):
        """Test a small end-to-end transformation."""
        df = pd.DataFrame({
            "Date": ["1/23/20", "1/24/20", "1/25/20"],
            "US": [0, 1, 2],
            "China": [100, 105, 110],
            "India": [0, 0, 1]
        })
        
        # Rename for conversion
        df = df.rename(columns={"Date": "date"})
        result = long_format_timeseries(df, metric_col="cases")
        
        assert len(result) > 0
        assert all(col in result.columns for col in ["date", "iso3", "country", "cases"])
        
        # Check USA data
        usa_data = result[result["iso3"] == "USA"].sort_values("date")
        if len(usa_data) > 0:
            assert usa_data["cases"].iloc[0] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
