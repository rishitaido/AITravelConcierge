# scripts/ingest.py
import pandas as pd
import os

DATA_DIR = "data"

def clean_csv(path):
    print(f"→ Loading {path}")
    try:
        df = pd.read_csv(path)
        df.dropna(axis=0, how='all', inplace=True)  # Drop empty rows
        df.dropna(axis=1, how='all', inplace=True)  # Drop empty cols
        print(f"✔ {path}: {df.shape[0]} rows, {df.shape[1]} columns")
        return df
    except Exception as e:
        print(f"⚠️ Error loading {path}: {e}")
        return None

def ingest_all():
    datasets = {
        "airports": "airports.csv",
        "customer_booking": "customer_booking.csv",
    }

    for name, file in datasets.items():
        path = os.path.join(DATA_DIR, file)
        df = clean_csv(path)
        # Add validation logic as needed
        if df is not None:
            print(f"✅ {name} cleaned successfully.\n")
            
'''
    # Validate text corpus
    text_path = os.path.join(DATA_DIR, "text_corpus.txt")
    if os.path.exists(text_path):
        with open(text_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            print(f"✔ Text corpus: {len(lines)} lines")
    else:
        print("⚠️ text_corpus.txt not found")

    # 3D Point Clouds (example: count .bin files)
    pc_dir = os.path.join(DATA_DIR, "point_clouds")
    if os.path.isdir(pc_dir):
        point_files = [f for f in os.listdir(pc_dir) if f.endswith(".bin")]
        print(f"✔ Found {len(point_files)} point cloud files in {pc_dir}")
    else:
        print("⚠️ point_clouds directory missing")
'''
if __name__ == "__main__":
    ingest_all()

#python scripts/ingest.py

