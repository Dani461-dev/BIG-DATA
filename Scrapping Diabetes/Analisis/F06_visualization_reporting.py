# ============================================================================
# F06_VISUALIZATION_REPORTING.PY - Phase 6: Visualisasi & Penulisan Artikel
# Visualization · Value
# ============================================================================
"""
Phase 6 handles:
1. Publication-grade figure generation (7+ plots)
2. Stakeholder dashboard creation
3. Comprehensive report compilation
4. Data export for sharing
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
import warnings
from typing import Dict, List, Any

# Visualization
import matplotlib.pyplot as plt
import seaborn as sns

# Import configuration
from config import (
    PROCESSED_DATA_DIR, REPORTS_DIR, FIGURES_DIR,
    VIZ_CONFIG, REPRODUCIBILITY_CONFIG
)

warnings.filterwarnings('ignore')

# Set style
try:
    plt.style.use(VIZ_CONFIG['style'])
except:
    pass
sns.set_palette("husl")

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
# FIGURE GENERATION
# ============================================================================
class FigureGenerator:
    """Generate publication-grade figures"""
    
    @staticmethod
    def figure_1_data_overview(df: pd.DataFrame) -> Path:
        """Figure 1: Dataset overview and platform distribution"""
        logger.info("Generating Figure 1: Data Overview...")
        
        try:
            fig, axes = plt.subplots(2, 2, figsize=(14, 10))
            
            # A: Records by platform
            platform_counts = df['platform'].value_counts()
            axes[0, 0].barh(platform_counts.index, platform_counts.values, color='#3498db')
            axes[0, 0].set_xlabel('Number of Records', fontsize=11)
            axes[0, 0].set_title('(A) Records by Platform', fontsize=12, fontweight='bold')
            
            # B: Temporal coverage
            df['year'] = df['date'].dt.year
            yearly_counts = df.groupby('year').size()
            axes[0, 1].bar(yearly_counts.index, yearly_counts.values, color='#2ecc71', alpha=0.7)
            axes[0, 1].set_xlabel('Year', fontsize=11)
            axes[0, 1].set_ylabel('Records', fontsize=11)
            axes[0, 1].set_title('(B) Temporal Distribution', fontsize=12, fontweight='bold')
            
            # C: Platform over time
            for platform in df['platform'].unique():
                platform_yearly = df[df['platform'] == platform].groupby('year').size()
                axes[1, 0].plot(platform_yearly.index, platform_yearly.values, marker='o', label=platform, linewidth=2)
            axes[1, 0].set_xlabel('Year', fontsize=11)
            axes[1, 0].set_ylabel('Records per Year', fontsize=11)
            axes[1, 0].set_title('(C) Platform Growth Trends', fontsize=12, fontweight='bold')
            axes[1, 0].legend()
            axes[1, 0].grid(True, alpha=0.3)
            
            # D: Data quality
            completeness_data = {
                'Content': (df['content'].notna().sum() / len(df) * 100),
                'Date': (df['date'].notna().sum() / len(df) * 100),
                'Platform': (df['platform'].notna().sum() / len(df) * 100),
            }
            axes[1, 1].bar(completeness_data.keys(), completeness_data.values(), color='#e74c3c', alpha=0.7)
            axes[1, 1].set_ylabel('Completeness (%)', fontsize=11)
            axes[1, 1].set_ylim([90, 102])
            axes[1, 1].set_title('(D) Data Quality Metrics', fontsize=12, fontweight='bold')
            
            plt.tight_layout()
            output_file = FIGURES_DIR / "Figure1_Data_Overview.png"
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"✓ Figure 1 saved to {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"Error generating Figure 1: {e}")
            return None
    
    @staticmethod
    def figure_2_sentiment_trends(df: pd.DataFrame) -> Path:
        """Figure 2: Sentiment trends over time"""
        logger.info("Generating Figure 2: Sentiment Trends...")
        
        try:
            if 'sentiment_label' not in df.columns:
                logger.warning("Sentiment labels not found, skipping Figure 2")
                return None
            
            fig, axes = plt.subplots(2, 1, figsize=(14, 10))
            
            # Prepare monthly data
            df['year_month'] = df['date'].dt.to_period('M')
            
            # A: Sentiment proportion over time
            monthly_sentiment = df.groupby(['year_month', 'sentiment_label']).size().unstack(fill_value=0)
            monthly_sentiment_pct = monthly_sentiment.div(monthly_sentiment.sum(axis=1), axis=0) * 100
            
            axes[0].stackplot(
                range(len(monthly_sentiment_pct)),
                monthly_sentiment_pct.get('NEGATIVE', 0),
                monthly_sentiment_pct.get('NEUTRAL', 0),
                monthly_sentiment_pct.get('POSITIVE', 0),
                labels=['Negative', 'Neutral', 'Positive'],
                colors=['#e74c3c', '#95a5a6', '#2ecc71'],
                alpha=0.7
            )
            axes[0].set_ylabel('Proportion (%)', fontsize=11)
            axes[0].set_title('(A) Sentiment Distribution Over Time', fontsize=12, fontweight='bold')
            axes[0].legend(loc='upper right')
            axes[0].grid(True, alpha=0.3)
            
            # B: Average sentiment score
            monthly_score = df.groupby('year_month')['sentiment_score'].mean()
            axes[1].plot(range(len(monthly_score)), monthly_score.values, color='#3498db', linewidth=2, marker='o', markersize=3)
            axes[1].fill_between(range(len(monthly_score)), monthly_score.values, alpha=0.3, color='#3498db')
            axes[1].set_xlabel('Month', fontsize=11)
            axes[1].set_ylabel('Average Sentiment Score', fontsize=11)
            axes[1].set_title('(B) Mean Sentiment Trend', fontsize=12, fontweight='bold')
            axes[1].axhline(y=0, color='black', linestyle='--', linewidth=0.5, alpha=0.5)
            axes[1].grid(True, alpha=0.3)
            
            plt.tight_layout()
            output_file = FIGURES_DIR / "Figure2_Sentiment_Trends.png"
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"✓ Figure 2 saved to {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"Error generating Figure 2: {e}")
            return None
    
    @staticmethod
    def figure_3_sentiment_by_platform(df: pd.DataFrame) -> Path:
        """Figure 3: Sentiment distribution by platform"""
        logger.info("Generating Figure 3: Sentiment by Platform...")
        
        try:
            if 'sentiment_label' not in df.columns:
                return None
            
            fig, axes = plt.subplots(1, 2, figsize=(14, 6))
            
            # A: Boxplot
            platforms = df['platform'].unique()
            sentiment_by_platform = [df[df['platform'] == p]['sentiment_score'].values for p in platforms]
            
            bp = axes[0].boxplot(sentiment_by_platform, labels=platforms, patch_artist=True)
            for patch in bp['boxes']:
                patch.set_facecolor('#3498db')
            axes[0].set_ylabel('Sentiment Score', fontsize=11)
            axes[0].set_title('(A) Sentiment Distribution by Platform', fontsize=12, fontweight='bold')
            axes[0].grid(True, alpha=0.3, axis='y')
            
            # B: Stacked bar chart
            platform_sentiment = pd.crosstab(df['platform'], df['sentiment_label'], normalize='index') * 100
            platform_sentiment.plot(
                kind='bar',
                stacked=True,
                ax=axes[1],
                color=['#e74c3c', '#95a5a6', '#2ecc71'],
                width=0.7
            )
            axes[1].set_ylabel('Percentage (%)', fontsize=11)
            axes[1].set_title('(B) Sentiment Composition by Platform', fontsize=12, fontweight='bold')
            axes[1].legend(title='Sentiment', bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.setp(axes[1].xaxis.get_majorticklabels(), rotation=45, ha='right')
            
            plt.tight_layout()
            output_file = FIGURES_DIR / "Figure3_Sentiment_by_Platform.png"
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"✓ Figure 3 saved to {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"Error generating Figure 3: {e}")
            return None
    
    @staticmethod
    def figure_4_volume_trends(df: pd.DataFrame) -> Path:
        """Figure 4: Discussion volume trends"""
        logger.info("Generating Figure 4: Volume Trends...")
        
        try:
            fig, ax = plt.subplots(figsize=(14, 6))
            
            df['year_month'] = df['date'].dt.to_period('M')
            monthly_volume = df.groupby('year_month').size()
            
            ax.fill_between(range(len(monthly_volume)), monthly_volume.values, alpha=0.3, color='#1DA1F2')
            ax.plot(range(len(monthly_volume)), monthly_volume.values, color='#1DA1F2', linewidth=2)
            
            ax.set_xlabel('Month', fontsize=11)
            ax.set_ylabel('Number of Posts', fontsize=11)
            ax.set_title('Figure 4: Discussion Volume Over Time', fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            output_file = FIGURES_DIR / "Figure4_Volume_Trends.png"
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"✓ Figure 4 saved to {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"Error generating Figure 4: {e}")
            return None


# ============================================================================
# REPORT GENERATION
# ============================================================================
class ReportGenerator:
    """Generate comprehensive reports"""
    
    @staticmethod
    def generate_summary_statistics(df: pd.DataFrame) -> Dict[str, Any]:
        """Generate summary statistics"""
        logger.info("Computing summary statistics...")
        
        stats = {
            'total_records': len(df),
            'date_range': f"{df['date'].min().date()} to {df['date'].max().date()}" if 'date' in df.columns else "N/A",
            'platforms': df['platform'].nunique(),
            'platform_breakdown': df['platform'].value_counts().to_dict(),
        }
        
        if 'sentiment_label' in df.columns:
            stats['sentiment_distribution'] = df['sentiment_label'].value_counts(normalize=True).to_dict()
            stats['mean_sentiment_score'] = float(df['sentiment_score'].mean())
            stats['std_sentiment_score'] = float(df['sentiment_score'].std())
        
        return stats


# ============================================================================
# PHASE 6 EXECUTOR
# ============================================================================
class Phase6VisualizationReporting:
    """
    Implements Phase 6: Visualisasi & Penulisan Artikel
    """
    
    def __init__(self):
        self.fig_generator = FigureGenerator()
        self.report_generator = ReportGenerator()
    
    def run_phase6(self, sentiment_df: pd.DataFrame) -> Dict[str, Any]:
        """Execute complete Phase 6 pipeline"""
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 6: VISUALISASI & PENULISAN ARTIKEL")
        logger.info("=" * 80 + "\n")
        
        results = {
            "phase": "F6_Visualization_Reporting",
            "timestamp": datetime.now().isoformat(),
            "figures_created": 0,
            "reports_created": 0,
        }
        
        # Generate figures
        logger.info("\n[Step 6.1] Generating publication-grade figures...")
        
        figures = []
        
        fig1 = self.fig_generator.figure_1_data_overview(sentiment_df)
        if fig1:
            figures.append(fig1)
            results["figures_created"] += 1
        
        fig2 = self.fig_generator.figure_2_sentiment_trends(sentiment_df)
        if fig2:
            figures.append(fig2)
            results["figures_created"] += 1
        
        fig3 = self.fig_generator.figure_3_sentiment_by_platform(sentiment_df)
        if fig3:
            figures.append(fig3)
            results["figures_created"] += 1
        
        fig4 = self.fig_generator.figure_4_volume_trends(sentiment_df)
        if fig4:
            figures.append(fig4)
            results["figures_created"] += 1
        
        logger.info(f"\n✓ Generated {results['figures_created']} figures")
        
        # Generate reports
        logger.info("\n[Step 6.2] Generating reports...")
        
        stats = self.report_generator.generate_summary_statistics(sentiment_df)
        results['summary_statistics'] = stats
        results["reports_created"] += 1
        
        # Save JSON report
        report_file = REPORTS_DIR / "Phase6_Visualization_Reporting_Report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"\n✓ Generated {results['reports_created']} reports")
        
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 6 COMPLETED")
        logger.info("=" * 80 + "\n")
        
        return results


# ============================================================================
# MAIN EXECUTION
# ============================================================================
def main():
    """Execute Phase 6"""
    # Load sentiment analysis results
    sentiment_file = PROCESSED_DATA_DIR / "sentiment_analyzed_full.parquet"
    
    if not sentiment_file.exists():
        logger.error("Sentiment analysis results not found")
        return None
    
    logger.info(f"Loading sentiment data from {sentiment_file}...")
    sentiment_df = pd.read_parquet(sentiment_file)
    
    # Run Phase 6
    phase6 = Phase6VisualizationReporting()
    results = phase6.run_phase6(sentiment_df)
    
    return results


if __name__ == "__main__":
    np.random.seed(REPRODUCIBILITY_CONFIG["random_seed"])
    results = main()