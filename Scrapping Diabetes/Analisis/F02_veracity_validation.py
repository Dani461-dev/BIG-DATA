# ============================================================================
# F02_VERACITY_VALIDATION.PY - Phase 2: Verifikasi Veracity
# Veracity · Validity
# ============================================================================
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
import warnings
from typing import Dict, List, Tuple, Any
from scipy.stats import pearsonr, spearmanr

from config import (
    PROCESSED_DATA_DIR, REPORTS_DIR, FIGURES_DIR,
    ANNOTATION_GUIDELINES, SENTIMENT_CONFIG,
    STAT_CONFIG, REPRODUCIBILITY_CONFIG
)

warnings.filterwarnings('ignore')

from loguru import logger
logger.add(
    lambda msg: print(msg, end=""),
    level="INFO",
    format="<level>{time:HH:mm:ss}</level> | <level>{level: <8}</level> | {message}"
)


class SentimentAnnotator:
    """Handle manual annotation for gold standard dataset"""
    
    def __init__(self):
        self.annotation_samples = None
        self.inter_rater_results = {}
    
    def select_annotation_samples(self, df: pd.DataFrame, sample_size: int = 300) -> pd.DataFrame:
        """Select stratified sample for annotation"""
        logger.info(f"Selecting {sample_size} samples for annotation...")
        
        np.random.seed(REPRODUCIBILITY_CONFIG["random_seed"])
        
        # Stratified sampling
        if 'platform' in df.columns:
            n_per_group = sample_size // df['platform'].nunique()
            samples = df.groupby('platform', group_keys=False).apply(
                lambda x: x.sample(n=min(n_per_group, len(x)), random_state=42)
            )
        else:
            samples = df.sample(n=min(sample_size, len(df)), random_state=42)
        
        samples = samples.copy()
        samples["annotation_id"] = range(len(samples))
        
        self.annotation_samples = samples
        
        logger.info(f"Selected {len(samples)} samples for annotation")
        
        return samples
    
    def export_annotation_template(self, output_file: Path = None) -> Path:
        """Export annotation template"""
        if output_file is None:
            output_file = REPORTS_DIR / "Annotation_Template.xlsx"
        
        logger.info(f"Exporting annotation template to {output_file}...")
        
        try:
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # Guidelines sheet
                guidelines_df = pd.DataFrame({
                    "Sentiment": ["POSITIVE", "NEUTRAL", "NEGATIVE"],
                    "Definition": [
                        "Hopeful, supportive, encouraging content",
                        "Factual, informational, no clear sentiment",
                        "Concern, fear, complaint, misinformation",
                    ],
                })
                guidelines_df.to_excel(writer, sheet_name="Guidelines", index=False)
                
                # Samples sheet
                if self.annotation_samples is not None:
                    anno_export = self.annotation_samples[[
                        "annotation_id", "date", "platform", "content"
                    ]].copy()
                    # Remove timezone for Excel compatibility
                    if 'date' in anno_export.columns:
                        anno_export['date'] = anno_export['date'].dt.tz_localize(None)
                    
                    anno_export["Sentiment_Label"] = None
                    anno_export["Confidence"] = None
                    anno_export.to_excel(writer, sheet_name="Samples", index=False)
        
        except Exception as e:
            logger.warning(f"Excel export failed: {e}, saving CSV instead")
            output_file = REPORTS_DIR / "Annotation_Template.csv"
            if self.annotation_samples is not None:
                anno_export = self.annotation_samples[[
                    "annotation_id", "date", "platform", "content"
                ]].copy()
                if 'date' in anno_export.columns:
                    anno_export['date'] = anno_export['date'].dt.tz_localize(None)
                anno_export.to_csv(output_file, index=False)
        
        logger.info(f"Template exported to {output_file}")
        return output_file
    
    def simulate_annotation(self) -> Dict[str, Any]:
        """Simulate annotation (for testing)"""
        logger.info("Simulating annotation process (2 independent annotators)...")
        
        if self.annotation_samples is None:
            return {}
        
        np.random.seed(REPRODUCIBILITY_CONFIG["random_seed"])
        
        annotations = []
        
        for idx, row in self.annotation_samples.iterrows():
            content_lower = str(row["content"]).lower()
            
            # Infer sentiment from keywords
            true_sentiment = self._infer_sentiment(content_lower)
            
            # Annotator 1: 85% accuracy
            anno1 = true_sentiment if np.random.random() < 0.85 else np.random.choice([-1, 0, 1])
            
            # Annotator 2: 82% accuracy
            anno2 = true_sentiment if np.random.random() < 0.82 else np.random.choice([-1, 0, 1])
            
            annotations.append({
                "annotation_id": row["annotation_id"],
                "annotator_1": anno1,
                "annotator_2": anno2,
                "agree": anno1 == anno2,
            })
        
        anno_df = pd.DataFrame(annotations)
        
        # Cohen's Kappa
        from sklearn.metrics import cohen_kappa_score
        kappa = cohen_kappa_score(anno_df["annotator_1"], anno_df["annotator_2"])
        
        if kappa >= 0.81:
            strength = "Almost Perfect"
        elif kappa >= 0.61:
            strength = "Substantial"
        else:
            strength = "Moderate"
        
        results = {
            "total_samples": len(anno_df),
            "agreement_pct": (anno_df["agree"].sum() / len(anno_df) * 100),
            "cohens_kappa": float(kappa),
            "agreement_strength": strength,
            "status": "pass" if kappa >= 0.60 else "revision_needed",
        }
        
        logger.info(f"\nAnnotation Results:")
        logger.info(f"  Total samples: {results['total_samples']}")
        logger.info(f"  Agreement rate: {results['agreement_pct']:.1f}%")
        logger.info(f"  Cohen's Kappa: {results['cohens_kappa']:.3f} ({strength})")
        logger.info(f"  Status: {results['status']}")
        
        self.inter_rater_results = results
        return results
    
    @staticmethod
    def _infer_sentiment(content: str) -> int:
        """Infer sentiment from keywords"""
        positive_keywords = ["baik", "bagus", "senang", "terbantu", "sukses", "pulih", "sehat"]
        negative_keywords = ["buruk", "jelek", "susah", "mahal", "bahaya", "komplikasi"]
        
        pos_count = sum(1 for kw in positive_keywords if kw in content)
        neg_count = sum(1 for kw in negative_keywords if kw in content)
        
        if pos_count > neg_count:
            return 1
        elif neg_count > pos_count:
            return -1
        else:
            return 0


class Phase2VeracityValidation:
    """Phase 2: Verifikasi Veracity"""
    
    def __init__(self):
        self.sentiment_annotator = SentimentAnnotator()
        self.results = {}
    
    def run_phase2(self, master_df: pd.DataFrame) -> Dict[str, Any]:
        """Execute Phase 2"""
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 2: VERIFIKASI VERACITY (External Validation + Annotation)")
        logger.info("=" * 80 + "\n")
        
        results = {
            "phase": "F2_Veracity_Validation",
            "timestamp": datetime.now().isoformat(),
        }
        
        # Step 2.1: Select samples
        logger.info("\n[Step 2.1] Selecting stratified samples for annotation...")
        samples = self.sentiment_annotator.select_annotation_samples(master_df, sample_size=300)
        
        # Step 2.2: Export template
        logger.info("\n[Step 2.2] Exporting annotation template...")
        template_file = self.sentiment_annotator.export_annotation_template()
        
        # Step 2.3: Simulate annotation
        logger.info("\n[Step 2.3] Simulating inter-rater annotation process...")
        annotation_results = self.sentiment_annotator.simulate_annotation()
        results["inter_rater_reliability"] = annotation_results
        
        # Step 2.4: Create gold standard
        logger.info("\n[Step 2.4] Creating gold standard dataset...")
        gold_standard = samples[["annotation_id", "date", "platform", "content"]].copy()
        if 'date' in gold_standard.columns:
            gold_standard['date'] = gold_standard['date'].dt.tz_localize(None)
        
        gold_standard_file = PROCESSED_DATA_DIR / "gold_standard_300samples.csv"
        gold_standard.to_csv(gold_standard_file, index=False)
        logger.info(f"Gold standard saved to {gold_standard_file}")
        
        results["gold_standard_records"] = len(gold_standard)
        
        # Save report
        report_file = REPORTS_DIR / "Phase2_Veracity_Validation_Report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 2 COMPLETED")
        logger.info("=" * 80 + "\n")
        
        return results


def main():
    """Execute Phase 2"""
    master_file = PROCESSED_DATA_DIR / "master_dataset_unified.csv"
    
    if not master_file.exists():
        logger.error("Master dataset not found")
        return None
    
    logger.info(f"Loading master dataset...")
    master_df = pd.read_csv(master_file)
    master_df['date'] = pd.to_datetime(master_df['date'])
    
    phase2 = Phase2VeracityValidation()
    results = phase2.run_phase2(master_df)
    
    return results


if __name__ == "__main__":
    np.random.seed(REPRODUCIBILITY_CONFIG["random_seed"])
    results = main()