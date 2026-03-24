import glob
import re
import os
import numpy as np
import pandas as pd
from pathlib import Path
from cornerstone.core.io import ngRawRead, toDataFrames
from cornerstone.core.parser import parse_filename

def make_dataframe(path, storage_file):
    results = []
    full_storage_path = Path(path) / storage_file
    
    # Try loading an existing df out of the storage file (.csv) and adding previously processed filenames to a set
    processed_files = set()
    if full_storage_path.exists():
        print("Loading existing dataframe...")
        try:
            df = pd.read_csv(full_storage_path)
            processed_files = set(df['filename'].astype(str))
        except Exception as e:
            print("Loading storage file failed: ", e)
            df = None
    else:

        df = None

    # Iterate over files in path and parse them (if not already in df)
    for f in Path(path).glob("*.raw"):
        if str(f) in processed_files: continue

        meta = parse_filename(f.name)
        if not meta: continue
        
        # Add a "type" tag based on metadata
        if meta["mc_iter"] is not None:
            meta["sim_type"] = "mc" 
        elif (meta["corner"] in ["Ktt", "Att"]) and (meta["temp"] == "Tt"):
            meta["sim_type"] = "typical"
        else:
            meta["sim_type"] = "etc"
        results.append(meta)
    
    if not results:
        print("No new files to process.")
        return df

    new_df = pd.DataFrame(results)

    if df is not None:
        combined_df = pd.concat([df, new_df], ignore_index=True, sort=False)
        print(f"Added {len(results)} new files to the existing database.")
        return combined_df
    else:
        print(f"Created new database with {len(results)} files.")
        return new_df