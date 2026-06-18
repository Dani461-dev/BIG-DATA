# ============================================================================
# F03_SENTIMENT_ANALYSIS.PY - Phase 3: Analisis Sentimen Multi-Platform
# Value · Validity
# ============================================================================
"""
Phase 3 handles:
1. Text preprocessing (NLP pipeline)
2. Sentiment model selection and configuration
3. Ensemble approach (VADER + TextBlob + optional IndoBERT)
4. Sentiment scoring and temporal trend analysis
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
import warnings
from typing import Dict, List, Tuple, Any

# NLP imports
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import re

# Try importing Sastrawi
try:
    from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
    factory = StemmerFactory()
    stemmer = factory.create_stemmer()
    SASTRAWI_AVAILABLE = True
except:
    stemmer = None
    SASTRAWI_AVAILABLE = False

# Sentiment models
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob

# ML imports
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

# Try importing transformers for IndoBERT
INDOBERT_AVAILABLE = False
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
    INDOBERT_AVAILABLE = True
except:
    torch = None
    pass

# Import configuration
from config import (
    PROCESSED_DATA_DIR, REPORTS_DIR, FIGURES_DIR,
    NLP_CONFIG, SENTIMENT_CONFIG, STAT_CONFIG,
    REPRODUCIBILITY_CONFIG
)

warnings.filterwarnings('ignore')

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

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
# TEXT PREPROCESSING PIPELINE
# ============================================================================
class TextPreprocessor:
    """NLP preprocessing for Indonesian + English text"""
    
    def __init__(self):
        self.stemmer = stemmer if SASTRAWI_AVAILABLE else None
        self.stop_words = set(stopwords.words('indonesian') + stopwords.words('english'))
        
        logger.info("Text preprocessor initialized")
        if not SASTRAWI_AVAILABLE:
            logger.warning("  Sastrawi not available - stemming disabled")
    
    def clean_text(self, text: str) -> str:
        """Clean text content"""
        if not isinstance(text, str):
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove HTML entities
        text = re.sub(r'&[a-z]+;', '', text)
        
        # Remove mentions and hashtags (but keep the text)
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'#(\w+)', r'\1', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^a-z0-9\s\.\,\!\?\-]', '', text)
        
        # Remove numbers if configured
        if NLP_CONFIG.get("remove_numbers", False):
            text = re.sub(r'\d+', '', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def tokenize(self, text: str) -> List[str]:
        """Tokenize text"""
        try:
            tokens = word_tokenize(text)
        except:
            tokens = text.split()
        
        return tokens
    
    def remove_stopwords(self, tokens: List[str]) -> List[str]:
        """Remove stopwords"""
        if NLP_CONFIG.get("remove_stopwords", True):
            tokens = [t for t in tokens if t not in self.stop_words]
        
        return tokens
    
    def stem(self, tokens: List[str]) -> List[str]:
        """Apply stemming"""
        if NLP_CONFIG.get("use_stemming", True) and self.stemmer:
            try:
                tokens = [self.stemmer.stem(t) for t in tokens]
            except:
                pass  # Keep original tokens if stemming fails
        
        return tokens
    
    def preprocess(self, text: str) -> str:
        """Full preprocessing pipeline"""
        # Clean
        text = self.clean_text(text)
        
        if not text:
            return ""
        
        # Tokenize
        tokens = self.tokenize(text)
        
        # Remove stopwords
        tokens = self.remove_stopwords(tokens)
        
        # Stem
        tokens = self.stem(tokens)
        
        # Rejoin
        processed_text = ' '.join(tokens)
        
        return processed_text


# ============================================================================
# SENTIMENT MODELS
# ============================================================================
class SentimentModels:
    """Container for multiple sentiment analysis models"""
    
    def __init__(self):
        self.models = {}
        self.preprocessor = TextPreprocessor()
        logger.info("Initializing sentiment models...")
    
    def init_vader(self):
        """Initialize VADER sentiment analyzer"""
        logger.info("  Loading VADER model...")
        self.models['vader'] = SentimentIntensityAnalyzer()
        logger.info("  ✓ VADER loaded")
    
    def init_textblob(self):
        """Initialize TextBlob sentiment analyzer"""
        logger.info("  TextBlob initialized")
        self.models['textblob'] = "textblob"
        logger.info("  ✓ TextBlob loaded")
    
    def init_indobert(self):
        """Initialize IndoBERT model (optional)"""
        if not INDOBERT_AVAILABLE:
            logger.warning("  IndoBERT not available (transformers not installed)")
            return
        
        logger.info("  Loading IndoBERT model...")
        try:
            # Check GPU availability
            device = 0 if torch.cuda.is_available() else -1
            device_name = "GPU" if device == 0 else "CPU"
            
            # Load tokenizer and model
            model_name = "indolem/indobert-base-uncased"
            logger.info(f"    Using model: {model_name} on {device_name}")
            
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSequenceClassification.from_pretrained(model_name)
            
            self.models['indobert'] = pipeline(
                "text-classification",
                model=model,
                tokenizer=tokenizer,
                device=device,
                truncation=True,
                max_length=512
            )
            logger.info(f"  ✓ IndoBERT loaded on {device_name}")
        except Exception as e:
            logger.warning(f"  IndoBERT load failed: {str(e)}")
            logger.info("  Falling back to VADER + TextBlob ensemble")
    
    def predict_vader(self, text: str) -> float:
        """Get VADER sentiment score"""
        # Preprocess
        processed_text = self.preprocessor.preprocess(text)
        
        if not processed_text:
            return 0.0
        
        # Predict
        try:
            scores = self.models['vader'].polarity_scores(processed_text)
            return float(scores['compound'])
        except:
            return 0.0
    
    def predict_textblob(self, text: str) -> float:
        """Get TextBlob sentiment score"""
        processed_text = self.preprocessor.preprocess(text)
        
        if not processed_text:
            return 0.0
        
        try:
            blob = TextBlob(processed_text)
            polarity = blob.sentiment.polarity  # -1 to 1
            return float(polarity)
        except:
            return 0.0
    
    def predict_indobert(self, text: str) -> float:
        """Get IndoBERT sentiment score"""
        if 'indobert' not in self.models:
            return 0.0
        
        try:
            result = self.models['indobert'](text[:512])  # Max 512 tokens
            
            label = result[0]['label']
            score = result[0]['score']
            
            # Map labels to sentiment
            # Adjust based on your specific model
            if 'positive' in label.lower() or label == 'LABEL_2':
                return float(score)
            elif 'negative' in label.lower() or label == 'LABEL_0':
                return float(-score)
            else:
                return 0.0
        except:
            return 0.0
    
    def predict_ensemble(self, text: str, weights: Dict[str, float] = None) -> float:
        """Get ensemble prediction (weighted average)"""
        if weights is None:
            weights = {'vader': 0.5, 'textblob': 0.3, 'indobert': 0.2}
        
        predictions = {}
        
        # Get predictions from available models
        if 'vader' in self.models:
            predictions['vader'] = self.predict_vader(text)
        
        if 'textblob' in self.models:
            predictions['textblob'] = self.predict_textblob(text)
        
        if 'indobert' in self.models:
            predictions['indobert'] = self.predict_indobert(text)
        
        # Weighted average
        if predictions:
            total_weight = sum(weights.get(model, 0) for model in predictions)
            if total_weight > 0:
                weighted_score = sum(
                    predictions[model] * weights.get(model, 0)
                    for model in predictions
                ) / total_weight
            else:
                weighted_score = 0.0
        else:
            weighted_score = 0.0
        
        # Clamp to [-1, 1]
        weighted_score = np.clip(float(weighted_score), -1.0, 1.0)
        
        return weighted_score


# ============================================================================
# SENTIMENT ANALYSIS EXECUTOR
# ============================================================================
class SentimentAnalyzer:
    """Execute sentiment analysis on corpus"""
    
    def __init__(self):
        self.sentiment_models = SentimentModels()
        self.results = None
        self.model_performance = {}
    
    def prepare_models(self):
        """Prepare all sentiment models"""
        logger.info("Preparing sentiment models...")
        
        self.sentiment_models.init_vader()
        self.sentiment_models.init_textblob()
        
        # Try IndoBERT if available
        if INDOBERT_AVAILABLE:
            try:
                self.sentiment_models.init_indobert()
            except Exception as e:
                logger.warning(f"IndoBERT initialization failed: {e}")
        
        logger.info("✓ Sentiment models ready\n")
    
    def analyze_corpus(self, df: pd.DataFrame, batch_size: int = 1000) -> pd.DataFrame:
        """
        Analyze sentiment for entire corpus
        
        Args:
            df: DataFrame with 'content' column
            batch_size: Progress report frequency
        """
        logger.info(f"Analyzing sentiment for {len(df)} documents...")
        
        sentiment_results = []
        
        for idx, row in df.iterrows():
            if idx % batch_size == 0 and idx > 0:
                logger.info(f"  Progress: {idx}/{len(df)}")
            
            content = row.get('content', '')
            
            # Skip empty content
            if not content or len(str(content).strip()) < 5:
                sentiment_results.append({
                    'sentiment_score': 0.0,
                    'sentiment_label': 'NEUTRAL',
                })
                continue
            
            # Get ensemble prediction
            try:
                score = self.sentiment_models.predict_ensemble(str(content))
            except:
                score = 0.0
            
            # Map to sentiment label based on thresholds
            positive_threshold = SENTIMENT_CONFIG.get("sentiment_thresholds", {}).get("positive", [0.1, 1.0])[0]
            negative_threshold = SENTIMENT_CONFIG.get("sentiment_thresholds", {}).get("negative", [-1.0, -0.1])[1]
            
            if score > positive_threshold:
                label = "POSITIVE"
            elif score < negative_threshold:
                label = "NEGATIVE"
            else:
                label = "NEUTRAL"
            
            sentiment_results.append({
                'sentiment_score': float(score),
                'sentiment_label': label,
            })
        
        # Add results to dataframe
        sentiment_df = pd.DataFrame(sentiment_results)
        df_analyzed = pd.concat([df.reset_index(drop=True), sentiment_df], axis=1)
        
        logger.info(f"✓ Sentiment analysis completed\n")
        logger.info(f"Label distribution:\n{df_analyzed['sentiment_label'].value_counts()}\n")
        
        self.results = df_analyzed
        return df_analyzed
    
    def temporal_sentiment_trends(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute temporal sentiment trends"""
        logger.info("Computing temporal sentiment trends...")
        
        # Ensure date column exists
        if 'date' not in df.columns:
            logger.warning("Date column not found")
            return pd.DataFrame()
        
        # Group by year-month
        df['year_month'] = df['date'].dt.to_period('M')
        
        # Compute metrics by period
        trends = df.groupby('year_month').agg({
            'sentiment_score': ['mean', 'std', 'count'],
        }).reset_index()
        
        trends.columns = ['year_month', 'avg_sentiment', 'sentiment_std', 'post_count']
        
        return trends
    
    def export_sentiment_analysis(self, df: pd.DataFrame):
        """Export sentiment analysis results"""
        logger.info("Exporting sentiment analysis results...")
        
        # Try Parquet first
        try:
            output_file = PROCESSED_DATA_DIR / "sentiment_analyzed_full.parquet"
            df.to_parquet(output_file, engine="pyarrow", compression="snappy")
            logger.info(f"  ✓ Parquet: {output_file}")
        except Exception as e:
            logger.warning(f"Parquet export failed: {e}")
        
        # Always save CSV
        summary_file = PROCESSED_DATA_DIR / "sentiment_analyzed_full.csv"
        df.to_csv(summary_file, index=False)
        logger.info(f"  ✓ CSV: {summary_file}")
        
        return summary_file


# ============================================================================
# PHASE 3 EXECUTOR
# ============================================================================
class Phase3SentimentAnalysis:
    """
    Implements Phase 3: Analisis Sentimen Multi-Platform
    """
    
    def __init__(self):
        self.analyzer = SentimentAnalyzer()
        self.results = {}
    
    def run_phase3(self, master_df: pd.DataFrame) -> Dict[str, Any]:
        """Execute complete Phase 3 pipeline"""
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 3: ANALISIS SENTIMEN MULTI-PLATFORM")
        logger.info("=" * 80 + "\n")
        
        results = {
            "phase": "F3_Sentiment_Analysis",
            "timestamp": datetime.now().isoformat(),
        }
        
        # Step 3.1: Prepare models
        logger.info("[Step 3.1] Preparing sentiment models...")
        self.analyzer.prepare_models()
        
        # Step 3.2: Analyze main corpus
        logger.info("[Step 3.2] Analyzing sentiment for main corpus...")
        analyzed_df = self.analyzer.analyze_corpus(master_df)
        results["main_corpus_records"] = len(analyzed_df)
        results["sentiment_distribution"] = analyzed_df['sentiment_label'].value_counts().to_dict()
        
        # Step 3.3: Compute temporal trends
        logger.info("[Step 3.3] Computing temporal sentiment trends...")
        trends_df = self.analyzer.temporal_sentiment_trends(analyzed_df)
        
        # Step 3.4: Export results
        logger.info("[Step 3.4] Exporting results...")
        self.analyzer.export_sentiment_analysis(analyzed_df)
        
        # Save trends
        trends_file = PROCESSED_DATA_DIR / "sentiment_trends_temporal.csv"
        trends_df.to_csv(trends_file, index=False)
        logger.info(f"  ✓ Trends: {trends_file}")
        
        # Generate visualization
        logger.info("[Step 3.5] Generating visualization...")
        self._visualize_sentiment_trends(analyzed_df)
        
        # Save report
        self._save_phase3_report(results)
        
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 3 COMPLETED SUCCESSFULLY")
        logger.info("=" * 80 + "\n")
        
        return results
    
    @staticmethod
    def _visualize_sentiment_trends(df: pd.DataFrame):
        """Create sentiment visualization"""
        logger.info("  Creating visualization...")
        
        try:
            # Prepare data
            df_copy = df.copy()
            df_copy['year_month'] = df_copy['date'].dt.to_period('M')
            monthly_sentiments = df_copy.groupby(['year_month', 'sentiment_label']).size().unstack(fill_value=0)
            
            # Create plot
            fig, ax = plt.subplots(figsize=(16, 8))
            
            monthly_sentiments.plot(
                kind='area',
                stacked=True,
                ax=ax,
                color=['#e74c3c', '#95a5a6', '#2ecc71'],
                alpha=0.8
            )
            
            ax.set_title('Sentiment Distribution Over Time (11 Years)', fontsize=16, fontweight='bold')
            ax.set_xlabel('Date', fontsize=12)
            ax.set_ylabel('Number of Posts', fontsize=12)
            ax.legend(title='Sentiment', labels=['Negative', 'Neutral', 'Positive'], fontsize=11)
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            output_file = FIGURES_DIR / "Phase3_Sentiment_Trends.png"
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            logger.info(f"  ✓ Visualization: {output_file}")
            plt.close()
        
        except Exception as e:
            logger.error(f"Visualization error: {str(e)}")
    
    @staticmethod
    def _save_phase3_report(results: Dict[str, Any]):
        """Save Phase 3 report"""
        report_file = REPORTS_DIR / "Phase3_Sentiment_Analysis_Report.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str, ensure_ascii=False)
        
        logger.info(f"  ✓ Report: {report_file}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================
def main():
    """Execute Phase 3"""
    
    # Try different data sources
    data_sources = [
        (PROCESSED_DATA_DIR / "master_dataset_unified.parquet", "parquet"),
        (PROCESSED_DATA_DIR / "master_dataset_unified.csv", "csv"),
    ]
    
    master_df = None
    
    for file_path, file_type in data_sources:
        if file_path.exists():
            try:
                logger.info(f"Loading master dataset from {file_path}...")
                if file_type == "parquet":
                    master_df = pd.read_parquet(file_path)
                else:
                    master_df = pd.read_csv(file_path)
                logger.info(f"✓ Loaded {len(master_df)} records\n")
                break
            except Exception as e:
                logger.warning(f"Failed to load {file_path}: {e}")
                continue
    
    if master_df is None:
        logger.error("Could not load master dataset. Run Phase 1 first.")
        return None
    
    # Ensure date column is datetime
    if 'date' in master_df.columns:
        master_df['date'] = pd.to_datetime(master_df['date'])
    
    # Run Phase 3
    phase3 = Phase3SentimentAnalysis()
    results = phase3.run_phase3(master_df)
    
    return results


if __name__ == "__main__":
    if torch is not None:
        np.random.seed(REPRODUCIBILITY_CONFIG.get("random_seed", 42))
        torch.manual_seed(REPRODUCIBILITY_CONFIG.get("torch_seed", 42))
    else:
        np.random.seed(REPRODUCIBILITY_CONFIG.get("random_seed", 42))
    
    results = main()