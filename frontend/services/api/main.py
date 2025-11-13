"""
COVID-19 Data API - FastAPI backend serving timeseries and aggregated data.
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date, datetime
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="COVID-19 Data API",
    description="Timeseries and aggregated COVID-19 data by country",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global data cache
_data_cache = {}
_last_load_time = None



# ============ Response Schemas (plain structures) ============
# Pydantic model classes removed for compatibility with pydantic v2.
# Endpoints will return plain dict/list structures instead of BaseModel instances.

# ============ Helper Functions ============

def load_data():
    """Load parquet data into cache."""
    global _data_cache, _last_load_time
    
    # Check both possible output locations for generated parquet files
    repo_root = Path(__file__).parent.parent.parent
    candidates = [repo_root / "etl" / "output", repo_root / "output"]

    try:
        timeseries_file = None
        for d in candidates:
            candidate = d / "timeseries.parquet"
            if candidate.exists():
                timeseries_file = candidate
                break

        if timeseries_file is None:
            logger.warning(f"Timeseries file not found in {candidates}")
            return False

        logger.info(f"Loading timeseries from {timeseries_file}")
        df = pd.read_parquet(timeseries_file)
        _data_cache["timeseries"] = df
        _last_load_time = datetime.now()
        logger.info(f"Loaded {len(df)} records from {len(df['iso3'].unique())} countries")
        return True
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return False


def get_timeseries_df() -> Optional[pd.DataFrame]:
    """Get cached timeseries dataframe."""
    if "timeseries" not in _data_cache:
        if not load_data():
            return None
    return _data_cache.get("timeseries")


# ============ API Endpoints ============

@app.on_event("startup")
async def startup_event():
    """Load data on startup."""
    logger.info("Starting COVID-19 API...")
    load_data()


@app.get("/health", tags=["Health"])
async def health_check():
    """Check API health."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/api/v1/countries", tags=["Countries"])
async def list_countries():
    """Get list of all countries in dataset."""
    df = get_timeseries_df()
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="Data not available")
    
    countries = df[["iso3", "country"]].drop_duplicates().sort_values("country")
    return [
        {"iso3": row["iso3"], "name": row["country"]}
        for _, row in countries.iterrows()
    ]


@app.get("/api/v1/summary", tags=["Summary"])
async def global_summary(date_param: Optional[date] = Query(None, description="Date (YYYY-MM-DD), defaults to latest")):
    """Get global aggregated summary for a specific date."""
    df = get_timeseries_df()
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="Data not available")
    
    # Convert date column to date type if needed
    if df["date"].dtype == "object":
        df["date"] = pd.to_datetime(df["date"]).dt.date
    
    if date_param is None:
        date_param = df["date"].max()
    
    # Filter for the specific date
    day_data = df[df["date"] == date_param]
    if day_data.empty:
        raise HTTPException(status_code=404, detail=f"No data for date {date_param}")
    
    # Calculate vaccination totals using only non-null values per country
    total_vacc = day_data["total_vaccinations"].sum()
    if pd.isna(total_vacc):
        total_vacc = 0
    
    fully_vacc = day_data["people_fully_vaccinated"].sum()
    if pd.isna(fully_vacc):
        fully_vacc = 0
    
    return {
        "date": str(date_param),
        "total_confirmed_cases": float(day_data["confirmed_cases"].sum() or 0),
        "total_deaths": float(day_data["deaths"].sum() or 0),
        "total_vaccinations": float(total_vacc),
        "people_fully_vaccinated": float(fully_vacc),
        "countries_affected": int((day_data["confirmed_cases"] > 0).sum())
    }


@app.get("/api/v1/countries/{iso3}/timeseries", tags=["Timeseries"])
async def country_timeseries(
    iso3: str,
    metric: Optional[str] = Query("all", description="Metric: confirmed_cases, deaths, vaccinations, or all"),
    from_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get timeseries data for a specific country."""
    df = get_timeseries_df()
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="Data not available")
    
    # Filter by ISO3
    iso3_upper = iso3.upper()
    country_data = df[df["iso3"] == iso3_upper].copy()
    
    if country_data.empty:
        raise HTTPException(status_code=404, detail=f"Country {iso3} not found")
    
    # Convert date column
    if country_data["date"].dtype == "object":
        country_data["date"] = pd.to_datetime(country_data["date"]).dt.date
    
    # Filter by date range
    if from_date:
        country_data = country_data[country_data["date"] >= from_date]
    if to_date:
        country_data = country_data[country_data["date"] <= to_date]
    
    country_data = country_data.sort_values("date")
    
    country_name = country_data["country"].iloc[0] if not country_data.empty else iso3
    
    # Build response
    data_points = []
    for _, row in country_data.iterrows():
        data_points.append({
            "date": str(row["date"]),
            "confirmed_cases": float(row["confirmed_cases"]) if pd.notna(row["confirmed_cases"]) else None,
            "deaths": float(row["deaths"]) if pd.notna(row["deaths"]) else None,
            "total_vaccinations": float(row["total_vaccinations"]) if pd.notna(row["total_vaccinations"]) else None,
            "people_vaccinated": float(row.get("people_vaccinated")) if pd.notna(row.get("people_vaccinated")) else None,
            "people_fully_vaccinated": float(row.get("people_fully_vaccinated")) if pd.notna(row.get("people_fully_vaccinated")) else None,
            "daily_vaccinations": float(row.get("daily_vaccinations")) if pd.notna(row.get("daily_vaccinations")) else None,
        })
    
    return {
        "iso3": iso3_upper,
        "country": country_name,
        "data": data_points
    }


@app.get("/api/v1/metrics", tags=["Metadata"])
async def available_metrics():
    """List available metrics in the dataset."""
    return {
        "metrics": [
            "confirmed_cases",
            "deaths",
            "total_vaccinations",
            "people_vaccinated",
            "people_fully_vaccinated",
            "daily_vaccinations"
        ]
    }


@app.get("/api/v1/dates", tags=["Metadata"])
async def available_dates():
    """Get date range of available data."""
    df = get_timeseries_df()
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="Data not available")
    
    if df["date"].dtype == "object":
        dates = pd.to_datetime(df["date"]).dt.date
    else:
        dates = df["date"]
    
    return {
        "min_date": str(dates.min()),
        "max_date": str(dates.max()),
        "total_days": int(dates.nunique())
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
