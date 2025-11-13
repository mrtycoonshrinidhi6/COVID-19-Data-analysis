"""
Integration tests for FastAPI backend.
Tests: endpoints, schemas, data loading, response validation.
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from datetime import date, datetime
import pandas as pd
import sys
import tempfile

# Mock data setup
@pytest.fixture
def mock_timeseries_data():
    """Create mock timeseries data for testing."""
    data = {
        "date": [date(2020, 3, 15), date(2020, 3, 16), date(2020, 3, 15), date(2020, 3, 16)],
        "country": ["United States", "United States", "United Kingdom", "United Kingdom"],
        "iso3": ["USA", "USA", "GBR", "GBR"],
        "confirmed_cases": [2000.0, 2500.0, 1000.0, 1200.0],
        "deaths": [50.0, 75.0, 30.0, 40.0],
        "total_vaccinations": [None, None, None, None],
        "people_vaccinated": [None, None, None, None],
        "people_fully_vaccinated": [None, None, None, None],
        "daily_vaccinations": [None, None, None, None],
    }
    return pd.DataFrame(data)


@pytest.fixture
def test_client(mock_timeseries_data, tmp_path):
    """Create test client with mock data."""
    # Save mock data to temporary file
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    parquet_file = output_dir / "timeseries.parquet"
    mock_timeseries_data.to_parquet(parquet_file)
    
    # Patch the data loading path
    import sys
    from pathlib import Path
    
    # Create a mock main module with patched path
    sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "api"))
    
    from main import app, _data_cache
    _data_cache["timeseries"] = mock_timeseries_data
    
    return TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self, test_client):
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestCountriesEndpoint:
    """Test countries listing endpoint."""
    
    def test_list_countries(self, test_client):
        response = test_client.get("/api/v1/countries")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check schema
        for item in data:
            assert "iso3" in item
            assert "name" in item
    
    def test_countries_contain_usa(self, test_client):
        response = test_client.get("/api/v1/countries")
        data = response.json()
        iso_codes = [c["iso3"] for c in data]
        assert "USA" in iso_codes


class TestSummaryEndpoint:
    """Test global summary endpoint."""
    
    def test_summary_latest_date(self, test_client):
        response = test_client.get("/api/v1/summary")
        assert response.status_code == 200
        data = response.json()
        
        # Validate schema
        assert "date" in data
        assert "total_confirmed_cases" in data
        assert "total_deaths" in data
        assert "total_vaccinations" in data
        assert "countries_affected" in data
        
        # Validate types
        assert isinstance(data["total_confirmed_cases"], (int, float))
        assert isinstance(data["total_deaths"], (int, float))
        assert isinstance(data["countries_affected"], int)
    
    def test_summary_specific_date(self, test_client):
        response = test_client.get("/api/v1/summary?date_param=2020-03-15")
        assert response.status_code == 200
        data = response.json()
        assert data["date"] == "2020-03-15"
        assert data["total_confirmed_cases"] == 3000.0  # USA: 2000 + GBR: 1000
        assert data["total_deaths"] == 80.0  # USA: 50 + GBR: 30
    
    def test_summary_invalid_date(self, test_client):
        response = test_client.get("/api/v1/summary?date_param=1999-01-01")
        assert response.status_code == 404


class TestTimeseriesEndpoint:
    """Test country timeseries endpoint."""
    
    def test_timeseries_usa(self, test_client):
        response = test_client.get("/api/v1/countries/USA/timeseries")
        assert response.status_code == 200
        data = response.json()
        
        # Validate schema
        assert data["iso3"] == "USA"
        assert data["country"] == "United States"
        assert "data" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 2
    
    def test_timeseries_data_points(self, test_client):
        response = test_client.get("/api/v1/countries/USA/timeseries")
        data = response.json()
        
        for point in data["data"]:
            assert "date" in point
            assert "confirmed_cases" in point
            assert "deaths" in point
    
    def test_timeseries_case_insensitive(self, test_client):
        response1 = test_client.get("/api/v1/countries/USA/timeseries")
        response2 = test_client.get("/api/v1/countries/usa/timeseries")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.json()["iso3"] == response2.json()["iso3"]
    
    def test_timeseries_date_filter(self, test_client):
        response = test_client.get("/api/v1/countries/USA/timeseries?from_date=2020-03-16&to_date=2020-03-16")
        assert response.status_code == 200
        data = response.json()
        
        # Should have only 1 data point for March 16
        assert len(data["data"]) == 1
        assert data["data"][0]["date"] == "2020-03-16"
    
    def test_timeseries_country_not_found(self, test_client):
        response = test_client.get("/api/v1/countries/XYZ/timeseries")
        assert response.status_code == 404


class TestMetadataEndpoints:
    """Test metadata endpoints."""
    
    def test_available_metrics(self, test_client):
        response = test_client.get("/api/v1/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert "confirmed_cases" in data["metrics"]
        assert "deaths" in data["metrics"]
    
    def test_available_dates(self, test_client):
        response = test_client.get("/api/v1/dates")
        assert response.status_code == 200
        data = response.json()
        
        assert "min_date" in data
        assert "max_date" in data
        assert "total_days" in data
        assert data["min_date"] == "2020-03-15"
        assert data["max_date"] == "2020-03-16"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
