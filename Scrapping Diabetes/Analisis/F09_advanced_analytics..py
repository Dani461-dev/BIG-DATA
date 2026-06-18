# ============================================================================
# PHASE 9: ADVANCED ANALYTICS
# Emotion Analysis · Topic Modeling · Early Warning · DDAI Index
# ============================================================================
"""
Phase 9 handles:
1. Topic Modeling (LDA - apa yang dibicarakan?)
2. Emotion Analysis (fear, hope, trust, anger - bukan hanya pos/neg)
3. Early Warning System (Google Trends vs Twitter lag)
4. Diabetes Digital Attention Index (DDAI) - custom index
5. Misinformation Detection
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import json
import warnings
from typing import Dict, List, Tuple, Any
import re

# NLP & Topic Modeling
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import gensim
from gensim import corpora
from gensim.models import LdaModel, CoherenceModel
from nltk.corpus import stopwords
import nltk

# Emotion detection
from textblob import TextBlob

# Visualization
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud

# Import configuration
from config import (
    PROCESSED_DATA_DIR, REPORTS_DIR, FIGURES_DIR,
    STAT_CONFIG, REPRODUCIBILITY_CONFIG
)

warnings.filterwarnings('ignore')

# Download NLTK data
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

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
# 1. TOPIC MODELING
# ============================================================================

class TopicModeler:
    """Topic modeling using LDA"""
    
    def __init__(self, n_topics: int = 10):
        self.n_topics = n_topics
        self.vectorizer = None
        self.lda_model = None
        self.feature_names = None
        self.results = {}
    
    def prepare_documents(self, df: pd.DataFrame, text_column: str = 'content') -> List[List[str]]:
        """Prepare documents for LDA"""
        logger.info("Preparing documents for topic modeling...")
        
        stop_words = set(stopwords.words('english') + stopwords.words('indonesian'))
        
        documents = []
        for text in df[text_column].fillna(''):
            if not isinstance(text, str) or len(text.strip()) < 10:
                continue
            
            # Clean
            text = text.lower()
            text = re.sub(r'[^a-z\s]', '', text)
            
            # Tokenize
            words = text.split()
            
            # Remove stopwords & short words
            words = [w for w in words if w not in stop_words and len(w) > 2]
            
            if words:
                documents.append(words)
        
        logger.info(f"Prepared {len(documents)} documents for LDA")
        return documents
    
    def fit_lda(self, documents: List[List[str]]) -> Dict[str, Any]:
        """Fit LDA model"""
        logger.info(f"Fitting LDA model with {self.n_topics} topics...")
        
        try:
            # Create dictionary
            dictionary = corpora.Dictionary(documents)
            
            # Filter extremes
            dictionary.filter_extremes(no_below=2, no_above=0.7)
            
            # Create corpus
            corpus = [dictionary.doc2bow(doc) for doc in documents]
            
            # Fit LDA
            self.lda_model = LdaModel(
                corpus=corpus,
                id2word=dictionary,
                num_topics=self.n_topics,
                random_state=REPRODUCIBILITY_CONFIG.get("random_seed", 42),
                passes=10,
                alpha='auto',
                per_word_topics=True
            )
            
            # Calculate coherence score
            coherence_model = CoherenceModel(
                model=self.lda_model,
                texts=documents,
                dictionary=dictionary,
                coherence='c_v'
            )
            coherence_score = coherence_model.get_coherence()
            
            logger.info(f"✓ LDA fitted successfully")
            logger.info(f"  Coherence Score: {coherence_score:.3f}")
            
            # Extract topics
            topics = {}
            for idx in range(self.n_topics):
                terms = self.lda_model.show_topic(idx, topn=10)
                topics[f"topic_{idx}"] = {
                    'terms': [term for term, prob in terms],
                    'weights': [float(prob) for term, prob in terms]
                }
            
            self.results = {
                'n_topics': self.n_topics,
                'coherence_score': float(coherence_score),
                'topics': topics,
                'n_documents': len(documents)
            }
            
            return self.results
        
        except Exception as e:
            logger.error(f"LDA fitting failed: {e}")
            return {}
    
    def display_topics(self) -> None:
        """Display top words per topic"""
        if not self.lda_model:
            return
        
        logger.info("\nTopic Distribution:")
        for idx, topic in self.results['topics'].items():
            top_words = topic['terms'][:5]
            logger.info(f"  {idx}: {', '.join(top_words)}")


# ============================================================================
# 2. EMOTION ANALYSIS
# ============================================================================

class EmotionAnalyzer:
    """Detect emotions beyond positive/negative"""
    
    @staticmethod
    def detect_emotions(text: str) -> Dict[str, float]:
        """
        Detect emotions in text
        Returns: fear, trust, joy, sadness, disgust, anger, surprise, anticipation
        """
        if not isinstance(text, str) or len(text.strip()) < 5:
            return {}
        
        text_lower = text.lower()
        
        # Emotion keywords (simplified NRC lexicon)
        emotions = {
            'fear': ['takut', 'khawatir', 'cemas', 'panik', 'fear', 'worry', 'anxiety'],
            'trust': ['percaya', 'yakin', 'aman', 'handal', 'trust', 'believe', 'safe'],
            'joy': ['senang', 'bahagia', 'gembira', 'happy', 'joy', 'excited', 'glad'],
            'sadness': ['sedih', 'prihatin', 'murung', 'sad', 'sorrowful', 'depressed'],
            'disgust': ['jijik', 'muak', 'kesal', 'disgust', 'sick', 'gross'],
            'anger': ['marah', 'kesal', 'geram', 'angry', 'furious', 'irritated'],
            'surprise': ['terkejut', 'heran', 'surprised', 'shocked', 'amazed'],
            'anticipation': ['antisipasi', 'berharap', 'expect', 'anticipate', 'await'],
        }
        
        emotion_scores = {}
        total_keywords = 0
        
        for emotion, keywords in emotions.items():
            count = sum(1 for keyword in keywords if keyword in text_lower)
            emotion_scores[emotion] = float(count)
            total_keywords += count
        
        # Normalize
        if total_keywords > 0:
            emotion_scores = {k: v / total_keywords for k, v in emotion_scores.items()}
        
        return emotion_scores
    
    @staticmethod
    def analyze_corpus_emotions(df: pd.DataFrame, text_column: str = 'content') -> pd.DataFrame:
        """Analyze emotions for entire corpus"""
        logger.info("Analyzing emotions in corpus...")
        
        emotion_list = []
        
        for idx, row in df.iterrows():
            if idx % 1000 == 0 and idx > 0:
                logger.info(f"  Progress: {idx}/{len(df)}")
            
            text = row.get(text_column, '')
            emotions = EmotionAnalyzer.detect_emotions(str(text))
            emotion_list.append(emotions)
        
        emotions_df = pd.DataFrame(emotion_list).fillna(0)
        
        logger.info(f"✓ Emotion analysis completed")
        
        return emotions_df


# ============================================================================
# 3. EARLY WARNING SYSTEM
# ============================================================================

class EarlyWarningSystem:
    """Detect leading indicators from Google Trends vs Social Media"""
    
    @staticmethod
    def detect_spikes(series: pd.Series, threshold: float = 1.5) -> List[Tuple[int, float]]:
        """Detect significant spikes in time series"""
        mean = series.mean()
        std = series.std()
        
        spikes = []
        for idx, value in enumerate(series):
            if value > mean + threshold * std:
                spikes.append((idx, float(value)))
        
        return spikes
    
    @staticmethod
    def calculate_lag_correlation(google_trends: pd.Series, twitter_sentiment: pd.Series, 
                                 max_lag: int = 3) -> Dict[int, float]:
        """
        Calculate cross-correlation at different lags
        Positive lag = Google Trends leads Twitter
        """
        correlations = {}
        
        for lag in range(-max_lag, max_lag + 1):
            if lag < 0:
                # Google Trends leads
                corr = google_trends.iloc[-lag:].corr(twitter_sentiment.iloc[:lag])
            elif lag > 0:
                # Twitter leads
                corr = google_trends.iloc[:-lag].corr(twitter_sentiment.iloc[lag:])
            else:
                # No lag
                corr = google_trends.corr(twitter_sentiment)
            
            correlations[lag] = float(corr) if not np.isnan(corr) else 0.0
        
        return correlations


# ============================================================================
# 4. DIABETES DIGITAL ATTENTION INDEX (DDAI)
# ============================================================================

class DiabetesDigitalAttentionIndex:
    """
    Custom index combining:
    - Search interest (Google Trends)
    - Discussion volume (social media posts)
    - Sentiment intensity (emotional content)
    - Growth rate (trending up/down)
    
    Score: 0-100
    """
    
    @staticmethod
    def calculate_ddai(
        df: pd.DataFrame,
        google_trends_data: pd.DataFrame = None,
        normalize: bool = True
    ) -> pd.DataFrame:
        """
        Calculate DDAI for each month
        
        DDAI = 0.4 * Volume_Score + 0.3 * Sentiment_Score + 0.2 * Growth_Score + 0.1 * Engagement_Score
        """
        logger.info("Calculating Diabetes Digital Attention Index (DDAI)...")
        
        # Prepare data
        df_copy = df.copy()
        df_copy['year_month'] = df_copy['date'].dt.to_period('M')
        
        # 1. Volume Score (40%)
        monthly_volume = df_copy.groupby('year_month').size()
        if normalize:
            volume_score = (monthly_volume - monthly_volume.min()) / (monthly_volume.max() - monthly_volume.min()) * 100
        else:
            volume_score = monthly_volume
        
        # 2. Sentiment Score (30%) - convert from -1..1 to 0..100
        monthly_sentiment = df_copy.groupby('year_month')['sentiment_score'].mean()
        sentiment_score = (monthly_sentiment + 1) / 2 * 100  # Convert to 0-100
        
        # 3. Growth Score (20%) - month-over-month growth
        growth_rate = monthly_volume.pct_change() * 100
        growth_score = growth_rate.fillna(0)
        growth_score = np.clip(growth_score, -50, 50)  # Cap at ±50%
        growth_score = (growth_score + 50) / 100 * 100  # Normalize to 0-100
        
        # 4. Engagement Score (10%) - sentiment volatility (higher = more discussion)
        monthly_sentiment_std = df_copy.groupby('year_month')['sentiment_score'].std()
        engagement_score = (monthly_sentiment_std / monthly_sentiment_std.max()) * 100
        engagement_score = engagement_score.fillna(0)
        
        # Calculate DDAI
        ddai_df = pd.DataFrame({
            'year_month': volume_score.index,
            'volume_score': volume_score.values * 0.4,
            'sentiment_score': sentiment_score.values * 0.3,
            'growth_score': growth_score.values * 0.2,
            'engagement_score': engagement_score.values * 0.1,
        })
        
        ddai_df['ddai'] = (
            ddai_df['volume_score'] +
            ddai_df['sentiment_score'] +
            ddai_df['growth_score'] +
            ddai_df['engagement_score']
        )
        
        ddai_df['ddai'] = np.clip(ddai_df['ddai'], 0, 100)
        
        logger.info(f"✓ DDAI calculated")
        logger.info(f"  Mean DDAI: {ddai_df['ddai'].mean():.1f}")
        logger.info(f"  Max DDAI: {ddai_df['ddai'].max():.1f}")
        
        return ddai_df


# ============================================================================
# 5. MISINFORMATION DETECTION
# ============================================================================

class MisinformationDetector:
    """Detect potential misinformation patterns"""
    
    @staticmethod
    def detect_myths(text: str) -> List[str]:
        """Detect common diabetes myths"""
        text_lower = text.lower()
        
        myths = {
            'insulin_addiction': ['insulin', 'addiction', 'addict'],
            'sugar_only_cause': ['gula', 'sugar', 'only cause'],
            'cure_claim': ['sembuh', 'cure', 'cured', 'terbukti'],
            'no_diet': ['tidak perlu', 'no need', 'diet', 'tidak diet'],
            'natural_only': ['obat alami', 'natural', 'organic only'],
        }
        
        detected = []
        for myth_type, keywords in myths.items():
            if any(kw in text_lower for kw in keywords):
                detected.append(myth_type)
        
        return detected
    
    @staticmethod
    def detect_misinformation_rate(df: pd.DataFrame, text_column: str = 'content') -> float:
        """
        Calculate percentage of posts with misinformation indicators
        """
        total = len(df)
        misinformation_count = 0
        
        for text in df[text_column].fillna(''):
            myths = MisinformationDetector.detect_myths(str(text))
            if myths:
                misinformation_count += 1
        
        rate = (misinformation_count / total * 100) if total > 0 else 0
        return float(rate)


# ============================================================================
# PHASE 9 EXECUTOR
# ============================================================================

class Phase9AdvancedAnalytics:
    """Advanced analytics with AI-powered insights"""
    
    def __init__(self):
        self.results = {}
    
    def run_phase9(self, sentiment_df: pd.DataFrame) -> Dict[str, Any]:
        """Execute complete Phase 9"""
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 9: ADVANCED ANALYTICS")
        logger.info("=" * 80 + "\n")
        
        results = {
            "phase": "F9_Advanced_Analytics",
            "timestamp": datetime.now().isoformat(),
        }
        
        # Step 1: Topic Modeling
        logger.info("[Step 1] Topic Modeling (LDA)...")
        topic_modeler = TopicModeler(n_topics=10)
        documents = topic_modeler.prepare_documents(sentiment_df)
        results['topic_modeling'] = topic_modeler.fit_lda(documents)
        topic_modeler.display_topics()
        
        # Step 2: Emotion Analysis
        logger.info("\n[Step 2] Emotion Analysis...")
        emotion_analyzer = EmotionAnalyzer()
        emotions_df = emotion_analyzer.analyze_corpus_emotions(sentiment_df)
        results['emotion_summary'] = {
            'mean_emotions': emotions_df.mean().to_dict(),
            'dominant_emotions': emotions_df.mean().nlargest(3).index.tolist(),
        }
        
        logger.info(f"Dominant emotions:")
        for emotion in results['emotion_summary']['dominant_emotions']:
            score = results['emotion_summary']['mean_emotions'][emotion]
            logger.info(f"  {emotion}: {score:.3f}")
        
        # Step 3: Early Warning System
        logger.info("\n[Step 3] Early Warning System...")
        sentiment_df_copy = sentiment_df.copy()
        sentiment_df_copy['year_month'] = sentiment_df_copy['date'].dt.to_period('M')
        monthly_sentiment = sentiment_df_copy.groupby('year_month')['sentiment_score'].mean()
        
        early_warning = EarlyWarningSystem()
        spikes = early_warning.detect_spikes(monthly_sentiment)
        
        results['early_warning'] = {
            'spike_detected': len(spikes) > 0,
            'n_spikes': len(spikes),
            'spike_months': [str(monthly_sentiment.index[spike[0]]) for spike in spikes],
        }
        
        logger.info(f"Spikes detected: {len(spikes)}")
        for month, value in spikes:
            logger.info(f"  {monthly_sentiment.index[month]}: {value:.3f}")
        
        # Step 4: DDAI Index
        logger.info("\n[Step 4] Diabetes Digital Attention Index (DDAI)...")
        ddai_calculator = DiabetesDigitalAttentionIndex()
        ddai_df = ddai_calculator.calculate_ddai(sentiment_df)
        results['ddai'] = ddai_df.to_dict(orient='records')
        
        # Save DDAI
        ddai_file = PROCESSED_DATA_DIR / "ddai_index.csv"
        ddai_df.to_csv(ddai_file, index=False)
        logger.info(f"  Saved to: {ddai_file}")
        
        # Step 5: Misinformation Detection
        logger.info("\n[Step 5] Misinformation Detection...")
        detector = MisinformationDetector()
        misinformation_rate = detector.detect_misinformation_rate(sentiment_df)
        results['misinformation'] = {
            'rate_percent': float(misinformation_rate),
            'status': 'concerning' if misinformation_rate > 10 else 'acceptable',
        }
        
        logger.info(f"Misinformation rate: {misinformation_rate:.1f}%")
        logger.info(f"Status: {results['misinformation']['status']}")
        
        # Visualization
        logger.info("\n[Step 6] Generating visualizations...")
        self._visualize_advanced_analytics(sentiment_df, emotions_df, ddai_df, topic_modeler)
        
        # Save report
        logger.info("\n[Step 7] Saving report...")
        self._save_phase9_report(results)
        
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 9 COMPLETED")
        logger.info("=" * 80 + "\n")
        
        return results
    
    @staticmethod
    def _visualize_advanced_analytics(
        sentiment_df: pd.DataFrame,
        emotions_df: pd.DataFrame,
        ddai_df: pd.DataFrame,
        topic_modeler: TopicModeler
    ):
        """Create comprehensive visualizations"""
        try:
            fig = plt.figure(figsize=(20, 14))
            gs = fig.add_gridspec(3, 2, hspace=0.35, wspace=0.3)
            
            fig.suptitle('PHASE 9: ADVANCED ANALYTICS\nEmotion, Topic, DDAI & Early Warning', 
                        fontsize=18, fontweight='bold')
            
            # 1. Emotion Distribution
            ax1 = fig.add_subplot(gs[0, 0])
            emotion_means = emotions_df.mean()
            emotion_means.plot(kind='barh', ax=ax1, color='#3498db')
            ax1.set_xlabel('Average Emotion Score', fontsize=11)
            ax1.set_title('Emotion Distribution in Diabetes Discourse', fontsize=13, fontweight='bold')
            ax1.grid(True, alpha=0.3, axis='x')
            
            # 2. DDAI Index
            ax2 = fig.add_subplot(gs[0, 1])
            ddai_df['year_month_str'] = ddai_df['year_month'].astype(str)
            ax2.plot(range(len(ddai_df)), ddai_df['ddai'].values, 
                    color='#e74c3c', linewidth=2.5, marker='o', markersize=5)
            ax2.fill_between(range(len(ddai_df)), ddai_df['ddai'].values, alpha=0.3, color='#e74c3c')
            ax2.set_ylabel('DDAI Score (0-100)', fontsize=11)
            ax2.set_title('Diabetes Digital Attention Index (DDAI)', fontsize=13, fontweight='bold')
            ax2.set_ylim([0, 100])
            ax2.grid(True, alpha=0.3)
            
            # Add labels for peaks
            max_idx = ddai_df['ddai'].idxmax()
            ax2.annotate(f"Peak: {ddai_df.loc[max_idx, 'ddai']:.1f}", 
                        xy=(max_idx, ddai_df.loc[max_idx, 'ddai']),
                        xytext=(10, 10), textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
                        fontsize=10, fontweight='bold')
            
            # 3. Emotion Trend
            ax3 = fig.add_subplot(gs[1, 0])
            sentiment_df_copy = sentiment_df.copy()
            sentiment_df_copy['year_month'] = sentiment_df_copy['date'].dt.to_period('M')
            top_emotions = emotions_df.mean().nlargest(3).index
            
            for emotion in top_emotions:
                monthly_emotion = sentiment_df_copy.groupby('year_month').apply(
                    lambda x: emotions_df.loc[x.index, emotion].mean()
                )
                ax3.plot(range(len(monthly_emotion)), monthly_emotion.values, 
                        marker='o', label=emotion, linewidth=2)
            
            ax3.set_ylabel('Emotion Score', fontsize=11)
            ax3.set_title('Top 3 Emotions Over Time', fontsize=13, fontweight='bold')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            
            # 4. DDAI Components
            ax4 = fig.add_subplot(gs[1, 1])
            components = ['volume_score', 'sentiment_score', 'growth_score', 'engagement_score']
            component_means = [ddai_df[col].mean() for col in components]
            colors_components = ['#2ecc71', '#3498db', '#e74c3c', '#f39c12']
            
            ax4.bar(range(len(components)), component_means, 
                   color=colors_components, edgecolor='black', linewidth=1.5)
            ax4.set_xticks(range(len(components)))
            ax4.set_xticklabels(['Volume\n(40%)', 'Sentiment\n(30%)', 'Growth\n(20%)', 'Engagement\n(10%)'])
            ax4.set_ylabel('Average Score', fontsize=11)
            ax4.set_title('DDAI Component Contribution', fontsize=13, fontweight='bold')
            ax4.grid(True, alpha=0.3, axis='y')
            
            # 5. Top Topics (text)
            ax5 = fig.add_subplot(gs[2, 0])
            ax5.axis('off')
            
            topics_text = "TOP DIABETES TOPICS (LDA)\n" + "="*40 + "\n\n"
            for i in range(min(5, len(topic_modeler.results['topics']))):
                topic_data = topic_modeler.results['topics'][f'topic_{i}']
                terms = ', '.join(topic_data['terms'][:5])
                topics_text += f"Topic {i+1}: {terms}\n\n"
            
            ax5.text(0.05, 0.95, topics_text, fontsize=11, verticalalignment='top',
                    family='monospace', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
            
            # 6. Key Insights (text)
            ax6 = fig.add_subplot(gs[2, 1])
            ax6.axis('off')
            
            insights_text = "KEY INSIGHTS\n" + "="*40 + "\n\n"
            insights_text += f"• Coherence Score: {topic_modeler.results['coherence_score']:.3f}\n"
            insights_text += f"  (Higher = better topics)\n\n"
            
            insights_text += f"• Average DDAI: {ddai_df['ddai'].mean():.1f}/100\n"
            insights_text += f"  (Current attention level)\n\n"
            
            max_emotion = emotions_df.mean().idxmax()
            insights_text += f"• Dominant Emotion: {max_emotion}\n"
            insights_text += f"  (Most felt in discourse)\n\n"
            
            insights_text += "• Action: Use DDAI for early warning\n"
            insights_text += "  system of emerging issues"
            
            ax6.text(0.05, 0.95, insights_text, fontsize=11, verticalalignment='top',
                    family='monospace', bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.7))
            
            plt.savefig(FIGURES_DIR / "09_Advanced_Analytics.png", dpi=300, bbox_inches='tight')
            logger.info("✓ Visualization saved")
            plt.close()
        
        except Exception as e:
            logger.error(f"Visualization error: {e}")
    
    @staticmethod
    def _save_phase9_report(results: Dict[str, Any]):
        """Save Phase 9 report"""
        report_file = REPORTS_DIR / "Phase9_Advanced_Analytics_Report.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str, ensure_ascii=False)
        
        logger.info(f"✓ Report saved: {report_file}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Execute Phase 9"""
    
    # Try to load sentiment data
    data_sources = [
        (PROCESSED_DATA_DIR / "sentiment_analyzed_full.parquet", "parquet"),
        (PROCESSED_DATA_DIR / "sentiment_analyzed_full.csv", "csv"),
    ]
    
    sentiment_df = None
    
    for file_path, file_type in data_sources:
        if file_path.exists():
            try:
                logger.info(f"Loading sentiment data from {file_path}...")
                if file_type == "parquet":
                    sentiment_df = pd.read_parquet(file_path)
                else:
                    sentiment_df = pd.read_csv(file_path)
                logger.info(f"✓ Loaded {len(sentiment_df)} records\n")
                break
            except Exception as e:
                logger.warning(f"Failed to load {file_path}: {e}")
                continue
    
    if sentiment_df is None:
        logger.error("Could not load sentiment data. Run Phase 3 first.")
        return None
    
    # Ensure date column is datetime
    if 'date' in sentiment_df.columns:
        sentiment_df['date'] = pd.to_datetime(sentiment_df['date'])
    
    # Run Phase 9
    phase9 = Phase9AdvancedAnalytics()
    results = phase9.run_phase9(sentiment_df)
    
    return results


if __name__ == "__main__":
    np.random.seed(REPRODUCIBILITY_CONFIG.get("random_seed", 42))
    results = main()