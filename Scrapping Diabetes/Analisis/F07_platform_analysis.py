# ============================================================================
# PHASE 7: PLATFORM-SPECIFIC ANALYSIS + RISKESDAS/IDF COMPARISON READY
# ============================================================================
"""
Analisis per platform dengan struktur siap untuk comparison:
- Digital sentiment ↔ Riskesdas behavior
- Search trends ↔ IDF prevalence
- Discussion patterns ↔ Medical reality
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, Any

from config import PROCESSED_DATA_DIR, REPORTS_DIR, FIGURES_DIR

sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (16, 10)

from loguru import logger

class PlatformAnalyzer:
    """Analisis per platform dengan comparison framework"""
    
    def __init__(self, master_df: pd.DataFrame):
        self.df = master_df
        self.results = {}
        self.comparison_data = {}  # Siap untuk Riskesdas/IDF comparison
    
    def analyze_twitter(self) -> Dict[str, Any]:
        """Twitter: Real-time reaction & news coverage"""
        logger.info("\n" + "="*80)
        logger.info("PLATFORM ANALYSIS: TWITTER")
        logger.info("="*80)
        
        twitter_df = self.df[self.df['platform'] == 'twitter'].copy()
        
        results = {
            "platform": "twitter",
            "total_posts": len(twitter_df),
            "date_range": f"{twitter_df['date'].min().date()} to {twitter_df['date'].max().date()}",
            "description": "Real-time reactions, news coverage, public discourse",
            "characteristics": {
                "use_case": "Breaking news, viral moments, emotional reactions",
                "audience": "All demographics, but younger dominant",
                "reliability": "Mixed - includes misinformation",
                "time_sensitivity": "Very high - daily changes",
            }
        }
        
        # Sentiment distribution
        if 'sentiment_label' in twitter_df.columns:
            sentiment_dist = twitter_df['sentiment_label'].value_counts(normalize=True).to_dict()
            results["sentiment_distribution"] = sentiment_dist
            
            # Structure for comparison
            results["comparison_metrics"] = {
                "positive_percentage": sentiment_dist.get('POSITIVE', 0) * 100,
                "neutral_percentage": sentiment_dist.get('NEUTRAL', 0) * 100,
                "negative_percentage": sentiment_dist.get('NEGATIVE', 0) * 100,
                "sentiment_mean": float(twitter_df['sentiment_score'].mean()),
                "sentiment_std": float(twitter_df['sentiment_score'].std()),
            }
            
            # Visualization - COMPARISON READY
            fig, axes = plt.subplots(2, 3, figsize=(18, 12))
            fig.suptitle('TWITTER ANALYSIS: Real-time Reactions\n(Untuk Comparison dengan Riskesdas/IDF)', 
                        fontsize=16, fontweight='bold', y=1.00)
            
            # 1. Sentiment pie chart
            colors = {'POSITIVE': '#2ecc71', 'NEUTRAL': '#95a5a6', 'NEGATIVE': '#e74c3c'}
            sentiment_counts = twitter_df['sentiment_label'].value_counts()
            wedges, texts, autotexts = axes[0, 0].pie(
                sentiment_counts.values,
                labels=sentiment_counts.index,
                autopct='%1.1f%%',
                colors=[colors.get(x, '#999') for x in sentiment_counts.index],
                startangle=90,
                textprops={'fontsize': 11, 'weight': 'bold'}
            )
            axes[0, 0].set_title('Sentiment Distribution\n(Digital sentiment)', 
                                fontsize=12, fontweight='bold')
            
            # 2. Sentiment over time - untuk melihat trend
            twitter_df['year_month'] = twitter_df['date'].dt.to_period('M')
            monthly_sentiment = twitter_df.groupby('year_month')['sentiment_score'].agg(['mean', 'std', 'count'])
            x_axis = range(len(monthly_sentiment))
            axes[0, 1].plot(x_axis, monthly_sentiment['mean'].values, 
                          color='#3498db', linewidth=2.5, marker='o', markersize=5, label='Mean sentiment')
            axes[0, 1].fill_between(
                x_axis,
                monthly_sentiment['mean'] - monthly_sentiment['std'],
                monthly_sentiment['mean'] + monthly_sentiment['std'],
                alpha=0.2, color='#3498db', label='±1 Std Dev'
            )
            axes[0, 1].axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
            axes[0, 1].set_title('Sentiment Trend (11 Years)\n(Track changes over time)', 
                               fontsize=12, fontweight='bold')
            axes[0, 1].set_ylabel('Sentiment Score (-1 to +1)')
            axes[0, 1].legend()
            axes[0, 1].grid(True, alpha=0.3)
            
            # 3. Year-over-year comparison
            twitter_df['year'] = twitter_df['date'].dt.year
            yearly_sentiment_stats = twitter_df.groupby('year')['sentiment_score'].agg(['mean', 'std', 'count'])
            axes[0, 2].errorbar(yearly_sentiment_stats.index, yearly_sentiment_stats['mean'], 
                              yerr=yearly_sentiment_stats['std'], 
                              fmt='o-', color='#3498db', linewidth=2.5, markersize=8, capsize=5)
            axes[0, 2].axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
            axes[0, 2].set_title('Year-over-Year Sentiment\n(Annual comparison for Riskesdas validation)', 
                               fontsize=12, fontweight='bold')
            axes[0, 2].set_ylabel('Mean Sentiment')
            axes[0, 2].set_xlabel('Year')
            axes[0, 2].grid(True, alpha=0.3)
            
            # 4. Volume trend
            monthly_volume = twitter_df.groupby('year_month').size()
            axes[1, 0].bar(range(len(monthly_volume)), monthly_volume.values, 
                         color='#3498db', alpha=0.7, edgecolor='black', linewidth=0.5)
            axes[1, 0].set_title('Monthly Volume\n(Discussion intensity)', 
                               fontsize=12, fontweight='bold')
            axes[1, 0].set_ylabel('Number of Posts')
            axes[1, 0].grid(True, alpha=0.3, axis='y')
            
            # 5. Sentiment composition by year
            yearly_sentiment = pd.crosstab(
                twitter_df['year'], 
                twitter_df['sentiment_label'], 
                normalize='index'
            ) * 100
            yearly_sentiment.plot(kind='bar', ax=axes[1, 1], 
                                color=['#e74c3c', '#95a5a6', '#2ecc71'],
                                edgecolor='black', linewidth=0.5)
            axes[1, 1].set_title('Sentiment Composition by Year\n(Compare with Riskesdas years)', 
                               fontsize=12, fontweight='bold')
            axes[1, 1].set_ylabel('Percentage (%)')
            axes[1, 1].legend(title='Sentiment', loc='best')
            axes[1, 1].set_xlabel('Year')
            plt.setp(axes[1, 1].xaxis.get_majorticklabels(), rotation=45)
            axes[1, 1].grid(True, alpha=0.3, axis='y')
            
            # 6. Comparison readiness table
            axes[1, 2].axis('off')
            comparison_info = f"""
            COMPARISON FRAMEWORK READY
            
            📊 KEY METRICS FOR VALIDATION:
            
            Total Posts: {len(twitter_df):,}
            Positive: {sentiment_dist.get('POSITIVE', 0)*100:.1f}%
            Neutral: {sentiment_dist.get('NEUTRAL', 0)*100:.1f}%
            Negative: {sentiment_dist.get('NEGATIVE', 0)*100:.1f}%
            
            Mean Sentiment: {twitter_df['sentiment_score'].mean():.3f}
            Std Dev: {twitter_df['sentiment_score'].std():.3f}
            
            📅 RISKESDAS COMPARISON POINTS:
            • Riskesdas 2018: Compare with 2018 digital
            • Riskesdas 2023: Compare with 2023 digital
            • IDF 2021: Compare with 2021 digital
            
            ✓ Ready for external validation
            """
            axes[1, 2].text(0.05, 0.95, comparison_info, fontsize=10, verticalalignment='top',
                          family='monospace', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
            
            plt.tight_layout()
            fig.savefig(FIGURES_DIR / "07_Twitter_Analysis_Comparison.png", dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"✓ Twitter analysis completed")
            logger.info(f"  Total posts: {len(twitter_df):,}")
            logger.info(f"  Sentiment - Pos: {sentiment_dist.get('POSITIVE', 0)*100:.1f}%, "
                       f"Neu: {sentiment_dist.get('NEUTRAL', 0)*100:.1f}%, "
                       f"Neg: {sentiment_dist.get('NEGATIVE', 0)*100:.1f}%")
        
        return results
    
    def analyze_youtube(self) -> Dict[str, Any]:
        """YouTube: Educational content & trusted sources"""
        logger.info("\n" + "="*80)
        logger.info("PLATFORM ANALYSIS: YOUTUBE")
        logger.info("="*80)
        
        youtube_df = self.df[self.df['platform'] == 'youtube'].copy()
        
        results = {
            "platform": "youtube",
            "total_videos": len(youtube_df),
            "date_range": f"{youtube_df['date'].min().date()} to {youtube_df['date'].max().date()}" if len(youtube_df) > 0 else "N/A",
            "description": "Educational content, expert discussions, long-form content",
            "characteristics": {
                "use_case": "Education, credible sources, detailed explanations",
                "audience": "Diverse, health-conscious viewers",
                "reliability": "Higher - usually from credible creators",
                "time_sensitivity": "Lower - evergreen content",
            }
        }
        
        if len(youtube_df) > 0 and 'sentiment_label' in youtube_df.columns:
            sentiment_dist = youtube_df['sentiment_label'].value_counts(normalize=True).to_dict()
            results["sentiment_distribution"] = sentiment_dist
            
            results["comparison_metrics"] = {
                "positive_percentage": sentiment_dist.get('POSITIVE', 0) * 100,
                "neutral_percentage": sentiment_dist.get('NEUTRAL', 0) * 100,
                "negative_percentage": sentiment_dist.get('NEGATIVE', 0) * 100,
                "sentiment_mean": float(youtube_df['sentiment_score'].mean()),
                "sentiment_std": float(youtube_df['sentiment_score'].std()),
            }
            
            fig, axes = plt.subplots(2, 3, figsize=(18, 12))
            fig.suptitle('YOUTUBE ANALYSIS: Educational Content\n(Untuk Comparison dengan IDF Educational Resources)', 
                        fontsize=16, fontweight='bold', y=1.00)
            
            colors = {'POSITIVE': '#2ecc71', 'NEUTRAL': '#95a5a6', 'NEGATIVE': '#e74c3c'}
            sentiment_counts = youtube_df['sentiment_label'].value_counts()
            
            axes[0, 0].pie(
                sentiment_counts.values,
                labels=sentiment_counts.index,
                autopct='%1.1f%%',
                colors=[colors.get(x, '#999') for x in sentiment_counts.index],
                startangle=90,
                textprops={'fontsize': 11, 'weight': 'bold'}
            )
            axes[0, 0].set_title('Sentiment Distribution\n(Content tone)', 
                               fontsize=12, fontweight='bold')
            
            # Sentiment trend
            youtube_df['year_month'] = youtube_df['date'].dt.to_period('M')
            if len(youtube_df['year_month'].unique()) > 1:
                monthly_sentiment = youtube_df.groupby('year_month')['sentiment_score'].agg(['mean', 'count'])
                axes[0, 1].plot(range(len(monthly_sentiment)), monthly_sentiment['mean'].values, 
                              color='#e67e22', linewidth=2.5, marker='o', markersize=6)
                axes[0, 1].axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
                axes[0, 1].set_title('Sentiment Trend\n(Educational consistency)', 
                                   fontsize=12, fontweight='bold')
                axes[0, 1].grid(True, alpha=0.3)
            
            # Year comparison
            youtube_df['year'] = youtube_df['date'].dt.year
            yearly_stats = youtube_df.groupby('year')['sentiment_score'].agg(['mean', 'count'])
            axes[0, 2].bar(yearly_stats.index, yearly_stats['mean'], 
                         color='#e67e22', alpha=0.7, edgecolor='black', linewidth=0.5)
            axes[0, 2].set_title('Sentiment by Year\n(Content quality tracking)', 
                               fontsize=12, fontweight='bold')
            axes[0, 2].set_ylabel('Mean Sentiment')
            axes[0, 2].grid(True, alpha=0.3, axis='y')
            
            # Volume
            monthly_volume = youtube_df.groupby('year_month').size()
            axes[1, 0].bar(range(len(monthly_volume)), monthly_volume.values, 
                         color='#e67e22', alpha=0.7, edgecolor='black', linewidth=0.5)
            axes[1, 0].set_title('Content Creation Rate\n(How often creators post)', 
                               fontsize=12, fontweight='bold')
            axes[1, 0].set_ylabel('Number of Videos')
            axes[1, 0].grid(True, alpha=0.3, axis='y')
            
            # Yearly breakdown
            yearly_composition = pd.crosstab(youtube_df['year'], youtube_df['sentiment_label'], normalize='index') * 100
            if not yearly_composition.empty:
                yearly_composition.plot(kind='bar', ax=axes[1, 1], 
                                      color=['#e74c3c', '#95a5a6', '#2ecc71'],
                                      edgecolor='black', linewidth=0.5)
                axes[1, 1].set_title('Content Sentiment Breakdown\n(Educational balance)', 
                                   fontsize=12, fontweight='bold')
                axes[1, 1].legend(title='Sentiment')
                axes[1, 1].set_xlabel('Year')
                plt.setp(axes[1, 1].xaxis.get_majorticklabels(), rotation=45)
            
            # Summary
            axes[1, 2].axis('off')
            summary_info = f"""
            YOUTUBE EDUCATION QUALITY
            
            📺 CONTENT METRICS:
            Total Videos: {len(youtube_df)}
            Positive Tone: {sentiment_dist.get('POSITIVE', 0)*100:.1f}%
            Neutral Tone: {sentiment_dist.get('NEUTRAL', 0)*100:.1f}%
            Critical Tone: {sentiment_dist.get('NEGATIVE', 0)*100:.1f}%
            
            Mean Sentiment: {youtube_df['sentiment_score'].mean():.3f}
            
            📊 IDF COMPARISON:
            • Compare with IDF recommended content
            • Assess educational quality
            • Track misinformation rate
            
            ✓ Quality assessment ready
            """
            axes[1, 2].text(0.05, 0.95, summary_info, fontsize=10, verticalalignment='top',
                          family='monospace', bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.7))
            
            plt.tight_layout()
            fig.savefig(FIGURES_DIR / "07_YouTube_Analysis_Comparison.png", dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"✓ YouTube analysis completed")
            logger.info(f"  Total videos: {len(youtube_df)}")
        
        return results
    
    def analyze_threads(self) -> Dict[str, Any]:
        """Threads: Community & peer support"""
        logger.info("\n" + "="*80)
        logger.info("PLATFORM ANALYSIS: THREADS")
        logger.info("="*80)
        
        threads_df = self.df[self.df['platform'] == 'threads'].copy()
        
        results = {
            "platform": "threads",
            "total_discussions": len(threads_df),
            "date_range": f"{threads_df['date'].min().date()} to {threads_df['date'].max().date()}" if len(threads_df) > 0 else "N/A",
            "description": "Peer support, community discussions, personal experiences",
            "characteristics": {
                "use_case": "Patient stories, peer support, lived experiences",
                "audience": "Engaged patients, caregivers",
                "reliability": "Mixed - authentic but not always medically accurate",
                "time_sensitivity": "Medium",
            }
        }
        
        if len(threads_df) > 0 and 'sentiment_label' in threads_df.columns:
            sentiment_dist = threads_df['sentiment_label'].value_counts(normalize=True).to_dict()
            results["sentiment_distribution"] = sentiment_dist
            
            results["comparison_metrics"] = {
                "positive_percentage": sentiment_dist.get('POSITIVE', 0) * 100,
                "neutral_percentage": sentiment_dist.get('NEUTRAL', 0) * 100,
                "negative_percentage": sentiment_dist.get('NEGATIVE', 0) * 100,
                "sentiment_mean": float(threads_df['sentiment_score'].mean()),
                "sentiment_std": float(threads_df['sentiment_score'].std()),
            }
            
            fig, axes = plt.subplots(2, 3, figsize=(18, 12))
            fig.suptitle('THREADS ANALYSIS: Community Voices\n(Patient Perspectives vs Official Data)', 
                        fontsize=16, fontweight='bold', y=1.00)
            
            colors = {'POSITIVE': '#2ecc71', 'NEUTRAL': '#95a5a6', 'NEGATIVE': '#e74c3c'}
            sentiment_counts = threads_df['sentiment_label'].value_counts()
            
            axes[0, 0].pie(
                sentiment_counts.values,
                labels=sentiment_counts.index,
                autopct='%1.1f%%',
                colors=[colors.get(x, '#999') for x in sentiment_counts.index],
                startangle=90,
                textprops={'fontsize': 11, 'weight': 'bold'}
            )
            axes[0, 0].set_title('Community Sentiment\n(Patient perspective)', 
                               fontsize=12, fontweight='bold')
            
            # Growth
            threads_df['year_month'] = threads_df['date'].dt.to_period('M')
            monthly_volume = threads_df.groupby('year_month').size()
            axes[0, 1].bar(range(len(monthly_volume)), monthly_volume.values, 
                         color='#9b59b6', alpha=0.7, edgecolor='black', linewidth=0.5)
            axes[0, 1].set_title('Community Growth\n(Emerging platform)', 
                               fontsize=12, fontweight='bold')
            axes[0, 1].set_ylabel('Posts per Month')
            axes[0, 1].grid(True, alpha=0.3, axis='y')
            
            # Sentiment trend
            monthly_sentiment = threads_df.groupby('year_month')['sentiment_score'].mean()
            if len(monthly_sentiment) > 1:
                axes[0, 2].plot(range(len(monthly_sentiment)), monthly_sentiment.values, 
                              color='#9b59b6', linewidth=2.5, marker='o', markersize=6)
                axes[0, 2].axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
                axes[0, 2].set_title('Sentiment Trajectory\n(Community mood tracking)', 
                                   fontsize=12, fontweight='bold')
                axes[0, 2].grid(True, alpha=0.3)
            
            # Composition over time
            threads_df['year_month_str'] = threads_df['date'].dt.strftime('%Y-%m')
            monthly_composition = pd.crosstab(
                threads_df['year_month_str'],
                threads_df['sentiment_label'],
                normalize='index'
            ) * 100
            
            if not monthly_composition.empty and len(monthly_composition) > 1:
                monthly_composition.plot(kind='area', ax=axes[1, 0], 
                                      color=['#e74c3c', '#95a5a6', '#2ecc71'],
                                      alpha=0.7)
                axes[1, 0].set_title('Sentiment Evolution\n(Community mood changes)', 
                                   fontsize=12, fontweight='bold')
                axes[1, 0].set_ylabel('Percentage (%)')
                axes[1, 0].legend(title='Sentiment', loc='best')
                axes[1, 0].grid(True, alpha=0.3)
            
            # Year analysis
            threads_df['year'] = threads_df['date'].dt.year
            yearly_sentiment = pd.crosstab(threads_df['year'], threads_df['sentiment_label'], normalize='index') * 100
            if not yearly_sentiment.empty:
                yearly_sentiment.plot(kind='bar', ax=axes[1, 1], 
                                    color=['#e74c3c', '#95a5a6', '#2ecc71'],
                                    edgecolor='black', linewidth=0.5)
                axes[1, 1].set_title('Sentiment by Year\n(Annual comparison)', 
                                   fontsize=12, fontweight='bold')
                axes[1, 1].set_ylabel('Percentage (%)')
                axes[1, 1].legend(title='Sentiment')
                plt.setp(axes[1, 1].xaxis.get_majorticklabels(), rotation=45)
            
            # Notes
            axes[1, 2].axis('off')
            notes = f"""
            COMMUNITY INSIGHTS
            
            👥 ENGAGEMENT METRICS:
            Total Discussions: {len(threads_df)}
            Positive Sentiment: {sentiment_dist.get('POSITIVE', 0)*100:.1f}%
            Neutral: {sentiment_dist.get('NEUTRAL', 0)*100:.1f}%
            Negative: {sentiment_dist.get('NEGATIVE', 0)*100:.1f}%
            
            ⚠️ DATA QUALITY NOTE:
            Threads dataset berantakan
            (High duplication rate)
            Use for trend indication only
            
            📋 RISKESDAS COMPARISON:
            Compare patient experiences
            with official health stats
            """
            axes[1, 2].text(0.05, 0.95, notes, fontsize=10, verticalalignment='top',
                          family='monospace', bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.5))
            
            plt.tight_layout()
            fig.savefig(FIGURES_DIR / "07_Threads_Analysis_Comparison.png", dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"✓ Threads analysis completed")
            logger.info(f"  Total discussions: {len(threads_df)}")
        
        return results
    
    def create_comparison_template(self):
        """Buat template untuk comparison dengan Riskesdas & IDF"""
        logger.info("\n" + "="*80)
        logger.info("CREATING COMPARISON TEMPLATE")
        logger.info("="*80)
        
        # Create comparison DataFrame template
        comparison_template = pd.DataFrame({
            'Metric': [
                'Total Data Points',
                'Positive Sentiment (%)',
                'Neutral Sentiment (%)',
                'Negative Sentiment (%)',
                'Mean Sentiment Score',
                'Data Period',
                'Primary Use Case',
                'Data Quality',
                'Reliability Score',
            ],
            'Twitter (Digital)': [
                len(self.df[self.df['platform'] == 'twitter']),
                '',
                '',
                '',
                '',
                '2016-2026',
                'Real-time reactions, news coverage',
                'Mixed - includes misinformation',
                'Medium (74% of digital data)',
            ],
            'YouTube (Digital)': [
                len(self.df[self.df['platform'] == 'youtube']),
                '',
                '',
                '',
                '',
                '2018-2026',
                'Educational content, credible sources',
                'Higher - curated content',
                'High (educational)',
            ],
            'Riskesdas 2023 (Official)': [
                '',
                '',
                '',
                '',
                '',
                'Survey 2023',
                'Population health epidemiology',
                'Very high - randomized survey',
                'Very high (gold standard)',
            ],
            'IDF Data (International)': [
                '',
                '',
                '',
                '',
                '',
                'Latest available',
                'Global diabetes trends',
                'High - medical data',
                'Very high (expert consensus)',
            ],
        })
        
        # Save template
        template_file = REPORTS_DIR / "Comparison_Template_Riskesdas_IDF.xlsx"
        try:
            with pd.ExcelWriter(template_file, engine='openpyxl') as writer:
                comparison_template.to_excel(writer, sheet_name='Digital vs Official', index=False)
                
                # Add Riskesdas sheet
                riskesdas_sheet = pd.DataFrame({
                    'Riskesdas Metric': ['Diabetes Prevalence %', 'Age Group', 'Gender Distribution', 'Treatment Coverage %'],
                    '2013': ['', '', '', ''],
                    '2018': ['', '', '', ''],
                    '2023': ['', '', '', ''],
                    'Our Digital Data 2023': ['', '', '', ''],
                })
                riskesdas_sheet.to_excel(writer, sheet_name='Riskesdas Comparison', index=False)
                
                # Add IDF sheet
                idf_sheet = pd.DataFrame({
                    'IDF Indicator': ['Global Diabetes Prevalence', 'SE Asia Prevalence', 'Indonesia Projection', 'Healthcare Access'],
                    'IDF Data': ['', '', '', ''],
                    'Our Digital Indication': ['', '', '', ''],
                    'Alignment': ['', '', '', ''],
                })
                idf_sheet.to_excel(writer, sheet_name='IDF Comparison', index=False)
        
        except Exception as e:
            logger.warning(f"Excel export failed: {e}, saving CSV instead")
            template_file = REPORTS_DIR / "Comparison_Template_Riskesdas_IDF.csv"
            comparison_template.to_csv(template_file, index=False)
        
        logger.info(f"✓ Comparison template created: {template_file}")
        logger.info("  Ready for you to fill with Riskesdas & IDF data")
        
        return template_file
    
    def run_all_platform_analysis(self) -> Dict[str, Any]:
        """Run semua analisis platform"""
        logger.info("\n" + "="*80)
        logger.info("PHASE 7: PLATFORM-SPECIFIC ANALYSIS + COMPARISON FRAMEWORK")
        logger.info("="*80)
        
        self.results['twitter'] = self.analyze_twitter()
        self.results['youtube'] = self.analyze_youtube()
        self.results['threads'] = self.analyze_threads()
        self.results['template_file'] = str(self.create_comparison_template())
        
        # Save results
        report_file = REPORTS_DIR / "Phase7_Platform_Analysis_Report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, default=str, ensure_ascii=False)
        
        logger.info(f"\n✓ Platform analysis completed")
        logger.info(f"  Report saved: {report_file}")
        logger.info(f"  Figures: {FIGURES_DIR}")
        logger.info(f"  Comparison template: {self.results['template_file']}")
        
        return self.results


def main():
    """Execute Phase 7"""
    master_file = PROCESSED_DATA_DIR / "master_dataset_unified.csv"
    
    logger.info(f"Loading master dataset...")
    master_df = pd.read_csv(master_file)
    master_df['date'] = pd.to_datetime(master_df['date'])
    
    analyzer = PlatformAnalyzer(master_df)
    results = analyzer.run_all_platform_analysis()
    
    return results


if __name__ == "__main__":
    results = main()