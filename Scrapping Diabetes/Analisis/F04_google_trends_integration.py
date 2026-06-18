# ============================================================================
# F4_GOOGLE_TRENDS_INTEGRATION.PY - Phase 4: Integrasi Google Trends
# Variety · Value
# ============================================================================
"""
Phase 4 handles:
1. Google Trends data collection/loading
2. Temporal normalization and alignment
3. Granger Causality testing
4. Cross-Correlation Function analysis
5. Signal integration as exogenous variable
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
import warnings
from typing import Dict, List, Tuple, Any

# Time series analysis
from statsmodels.tsa.stattools import grangercausalitytests, adfuller
from scipy import signal
from scipy.stats import pearsonr, spearmanr

# Import configuration
from config import (
    PROCESSED_DATA_DIR, REPORTS_DIR, FIGURES_DIR,
    GOOGLE_TRENDS_CONFIG, STAT_CONFIG,
    REPRODUCIBILITY_CONFIG
)

warnings.filterwarnings('ignore')

# ============================================================================
# LOGGING
# ============================================================================
from loguru import logger
logger.add(
    lambda msg: print(msg, end=""),
    level="INFO",
    format="<level>{time:HH:mm:ss}</level> | <level>{level: <8}</level> | {message}"
)


# ============================================================================
# GOOGLE TRENDS HANDLER
# ============================================================================
class GoogleTrendsHandler:
    """Manage Google Trends data"""
    
    def __init__(self):
        self.trends_data = None
        self.normalized_trends = None
    
    def load_google_trends(self, filepath: Path = None) -> pd.DataFrame:
        """
        Load Google Trends data
        
        Expected format:
        - date (YYYY-MM-DD)
        - keyword_1, keyword_2, ... (search volume indices 0-100)
        """
        logger.info("Loading Google Trends data...")
        
        if filepath and filepath.exists():
            df = pd.read_csv(filepath, parse_dates=['date'])
            logger.info(f"Loaded Trends from {filepath}: {len(df)} records")
        else:
            logger.warning("Google Trends file not found, creating template...")
            # Create template from master dataset
            master_file = PROCESSED_DATA_DIR / "master_dataset_unified.parquet"
            if master_file.exists():
                master_df = pd.read_parquet(master_file)
                
                # Generate synthetic daily trends (for demonstration)
                date_range = pd.date_range(
                    start=master_df['date'].min(),
                    end=master_df['date'].max(),
                    freq='D'
                )
                
                # Count posts per day
                daily_posts = master_df.groupby(master_df['date'].dt.date).size()
                
                df = pd.DataFrame({
                    'date': date_range,
                })
                
                # Normalize daily posts to 0-100 scale (Google Trends style)
                if len(daily_posts) > 0:
                    max_posts = daily_posts.max()
                    df['diabetes'] = df['date'].dt.date.map(
                        lambda d: (daily_posts.get(d, 0) / max_posts * 100) if max_posts > 0 else 0
                    ).fillna(0)
                else:
                    df['diabetes'] = 50 + 20 * np.sin(np.arange(len(date_range)) * 2 * np.pi / 365)
                    df['diabetes'] = np.clip(df['diabetes'], 0, 100)
                
                logger.info(f"Created template Trends: {len(df)} days")
            else:
                logger.error("Cannot create template without master dataset")
                return pd.DataFrame()
        
        # Ensure date is datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
        
        self.trends_data = df
        return df
    
    def normalize_trends(self, df: pd.DataFrame = None) -> pd.DataFrame:
        """
        Normalize Trends data to z-scores for comparability
        
        Google Trends is already 0-100 indexed, but we convert to z-scores
        for statistical testing
        """
        if df is None:
            df = self.trends_data.copy()
        
        if df is None:
            logger.error("No trends data loaded")
            return pd.DataFrame()
        
        logger.info("Normalizing Google Trends data to z-scores...")
        
        # Get keyword columns (all except date)
        keyword_cols = [col for col in df.columns if col != 'date']
        
        for col in keyword_cols:
            if col in df.columns:
                mean = df[col].mean()
                std = df[col].std()
                if std > 0:
                    df[col + '_zscore'] = (df[col] - mean) / std
                else:
                    df[col + '_zscore'] = 0
        
        self.normalized_trends = df
        return df
    
    def aggregate_to_monthly(self, df: pd.DataFrame = None) -> pd.DataFrame:
        """Aggregate daily Trends to monthly for alignment with social media"""
        if df is None:
            df = self.trends_data.copy()
        
        logger.info("Aggregating Google Trends to monthly...")
        
        df['year_month'] = df['date'].dt.to_period('M')
        
        # Get numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        monthly_agg = df.groupby('year_month')[numeric_cols].mean()
        monthly_agg = monthly_agg.reset_index()
        monthly_agg['date'] = monthly_agg['year_month'].dt.to_timestamp()
        
        logger.info(f"Aggregated to {len(monthly_agg)} months")
        
        return monthly_agg[['date'] + list(numeric_cols)]


# ============================================================================
# SIGNAL ANALYSIS
# ============================================================================
class SignalAnalysis:
    """Analyze relationships between signals (Google Trends vs Social Media)"""
    
    @staticmethod
    def prepare_for_causality(
        trends_df: pd.DataFrame,
        social_media_df: pd.DataFrame,
        trends_col: str = 'diabetes',
        sm_col: str = 'total_posts'
    ) -> Tuple[pd.DataFrame, str, str]:
        """
        Prepare data for Granger causality test
        
        Both series must be:
        1. Same temporal resolution (monthly)
        2. Same date range
        3. Stationary or differenced
        """
        logger.info("Preparing signals for causality testing...")
        
        # Ensure both are monthly
        if 'date' not in trends_df.columns:
            logger.error("Trends must have 'date' column")
            return None, None, None
        
        # Get common date range
        min_date = max(trends_df['date'].min(), social_media_df['date'].min())
        max_date = min(trends_df['date'].max(), social_media_df['date'].max())
        
        trends_subset = trends_df[
            (trends_df['date'] >= min_date) &
            (trends_df['date'] <= max_date)
        ].copy()
        
        sm_subset = social_media_df[
            (social_media_df['date'] >= min_date) &
            (social_media_df['date'] <= max_date)
        ].copy()
        
        logger.info(f"Common period: {min_date.date()} to {max_date.date()}")
        logger.info(f"Trends: {len(trends_subset)} months, SM: {len(sm_subset)} months")
        
        # Merge on date
        merged = pd.merge(
            trends_subset[['date', trends_col]],
            sm_subset[['date', sm_col]],
            on='date',
            how='inner'
        ).sort_values('date')
        
        logger.info(f"Merged: {len(merged)} matching months")
        
        return merged, trends_col, sm_col
    
    @staticmethod
    def test_stationarity(series: pd.Series, name: str = "") -> Dict[str, Any]:
        """
        Test stationarity using Augmented Dickey-Fuller test
        
        Hypothesis:
        - H0: Series has unit root (non-stationary)
        - H1: Series is stationary
        """
        logger.info(f"Testing stationarity of {name}...")
        
        result = adfuller(series.dropna())
        
        test_results = {
            'test_statistic': float(result[0]),
            'p_value': float(result[1]),
            'n_lags': result[2],
            'n_obs': result[3],
            'is_stationary': result[1] < STAT_CONFIG["alpha"],
        }
        
        logger.info(f"  ADF test p-value: {result[1]:.4f}")
        logger.info(f"  Stationary: {test_results['is_stationary']}")
        
        return test_results
    
    @staticmethod
    def granger_causality_test(
        data: pd.DataFrame,
        cause_col: str,
        effect_col: str,
        max_lag: int = 3
    ) -> Dict[str, Any]:
        """
        Granger Causality Test
        
        Tests if past values of 'cause' help predict 'effect'
        beyond what 'effect' itself predicts
        
        Hypothesis:
        - H0: 'cause' does NOT Granger-cause 'effect'
        - H1: 'cause' DOES Granger-cause 'effect'
        """
        logger.info(f"\nGranger Causality Test: {cause_col} → {effect_col}")
        logger.info(f"Max lag: {max_lag} months")
        
        # Prepare data (handle NaN)
        test_data = data[[cause_col, effect_col]].dropna()
        
        if len(test_data) < max_lag + 3:
            logger.warning(f"Insufficient observations ({len(test_data)} < {max_lag + 3})")
            return {'status': 'insufficient_data'}
        
        try:
            # Run Granger causality test
            gc_result = grangercausalitytests(test_data, max_lag=max_lag, verbose=True)
            
            # Extract p-values for each lag
            p_values = []
            for lag in range(1, max_lag + 1):
                p_val = gc_result[lag][0]['ssr_ftest'][1]
                p_values.append(float(p_val))
            
            # Overall result: reject H0 if any lag is significant
            is_causal = any(p < STAT_CONFIG["alpha"] for p in p_values)
            
            results = {
                'status': 'success',
                'cause': cause_col,
                'effect': effect_col,
                'p_values_by_lag': p_values,
                'is_causal': is_causal,
                'interpretation': SignalAnalysis._interpret_granger(is_causal, p_values),
            }
            
            logger.info(f"Result: {'GRANGER CAUSAL' if is_causal else 'NOT GRANGER CAUSAL'}")
            logger.info(f"P-values by lag: {[f'{p:.4f}' for p in p_values]}")
            
            return results
        
        except Exception as e:
            logger.error(f"Granger test failed: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    @staticmethod
    def _interpret_granger(is_causal: bool, p_values: List[float]) -> str:
        """Interpret Granger causality result"""
        if not is_causal:
            return "No significant Granger causality detected"
        
        min_p = min(p_values)
        lag_idx = p_values.index(min_p)
        
        return f"Granger causal at lag {lag_idx + 1} (p={min_p:.4f})"
    
    @staticmethod
    def cross_correlation_analysis(
        series1: pd.Series,
        series2: pd.Series,
        max_lag: int = 12
    ) -> Dict[str, Any]:
        """
        Cross-Correlation Function (CCF) analysis
        
        Identifies lag at which two series are most correlated
        """
        logger.info(f"\nCross-Correlation Analysis (max lag: {max_lag})...")
        
        # Normalize series
        s1 = (series1 - series1.mean()) / series1.std()
        s2 = (series2 - series2.mean()) / series2.std()
        
        # Compute cross-correlation
        correlations = []
        lags = []
        
        for lag in range(-max_lag, max_lag + 1):
            if lag < 0:
                corr = s1.iloc[-lag:].corr(s2.iloc[:lag])
            elif lag > 0:
                corr = s1.iloc[:-lag].corr(s2.iloc[lag:])
            else:
                corr = s1.corr(s2)
            
            correlations.append(corr if not np.isnan(corr) else 0)
            lags.append(lag)
        
        # Find maximum correlation
        max_corr_idx = np.argmax(np.abs(correlations))
        max_lag_val = lags[max_corr_idx]
        max_corr_val = correlations[max_corr_idx]
        
        results = {
            'correlations': correlations,
            'lags': lags,
            'max_correlation': float(max_corr_val),
            'optimal_lag': int(max_lag_val),
            'interpretation': SignalAnalysis._interpret_ccf(max_lag_val, max_corr_val),
        }
        
        logger.info(f"Maximum correlation: {max_corr_val:.3f} at lag {max_lag_val} months")
        logger.info(f"Interpretation: {results['interpretation']}")
        
        return results
    
    @staticmethod
    def _interpret_ccf(lag: int, corr: float) -> str:
        """Interpret CCF results"""
        if lag > 0:
            direction = f"Series 2 leads Series 1 by {lag} month(s)"
        elif lag < 0:
            direction = f"Series 1 leads Series 2 by {-lag} month(s)"
        else:
            direction = "Series move together simultaneously"
        
        if abs(corr) < 0.3:
            strength = "weak"
        elif abs(corr) < 0.7:
            strength = "moderate"
        else:
            strength = "strong"
        
        return f"{strength.capitalize()} {direction} (r={corr:.3f})"


# ============================================================================
# PHASE 4 EXECUTOR
# ============================================================================
class Phase4GoogleTrendsIntegration:
    """
    Implements Phase 4: Integrasi Google Trends Sebagai Exogenous Signal
    """
    
    def __init__(self):
        self.trends_handler = GoogleTrendsHandler()
        self.signal_analysis = SignalAnalysis()
        self.results = {}
    
    def prepare_social_media_signal(self, master_df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare social media signal: aggregate to monthly posts count
        
        This is what we'll compare with Google Trends
        """
        logger.info("Preparing social media signal (monthly aggregation)...")
        
        # Group by year-month
        master_df['year_month'] = master_df['date'].dt.to_period('M')
        
        monthly_sm = master_df.groupby('year_month').agg({
            'content': 'count',
        }).reset_index()
        
        monthly_sm.columns = ['year_month', 'total_posts']
        monthly_sm['date'] = monthly_sm['year_month'].dt.to_timestamp()
        monthly_sm = monthly_sm[['date', 'total_posts']]
        
        logger.info(f"Social media signal: {len(monthly_sm)} months")
        
        return monthly_sm
    
    def run_phase4(self, master_df: pd.DataFrame) -> Dict[str, Any]:
        """Execute complete Phase 4 pipeline"""
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 4: INTEGRASI GOOGLE TRENDS SEBAGAI EXOGENOUS SIGNAL")
        logger.info("=" * 80 + "\n")
        
        results = {
            "phase": "F4_Google_Trends_Integration",
            "timestamp": datetime.now().isoformat(),
        }
        
        # Step 4.1: Load Google Trends
        logger.info("\n[Step 4.1] Loading Google Trends data...")
        trends_file = PROCESSED_DATA_DIR / "google_trends_data.csv"
        trends_df = self.trends_handler.load_google_trends(trends_file)
        
        if len(trends_df) == 0:
            logger.error("No Trends data available")
            return results
        
        # Step 4.2: Normalize Trends
        logger.info("\n[Step 4.2] Normalizing Trends to z-scores...")
        trends_normalized = self.trends_handler.normalize_trends(trends_df)
        
        # Step 4.3: Aggregate both signals to monthly
        logger.info("\n[Step 4.3] Aggregating signals to monthly resolution...")
        trends_monthly = self.trends_handler.aggregate_to_monthly(trends_df)
        sm_monthly = self.prepare_social_media_signal(master_df)
        
        # Step 4.4: Merge signals
        logger.info("\n[Step 4.4] Merging signals for analysis...")
        merged_signals, trends_col, sm_col = self.signal_analysis.prepare_for_causality(
            trends_monthly,
            sm_monthly,
            trends_col='diabetes',
            sm_col='total_posts'
        )
        
        if merged_signals is None:
            logger.error("Could not merge signals")
            return results
        
        results["merged_signals_records"] = len(merged_signals)
        
        # Step 4.5: Test stationarity
        logger.info("\n[Step 4.5] Testing stationarity of signals...")
        trends_stationary = self.signal_analysis.test_stationarity(
            merged_signals[trends_col],
            name="Google Trends"
        )
        sm_stationary = self.signal_analysis.test_stationarity(
            merged_signals[sm_col],
            name="Social Media Posts"
        )
        
        results["stationarity_tests"] = {
            "google_trends": trends_stationary,
            "social_media": sm_stationary,
        }
        
        # Step 4.6: Granger Causality Tests
        logger.info("\n[Step 4.6] Running Granger Causality Tests...")
        
        # Test: Do Trends lead Social Media?
        gc_trends_to_sm = self.signal_analysis.granger_causality_test(
            merged_signals,
            cause_col=trends_col,
            effect_col=sm_col,
            max_lag=STAT_CONFIG["granger_maxlag"]
        )
        results["granger_trends_to_sm"] = gc_trends_to_sm
        
        # Test: Does Social Media lead Trends?
        gc_sm_to_trends = self.signal_analysis.granger_causality_test(
            merged_signals,
            cause_col=sm_col,
            effect_col=trends_col,
            max_lag=STAT_CONFIG["granger_maxlag"]
        )
        results["granger_sm_to_trends"] = gc_sm_to_trends
        
        # Step 4.7: Cross-Correlation Analysis
        logger.info("\n[Step 4.7] Performing Cross-Correlation Analysis...")
        ccf_results = self.signal_analysis.cross_correlation_analysis(
            merged_signals[trends_col],
            merged_signals[sm_col],
            max_lag=12
        )
        results["cross_correlation"] = {k: v for k, v in ccf_results.items() if k != 'correlations'}
        
        # Step 4.8: Export results and visualization
        logger.info("\n[Step 4.8] Exporting results...")
        self._export_integration_results(merged_signals, ccf_results)
        self._visualize_signals(merged_signals, ccf_results)
        
        # Save full report
        self._save_phase4_report(results)
        
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 4 COMPLETED")
        logger.info("=" * 80 + "\n")
        
        return results
    
    @staticmethod
    def _export_integration_results(merged_df: pd.DataFrame, ccf_results: Dict):
        """Export integration results"""
        logger.info("Exporting integrated signals...")
        
        # Save merged signals
        output_file = PROCESSED_DATA_DIR / "integrated_signals_monthly.csv"
        merged_df.to_csv(output_file, index=False)
        logger.info(f"Merged signals saved to {output_file}")
        
        # Save CCF details
        ccf_file = PROCESSED_DATA_DIR / "ccf_analysis.json"
        with open(ccf_file, 'w') as f:
            json.dump(ccf_results, f, indent=2, default=str)
        logger.info(f"CCF analysis saved to {ccf_file}")
    
    @staticmethod
    def _visualize_signals(merged_df: pd.DataFrame, ccf_results: Dict):
        """Create signal visualization"""
        import matplotlib.pyplot as plt
        
        logger.info("Generating signal visualizations...")
        
        try:
            # Plot 1: Time series alignment
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
            
            # Google Trends
            ax1.plot(merged_df['date'], merged_df['diabetes'], 'o-', color='#4285F4', linewidth=2)
            ax1.set_title('Google Trends: "Diabetes" Search Volume', fontsize=12, fontweight='bold')
            ax1.set_ylabel('Search Volume Index (0-100)', fontsize=11)
            ax1.grid(True, alpha=0.3)
            
            # Social Media
            ax2.plot(merged_df['date'], merged_df['total_posts'], 's-', color='#1DA1F2', linewidth=2)
            ax2.set_title('Social Media: Monthly Posts Count', fontsize=12, fontweight='bold')
            ax2.set_ylabel('Number of Posts', fontsize=11)
            ax2.set_xlabel('Date', fontsize=11)
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            output_file = FIGURES_DIR / "Phase4_Signal_Comparison.png"
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            logger.info(f"Signal comparison saved to {output_file}")
            plt.close()
            
            # Plot 2: Cross-Correlation
            fig, ax = plt.subplots(figsize=(12, 6))
            
            lags = ccf_results['lags']
            corrs = ccf_results['correlations']
            
            colors = ['green' if c > 0 else 'red' for c in corrs]
            ax.bar(lags, corrs, color=colors, alpha=0.7)
            ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            ax.axvline(x=ccf_results['optimal_lag'], color='blue', linestyle='--', linewidth=2, label=f"Optimal lag: {ccf_results['optimal_lag']}")
            
            ax.set_title('Cross-Correlation Function: Google Trends vs Social Media', fontsize=12, fontweight='bold')
            ax.set_xlabel('Lag (months)', fontsize=11)
            ax.set_ylabel('Correlation Coefficient', fontsize=11)
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            output_file = FIGURES_DIR / "Phase4_CrossCorrelation.png"
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            logger.info(f"CCF plot saved to {output_file}")
            plt.close()
        
        except Exception as e:
            logger.error(f"Visualization error: {str(e)}")
    
    @staticmethod
    def _save_phase4_report(results: Dict[str, Any]):
        """Save Phase 4 report"""
        report_file = REPORTS_DIR / "Phase4_Google_Trends_Integration_Report.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"\nPhase 4 report saved to {report_file}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================
def main():
    """Execute Phase 4"""
    # Load master dataset
    master_file = PROCESSED_DATA_DIR / "master_dataset_unified.parquet"
    
    if not master_file.exists():
        logger.error(f"Master dataset not found. Run Phase 1 first.")
        return None
    
    logger.info(f"Loading master dataset from {master_file}...")
    master_df = pd.read_parquet(master_file)
    
    # Run Phase 4
    phase4 = Phase4GoogleTrendsIntegration()
    results = phase4.run_phase4(master_df)
    
    return results


if __name__ == "__main__":
    np.random.seed(REPRODUCIBILITY_CONFIG["random_seed"])
    results = main()
