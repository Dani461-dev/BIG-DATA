# ============================================================================
# F5_LONGITUDINAL_MODELING.PY - Phase 5: Pemodelan Tren Longitudinal
# Velocity · Value · Validity
# ============================================================================
"""
Phase 5 handles:
1. Time series decomposition (STL)
2. ARIMA/SARIMA fitting and forecasting
3. Facebook Prophet modeling
4. Joinpoint Regression (APC - Annual Percent Change)
5. Trend identification and inflection point detection
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
import warnings
from typing import Dict, List, Tuple, Any

# Time series models
from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.arima.model import ARIMA
import pmdarima as pm
from prophet import Prophet

# Statistical analysis
from scipy import stats

# Import configuration
from config import (
    PROCESSED_DATA_DIR, REPORTS_DIR, FIGURES_DIR,
    STAT_CONFIG, REPRODUCIBILITY_CONFIG
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
# TIME SERIES ANALYSIS
# ============================================================================
class TimeSeriesAnalyzer:
    """Analyze temporal patterns in sentiment data"""
    
    @staticmethod
    def prepare_time_series(df: pd.DataFrame, aggregation: str = 'M') -> pd.DataFrame:
        """
        Prepare time series data from sentiment dataframe
        
        Args:
            df: DataFrame with 'date' and 'sentiment_score' columns
            aggregation: 'D' (daily), 'W' (weekly), 'M' (monthly)
        """
        logger.info(f"Preparing time series (aggregation: {aggregation})...")
        
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Aggregate sentiment
        ts_data = df.groupby(pd.Grouper(key='date', freq=aggregation)).agg({
            'sentiment_score': 'mean',
            'content': 'count'
        }).reset_index()
        
        ts_data.columns = ['date', 'sentiment', 'volume']
        ts_data = ts_data.dropna()
        
        logger.info(f"Time series prepared: {len(ts_data)} periods")
        
        return ts_data
    
    @staticmethod
    def stl_decomposition(ts_data: pd.DataFrame, seasonal: int = 13) -> Dict[str, Any]:
        """
        STL (Seasonal and Trend decomposition using Loess)
        
        Decomposes sentiment into:
        - Trend: Long-term direction
        - Seasonal: Recurring patterns
        - Residual: Unexplained variation
        """
        logger.info("Performing STL decomposition...")
        
        # Ensure we have enough data points for seasonal decomposition
        if len(ts_data) < 2 * seasonal:
            logger.warning(f"Insufficient data for seasonal={seasonal}, reducing...")
            seasonal = max(4, len(ts_data) // 4)
        
        try:
            result = STL(ts_data['sentiment'], seasonal=seasonal, trend=13)
            decomposition = result.fit()
            
            components = {
                'trend': decomposition.trend.values,
                'seasonal': decomposition.seasonal.values,
                'residual': decomposition.resid.values,
            }
            
            logger.info(f"✓ STL completed (seasonal={seasonal})")
            
            return {
                'status': 'success',
                'components': components,
                'seasonal_strength': float(1 - np.var(decomposition.resid) / np.var(decomposition.seasonal + decomposition.resid)),
                'trend_strength': float(1 - np.var(decomposition.resid) / np.var(decomposition.trend + decomposition.resid)),
            }
        
        except Exception as e:
            logger.error(f"STL decomposition failed: {str(e)}")
            return {'status': 'failed', 'error': str(e)}


# ============================================================================
# ARIMA MODELING
# ============================================================================
class ARIMAModeler:
    """ARIMA/SARIMA time series forecasting"""
    
    @staticmethod
    def auto_arima(time_series: pd.Series, seasonal_period: int = 12) -> Dict[str, Any]:
        """
        Automatically determine optimal ARIMA(p,d,q) parameters
        
        Uses AIC criterion and unit root tests
        """
        logger.info("Running auto-ARIMA parameter selection...")
        
        try:
            # Auto ARIMA
            auto_model = pm.auto_arima(
                time_series,
                start_p=0, start_q=0, max_p=STAT_CONFIG['arima_auto_max_p'],
                max_d=STAT_CONFIG['arima_auto_max_d'], max_q=STAT_CONFIG['arima_auto_max_q'],
                seasonal=True, m=seasonal_period,
                stepwise=True, trace=False,
                information_criterion='aic',
            )
            
            order = auto_model.order
            seasonal_order = auto_model.seasonal_order
            
            logger.info(f"✓ Auto-ARIMA: ARIMA{order}x{seasonal_order}")
            logger.info(f"  AIC: {auto_model.aic():.2f}")
            
            return {
                'status': 'success',
                'order': order,
                'seasonal_order': seasonal_order,
                'aic': float(auto_model.aic()),
                'bic': float(auto_model.bic()),
            }
        
        except Exception as e:
            logger.error(f"Auto-ARIMA failed: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
    
    @staticmethod
    def fit_arima(
        time_series: pd.Series,
        order: Tuple[int, int, int],
        seasonal_order: Tuple[int, int, int, int]
    ) -> Dict[str, Any]:
        """
        Fit SARIMA model and generate diagnostics
        """
        logger.info(f"Fitting ARIMA{order}x{seasonal_order}...")
        
        try:
            model = ARIMA(
                time_series,
                order=order,
                seasonal_order=seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False
            )
            
            results = model.fit()
            
            # Generate forecast
            forecast = results.get_forecast(steps=12)  # 12-month forecast
            
            logger.info(f"✓ ARIMA fitted successfully")
            logger.info(f"  AIC: {results.aic:.2f}, BIC: {results.bic:.2f}")
            
            return {
                'status': 'success',
                'model': results,
                'aic': float(results.aic),
                'bic': float(results.bic),
                'forecast_mean': forecast.predicted_mean.values,
                'forecast_ci': forecast.conf_int().values,
                'diagnostics': {
                    'ljung_box_pvalue': 'N/A', 
                    'normality': float(results.diagnostics['Normality (JB)'].iloc[1]),
                }
            }
        
        except Exception as e:
            logger.error(f"ARIMA fitting failed: {str(e)}")
            return {'status': 'failed', 'error': str(e)}


# ============================================================================
# PROPHET MODELING
# ============================================================================
class ProphetModeler:
    """Facebook Prophet for time series forecasting"""
    
    @staticmethod
    def fit_prophet(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Fit Facebook Prophet model
        
        Args:
            df: DataFrame with 'date' (column 'ds') and sentiment (column 'y')
        """
        logger.info("Fitting Facebook Prophet model...")
        
        try:
            # Prepare data for Prophet
            prophet_df = df[['date', 'sentiment']].copy()
            prophet_df['date'] = prophet_df['date'].dt.tz_localize(None) # Remove timezone for Prophet
            prophet_df.columns = ['ds', 'y']
            
            # Initialize and fit model
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=False,
                daily_seasonality=False,
                changepoint_prior_scale=0.05,
                seasonality_prior_scale=10,
            )
            
            model.fit(prophet_df)
            
            # Generate forecast
            future = model.make_future_dataframe(periods=12, freq='MS')
            forecast = model.predict(future)
            
            logger.info(f"✓ Prophet fitted successfully")
            
            return {
                'status': 'success',
                'model': model,
                'forecast': forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(12),
                'components': model.seasonalities,
            }
        
        except Exception as e:
            logger.error(f"Prophet modeling failed: {str(e)}")
            return {'status': 'failed', 'error': str(e)}


# ============================================================================
# JOINPOINT REGRESSION (APC ANALYSIS)
# ============================================================================
class JoinpointAnalyzer:
    """Joinpoint Regression for Annual Percent Change (APC) calculation"""
    
    @staticmethod
    def calculate_apc(self, y: np.ndarray, years: np.ndarray = None) -> Dict[str, Any]:
        logger.info("Calculating Annual Percent Change (APC)...")
        
        # y is already numpy array, no need .values
        if isinstance(y, pd.Series):
            y = y.values

        if years is None:
            years = np.arange(len(y))
        
        # Fit linear regression
        z = np.polyfit(years, y, 1)
        slope = z[0]
        
        # Calculate APC
        # APC = (exp(slope) - 1) * 100
        mean_value = np.mean(y)
        
        if mean_value != 0:
            apc = (slope / mean_value) * 100
        else:
            apc = 0
        
        # Confidence interval (via bootstrap)
        apc_ci = JoinpointAnalyzer._bootstrap_apc_ci(y, years, n_bootstrap=1000)
        
        logger.info(f"✓ APC calculated: {apc:.2f}% per year")
        logger.info(f"  95% CI: [{apc_ci[0]:.2f}%, {apc_ci[1]:.2f}%]")
        
        return {
            'apc': float(apc),
            'apc_ci': apc_ci,
            'slope': float(slope),
            'interpretation': JoinpointAnalyzer._interpret_apc(apc),
        }
    
    @staticmethod
    def _bootstrap_apc_ci(y: np.ndarray, years: np.ndarray, n_bootstrap: int = 1000) -> Tuple[float, float]:
        """Bootstrap confidence interval for APC"""
        apc_values = []
        
        for _ in range(n_bootstrap):
            idx = np.random.choice(len(y), size=len(y), replace=True)
            y_boot = y[idx]
            
            z_boot = np.polyfit(years, y_boot, 1)
            slope_boot = z_boot[0]
            
            mean_boot = np.mean(y_boot)
            if mean_boot != 0:
                apc_boot = (slope_boot / mean_boot) * 100
                apc_values.append(apc_boot)
        
        apc_values = np.array(apc_values)
        
        ci_lower = np.percentile(apc_values, 2.5)
        ci_upper = np.percentile(apc_values, 97.5)
        
        return (float(ci_lower), float(ci_upper))
    
    @staticmethod
    def _interpret_apc(apc: float) -> str:
        """Interpret APC value"""
        if apc > 5:
            return f"Significant increase: +{apc:.1f}% per year (rapid growth)"
        elif apc > 0:
            return f"Increase: +{apc:.1f}% per year (moderate growth)"
        elif apc > -5:
            return f"Decrease: {apc:.1f}% per year (moderate decline)"
        else:
            return f"Significant decrease: {apc:.1f}% per year (rapid decline)"


# ============================================================================
# PHASE 5 EXECUTOR
# ============================================================================
class Phase5LongitudinalModeling:
    """
    Implements Phase 5: Pemodelan Tren Longitudinal
    """
    
    def __init__(self):
        self.ts_analyzer = TimeSeriesAnalyzer()
        self.arima_modeler = ARIMAModeler()
        self.prophet_modeler = ProphetModeler()
        self.jp_analyzer = JoinpointAnalyzer()
    
    def run_phase5(self, sentiment_df: pd.DataFrame) -> Dict[str, Any]:
        """Execute complete Phase 5 pipeline"""
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 5: PEMODELAN TREN LONGITUDINAL (11 Tahun)")
        logger.info("=" * 80 + "\n")
        
        results = {
            "phase": "F5_Longitudinal_Modeling",
            "timestamp": datetime.now().isoformat(),
        }
        
        # Step 5.1: Prepare monthly time series
        logger.info("\n[Step 5.1] Preparing monthly time series...")
        ts_monthly = self.ts_analyzer.prepare_time_series(sentiment_df, aggregation='M')
        
        if len(ts_monthly) < 12:
            logger.error("Insufficient monthly data for time series analysis")
            return results
        
        # Step 5.2: STL Decomposition
        logger.info("\n[Step 5.2] STL Decomposition...")
        stl_results = self.ts_analyzer.stl_decomposition(ts_monthly)
        results["stl_decomposition"] = stl_results
        
        # Step 5.3: Auto-ARIMA
        logger.info("\n[Step 5.3] Auto-ARIMA parameter selection...")
        arima_params = self.arima_modeler.auto_arima(ts_monthly['sentiment'])
        results["arima_parameters"] = arima_params
        
        if arima_params['status'] == 'success':
            # Step 5.4: Fit ARIMA
            logger.info("\n[Step 5.4] Fitting ARIMA model...")
            arima_results = self.arima_modeler.fit_arima(
                ts_monthly['sentiment'],
                order=arima_params['order'],
                seasonal_order=arima_params['seasonal_order']
            )
            results["arima_fit"] = {k: v for k, v in arima_results.items() if k != 'model'}
        
        # Step 5.5: Prophet Modeling
        logger.info("\n[Step 5.5] Fitting Facebook Prophet model...")
        prophet_results = self.prophet_modeler.fit_prophet(ts_monthly)
        results["prophet_fit"] = {k: v for k, v in prophet_results.items() if k != 'model'}
        
        # Step 5.6: APC Analysis (Joinpoint)
        logger.info("\n[Step 5.6] Joinpoint Regression (Annual Percent Change)...")
        years = np.arange(len(ts_monthly))
        apc_results = self.jp_analyzer.calculate_apc(ts_monthly['sentiment'].values, years)
        results["annual_percent_change"] = apc_results
        
        # Save results
        self._save_phase5_results(results, ts_monthly)
        
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 5 COMPLETED")
        logger.info("=" * 80 + "\n")
        
        return results
    
    @staticmethod
    def _save_phase5_results(results: Dict[str, Any], ts_data: pd.DataFrame):
        """Save Phase 5 results"""
        logger.info("Saving Phase 5 results...")
        
        # Save time series data
        ts_file = PROCESSED_DATA_DIR / "time_series_monthly.csv"
        ts_data.to_csv(ts_file, index=False)
        logger.info(f"Time series saved to {ts_file}")
        
        # Save results JSON
        report_file = REPORTS_DIR / "Phase5_Longitudinal_Modeling_Report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Phase 5 report saved to {report_file}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================
def main():
    """Execute Phase 5"""
    # Load sentiment analysis results
    sentiment_file = PROCESSED_DATA_DIR / "sentiment_analyzed_full.parquet"
    
    if not sentiment_file.exists():
        logger.error("Sentiment analysis results not found")
        return None
    
    logger.info(f"Loading sentiment data from {sentiment_file}...")
    sentiment_df = pd.read_parquet(sentiment_file)
    
    # Run Phase 5
    phase5 = Phase5LongitudinalModeling()
    results = phase5.run_phase5(sentiment_df)
    
    return results


if __name__ == "__main__":
    np.random.seed(REPRODUCIBILITY_CONFIG["random_seed"])
    results = main()
