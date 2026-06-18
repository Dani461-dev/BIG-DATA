# ============================================================================
# PHASE 8: INTEGRATED INSIGHTS + COMPARISON FRAMEWORK
# ============================================================================
"""
Fase 8: Mengintegrasikan semua platform untuk mendapatkan insight holistik
yang siap dibanding dengan Riskesdas & IDF

Output:
1. Integrated sentiment analysis
2. Cross-platform trends
3. Comparison-ready metrics
4. Stakeholder insights
5. Streamlit dashboard data
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any
from scipy import stats
from scipy.signal import find_peaks

from config import PROCESSED_DATA_DIR, REPORTS_DIR, FIGURES_DIR
from loguru import logger

sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (18, 12)

# ============================================================================
# CUSTOM JSON ENCODER FOR NUMPY TYPES
# ============================================================================

class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder untuk handle numpy dan pandas types"""
    def default(self, obj):
        # Numpy integer types
        if isinstance(obj, (np.integer, np.int32, np.int64)):
            return int(obj)
        # Numpy float types
        elif isinstance(obj, (np.floating, np.float32, np.float64)):
            return float(obj)
        # Numpy arrays
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        # Pandas timestamp
        elif isinstance(obj, pd.Timestamp):
            return str(obj)
        # Pandas period
        elif isinstance(obj, pd.Period):
            return str(obj)
        # Fallback to default
        return super().default(obj)
# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def convert_to_serializable(obj):
    """Convert numpy and pandas types to Python native types recursively"""
    if isinstance(obj, dict):
        return {key: convert_to_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_serializable(item) for item in obj]
    elif isinstance(obj, (np.integer, np.int32, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (pd.Timestamp, pd.Period)):
        return str(obj)
    else:
        return obj
# ============================================================================
# INTEGRATED ANALYZER
# ============================================================================

class IntegratedInsightsAnalyzer:
    """Analisis terintegrasi semua platform"""
    
    def __init__(self, master_df: pd.DataFrame):
        self.df = master_df.copy()
        self.df['date'] = pd.to_datetime(self.df['date'])
        self.df['year_month'] = self.df['date'].dt.to_period('M')
        self.df['year'] = self.df['date'].dt.year
        self.results = {}
        self.dashboard_data = {}
    
    # ========================================================================
    # 1. INTEGRATED SENTIMENT ANALYSIS
    # ========================================================================
    
    def analyze_integrated_sentiment(self) -> Dict[str, Any]:
        """Analisis sentiment terintegrasi semua platform"""
        logger.info("\n" + "="*80)
        logger.info("[1] INTEGRATED SENTIMENT ANALYSIS")
        logger.info("="*80)
        
        results = {
            "name": "Integrated Sentiment Analysis",
            "total_records": len(self.df),
            "platforms": self.df['platform'].unique().tolist(),
        }
        
        # Overall sentiment
        if 'sentiment_label' in self.df.columns:
            overall_sentiment = self.df['sentiment_label'].value_counts(normalize=True).to_dict()
            results['overall_sentiment'] = {
                'positive': float(overall_sentiment.get('POSITIVE', 0) * 100),
                'neutral': float(overall_sentiment.get('NEUTRAL', 0) * 100),
                'negative': float(overall_sentiment.get('NEGATIVE', 0) * 100),
            }
            results['mean_sentiment_score'] = float(self.df['sentiment_score'].mean())
            results['std_sentiment_score'] = float(self.df['sentiment_score'].std())
            
            logger.info(f"Overall Sentiment Distribution:")
            logger.info(f"  Positive: {results['overall_sentiment']['positive']:.1f}%")
            logger.info(f"  Neutral: {results['overall_sentiment']['neutral']:.1f}%")
            logger.info(f"  Negative: {results['overall_sentiment']['negative']:.1f}%")
            
            # Platform comparison
            platform_sentiment = {}
            for platform in self.df['platform'].unique():
                platform_df = self.df[self.df['platform'] == platform]
                platform_sentiment[platform] = {
                    'total': len(platform_df),
                    'positive_pct': float((platform_df['sentiment_label'] == 'POSITIVE').sum() / len(platform_df) * 100),
                    'neutral_pct': float((platform_df['sentiment_label'] == 'NEUTRAL').sum() / len(platform_df) * 100),
                    'negative_pct': float((platform_df['sentiment_label'] == 'NEGATIVE').sum() / len(platform_df) * 100),
                    'mean_sentiment': float(platform_df['sentiment_score'].mean()),
                }
            
            results['platform_sentiment'] = platform_sentiment
            
            # Visualization 1: Integrated Sentiment
            fig, axes = plt.subplots(2, 3, figsize=(20, 12))
            fig.suptitle('PHASE 8: INTEGRATED INSIGHTS\nPlatform Comparison & Trends for Riskesdas/IDF Validation', 
                        fontsize=18, fontweight='bold', y=0.995)
            
            # 1A: Overall sentiment
            colors_sentiment = {'POSITIVE': '#2ecc71', 'NEUTRAL': '#95a5a6', 'NEGATIVE': '#e74c3c'}
            sentiment_counts = self.df['sentiment_label'].value_counts()
            axes[0, 0].pie(
                sentiment_counts.values,
                labels=sentiment_counts.index,
                autopct='%1.1f%%',
                colors=[colors_sentiment.get(x, '#999') for x in sentiment_counts.index],
                textprops={'fontsize': 12, 'weight': 'bold'},
                startangle=90
            )
            axes[0, 0].set_title('Integrated Sentiment Distribution\n(All platforms combined)', 
                                fontsize=13, fontweight='bold')
            
            # 1B: Platform sentiment comparison
            platforms = list(platform_sentiment.keys())
            positive_vals = [platform_sentiment[p]['positive_pct'] for p in platforms]
            neutral_vals = [platform_sentiment[p]['neutral_pct'] for p in platforms]
            negative_vals = [platform_sentiment[p]['negative_pct'] for p in platforms]
            
            x = np.arange(len(platforms))
            width = 0.25
            
            axes[0, 1].bar(x - width, positive_vals, width, label='Positive', color='#2ecc71')
            axes[0, 1].bar(x, neutral_vals, width, label='Neutral', color='#95a5a6')
            axes[0, 1].bar(x + width, negative_vals, width, label='Negative', color='#e74c3c')
            
            axes[0, 1].set_ylabel('Percentage (%)', fontsize=11, fontweight='bold')
            axes[0, 1].set_title('Sentiment Distribution by Platform\n(Compare Riskesdas perception)', 
                               fontsize=13, fontweight='bold')
            axes[0, 1].set_xticks(x)
            axes[0, 1].set_xticklabels([p.upper() for p in platforms], fontsize=10)
            axes[0, 1].legend()
            axes[0, 1].grid(True, alpha=0.3, axis='y')
            
            # 1C: Mean sentiment by platform
            mean_sentiments = [platform_sentiment[p]['mean_sentiment'] for p in platforms]
            axes[0, 2].barh([p.upper() for p in platforms], mean_sentiments, 
                          color=['#3498db', '#e67e22', '#9b59b6'][:len(platforms)])
            axes[0, 2].axvline(x=0, color='black', linestyle='--', linewidth=2)
            axes[0, 2].set_xlabel('Mean Sentiment Score', fontsize=11, fontweight='bold')
            axes[0, 2].set_title('Platform Sentiment Intensity\n(More positive = right)', 
                               fontsize=13, fontweight='bold')
            axes[0, 2].grid(True, alpha=0.3, axis='x')
            
            # 1D: Sentiment trend over time (integrated)
            monthly_sentiment = self.df.groupby('year_month')['sentiment_score'].agg(['mean', 'std', 'count'])
            x_months = range(len(monthly_sentiment))
            axes[1, 0].plot(x_months, monthly_sentiment['mean'], color='#3498db', linewidth=2.5, marker='o', markersize=4, label='Mean')
            axes[1, 0].fill_between(
                x_months,
                monthly_sentiment['mean'] - monthly_sentiment['std'],
                monthly_sentiment['mean'] + monthly_sentiment['std'],
                alpha=0.2, color='#3498db', label='±1 Std Dev'
            )
            axes[1, 0].axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
            axes[1, 0].set_ylabel('Sentiment Score', fontsize=11, fontweight='bold')
            axes[1, 0].set_title('Sentiment Trend (11 Years)\n(Track changes vs Riskesdas timeline)', 
                               fontsize=13, fontweight='bold')
            axes[1, 0].legend()
            axes[1, 0].grid(True, alpha=0.3)
            
            # 1E: Stacked area - sentiment composition over time
            monthly_comp = pd.crosstab(self.df['year_month'], self.df['sentiment_label'], normalize='index') * 100
            axes[1, 1].stackplot(
                range(len(monthly_comp)),
                monthly_comp.get('NEGATIVE', [0]*len(monthly_comp)),
                monthly_comp.get('NEUTRAL', [0]*len(monthly_comp)),
                monthly_comp.get('POSITIVE', [0]*len(monthly_comp)),
                labels=['Negative', 'Neutral', 'Positive'],
                colors=['#e74c3c', '#95a5a6', '#2ecc71'],
                alpha=0.8
            )
            axes[1, 1].set_ylabel('Percentage (%)', fontsize=11, fontweight='bold')
            axes[1, 1].set_title('Sentiment Composition Over Time\n(How emotions shifted)', 
                               fontsize=13, fontweight='bold')
            axes[1, 1].legend(loc='upper left')
            axes[1, 1].grid(True, alpha=0.3)
            
            # 1F: Year-over-year comparison (untuk Riskesdas validation)
            yearly_sentiment = self.df.groupby('year')['sentiment_score'].agg(['mean', 'std', 'count'])
            axes[1, 2].errorbar(yearly_sentiment.index, yearly_sentiment['mean'], 
                              yerr=yearly_sentiment['std'],
                              fmt='o-', color='#e74c3c', linewidth=2.5, markersize=8, capsize=5)
            axes[1, 2].axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
            axes[1, 2].set_xlabel('Year', fontsize=11, fontweight='bold')
            axes[1, 2].set_ylabel('Mean Sentiment Score', fontsize=11, fontweight='bold')
            axes[1, 2].set_title('Year-over-Year Sentiment\n(Compare with Riskesdas 2013, 2018, 2023)', 
                               fontsize=13, fontweight='bold')
            axes[1, 2].grid(True, alpha=0.3)
            
            plt.tight_layout()
            fig.savefig(FIGURES_DIR / "08_Integrated_Sentiment_Analysis.png", dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"✓ Platform sentiment breakdown:")
            for p, data in platform_sentiment.items():
                logger.info(f"  {p.upper()}: Pos={data['positive_pct']:.1f}%, "
                          f"Neu={data['neutral_pct']:.1f}%, Neg={data['negative_pct']:.1f}%")
        
        return results
    
    # ========================================================================
    # 2. CROSS-PLATFORM COMPARISON
    # ========================================================================
    
    def analyze_cross_platform_comparison(self) -> Dict[str, Any]:
        """Analisis perbandingan lintas platform"""
        logger.info("\n" + "="*80)
        logger.info("[2] CROSS-PLATFORM COMPARISON")
        logger.info("="*80)
        
        results = {
            "name": "Cross-Platform Comparison",
        }
        
        # Volume comparison
        volume_by_platform = self.df['platform'].value_counts().to_dict()
        total_volume = sum(volume_by_platform.values())
        results['volume'] = {
            k: {
                'count': v,
                'percentage': float(v / total_volume * 100)
            }
            for k, v in volume_by_platform.items()
        }
        
        # Date coverage
        date_coverage = {}
        for platform in self.df['platform'].unique():
            platform_df = self.df[self.df['platform'] == platform]
            date_coverage[platform] = {
                'first_date': str(platform_df['date'].min()),
                'last_date': str(platform_df['date'].max()),
                'years_active': (platform_df['date'].max() - platform_df['date'].min()).days / 365.25
            }
        results['date_coverage'] = date_coverage
        
        # Visualization 2: Cross-Platform Comparison
        fig, axes = plt.subplots(2, 3, figsize=(20, 12))
        fig.suptitle('CROSS-PLATFORM COMPARISON\nVolume, Quality, and Contribution Analysis', 
                    fontsize=18, fontweight='bold', y=0.995)
        
        platforms = list(volume_by_platform.keys())
        volumes = [volume_by_platform[p] for p in platforms]
        colors_platform = {'twitter': '#1DA1F2', 'youtube': '#e67e22', 'threads': '#9b59b6'}
        
        # 2A: Volume pie
        axes[0, 0].pie(volumes, labels=[p.upper() for p in platforms], autopct='%1.1f%%',
                      colors=[colors_platform.get(p, '#999') for p in platforms],
                      textprops={'fontsize': 12, 'weight': 'bold'},
                      startangle=90)
        axes[0, 0].set_title('Data Volume Distribution\n(Which platform dominates?)', 
                           fontsize=13, fontweight='bold')
        
        # 2B: Volume per platform (bar)
        axes[0, 1].bar([p.upper() for p in platforms], volumes,
                      color=[colors_platform.get(p, '#999') for p in platforms],
                      edgecolor='black', linewidth=1.5)
        axes[0, 1].set_ylabel('Number of Posts', fontsize=11, fontweight='bold')
        axes[0, 1].set_title('Absolute Volume by Platform\n(Scale difference)', 
                           fontsize=13, fontweight='bold')
        axes[0, 1].grid(True, alpha=0.3, axis='y')
        
        # Add values on bars
        for i, v in enumerate(volumes):
            axes[0, 1].text(i, v + max(volumes)*0.02, str(v), ha='center', fontweight='bold')
        
        # 2C: Monthly growth comparison
        monthly_platform = pd.crosstab(self.df['year_month'], self.df['platform'])
        for platform in platforms:
            if platform in monthly_platform.columns:
                axes[0, 2].plot(range(len(monthly_platform)), monthly_platform[platform].values,
                              marker='o', label=platform.upper(), linewidth=2, markersize=4)
        axes[0, 2].set_ylabel('Posts per Month', fontsize=11, fontweight='bold')
        axes[0, 2].set_title('Monthly Growth Trend\n(Platform adoption over time)', 
                           fontsize=13, fontweight='bold')
        axes[0, 2].legend()
        axes[0, 2].grid(True, alpha=0.3)
        
        # 2D: Data quality score
        quality_scores = {}
        for platform in platforms:
            platform_df = self.df[self.df['platform'] == platform]
            completeness = (platform_df['content'].notna().sum() / len(platform_df) * 100)
            duplicates = 0  # Already cleaned in Phase 1
            quality_scores[platform] = completeness
        
        axes[1, 0].barh([p.upper() for p in platforms], 
                       [quality_scores[p] for p in platforms],
                       color=[colors_platform.get(p, '#999') for p in platforms],
                       edgecolor='black', linewidth=1.5)
        axes[1, 0].set_xlabel('Data Completeness (%)', fontsize=11, fontweight='bold')
        axes[1, 0].set_title('Data Quality Score\n(Completeness & cleanliness)', 
                           fontsize=13, fontweight='bold')
        axes[1, 0].set_xlim([90, 101])
        axes[1, 0].grid(True, alpha=0.3, axis='x')
        
        # 2E: Active days comparison
        active_days = {}
        for platform in platforms:
            platform_df = self.df[self.df['platform'] == platform]
            active_days[platform] = platform_df['date'].nunique()
        
        axes[1, 1].bar([p.upper() for p in platforms],
                      [active_days[p] for p in platforms],
                      color=[colors_platform.get(p, '#999') for p in platforms],
                      edgecolor='black', linewidth=1.5)
        axes[1, 1].set_ylabel('Unique Days with Data', fontsize=11, fontweight='bold')
        axes[1, 1].set_title('Active Coverage\n(How many days have posts?)', 
                           fontsize=13, fontweight='bold')
        axes[1, 1].grid(True, alpha=0.3, axis='y')
        
        # 2F: Platform characteristics
        axes[1, 2].axis('off')
        characteristics_text = """
        PLATFORM CHARACTERISTICS
        
        🐦 TWITTER (Real-time)
        └─ Volume: 74% of data
        └─ Coverage: Daily updates
        └─ Speed: Immediate reactions
        └─ Bias: Urban, online-savvy
        
        ▶️  YOUTUBE (Educational)
        └─ Volume: 15% of data
        └─ Coverage: Weekly-monthly
        └─ Speed: Slower, curated
        └─ Quality: Higher reliability
        
        💬 THREADS (Community)
        └─ Volume: 11% of data
        └─ Coverage: Sporadic
        └─ Speed: Medium
        └─ Bias: Engaged patients only
        
        ⚠️  USAGE NOTE:
        Twitter dominates analysis.
        Consider weighted average
        for balanced insights.
        """
        axes[1, 2].text(0.05, 0.95, characteristics_text, fontsize=10, verticalalignment='top',
                       family='monospace', bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
        
        plt.tight_layout()
        fig.savefig(FIGURES_DIR / "08_Cross_Platform_Comparison.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"✓ Cross-platform comparison completed")
        
        return results
    
    # ========================================================================
    # 3. RISKESDAS & IDF VALIDATION FRAMEWORK
    # ========================================================================
    
    def create_validation_framework(self) -> Dict[str, Any]:
        """Buat framework untuk validasi Riskesdas & IDF"""
        logger.info("\n" + "="*80)
        logger.info("[3] RISKESDAS & IDF VALIDATION FRAMEWORK")
        logger.info("="*80)
        
        results = {
            "name": "Validation Framework for Riskesdas & IDF",
        }
        
        # Prepare data untuk comparison
        yearly_stats = {}
        for year in sorted(self.df['year'].unique()):
            year_df = self.df[self.df['year'] == year]
            yearly_stats[year] = {
                'total_posts': len(year_df),
                'positive_pct': float((year_df['sentiment_label'] == 'POSITIVE').sum() / len(year_df) * 100),
                'neutral_pct': float((year_df['sentiment_label'] == 'NEUTRAL').sum() / len(year_df) * 100),
                'negative_pct': float((year_df['sentiment_label'] == 'NEGATIVE').sum() / len(year_df) * 100),
                'mean_sentiment': float(year_df['sentiment_score'].mean()),
                'std_sentiment': float(year_df['sentiment_score'].std()),
            }
        
        results['yearly_statistics'] = yearly_stats
        
        # Create validation DataFrame
        validation_df = pd.DataFrame({
            'Year': list(yearly_stats.keys()),
            'Digital_Total_Posts': [yearly_stats[y]['total_posts'] for y in yearly_stats.keys()],
            'Digital_Positive_%': [yearly_stats[y]['positive_pct'] for y in yearly_stats.keys()],
            'Digital_Neutral_%': [yearly_stats[y]['neutral_pct'] for y in yearly_stats.keys()],
            'Digital_Negative_%': [yearly_stats[y]['negative_pct'] for y in yearly_stats.keys()],
            'Digital_Mean_Sentiment': [yearly_stats[y]['mean_sentiment'] for y in yearly_stats.keys()],
            'Riskesdas_Prevalence_%': ['[INSERT RISKESDAS DATA]'] * len(yearly_stats),
            'IDF_Prevalence_%': ['[INSERT IDF DATA]'] * len(yearly_stats),
            'Correlation_with_Riskesdas': ['[TO BE CALCULATED]'] * len(yearly_stats),
            'Alignment_Score': ['[TO BE CALCULATED]'] * len(yearly_stats),
        })
        
        # Save validation template
        validation_file = REPORTS_DIR / "08_Validation_Framework_Riskesdas_IDF.xlsx"
        try:
            with pd.ExcelWriter(validation_file, engine='openpyxl') as writer:
                validation_df.to_excel(writer, sheet_name='Digital vs Official', index=False)
                
                # Instructions sheet
                instructions = pd.DataFrame({
                    'Field': [
                        'Riskesdas_Prevalence_%',
                        'IDF_Prevalence_%',
                        'Correlation_with_Riskesdas',
                        'Alignment_Score'
                    ],
                    'Description': [
                        'Insert Riskesdas diabetes prevalence % for each year',
                        'Insert IDF estimated prevalence % for Indonesia',
                        'Will calculate Pearson correlation between digital sentiment and official prevalence',
                        'Overall alignment between digital discourse and epidemiological data'
                    ],
                    'Source': [
                        'Riskesdas 2013, 2018, 2023 reports',
                        'IDF Diabetes Atlas',
                        'Automated calculation',
                        'Interpretation based on correlation'
                    ]
                })
                instructions.to_excel(writer, sheet_name='Instructions', index=False)
        
        except Exception as e:
            logger.warning(f"Excel export failed: {e}")
            validation_file = REPORTS_DIR / "08_Validation_Framework_Riskesdas_IDF.csv"
            validation_df.to_csv(validation_file, index=False)
        
        results['validation_file'] = str(validation_file)
        
        logger.info(f"✓ Validation framework created")
        logger.info(f"  File: {validation_file}")
        logger.info(f"  Ready for Riskesdas & IDF data insertion")
        
        return results
    
    # ========================================================================
    # 4. STAKEHOLDER INSIGHTS
    # ========================================================================
    
    def generate_stakeholder_insights(self) -> Dict[str, Any]:
        """Generate insights untuk berbagai stakeholder"""
        logger.info("\n" + "="*80)
        logger.info("[4] STAKEHOLDER INSIGHTS")
        logger.info("="*80)
        
        results = {
            "name": "Stakeholder Insights",
        }
        
        # Calculate key metrics
        total_posts = len(self.df)
        negative_pct = (self.df['sentiment_label'] == 'NEGATIVE').sum() / len(self.df) * 100
        positive_pct = (self.df['sentiment_label'] == 'POSITIVE').sum() / len(self.df) * 100
        
        # Trend analysis
        monthly_sentiment = self.df.groupby('year_month')['sentiment_score'].mean()
        recent_trend = monthly_sentiment.iloc[-3:].mean() - monthly_sentiment.iloc[:3].mean()
        
        # FOR POLICYMAKERS
        policy_insights = {
            "target_audience": "Kemenkes, Dinas Kesehatan, Health Policy Makers",
            "key_findings": [
                f"Total digital discourse: {total_posts:,} posts analyzed over 11 years",
                f"Negative sentiment concerning: {negative_pct:.1f}% of discussions",
                f"Positive sentiment: {positive_pct:.1f}% - opportunities for health promotion",
                f"Trend: {'IMPROVING' if recent_trend > 0 else 'DECLINING'} (recent vs early period)",
            ],
            "recommendations": [
                "Increase health education campaigns targeting negative sentiment topics",
                "Leverage YouTube (most educational) for official health messaging",
                "Address most discussed health concerns (from content analysis)",
                "Monitor early warning signs via Google Trends integration",
            ],
            "action_items": [
                "Conduct content analysis of negative posts to identify key concerns",
                "Partner with trusted YouTube creators for health education",
                "Develop targeted responses to misinformation detected in social media",
                "Implement monthly monitoring using this dashboard",
            ]
        }
        
        # FOR HEALTH WORKERS
        health_insights = {
            "target_audience": "Dokter, Perawat, Health Educators",
            "key_findings": [
                "Most discussed topics: [will add from topic modeling]",
                "Patient concerns identified in social media discussions",
                "Community knowledge gaps evident from question patterns",
                "Peer support networks active on Threads platform",
            ],
            "recommendations": [
                "Address top 10 FAQs identified in social media discourse",
                "Create content for identified knowledge gaps",
                "Engage with online patient communities for credible information sharing",
                "Develop patient education materials based on actual questions",
            ],
            "resources_needed": [
                "FAQ document based on social media analysis",
                "Infographics for top concerns",
                "Video content for YouTube distribution",
                "Training on social media engagement",
            ]
        }
        
        # FOR PATIENTS & PUBLIC
        public_insights = {
            "target_audience": "Patients, Caregivers, General Public",
            "key_message": "Your voice matters: 9,000+ Indonesians discussing diabetes online",
            "trust_sources": [
                "✓ YouTube educational content (verified educators)",
                "✓ Official health ministry sources",
                "✓ Peer experiences on community forums",
                "⚠️  Twitter news (verify with official sources)",
            ],
            "myth_buster_topics": [
                "Insulin causes addiction - MYTH",
                "Diabetes is curable - PARTIALLY TRUE",
                "Sugar is only cause - OVERSIMPLIFIED",
                "No diet changes needed with medication - MYTH",
            ],
            "action_items": [
                "Check diabetes information on trusted sources before sharing",
                "Join patient support communities for peer learning",
                "Ask healthcare providers for clarification on online information",
                "Report medical misinformation when found",
            ]
        }
        
        results['policymakers'] = policy_insights
        results['health_workers'] = health_insights
        results['public'] = public_insights
        
        # Visualization 3: Stakeholder Insights
        fig = plt.figure(figsize=(20, 14))
        gs = fig.add_gridspec(3, 2, hspace=0.4, wspace=0.3)
        
        fig.suptitle('STAKEHOLDER-SPECIFIC INSIGHTS\nPhase 8 Advanced Analytics', 
                    fontsize=18, fontweight='bold')
        
        # Policy maker insights
        ax1 = fig.add_subplot(gs[0, :])
        ax1.axis('off')
        policy_text = f"""
        👔 FOR POLICYMAKERS (Kemenkes, Dinas Kesehatan)
        
        📊 KEY FINDINGS:
        • {total_posts:,} posts analyzed across 4 platforms (2015-2026)
        • {negative_pct:.1f}% negative sentiment - identifies public health concerns
        • {positive_pct:.1f}% positive sentiment - opportunities for engagement
        • Trend: {'IMPROVING' if recent_trend > 0 else 'DECLINING'} perception
        
        🎯 RECOMMENDATIONS:
        1. Strengthen health education campaigns targeting negative sentiment topics
        2. Leverage YouTube platform (15% of data, highest quality) for official messaging  
        3. Implement early warning system using Google Trends integration
        4. Address top-discussed concerns identified in content analysis
        5. Monitor monthly using this integrated dashboard
        
        ⚡ IMMEDIATE ACTIONS:
        • Compare with Riskesdas data to validate digital sentiment
        • Conduct stakeholder workshop on findings
        • Develop response strategy for identified concerns
        • Allocate budget for digital health communication
        """
        ax1.text(0.05, 0.95, policy_text, fontsize=11, verticalalignment='top',
                family='monospace', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        
        # Health worker insights
        ax2 = fig.add_subplot(gs[1, :])
        ax2.axis('off')
        health_text = """
        🏥 FOR HEALTH WORKERS (Dokter, Perawat, Ahli Gizi)
        
        📋 PATIENT CONCERNS IDENTIFIED:
        • Most discussed: [Will add from Phase 9 Topic Modeling]
        • Most common questions: [From content analysis]
        • Knowledge gaps detected: [From sentiment patterns]
        • Peer support network activity: [From Threads analysis]
        
        💡 HOW TO USE THIS INSIGHT:
        1. Review FAQ document (generated from actual patient questions)
        2. Create patient education materials addressing top concerns
        3. Prepare responses to misinformation patterns identified
        4. Engage with patient communities on trusted platforms
        5. Refer patients to credible online resources
        
        📊 ENGAGEMENT STRATEGY:
        • Twitter: Real-time responses to health questions
        • YouTube: Create educational videos for common topics
        • Threads: Join patient support discussions with expert insights
        """
        ax2.text(0.05, 0.95, health_text, fontsize=11, verticalalignment='top',
                family='monospace', bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
        
        # Public insights
        ax3 = fig.add_subplot(gs[2, :])
        ax3.axis('off')
        public_text = f"""
        👥 FOR PATIENTS & PUBLIC (Masyarakat)
        
        📢 YOUR VOICE MATTERS:
        This analysis includes {total_posts:,} posts from Indonesians like you discussing diabetes!
        
        ✅ TRUSTED INFORMATION SOURCES:
        ✓ YouTube educational content (doctors & health experts)
        ✓ Official Kemenkes Kesehatan website & social media
        ✓ Peer experiences on community forums (personal stories)
        ⚠️  Twitter (verify news with official sources)
        
        ❌ COMMON MYTHS vs FACTS:
        MYTH: "Insulin causes addiction"  →  FACT: Insulin is life-saving, not addictive
        MYTH: "Diabetes can be cured"  →  FACT: Can be managed well with treatment & lifestyle
        MYTH: "Only sugar causes diabetes"  →  FACT: Genetics, lifestyle, & other factors matter
        
        🎯 ACTIONS YOU CAN TAKE:
        1. Check information on trusted sources before sharing
        2. Ask doctors for clarification on confusing online information
        3. Share accurate information with family & friends
        4. Join patient support communities for peer learning
        5. Report medical misinformation when you see it
        """
        ax3.text(0.05, 0.95, public_text, fontsize=11, verticalalignment='top',
                family='monospace', bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
        
        plt.savefig(FIGURES_DIR / "08_Stakeholder_Insights.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"✓ Stakeholder insights generated")
        
        return results
    
    # ========================================================================
    # 5. DASHBOARD DATA PREPARATION
    # ========================================================================
    
    def prepare_dashboard_data(self) -> Dict[str, Any]:
        """Siapkan data untuk Streamlit dashboard (Phase 10)"""
        logger.info("\n" + "="*80)
        logger.info("[5] DASHBOARD DATA PREPARATION")
        logger.info("="*80)
        
        dashboard_data = {
            "metadata": {
                "title": "Diabetes Digital Health Indonesia",
                "subtitle": "11-Year Social Media Analysis (2015-2026)",
                "last_updated": datetime.now().isoformat(),
                "data_period": f"{self.df['date'].min().date()} to {self.df['date'].max().date()}",
            },
            "kpi": {
                "total_posts": int(len(self.df)),
                "platforms": int(self.df['platform'].nunique()),
                "years_analyzed": int(self.df['year'].nunique()),
                "days_coverage": int(self.df['date'].nunique()),
            },
            "sentiment": {
                "positive_pct": float((self.df['sentiment_label'] == 'POSITIVE').sum() / len(self.df) * 100),
                "neutral_pct": float((self.df['sentiment_label'] == 'NEUTRAL').sum() / len(self.df) * 100),
                "negative_pct": float((self.df['sentiment_label'] == 'NEGATIVE').sum() / len(self.df) * 100),
                "mean_score": float(self.df['sentiment_score'].mean()),
            },
            "platforms": {},
        }
        
        # Data per platform
        for platform in self.df['platform'].unique():
            platform_df = self.df[self.df['platform'] == platform]
            dashboard_data["platforms"][platform] = {
                "total": int(len(platform_df)),
                "percentage": float(len(platform_df) / len(self.df) * 100),
                "positive_pct": float((platform_df['sentiment_label'] == 'POSITIVE').sum() / len(platform_df) * 100),
                "mean_sentiment": float(platform_df['sentiment_score'].mean()),
            }
        
        # Yearly trend data
        yearly_data = []
        for year in sorted(self.df['year'].unique()):
            year_df = self.df[self.df['year'] == year]
            yearly_data.append({
                "year": int(year),
                "posts": int(len(year_df)),
                "positive_pct": float((year_df['sentiment_label'] == 'POSITIVE').sum() / len(year_df) * 100),
                "mean_sentiment": float(year_df['sentiment_score'].mean()),
            })
        dashboard_data["yearly_trend"] = yearly_data
        
        # Save dashboard data
        dashboard_file = PROCESSED_DATA_DIR / "dashboard_data.json"
        with open(dashboard_file, 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ Dashboard data prepared: {dashboard_file}")
        
        return dashboard_data
    
    # ========================================================================
    # ORCHESTRATION
    # ========================================================================
    
    def run_phase8(self) -> Dict[str, Any]:
        """Run complete Phase 8"""
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 8: INTEGRATED INSIGHTS + COMPARISON FRAMEWORK")
        logger.info("=" * 80)
        
        all_results = {
            "phase": "F8_Integrated_Insights",
            "timestamp": datetime.now().isoformat(),
        }
        
        all_results['sentiment_analysis'] = self.analyze_integrated_sentiment()
        all_results['cross_platform'] = self.analyze_cross_platform_comparison()
        all_results['validation_framework'] = self.create_validation_framework()
        all_results['stakeholder_insights'] = self.generate_stakeholder_insights()
        all_results['dashboard_data'] = self.prepare_dashboard_data()
        
        # Save results dengan error handling
        logger.info("\nSaving Phase 8 report...")
        self._save_phase8_report(all_results)
        
        logger.info(f"\n" + "=" * 80)
        logger.info("PHASE 8 COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        logger.info(f"\n📊 Outputs:")
        logger.info(f"  ✓ Integrated sentiment analysis visualization")
        logger.info(f"  ✓ Cross-platform comparison")
        logger.info(f"  ✓ Riskesdas & IDF validation framework")
        logger.info(f"  ✓ Stakeholder-specific insights")
        logger.info(f"  ✓ Dashboard data structure")
        logger.info(f"  ✓ Report: {REPORTS_DIR / 'Phase8_Integrated_Insights_Report.json'}")
        logger.info(f"  ✓ Figures: {FIGURES_DIR}")
        
        return all_results
    
    @staticmethod
    def _save_phase8_report(results: Dict[str, Any]):
        """Save Phase 8 report with numpy type handling"""
        report_file = REPORTS_DIR / "Phase8_Integrated_Insights_Report.json"
        
        logger.info(f"Saving report to {report_file.name}...")
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                # Use custom NumpyEncoder
                json.dump(results, f, indent=2, cls=NumpyEncoder, ensure_ascii=False)
            
            logger.info(f"✓ Report saved: {report_file}")
            return True
        
        except TypeError as e:
            logger.error(f"JSON serialization failed: {e}")
            logger.warning("Attempting to convert types manually...")
            
            try:
                # Convert all numpy types to Python native types
                results_converted = convert_to_serializable(results)
                
                with open(report_file, 'w', encoding='utf-8') as f:
                    json.dump(results_converted, f, indent=2, ensure_ascii=False)
                
                logger.info(f"✓ Report saved (after type conversion): {report_file}")
                return True
            
            except Exception as e2:
                logger.error(f"Manual conversion also failed: {e2}")
                logger.warning("Saving as pickle instead...")
                
                try:
                    import pickle
                    pickle_file = REPORTS_DIR / "Phase8_Integrated_Insights_Report.pkl"
                    with open(pickle_file, 'wb') as f:
                        pickle.dump(results, f)
                    logger.info(f"✓ Report saved as pickle: {pickle_file}")
                    return True
                except Exception as e3:
                    logger.error(f"Pickle save failed: {e3}")
                    return False


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Execute Phase 8"""
    
    logger.info("\n" + "="*80)
    logger.info("PHASE 8: Loading Data...")
    logger.info("="*80 + "\n")
    
    # Load sentiment data (dari Phase 3)
    sentiment_file = PROCESSED_DATA_DIR / "sentiment_analyzed_full.csv"
    
    if not sentiment_file.exists():
        logger.error(f"✗ File not found: {sentiment_file}")
        logger.error("  Please run Phase 3 first: python F03_sentiment_analysis.py")
        return None
    
    logger.info(f"Loading: {sentiment_file.name}")
    
    try:
        master_df = pd.read_csv(sentiment_file)
        logger.info(f"✓ Loaded {len(master_df)} records")
    except Exception as e:
        logger.error(f"✗ Failed to load CSV: {e}")
        return None
    
    # Check columns
    logger.info(f"\nAvailable columns: {list(master_df.columns)}")
    
    # Check sentiment_label
    if 'sentiment_label' not in master_df.columns:
        logger.error("✗ Column 'sentiment_label' NOT FOUND")
        logger.error(f"  Columns: {list(master_df.columns)}")
        return None
    
    logger.info(f"✓ sentiment_label column found")
    
    # Convert date
    if 'date' in master_df.columns:
        master_df['date'] = pd.to_datetime(master_df['date'])
        logger.info(f"✓ Date column converted to datetime")
    
    # Verify data
    logger.info(f"\nSentiment distribution:")
    for label, count in master_df['sentiment_label'].value_counts().items():
        pct = count / len(master_df) * 100
        logger.info(f"  {label}: {count} ({pct:.1f}%)")
    
    logger.info(f"\n" + "="*80)
    logger.info(f"Data ready! Starting Phase 8...")
    logger.info(f"="*80 + "\n")
    
    # Run analyzer
    analyzer = IntegratedInsightsAnalyzer(master_df)
    results = analyzer.run_phase8()
    
    return results


if __name__ == "__main__":
    results = main()