"""
ETL Transform Utilities for COVID-19 Data Processing.
Handles ISO3 canonicalization, date normalization, monotonicity fixes, and data validation.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# ISO3 country mapping - canonical reference
ISO3_COUNTRY_MAPPING = {
    "US": "USA", "United States": "USA", "USA": "USA", "United States of America": "USA",
    "UK": "GBR", "United Kingdom": "GBR", "GBR": "GBR", "England": "GBR",
    "China": "CHN", "CHN": "CHN", "People's Republic of China": "CHN",
    "India": "IND", "IND": "IND",
    "Brazil": "BRA", "BRA": "BRA",
    "France": "FRA", "FRA": "FRA",
    "Germany": "DEU", "DEU": "DEU",
    "Italy": "ITA", "ITA": "ITA",
    "Spain": "ESP", "ESP": "ESP",
    "Japan": "JPN", "JPN": "JPN",
    "Canada": "CAN", "CAN": "CAN",
    "South Korea": "KOR", "Korea, South": "KOR", "KOR": "KOR",
    "North Korea": "PRK", "Korea, North": "PRK", "PRK": "PRK",
    "Russia": "RUS", "RUS": "RUS",
    "Mexico": "MEX", "MEX": "MEX",
    "Australia": "AUS", "AUS": "AUS",
    "Argentina": "ARG", "ARG": "ARG",
    "South Africa": "ZAF", "ZAF": "ZAF",
    "Egypt": "EGY", "EGY": "EGY",
    "Nigeria": "NGA", "NGA": "NGA",
    "Indonesia": "IDN", "IDN": "IDN",
    "Afghanistan": "AFG", "AFG": "AFG",
    "Pakistan": "PAK", "PAK": "PAK",
    "Bangladesh": "BGD", "BGD": "BGD",
    "Thailand": "THA", "THA": "THA",
    "Vietnam": "VNM", "VNM": "VNM",
    "Philippines": "PHL", "PHL": "PHL",
    "Turkey": "TUR", "TUR": "TUR",
    "Iran": "IRN", "IRN": "IRN",
    "Iraq": "IRQ", "IRQ": "IRQ",
    "Saudi Arabia": "SAU", "SAU": "SAU",
    "United Arab Emirates": "ARE", "ARE": "ARE",
    "Israel": "ISR", "ISR": "ISR",
    "Belgium": "BEL", "BEL": "BEL",
    "Netherlands": "NLD", "NLD": "NLD",
    "Greece": "GRC", "GRC": "GRC",
    "Portugal": "PRT", "PRT": "PRT",
    "Poland": "POL", "POL": "POL",
    "Romania": "ROU", "ROU": "ROU",
    "Hungary": "HUN", "HUN": "HUN",
    "Austria": "AUT", "AUT": "AUT",
    "Switzerland": "CHE", "CHE": "CHE",
    "Sweden": "SWE", "SWE": "SWE",
    "Norway": "NOR", "NOR": "NOR",
    "Denmark": "DNK", "DNK": "DNK",
    "Finland": "FIN", "FIN": "FIN",
    "Ireland": "IRL", "IRL": "IRL",
    "New Zealand": "NZL", "NZL": "NZL",
    "Czechia": "CZE", "CZE": "CZE",
    "Chile": "CHL", "CHL": "CHL",
    "Peru": "PER", "PER": "PER",
    "Colombia": "COL", "COL": "COL",
    "Ecuador": "ECU", "ECU": "ECU",
    "Bolivia": "BOL", "BOL": "BOL",
    "Paraguay": "PRY", "PRY": "PRY",
    "Uruguay": "URY", "URY": "URY",
    "Venezuela": "VEN", "VEN": "VEN",
    "Guatemala": "GTM", "GTM": "GTM",
    "Honduras": "HND", "HND": "HND",
    "El Salvador": "SLV", "SLV": "SLV",
    "Nicaragua": "NIC", "NIC": "NIC",
    "Costa Rica": "CRI", "CRI": "CRI",
    "Panama": "PAN", "PAN": "PAN",
    "Cuba": "CUB", "CUB": "CUB",
    "Dominican Republic": "DOM", "DOM": "DOM",
    "Haiti": "HTI", "HTI": "HTI",
    "Jamaica": "JAM", "JAM": "JAM",
    "Trinidad and Tobago": "TTO", "TTO": "TTO",
    "Bahamas": "BHS", "BHS": "BHS",
    "Barbados": "BRB", "BRB": "BRB",
    "Belize": "BLZ", "BLZ": "BLZ",
    "Suriname": "SUR", "SUR": "SUR",
    "Guyana": "GUY", "GUY": "GUY",
}


def normalize_date(date_str: str) -> Optional[pd.Timestamp]:
    """Normalize various date formats to pandas Timestamp."""
    if pd.isna(date_str) or date_str == "":
        return None
    
    try:
        # Try common date formats
        for fmt in ["%Y-%m-%d", "%m/%d/%y", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"]:
            try:
                return pd.Timestamp(pd.to_datetime(date_str, format=fmt))
            except:
                continue
        # Fallback to pandas' flexible parsing
        return pd.Timestamp(pd.to_datetime(date_str))
    except Exception as e:
        logger.warning(f"Failed to parse date '{date_str}': {e}")
        return None


def get_iso3_code(country_name: str) -> Optional[str]:
    """Map country name to ISO3 code."""
    if pd.isna(country_name):
        return None
    
    # Normalize input
    country_name_norm = str(country_name).strip().lower()
    
    # Direct lookup (case-insensitive, strip whitespace)
    for key, value in ISO3_COUNTRY_MAPPING.items():
        if key.strip().lower() == country_name_norm:
            return value
    
    # Partial match as fallback
    for key, value in ISO3_COUNTRY_MAPPING.items():
        if key.strip().lower() in country_name_norm or country_name_norm in key.strip().lower():
            return value
    
    # Special fallback for common US variants
    if country_name_norm in ["united states", "usa", "us", "united states of america"]:
        return "USA"
    
    logger.warning(f"Could not map country: {country_name}")
    return None


def fix_monotonicity(series: pd.Series) -> pd.Series:
    """
    Fix non-monotonic cumulative data by converting to daily differences when needed.
    Cumulative data should never decrease. If it does, reset using daily diffs.
    """
    result = series.copy()
    
    # Fill NaN with forward fill then backward fill
    result = result.fillna(method='ffill').fillna(method='bfill')
    
    # Check for non-monotonic sequences
    for i in range(1, len(result)):
        if pd.notna(result.iloc[i]) and pd.notna(result.iloc[i-1]):
            if result.iloc[i] < result.iloc[i-1]:
                # Attempt to replace with forward fill value
                result.iloc[i] = result.iloc[i-1]
    
    return result


def long_format_timeseries(df: pd.DataFrame, metric_col: str, date_col: str = "date", 
                           country_col: str = "country") -> pd.DataFrame:
    """
    Convert wide-format country data to long-format timeseries.
    Input: rows=dates, columns=countries
    Output: [date, country, iso3, metric]
    """
    df = df.copy()
    
    # Rename index if needed
    if date_col not in df.columns and df.index.name == "Date":
        df = df.reset_index()
    
    # Get date and country columns
    date_values = df[df.columns[0]].values if date_col not in df.columns else df[date_col].values
    country_names = df.columns[1:] if date_col not in df.columns else df.drop(columns=[date_col]).columns
    
    records = []
    for country in country_names:
        if country not in df.columns:
            continue
        
        iso3 = get_iso3_code(country)
        if iso3 is None:
            logger.warning(f"Skipping country {country} - no ISO3 mapping")
            continue
        
        for date_val, metric_val in zip(date_values, df[country].values):
            normalized_date = normalize_date(str(date_val))
            if normalized_date is None:
                continue
            
            if pd.notna(metric_val):
                try:
                    metric_val = float(metric_val)
                    if metric_val < 0:
                        metric_val = np.nan
                except:
                    metric_val = np.nan
            
            records.append({
                "date": normalized_date.date(),
                "country": country,
                "iso3": iso3,
                metric_col: metric_val
            })
    
    return pd.DataFrame(records)


def load_and_transform_cases_deaths(cases_path: str, deaths_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load and transform cases and deaths CSVs from Johns Hopkins format."""
    logger.info("Loading cases data...")
    cases_df = pd.read_csv(cases_path)
    
    logger.info("Loading deaths data...")
    deaths_df = pd.read_csv(deaths_path)
    
    # Transform to long format
    logger.info("Converting cases to long format...")
    cases_long = long_format_timeseries(cases_df, metric_col="confirmed_cases")
    
    logger.info("Converting deaths to long format...")
    deaths_long = long_format_timeseries(deaths_df, metric_col="deaths")
    
    # Fix monotonicity
    logger.info("Fixing monotonicity in cases...")
    cases_long = cases_long.sort_values(["iso3", "date"])
    for iso3 in cases_long["iso3"].unique():
        mask = cases_long["iso3"] == iso3
        cases_long.loc[mask, "confirmed_cases"] = fix_monotonicity(
            cases_long.loc[mask, "confirmed_cases"]
        )
    
    logger.info("Fixing monotonicity in deaths...")
    deaths_long = deaths_long.sort_values(["iso3", "date"])
    for iso3 in deaths_long["iso3"].unique():
        mask = deaths_long["iso3"] == iso3
        deaths_long.loc[mask, "deaths"] = fix_monotonicity(
            deaths_long.loc[mask, "deaths"]
        )
    
    return cases_long, deaths_long


def load_and_transform_vaccinations(vacc_path: str) -> pd.DataFrame:
    """Load and transform vaccinations CSV."""
    logger.info("Loading vaccinations data...")
    vacc_df = pd.read_csv(vacc_path)
    
    # Select relevant columns
    if "country" in vacc_df.columns and "date" in vacc_df.columns:
        vacc_df = vacc_df[["country", "date", "total_vaccinations", "people_vaccinated", 
                           "people_fully_vaccinated", "daily_vaccinations"]].copy()
    
    # Normalize dates and add ISO3
    vacc_df["date"] = vacc_df["date"].apply(normalize_date)
    vacc_df["date"] = vacc_df["date"].dt.date
    vacc_df["iso3"] = vacc_df["country"].apply(get_iso3_code)
    
    # Drop records without ISO3
    vacc_df = vacc_df.dropna(subset=["iso3"])
    
    # Fill missing vaccinations with forward fill
    vacc_df = vacc_df.sort_values(["iso3", "date"])
    for col in ["total_vaccinations", "people_vaccinated", "people_fully_vaccinated", "daily_vaccinations"]:
        if col in vacc_df.columns:
            vacc_df[col] = vacc_df.groupby("iso3")[col].transform(
                lambda x: x.fillna(method='ffill')
            )
    
    logger.info(f"Loaded {len(vacc_df)} vaccination records")
    return vacc_df[["date", "country", "iso3", "total_vaccinations", "people_vaccinated", 
                    "people_fully_vaccinated", "daily_vaccinations"]]


def validate_data(df: pd.DataFrame) -> bool:
    """Validate data quality."""
    if df.empty:
        logger.error("Data frame is empty")
        return False
    
    required_cols = ["date", "iso3", "country"]
    for col in required_cols:
        if col not in df.columns:
            logger.error(f"Missing required column: {col}")
            return False
    
    # Check for reasonable date range
    min_date = df["date"].min()
    max_date = df["date"].max()
    logger.info(f"Date range: {min_date} to {max_date}")
    
    # Check for reasonable metric values
    for col in df.columns:
        if col not in required_cols and df[col].dtype in [np.float64, np.int64]:
            null_pct = df[col].isna().sum() / len(df) * 100
            logger.info(f"Column {col}: {null_pct:.1f}% null values")
    
    return True
