# ============================================================================
# F01_DATA_FOUNDATION.PY - Phase 1: Fondasi Data
# Volume · Variety · Velocity
# ============================================================================
"""
Phase 1 handles:
1. Dataset inventory and audit
2. Data loading from multiple sources
3. Temporal standardization (UTC+7)
4. Format standardization
5. Duplicate detection and removal
6. Quality metrics computation
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import logging
import warnings
from typing import Dict, List, Tuple, Any
import json
import hashlib

# Import configuration
from config import (
    RAW_DATA_DIR, PROCESSED_DATA_DIR, REPORTS_DIR,
    DATASET_CONFIG, TIMEZONE, DATA_QUALITY,
    LOGGING_CONFIG, REPRODUCIBILITY_CONFIG, get_all_platforms
)

warnings.filterwarnings('ignore')

# ============================================================================
# LOGGING SETUP
# ============================================================================
from loguru import logger
logger.remove()
logger.add(
    LOGGING_CONFIG["log_file"],
    level=LOGGING_CONFIG["level"],
    format=LOGGING_CONFIG["format"]
)
logger.add(
    lambda msg: print(msg, end=""),
    level=LOGGING_CONFIG["level"],
    format="<level>{time:HH:mm:ss}</level> | <level>{level: <8}</level> | {message}"
)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
class DataQualityReporter:
    """Report data quality metrics"""

    def __init__(self):
        self.metrics = {}

    def add_metric(self, platform: str, metric_name: str, value: Any):
        """Add a quality metric"""
        if platform not in self.metrics:
            self.metrics[platform] = {}
        self.metrics[platform][metric_name] = value

    def generate_report(self) -> str:
        """Generate formatted report"""
        report = "\n" + "=" * 80 + "\n"
        report += "DATA QUALITY REPORT\n"
        report += "=" * 80 + "\n"

        for platform, metrics in self.metrics.items():
            report += f"\n[{platform.upper()}]\n"
            report += "-" * 40 + "\n"
            for metric_name, value in metrics.items():
                if isinstance(value, float):
                    report += f"  {metric_name:.<35} {value:.2f}\n"
                else:
                    report += f"  {metric_name:.<35} {value}\n"

        report += "\n" + "=" * 80 + "\n"
        return report

    def save_report(self, filepath: Path):
        """Save report to file"""
        report = self.generate_report()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"Quality report saved to {filepath}")

    def to_json(self) -> str:
        """Convert metrics to JSON"""
        return json.dumps(self.metrics, indent=2, default=str)


class DataValidator:
    """Validate data quality and structure"""

    @staticmethod
    def check_completeness(df: pd.DataFrame, column: str, threshold: float = 0.85) -> Tuple[bool, float]:
        """Check data completeness for a column"""
        non_null_pct = df[column].notna().sum() / len(df)
        is_valid = non_null_pct >= threshold
        return is_valid, non_null_pct

    @staticmethod
    def check_duplicates(df: pd.DataFrame, subset: List[str] = None) -> Tuple[bool, float]:
        """Check duplicate records"""
        if subset:
            dup_count = df.duplicated(subset=subset).sum()
        else:
            dup_count = df.duplicated().sum()
        dup_pct = dup_count / len(df)
        is_valid = dup_pct <= 0.05
        return is_valid, dup_pct

    @staticmethod
    def check_text_length(series: pd.Series, min_len: int = 10) -> Tuple[bool, float]:
        """Check if text meets minimum length"""
        valid_pct = (series.str.len() >= min_len).sum() / len(series)
        is_valid = valid_pct >= 0.85
        return is_valid, valid_pct


# ============================================================================
# PHASE 1: DATA LOADING & STANDARDIZATION
# ============================================================================
class Phase1DataFoundation:
    """
    Implements Phase 1: Fondasi Data
    - Loads data from multiple sources
    - Standardizes format and temporal dimensions
    - Performs quality audits
    """

    def __init__(self, raw_data_dir: Path = RAW_DATA_DIR):
        self.raw_data_dir = raw_data_dir
        self.processed_data = {}
        self.quality_metrics = DataQualityReporter()
        self.validator = DataValidator()
        logger.info("Initializing Phase 1: Data Foundation")

    # ========================================================================
    # 1.1 INVENTORY & AUDIT
    # ========================================================================
    def create_dataset_inventory(self) -> pd.DataFrame:
        """Create inventory of all datasets"""
        logger.info("Creating dataset inventory...")

        inventory_rows = []
        for platform in get_all_platforms():
            config = DATASET_CONFIG[platform]
            platform_files = list(self.raw_data_dir.glob(config["file_pattern"]))

            for file_path in platform_files:
                try:
                    df = pd.read_csv(file_path, nrows=1)
                    file_size_mb = file_path.stat().st_size / (1024 ** 2)

                    inventory_rows.append({
                        "platform": platform,
                        "filename": file_path.name,
                        "file_size_mb": file_size_mb,
                        "columns": len(df.columns),
                        "expected_records": config["expected_records"],
                        "date_range": f"{config['start_year']}-{config['end_year']}",
                        "last_modified": datetime.fromtimestamp(file_path.stat().st_mtime),
                    })
                except Exception as e:
                    logger.warning(f"Could not read {file_path}: {str(e)}")

        inventory_df = pd.DataFrame(inventory_rows)

        inventory_path = REPORTS_DIR / "Dataset_Inventory.csv"
        inventory_df.to_csv(inventory_path, index=False)
        logger.info(f"Dataset inventory saved to {inventory_path}")

        return inventory_df

    # ========================================================================
    # 1.2 DATA LOADING
    # ========================================================================
    def load_platform_data(self, platform: str) -> pd.DataFrame:
        """Load data for specific platform"""
        logger.info(f"Loading data for {platform}...")

        config = DATASET_CONFIG[platform]
        file_pattern = config["file_pattern"]
        files = list(self.raw_data_dir.glob(file_pattern))

        if not files:
            logger.warning(f"No files found for pattern {file_pattern}")
            return pd.DataFrame()

        dfs = []
        for file_path in files:
            try:
                df = pd.read_csv(file_path, encoding='utf-8', low_memory=False)
                logger.info(f"  Loaded {file_path.name}: {len(df)} rows")
                dfs.append(df)
            except Exception as e:
                logger.error(f"  Error loading {file_path}: {str(e)}")

        if not dfs:
            return pd.DataFrame()

        df_combined = pd.concat(dfs, ignore_index=True)
        logger.info(f"Total records for {platform}: {len(df_combined)}")

        return df_combined

    def load_all_data(self) -> Dict[str, pd.DataFrame]:
        """Load data from all platforms"""
        logger.info("Loading all platform data...")

        all_data = {}
        for platform in get_all_platforms():
            all_data[platform] = self.load_platform_data(platform)

        self.processed_data = all_data
        return all_data

    # ========================================================================
    # 1.3 STANDARDIZATION
    # ========================================================================
    def standardize_timestamps(self, df: pd.DataFrame, platform: str) -> pd.DataFrame:
        config = DATASET_CONFIG[platform]
        date_col = config["date_column"]

        if date_col not in df.columns:
            logger.warning(f"Date column {date_col} not found in {platform}")
            return df

        try:
            def clean_relative_date(val):
                if not isinstance(val, str):
                    return val
                if 'ago' in val.lower():
                    return None
                return val

            df[date_col] = df[date_col].apply(clean_relative_date)

            if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

            if df[date_col].dt.tz is None:
                df[date_col] = df[date_col].dt.tz_localize('UTC').dt.tz_convert(TIMEZONE)
            else:
                df[date_col] = df[date_col].dt.tz_convert(TIMEZONE)

            logger.info(f"  Timestamps standardized for {platform}")

        except Exception as e:
            logger.error(f"  Error standardizing timestamps for {platform}: {str(e)}")

        return df

    def standardize_schema(self, df: pd.DataFrame, platform: str) -> pd.DataFrame:
        """Standardize DataFrame schema"""
        config = DATASET_CONFIG[platform]

        df["platform"] = platform

        if config["date_column"] in df.columns:
            df = df.rename(columns={config["date_column"]: "date"})

        if config["content_column"] in df.columns:
            df = df.rename(columns={config["content_column"]: "content"})

        if config["id_column"] in df.columns:
            df = df.rename(columns={config["id_column"]: "source_id"})

        # FIX Bug: cast source_id ke string SEBELUM digunakan sebagai kunci duplikasi.
        # Ini penting agar PyArrow tidak crash saat to_parquet(), tapi bukan untuk dedup.
        if "source_id" in df.columns:
            df["source_id"] = df["source_id"].astype(str)

        df["load_timestamp"] = datetime.now(tz=None)
        df["data_source"] = platform

        return df

    def standardize_text(self, text: str) -> str:
        """Standardize text formatting"""
        if not isinstance(text, str):
            return ""

        text = text.encode('utf-8', errors='ignore').decode('utf-8')
        text = ' '.join(text.split())

        return text

    # ========================================================================
    # 1.4 DATA CLEANING
    # ========================================================================
    def _build_content_hash(self, df: pd.DataFrame) -> pd.Series:
        """
        FIX: Buat hash unik dari gabungan content + platform + date.

        Alasan: source_id tidak bisa diandalkan sebagai kunci duplikasi karena:
        - Twitter  : tweet ID numerik (bagus, tapi sudah di-cast ke str)
        - Threads  : URL atau NaN → setelah astype(str) semua jadi "nan" yang identik
        - YouTube  : kolom id tidak ada → source_id = NaN → jadi "nan" juga

        Dampak sebelumnya:
        - Threads 1299 baris → 53 (95.91% terbuang)
        - YouTube 1818 baris → 5  (99.72% terbuang)

        Dengan content_hash, duplikasi berbasis ISI konten bukan ID eksternal,
        sehingga hanya konten yang benar-benar sama yang dibuang.
        """
        date_str = df["date"].astype(str) if "date" in df.columns else pd.Series([""] * len(df))
        content_str = df["content"].astype(str) if "content" in df.columns else pd.Series([""] * len(df))
        platform_str = df["platform"].astype(str) if "platform" in df.columns else pd.Series([""] * len(df))

        combined = content_str + "||" + platform_str + "||" + date_str
        return combined.apply(lambda x: hashlib.md5(x.encode('utf-8', errors='ignore')).hexdigest())

    def handle_duplicates(self, df: pd.DataFrame, platform: str) -> pd.DataFrame:
        """
        Remove duplicate records.

        FIX: Strategi duplikasi diubah dari subset=['source_id','platform']
        menjadi subset=['content_hash'] untuk menghindari false-positive dedup
        ketika source_id berisi NaN (Threads, YouTube).
        source_id tetap disimpan sebagai referensi asli.
        """
        logger.info(f"Handling duplicates for {platform}...")

        initial_len = len(df)

        # Buat content_hash sebagai kunci deduplikasi yang andal
        df["content_hash"] = self._build_content_hash(df)

        # Dedup berdasarkan hash konten, bukan source_id
        df = df.drop_duplicates(subset=["content_hash"], keep="first")

        dup_removed = initial_len - len(df)
        dup_pct = (dup_removed / initial_len * 100) if initial_len > 0 else 0

        logger.info(f"  Removed {dup_removed} duplicates ({dup_pct:.2f}%)")
        self.quality_metrics.add_metric(platform, "duplicates_removed", dup_removed)

        return df

    def clean_text_content(self, df: pd.DataFrame, platform: str) -> pd.DataFrame:
        """Clean and standardize text content"""
        logger.info(f"Cleaning text content for {platform}...")

        if "content" not in df.columns:
            return df

        df["content"] = df["content"].astype(str).apply(self.standardize_text)

        min_len = DATA_QUALITY["min_text_length"]
        before_len = len(df)
        df = df[df["content"].str.len() >= min_len]
        removed = before_len - len(df)

        logger.info(f"  Removed {removed} short texts")

        return df

    def handle_missing_values(self, df: pd.DataFrame, platform: str) -> pd.DataFrame:
        """Handle missing values"""
        logger.info(f"Handling missing values for {platform}...")

        if "date" in df.columns:
            df = df.dropna(subset=["date"])

        if "content" in df.columns:
            df = df[df["content"].notna() & (df["content"] != "")]

        return df

    # ========================================================================
    # 1.5 QUALITY VALIDATION
    # ========================================================================
    def validate_platform_data(self, df: pd.DataFrame, platform: str) -> Dict[str, Any]:
        """Validate data quality for platform"""
        logger.info(f"Validating data for {platform}...")

        metrics = {
            "platform": platform,
            "total_records": len(df),
            "date_range": f"{df['date'].min()} to {df['date'].max()}" if "date" in df.columns else "N/A",
        }

        for col in ["date", "content"]:
            if col in df.columns:
                is_valid, pct = self.validator.check_completeness(df, col)
                metrics[f"{col}_completeness"] = pct

        if "content" in df.columns:
            is_valid, pct = self.validator.check_text_length(df["content"])
            metrics[f"content_valid_length"] = pct

        is_valid, dup_pct = self.validator.check_duplicates(df, subset=["content_hash"])
        metrics["duplicate_percentage"] = dup_pct

        logger.info(f"  Quality metrics: {json.dumps(metrics, indent=2, default=str)}")

        return metrics

    # ========================================================================
    # 1.6 EXPORT & CONSOLIDATION
    # ========================================================================
    def export_processed_platform(self, platform: str, df: pd.DataFrame):
        """Export processed platform data"""

        output_file = PROCESSED_DATA_DIR / f"{platform}_processed.parquet"
        df.to_parquet(output_file, engine="pyarrow", compression="snappy")
        logger.info(f"Exported {platform} to {output_file}")

        csv_file = PROCESSED_DATA_DIR / f"{platform}_processed.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        logger.info(f"Exported {platform} to {csv_file}")

        return output_file

    def create_unified_master_file(self) -> pd.DataFrame:
        logger.info("Creating unified master file...")

        all_dfs = []
        for platform, df in self.processed_data.items():
            if len(df) > 0:
                all_dfs.append(df)

        if not all_dfs:
            logger.error("No data to consolidate")
            return pd.DataFrame()

        master_df = pd.concat(all_dfs, ignore_index=True)

        if "date" in master_df.columns:
            master_df["date"] = pd.to_datetime(master_df["date"], errors='coerce', utc=True)
            master_df["date"] = master_df["date"].dt.tz_convert(TIMEZONE)

        # FIX: Pastikan source_id bertipe string agar PyArrow tidak crash
        if "source_id" in master_df.columns:
            master_df["source_id"] = master_df["source_id"].astype(str)

        master_df = master_df.sort_values("date", na_position='last').reset_index(drop=True)

        logger.info(f"Master file created: {len(master_df)} total records")

        master_file_csv = PROCESSED_DATA_DIR / "master_dataset_unified.csv"
        master_df.to_csv(master_file_csv, index=False, encoding='utf-8-sig')
        logger.info(f"Master dataset exported to {master_file_csv}")

        try:
            master_file = PROCESSED_DATA_DIR / "master_dataset_unified.parquet"
            master_df.to_parquet(master_file, engine="pyarrow", compression="snappy")
            logger.info(f"Also saved as parquet: {master_file}")
        except Exception as e:
            logger.warning(f"Parquet export failed: {str(e)}, using CSV instead")

        return master_df

    # ========================================================================
    # ORCHESTRATION
    # ========================================================================
    def run_phase1(self) -> Dict[str, Any]:
        """Execute complete Phase 1 pipeline"""
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 1: FONDASI DATA (Inventory, Load, Standardize, Validate)")
        logger.info("=" * 80 + "\n")

        results = {
            "phase": "F1_Data_Foundation",
            "timestamp": datetime.now().isoformat(),
            "platforms_processed": [],
            "quality_summary": {},
        }

        logger.info("\n[Step 1.1] Creating dataset inventory...")
        inventory = self.create_dataset_inventory()
        logger.info(f"\nInventory:\n{inventory}")

        logger.info("\n[Step 1.2] Loading data from all platforms...")
        self.load_all_data()

        logger.info("\n[Step 1.3-1.5] Processing, standardizing, and validating each platform...\n")
        for platform in get_all_platforms():
            df = self.processed_data[platform]

            if len(df) == 0:
                logger.warning(f"No data for {platform}, skipping")
                continue

            logger.info(f"\n--- Processing {platform.upper()} ---")

            df = self.standardize_timestamps(df, platform)
            df = self.standardize_schema(df, platform)
            df = self.handle_missing_values(df, platform)
            df = self.handle_duplicates(df, platform)
            df = self.clean_text_content(df, platform)

            quality_metrics = self.validate_platform_data(df, platform)
            results["quality_summary"][platform] = quality_metrics

            self.export_processed_platform(platform, df)

            for key, value in quality_metrics.items():
                if key != "platform":
                    self.quality_metrics.add_metric(platform, key, value)

            self.processed_data[platform] = df
            results["platforms_processed"].append(platform)

        logger.info("\n[Step 1.6] Creating unified master dataset...")
        master_df = self.create_unified_master_file()
        results["master_dataset_shape"] = master_df.shape
        results["master_dataset_records_by_platform"] = master_df["platform"].value_counts().to_dict()

        logger.info("\nGenerating quality report...")
        report_file = REPORTS_DIR / "Phase1_Data_Quality_Report.txt"
        self.quality_metrics.save_report(report_file)

        logger.info("\n" + self.quality_metrics.generate_report())
        logger.info("=" * 80)
        logger.info("PHASE 1 COMPLETED SUCCESSFULLY")
        logger.info("=" * 80 + "\n")

        return results


# ============================================================================
# MAIN EXECUTION
# ============================================================================
def main():
    """Execute Phase 1"""
    np.random.seed(REPRODUCIBILITY_CONFIG["random_seed"])

    phase1 = Phase1DataFoundation()
    results = phase1.run_phase1()

    return results


if __name__ == "__main__":
    results = main()
    print("\nPhase 1 Results:", json.dumps(results, indent=2, default=str))