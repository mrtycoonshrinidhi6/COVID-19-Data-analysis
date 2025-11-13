"""
ETL Main Pipeline Runner - orchestrates data ingestion and transformation.
"""

import os
import sys
import logging
from pathlib import Path
import pandas as pd

from transform_utils import (
    load_and_transform_cases_deaths,
    load_and_transform_vaccinations,
    validate_data
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Raw data directory
RAW_DATA_DIR = Path(__file__).parent.parent.parent.parent / "raw"
OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def run_etl():
    """Execute the complete ETL pipeline."""
    logger.info("Starting COVID-19 ETL Pipeline")
    logger.info(f"Raw data directory: {RAW_DATA_DIR}")
    logger.info(f"Output directory: {OUTPUT_DIR}")
    
    # Find input files
    cases_file = RAW_DATA_DIR / "CONVENIENT_global_confirmed_cases.csv"
    deaths_file = RAW_DATA_DIR / "CONVENIENT_global_deaths.csv"
    vacc_file = RAW_DATA_DIR / "country_vaccinations.csv"
    
    if not cases_file.exists():
        logger.error(f"Cases file not found: {cases_file}")
        return False
    
    if not deaths_file.exists():
        logger.error(f"Deaths file not found: {deaths_file}")
        return False
    
    if not vacc_file.exists():
        logger.error(f"Vaccinations file not found: {vacc_file}")
        return False
    
    try:
        # Load and transform cases/deaths
        logger.info("Processing cases and deaths data...")
        cases_df, deaths_df = load_and_transform_cases_deaths(str(cases_file), str(deaths_file))
        
        # Merge cases and deaths
        logger.info("Merging cases and deaths...")
        timeseries_df = cases_df.merge(
            deaths_df,
            on=["date", "country", "iso3"],
            how="outer"
        )
        
        # Load vaccinations
        logger.info("Processing vaccinations data...")
        vacc_df = load_and_transform_vaccinations(str(vacc_file))
        
        # Merge with vaccinations
        logger.info("Merging with vaccinations...")
        timeseries_df = timeseries_df.merge(
            vacc_df,
            on=["date", "country", "iso3"],
            how="left"
        )
        
        # Validate
        if not validate_data(timeseries_df):
            logger.error("Data validation failed")
            return False
        
        # Sort and save
        logger.info("Sorting and saving results...")
        timeseries_df = timeseries_df.sort_values(["iso3", "date"])
        
        output_file = OUTPUT_DIR / "timeseries.parquet"
        timeseries_df.to_parquet(output_file, index=False, compression="snappy")
        logger.info(f"Saved timeseries to {output_file}")
        logger.info(f"Total records: {len(timeseries_df)}")
        logger.info(f"Countries: {timeseries_df['iso3'].nunique()}")
        logger.info(f"Date range: {timeseries_df['date'].min()} to {timeseries_df['date'].max()}")
        
        # Save individual metrics for easier access
        logger.info("Saving individual metric files...")
        cases_df.to_parquet(OUTPUT_DIR / "cases_timeseries.parquet", index=False, compression="snappy")
        deaths_df.to_parquet(OUTPUT_DIR / "deaths_timeseries.parquet", index=False, compression="snappy")
        vacc_df.to_parquet(OUTPUT_DIR / "vaccinations_timeseries.parquet", index=False, compression="snappy")
        
        logger.info("ETL Pipeline completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"ETL Pipeline failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = run_etl()
    sys.exit(0 if success else 1)
