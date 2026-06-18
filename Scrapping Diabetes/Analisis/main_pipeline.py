# ============================================================================
# MAIN_PIPELINE.PY - Complete Pipeline Orchestrator
# Coordinates all phases: F1-F6
# ============================================================================
"""
Main execution script for the complete Diabetes Social Media Sentiment Analysis pipeline.

This script orchestrates:
- Phase 1: Data Foundation (cleaning, standardization)
- Phase 2: Veracity Validation (Riskesdas, annotation)
- Phase 3: Sentiment Analysis (multi-model, ensemble)
- Phase 4: Google Trends Integration (Granger, CCF)
- Phase 5: Longitudinal Modeling (ARIMA, Prophet, Joinpoint)
- Phase 6: Visualization & Reporting

Execution Flow:
1. Check data prerequisites
2. Execute each phase sequentially
3. Validate phase outputs
4. Generate consolidated report
5. Export final datasets and visualizations
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
import sys
import traceback
from typing import Dict, Any, List

# Import configuration
from config import (
    PROJECT_ROOT, PROCESSED_DATA_DIR, REPORTS_DIR, FIGURES_DIR,
    LOGGING_CONFIG, REPRODUCIBILITY_CONFIG
)

from loguru import logger


# ============================================================================
# LOGGING SETUP
# ============================================================================
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
# PIPELINE ORCHESTRATOR
# ============================================================================
class PipelineOrchestrator:
    """
    Manages complete pipeline execution with error handling and reporting
    """

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.phase_results = {}
        self.phase_status = {}
        self.errors = []

        logger.info("Initializing Pipeline Orchestrator...")

    # ========================================================================
    # PHASE EXECUTION
    # ========================================================================
    def execute_phase1(self) -> bool:
        """Execute Phase 1: Data Foundation"""
        logger.info("\n" + "█" * 80)
        logger.info("EXECUTING PHASE 1: DATA FOUNDATION")
        logger.info("█" * 80)

        try:
            from F01_data_foundation import Phase1DataFoundation

            phase1 = Phase1DataFoundation()
            results = phase1.run_phase1()

            self.phase_results['F1'] = results
            self.phase_status['F1'] = 'SUCCESS'

            logger.info(f"\n✓ Phase 1 completed successfully")
            logger.info(f"  Platforms processed: {results['platforms_processed']}")
            logger.info(f"  Master dataset: {results['master_dataset_shape']}")

            return True

        except Exception as e:
            error_msg = f"Phase 1 FAILED: {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            self.phase_status['F1'] = 'FAILED'
            traceback.print_exc()
            return False

    def execute_phase2(self) -> bool:
        """Execute Phase 2: Veracity Validation"""
        logger.info("\n" + "█" * 80)
        logger.info("EXECUTING PHASE 2: VERACITY VALIDATION")
        logger.info("█" * 80)

        master_file = PROCESSED_DATA_DIR / "master_dataset_unified.parquet"
        if not master_file.exists():
            error_msg = "Phase 2 SKIPPED: Master dataset not found (run Phase 1 first)"
            logger.warning(error_msg)
            self.phase_status['F2'] = 'SKIPPED'
            return False

        try:
            from F02_veracity_validation import Phase2VeracityValidation

            master_df = pd.read_parquet(master_file)

            phase2 = Phase2VeracityValidation()
            results = phase2.run_phase2(master_df)

            self.phase_results['F2'] = results
            self.phase_status['F2'] = 'SUCCESS'

            logger.info(f"\n✓ Phase 2 completed successfully")
            logger.info(f"  Riskesdas correlation: {results.get('riskesdas_correlation', {}).get('status', 'N/A')}")
            logger.info(f"  Inter-rater Kappa: {results.get('inter_rater_reliability', {}).get('cohens_kappa', 'N/A')}")

            return True

        except Exception as e:
            error_msg = f"Phase 2 FAILED: {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            self.phase_status['F2'] = 'FAILED'
            traceback.print_exc()
            return False

    def execute_phase3(self) -> bool:
        """Execute Phase 3: Sentiment Analysis"""
        logger.info("\n" + "█" * 80)
        logger.info("EXECUTING PHASE 3: SENTIMENT ANALYSIS")
        logger.info("█" * 80)

        master_file = PROCESSED_DATA_DIR / "master_dataset_unified.parquet"
        if not master_file.exists():
            error_msg = "Phase 3 SKIPPED: Master dataset not found"
            logger.warning(error_msg)
            self.phase_status['F3'] = 'SKIPPED'
            return False

        try:
            from F03_sentiment_analysis import Phase3SentimentAnalysis

            master_df = pd.read_parquet(master_file)

            gold_standard_file = PROCESSED_DATA_DIR / "gold_standard_annotated.parquet"
            gold_standard_df = None
            if gold_standard_file.exists():
                gold_standard_df = pd.read_parquet(gold_standard_file)

            phase3 = Phase3SentimentAnalysis()
            results = phase3.run_phase3(master_df, gold_standard_df)

            self.phase_results['F3'] = results
            self.phase_status['F3'] = 'SUCCESS'

            logger.info(f"\n✓ Phase 3 completed successfully")
            logger.info(f"  Records analyzed: {results.get('main_corpus_records', 'N/A')}")
            logger.info(f"  Sentiment distribution: {results.get('sentiment_distribution', {})}")

            return True

        except Exception as e:
            error_msg = f"Phase 3 FAILED: {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            self.phase_status['F3'] = 'FAILED'
            traceback.print_exc()
            return False

    def execute_phase4(self) -> bool:
        """Execute Phase 4: Google Trends Integration"""
        logger.info("\n" + "█" * 80)
        logger.info("EXECUTING PHASE 4: GOOGLE TRENDS INTEGRATION")
        logger.info("█" * 80)

        master_file = PROCESSED_DATA_DIR / "master_dataset_unified.parquet"
        if not master_file.exists():
            error_msg = "Phase 4 SKIPPED: Master dataset not found"
            logger.warning(error_msg)
            self.phase_status['F4'] = 'SKIPPED'
            return False

        try:
            from F04_google_trends_integration import Phase4GoogleTrendsIntegration

            master_df = pd.read_parquet(master_file)

            phase4 = Phase4GoogleTrendsIntegration()
            results = phase4.run_phase4(master_df)

            self.phase_results['F4'] = results
            self.phase_status['F4'] = 'SUCCESS'

            logger.info(f"\n✓ Phase 4 completed successfully")
            logger.info(f"  Merged signals: {results.get('merged_signals_records', 'N/A')} months")

            return True

        except Exception as e:
            error_msg = f"Phase 4 FAILED: {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            self.phase_status['F4'] = 'FAILED'
            traceback.print_exc()
            return False

    def execute_phase5(self) -> bool:
        """Execute Phase 5: Longitudinal Modeling"""
        logger.info("\n" + "█" * 80)
        logger.info("EXECUTING PHASE 5: LONGITUDINAL MODELING")
        logger.info("█" * 80)

        sentiment_file = PROCESSED_DATA_DIR / "sentiment_analyzed_full.parquet"
        if not sentiment_file.exists():
            logger.warning("Sentiment analysis results not found, skipping Phase 5")
            self.phase_status['F5'] = 'SKIPPED'
            return False

        try:
            from F05_longitudinal_modeling import Phase5LongitudinalModeling

            sentiment_df = pd.read_parquet(sentiment_file)

            phase5 = Phase5LongitudinalModeling()
            results = phase5.run_phase5(sentiment_df)

            self.phase_results['F5'] = results
            self.phase_status['F5'] = 'SUCCESS'

            logger.info(f"\n✓ Phase 5 completed successfully")
            logger.info(f"  Time series models fitted")

            return True

        except Exception as e:
            error_msg = f"Phase 5 FAILED: {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            self.phase_status['F5'] = 'FAILED'
            traceback.print_exc()
            return False

    def execute_phase6(self) -> bool:
        """Execute Phase 6: Visualization & Reporting"""
        logger.info("\n" + "█" * 80)
        logger.info("EXECUTING PHASE 6: VISUALIZATION & REPORTING")
        logger.info("█" * 80)

        try:
            from F06_visualization_reporting import Phase6VisualizationReporting

            sentiment_file = PROCESSED_DATA_DIR / "sentiment_analyzed_full.parquet"
            if not sentiment_file.exists():
                logger.warning("Sentiment data not available for Phase 6")
                self.phase_status['F6'] = 'PARTIAL'
                return False

            sentiment_df = pd.read_parquet(sentiment_file)

            phase6 = Phase6VisualizationReporting()
            results = phase6.run_phase6(sentiment_df)

            self.phase_results['F6'] = results
            self.phase_status['F6'] = 'SUCCESS'

            logger.info(f"\n✓ Phase 6 completed successfully")
            logger.info(f"  Figures generated: {results.get('figures_created', 0)}")

            return True

        except Exception as e:
            error_msg = f"Phase 6 FAILED: {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            self.phase_status['F6'] = 'FAILED'
            traceback.print_exc()
            return False

    # ========================================================================
    # MAIN ORCHESTRATION
    # ========================================================================
    def run_complete_pipeline(self, phases: List[int] = None) -> Dict[str, Any]:
        """
        Execute complete pipeline

        Args:
            phases: List of phases to run (1-6). If None, runs all.
        """
        self.start_time = datetime.now()

        logger.info("\n" + "=" * 80)
        logger.info("DIABETES SOCIAL MEDIA SENTIMENT & TREND ANALYSIS PIPELINE")
        logger.info("Complete Framework 8V Implementation")
        logger.info("=" * 80)
        logger.info(f"Start time: {self.start_time}")
        logger.info(f"Project directory: {PROJECT_ROOT}")
        logger.info(f"Output directory: {REPORTS_DIR}")
        logger.info("=" * 80)

        if phases is None:
            phases = [1, 2, 3, 4, 5, 6]

        logger.info(f"\nPhases to execute: {phases}\n")

        # Execute each phase
        if 1 in phases:
            if not self.execute_phase1():
                logger.warning("Phase 1 failed, stopping pipeline")
                return self._get_summary()

        if 2 in phases:
            self.execute_phase2()

        if 3 in phases:
            self.execute_phase3()

        if 4 in phases:
            self.execute_phase4()

        if 5 in phases:
            self.execute_phase5()

        if 6 in phases:
            self.execute_phase6()

        # Generate final report
        self.end_time = datetime.now()
        self._generate_final_report()

        return self._get_summary()

    # ========================================================================
    # REPORTING
    # ========================================================================
    def _get_summary(self) -> Dict[str, Any]:
        """Get execution summary"""
        return {
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': (
                (self.end_time - self.start_time).total_seconds()
                if (self.start_time and self.end_time) else None
            ),
            'phase_status': self.phase_status,
            'errors': self.errors,
            'total_errors': len(self.errors),
            'success': len(self.errors) == 0,
        }

    def _generate_final_report(self):
        """Generate comprehensive final report"""
        logger.info("\n" + "=" * 80)
        logger.info("GENERATING FINAL REPORT")
        logger.info("=" * 80)

        summary = self._get_summary()

        # FIX 1: Guard None — duration_seconds bisa None jika pipeline crash sebelum end_time di-set
        duration_sec = summary['duration_seconds']
        if duration_sec is not None:
            duration_str = f"{duration_sec:.1f} seconds (~{duration_sec / 60:.1f} minutes)"
        else:
            duration_str = "N/A"

        # FIX 2: Bangun header report sebagai string biasa (bukan f-string multiline)
        # agar loop for phase_id bisa berjalan di dalam method dan concatenate ke report_text
        report_text = (
            "\n"
            "================================================================================\n"
            "PIPELINE EXECUTION REPORT\n"
            "================================================================================\n"
            "\n"
            "Execution Summary:\n"
            f"  Start Time    : {summary['start_time']}\n"
            f"  End Time      : {summary['end_time'] or 'N/A'}\n"
            f"  Total Duration: {duration_str}\n"
            "\n"
            "Phase Status:\n"
        )

        # FIX 3: Loop di dalam method — concatenate satu baris per phase
        phase_names = {
            1: 'Data Foundation',
            2: 'Veracity Validation',
            3: 'Sentiment Analysis',
            4: 'Google Trends Integration',
            5: 'Longitudinal Modeling',
            6: 'Visualization & Reporting',
        }
        for phase_id in [1, 2, 3, 4, 5, 6]:
            status = self.phase_status.get(f'F{phase_id}', 'NOT RUN') or 'NOT RUN'
            pad_name = (phase_names[phase_id] + '.').ljust(40, '.')
            report_text += f"  Phase {phase_id}: {pad_name} {status}\n"

        # Error section
        if self.errors:
            report_text += f"\nErrors ({len(self.errors)}):\n"
            for i, error in enumerate(self.errors, 1):
                report_text += f"  {i}. {error}\n"
        else:
            report_text += "\n✓ NO ERRORS - Pipeline completed successfully!\n"

        # Footer
        report_text += (
            "\n"
            "Output Files:\n"
            f"  Reports       : {REPORTS_DIR}\n"
            f"  Figures       : {FIGURES_DIR}\n"
            f"  Processed Data: {PROCESSED_DATA_DIR}\n"
            "\n"
            "Key Outputs:\n"
            "  - Master Dataset        : master_dataset_unified.parquet\n"
            "  - Sentiment Analysis    : sentiment_analyzed_full.parquet\n"
            "  - Temporal Trends       : sentiment_trends_temporal.csv\n"
            "  - Integrated Signals    : integrated_signals_monthly.csv\n"
            "\n"
            "Recommended Next Steps:\n"
            f"  1. Review Phase reports in {REPORTS_DIR}\n"
            f"  2. Examine generated visualizations in {FIGURES_DIR}\n"
            "  3. For Phase 2: Complete manual annotation (if using gold standard)\n"
            "  4. For Phase 5: Fine-tune model parameters based on validation metrics\n"
            "  5. Prepare manuscript (Lancet Digital Health, JMIR, BMC Public Health)\n"
            "\n"
            "================================================================================\n"
            f"End of Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            "================================================================================\n"
        )

        logger.info(report_text)

        # Save report file
        report_file = REPORTS_DIR / "PIPELINE_EXECUTION_REPORT.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
        logger.info(f"Final report saved to {report_file}")

        # Save JSON summary
        json_file = REPORTS_DIR / "pipeline_summary.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': summary,
                'phase_results': self.phase_results,
            }, f, indent=2, default=str)
        logger.info(f"JSON summary saved to {json_file}")


# ============================================================================
# ENTRY POINT
# ============================================================================
def main():
    """Main entry point"""

    np.random.seed(REPRODUCIBILITY_CONFIG["random_seed"])

    orchestrator = PipelineOrchestrator()

    try:
        # FIX: Jalankan semua phase 1-6
        summary = orchestrator.run_complete_pipeline(phases=[1, 2, 3, 4, 5, 6])

        logger.info("\n" + "=" * 80)
        logger.info("PIPELINE SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Status: {'✓ SUCCESS' if summary['success'] else '✗ FAILED'}")

        # FIX: Guard None sebelum format :.1f
        duration_sec = summary.get('duration_seconds')
        if duration_sec is not None:
            logger.info(f"Duration: {duration_sec:.1f} seconds")
        else:
            logger.info("Duration: N/A")

        logger.info(f"Total Errors: {summary['total_errors']}")
        logger.info("=" * 80)

        return 0 if summary['success'] else 1

    except KeyboardInterrupt:
        logger.error("\nPipeline interrupted by user")
        return 2
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        traceback.print_exc()
        return 3


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)