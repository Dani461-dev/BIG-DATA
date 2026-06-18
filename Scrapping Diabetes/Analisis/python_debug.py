from pathlib import Path
import pandas as pd

print("=" * 80)
print("CHECKING SENTIMENT DATA")
print("=" * 80)

data_dir = Path("data/processed")
sentiment_csv = data_dir / "sentiment_analyzed_full.csv"

if sentiment_csv.exists():
    print(f"\n✓ File found: {sentiment_csv}")
    print(f"  Size: {sentiment_csv.stat().st_size / 1024 / 1024:.1f} MB")
    
    try:
        # Load first 10 rows
        df = pd.read_csv(sentiment_csv, nrows=10)
        
        print(f"\n✓ Successfully loaded!")
        print(f"  Total rows: {len(pd.read_csv(sentiment_csv))}")
        print(f"  Columns: {list(df.columns)}")
        
        print(f"\nFirst 3 rows:")
        print(df[['date', 'platform', 'sentiment_label', 'sentiment_score']].head(3).to_string())
        
        # Check sentiment_label
        if 'sentiment_label' in df.columns:
            print(f"\n✓ sentiment_label column EXISTS")
            full_df = pd.read_csv(sentiment_csv)
            print(f"  Distribution:")
            for label, count in full_df['sentiment_label'].value_counts().items():
                pct = count / len(full_df) * 100
                print(f"    {label}: {count} ({pct:.1f}%)")
        else:
            print(f"\n✗ sentiment_label column NOT FOUND")
            print(f"  Columns available: {list(df.columns)}")
    
    except Exception as e:
        print(f"\n✗ Error reading CSV: {e}")
        print(f"  Type: {type(e).__name__}")
else:
    print(f"\n✗ File not found: {sentiment_csv}")