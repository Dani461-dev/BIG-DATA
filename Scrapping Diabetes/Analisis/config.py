# ============================================================================
# CONFIG.PY - Global Configuration & Parameters
# ============================================================================
import os
from pathlib import Path
from datetime import datetime
from turtle import pd
from typing import Dict, List

# ============================================================================
# PATH CONFIGURATION
# ============================================================================
PROJECT_ROOT = Path(__file__).parent.absolute()
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
FIGURES_DIR = OUTPUT_DIR / "figures"
REPORTS_DIR = OUTPUT_DIR / "reports"
LOGS_DIR = PROJECT_ROOT / "logs"
CACHE_DIR = PROJECT_ROOT / ".cache"

# Create directories if they don't exist
for directory in [
    DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, OUTPUT_DIR, 
    FIGURES_DIR, REPORTS_DIR, LOGS_DIR, CACHE_DIR
]:
    directory.mkdir(parents=True, exist_ok=True)

# ============================================================================
# DATASET CONFIGURATION
# ============================================================================
DATASET_CONFIG = {
    "twitter": {
        "file_pattern": "Diabetes_X_All.csv",  # ← Sesuai nama file Anda
        "date_column": "date",
        "content_column": "text_clean",
        "id_column": "id",
        "start_year": 2016,
        "end_year": 2026,
        "expected_records": 9253,
    },
    "threads": {
        "file_pattern": "threads_diabetes_final.csv",  # ← Update nama file
        "date_column": "date",
        "content_column": "comment",
        "id_column": "post_url",
        "start_year": 2024,
        "end_year": 2026,
        "expected_records": 1300,
    },
    "youtube": {
        "file_pattern": "youtube_merged_updated.csv",
        "date_column": "tanggal",      # ← Ganti dari "date" ke "tanggal"
        "content_column": "comment",   # ← Sudah ada, pastikan ini
        "id_column": "video_id",
        "start_year": 2018,
        "end_year": 2026,
        "expected_records": 1880,
    },

    "google_trends": {
        "file_pattern": "google_trends_data.csv",
        "date_column": "date",
        "content_column": "diabetes",
        "id_column": "date",
        "start_year": 2015,
        "end_year": 2026,
        "expected_records": 4179,
    },
}
# ============================================================================
# TIMEZONE & TEMPORAL CONFIGURATION
# ============================================================================
TIMEZONE = "Asia/Jakarta"  # UTC+7
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

# Define important dates & events in Indonesian health context
MAJOR_EVENTS = {
    "2020-03-02": "COVID-19 First Case Indonesia",
    "2020-03-17": "PSBB Announced",
    "2020-12-27": "Vaccination Campaign Started",
    "2022-01-07": "UU PDP Enacted",
    "2023-10-26": "Law No. 27 of 2022 (Health Law) Implementation",
}

SEASONAL_EVENTS = {
    "01": "New Year (Health Resolutions)",
    "03": "World Health Day Prep",
    "04": "World Health Day (April 7)",
    "06": "Ramadan (Variable)",
    "07": "Post-Ramadan",
    "11": "World Diabetes Day (Nov 14) - Awareness Month",
}

# ============================================================================
# DATA QUALITY THRESHOLDS
# ============================================================================
DATA_QUALITY = {
    "min_completeness": 0.85,  # Minimum 85% non-null records
    "max_duplicates_pct": 0.05,  # Max 5% duplicate records
    "min_text_length": 10,  # Minimum character length for text
    "max_text_length": 5000,  # Maximum character length
    "encoding": "utf-8",
    "timezone_target": "Asia/Jakarta",
}

# ============================================================================
# NLP & PREPROCESSING CONFIGURATION
# ============================================================================
NLP_CONFIG = {
    # Text cleaning
    "remove_urls": True,
    "remove_emails": True,
    "remove_mentions": False,  # Keep for analysis
    "remove_hashtags": False,  # Keep for analysis
    "remove_numbers": False,
    "lowercase": True,
    "remove_extra_whitespace": True,
    
    # Tokenization
    "tokenizer": "nltk",  # options: nltk, spacy
    
    # Stopwords
    "remove_stopwords": True,
    "stopwords_lang": ["indonesian", "english"],
    
    # Stemming/Lemmatization
    "use_stemming": True,
    "stemmer": "sastrawi",  # Indonesian stemmer
    
    # Normalization
    "normalize_unicode": True,
    "handle_slang": True,
    "slang_dict_file": None,  # Path to custom slang dictionary
}

# ============================================================================
# SENTIMENT ANALYSIS CONFIGURATION
# ============================================================================
SENTIMENT_CONFIG = {
    # Model selection
    "primary_model": "indobert",  # options: indobert, vader, textblob, ensemble
    "secondary_model": "vader",  # For ensemble
    
    # IndoBERT Configuration
    "indobert_model": "indobert-base-p2",
    "indobert_max_length": 512,
    "indobert_batch_size": 32,
    "indobert_device": "cuda",  # options: cuda, cpu
    
    # VADER Configuration
    "vader_language": "english",  # VADER optimized for English
    
    # Fine-tuning
    "finetune_on_gold_standard": True,
    "train_test_split": 0.7,
    "validation_split": 0.15,
    "epochs": 3,
    "learning_rate": 2e-5,
    
    # Classification thresholds
    "sentiment_thresholds": {
        "negative": (-1.0, -0.1),
        "neutral": (-0.1, 0.1),
        "positive": (0.1, 1.0),
    },
    
    # Validation
    "target_kappa_score": 0.60,  # Cohen's Kappa threshold
    "target_accuracy": 0.85,
    "validation_sample_size": 500,  # For inter-rater reliability
}

# ============================================================================
# ANNOTATION GUIDELINES FOR SENTIMENT LABELING
# ============================================================================
ANNOTATION_GUIDELINES = {
    "positive": {
        "description": "Content expresses hopeful, supportive, or encouraging sentiment",
        "examples": [
            "Diabetes bisa dikelola dengan baik dengan diet dan olahraga teratur",
            "Program kesehatan kami sangat membantu pasien diabetes",
            "Senang dengan teknologi CGM yang baru untuk monitoring",
        ],
        "label": 1,
    },
    "neutral": {
        "description": "Content is factual, informational, or lacks clear sentiment",
        "examples": [
            "Diabetes mellitus adalah penyakit metabolik",
            "Hari Diabetes Dunia diperingati tanggal 14 November",
            "Jurnal baru tentang prevalensi diabetes di Indonesia",
        ],
        "label": 0,
    },
    "negative": {
        "description": "Content expresses concern, fear, complaint, or misinformation",
        "examples": [
            "Diabetes ini menakutkan, tidak ada obat permanen",
            "Insulin mahal dan tidak terjangkau",
            "Jamu tradisional adalah satu-satunya cara mengobati diabetes",  # Misinformation flag
        ],
        "label": -1,
    },
}

# ============================================================================
# GOOGLE TRENDS CONFIGURATION
# ============================================================================
GOOGLE_TRENDS_CONFIG = {
    # Keywords to track
    "keywords": [
        "diabetes",
        "diabetes mellitus",
        "diabetes tipe 2",
        "insulin",
        "gula darah",
        "kolesterol",
        "hipertensi",
        "diet diabetes",
        "gejala diabetes",
    ],
    
    # Geographic focus
    "geo": "ID",  # Indonesia
    "timezone": 420,  # UTC+7
    
    # Temporal parameters
    "interval": "monthly",  # Granularity for analysis
    "date_range": ("2015-01-01", "2026-12-31"),
    
    # Rate limiting
    "rate_limit_delay": 2,  # seconds between requests
    "max_retries": 3,
}

# ============================================================================
# STATISTICAL TESTING CONFIGURATION
# ============================================================================
STAT_CONFIG = {
    # Significance level
    "alpha": 0.05,
    "confidence_level": 0.95,
    
    # Normality test
    "normality_test": "shapiro",  # options: shapiro, ks
    
    # Correlation
    "correlation_method": "pearson",  # options: pearson, spearman, kendall
    
    # Time series
    "arima_auto_max_p": 5,
    "arima_auto_max_d": 2,
    "arima_auto_max_q": 5,
    "arima_seasonal_m": 12,  # Monthly seasonality
    
    # Granger Causality
    "granger_maxlag": 3,  # Max lag in months
    
    # Multiple testing correction
    "correction_method": "bonferroni",  # options: bonferroni, fdr_bh
}

# ============================================================================
# VISUALIZATION CONFIGURATION
# ============================================================================
VIZ_CONFIG = {
    # Figure sizes
    "figure_size_single": (12, 6),
    "figure_size_double": (16, 10),
    "figure_size_multi": (18, 12),
    
    # DPI for different outputs
    "dpi_screen": 100,
    "dpi_pdf": 300,
    "dpi_print": 600,
    
    # Color schemes
    "color_sentiment": {
        "positive": "#2ecc71",  # Green
        "neutral": "#95a5a6",   # Gray
        "negative": "#e74c3c",  # Red
    },
    
    "color_platform": {
        "twitter": "#1DA1F2",    # Twitter blue
        "threads": "#000000",    # Black
        "youtube": "#FF0000",    # Red
        "google_trends": "#4285F4",  # Google blue
    },
    
    # Font configuration
    "font_family": "sans-serif",
    "font_size_title": 16,
    "font_size_label": 12,
    "font_size_tick": 10,
    
    # Plot style
    "style": "seaborn-v0_8-darkgrid",
    "grid_alpha": 0.3,
    
    # Format exports
    "export_formats": ["png", "pdf", "svg"],
    "high_res_export": True,
}

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} | {message}",
    "rotation": "500 MB",
    "retention": "10 days",
    "log_file": LOGS_DIR / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
}

# ============================================================================
# VALIDATION & QUALITY ASSURANCE
# ============================================================================
QA_CONFIG = {
    # Data validation thresholds
    "duplicate_detection_method": "exact",  # options: exact, fuzzy
    "fuzzy_match_threshold": 0.95,
    
    # Outlier detection
    "outlier_detection": "iqr",  # options: iqr, zscore
    "outlier_threshold": 3.0,  # Standard deviations for zscore
    
    # Time series checks
    "check_temporal_continuity": True,
    "allow_gaps_days": 7,  # Max allowed gap in days
    
    # Text validation
    "check_language": True,
    "expected_languages": ["id", "en", "mixed"],
    "min_confidence_language": 0.8,
}

# ============================================================================
# RISKESDAS CONFIGURATION (For External Validation)
# ============================================================================
RISKESDAS_CONFIG = {
    "riskesdas_years": [2013, 2018, 2023],
    "disease_codes": {
        "diabetes_mellitus": "E11",  # ICD-10
        "hypertension": "I10",
        "obesity": "E66",
    },
    # Expected data source URL pattern
    "data_source": "https://www.kemkes.go.id/article/view/[year]/riskesdas-[year]",
    "format": "xlsx",  # Usually XLSX from Kemenkes
}

# ============================================================================
# EXPORT & REPORTING CONFIGURATION
# ============================================================================
EXPORT_CONFIG = {
    # CSV export
    "csv_sep": ",",
    "csv_encoding": "utf-8-sig",
    "csv_index": False,
    
    # Excel export
    "excel_engine": "openpyxl",
    
    # Parquet (efficient for large files)
    "parquet_compression": "snappy",
    
    # HTML reports
    "html_theme": "bootstrap",
    
    # Metadata to include
    "include_metadata": True,
    "metadata_fields": ["timestamp", "data_source", "version", "analyst"],
}

# ============================================================================
# REPRODUCIBILITY & VERSIONING
# ============================================================================
REPRODUCIBILITY_CONFIG = {
    "random_seed": 42,
    "torch_seed": 42,
    "numpy_seed": 42,
    
    # Version tracking
    "project_version": "1.0.0",
    "pipeline_version": "2024.01",
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def get_platform_config(platform: str) -> Dict:
    """Get configuration for a specific platform"""
    return DATASET_CONFIG.get(platform, {})

def get_all_platforms() -> List[str]:
    """Get list of all configured platforms"""
    return list(DATASET_CONFIG.keys())

def get_date_range(platform: str = None) -> tuple:
    """Get date range for analysis"""
    if platform and platform in DATASET_CONFIG:
        cfg = DATASET_CONFIG[platform]
        return (cfg["start_year"], cfg["end_year"])
    return (2015, 2026)  # Overall range

def get_expected_records(platform: str = None) -> int:
    """Get expected record count for platform"""
    if platform and platform in DATASET_CONFIG:
        return DATASET_CONFIG[platform]["expected_records"]
    return sum(cfg["expected_records"] for cfg in DATASET_CONFIG.values())

# ============================================================================
# PRINT SUMMARY
# ============================================================================
if __name__ == "__main__":
    print("=" * 80)
    print("CONFIGURATION SUMMARY")
    print("=" * 80)
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Data Directory: {DATA_DIR}")
    print(f"Output Directory: {OUTPUT_DIR}")
    print(f"\nConfigured Platforms: {get_all_platforms()}")
    print(f"Total Expected Records: {get_expected_records():,}")
    print(f"Analysis Period: {get_date_range()[0]}-{get_date_range()[1]}")
    print(f"Timezone: {TIMEZONE}")
    print("=" * 80)
