import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from cornerstone.core.io import ngRawRead, toDataFrames
from cornerstone.core.parser import parse_filename

def calculate_gm(df_sim):
    """Calculates gm from the simulation dataframe."""
    results = {}
    vin = df_sim["v(vin)"].values
    
    # Search for cols that resemble i(v.xdut.v1), i(v.xdut.v2), etc.
    probe_pattern = r"i\(v\.xdut\.(?P<dev>v\d+)\)"

    for col in df_sim.columns:
        match = re.search(probe_pattern, col)
        if match:
            dev_name = match.group("dev") # f.e. 'v1'
            iout = df_sim[col].values
            gm_curve = np.abs(np.gradient(iout, vin))
            results[f"gm_{dev_name}"] = np.mean(gm_curve)
            
    return results # f.e. {'gm_v1': 1.2e-4, 'gm_v2': 1.1e-4}

def process_gm_row(filename, force):
        try:
            raw_data = ngRawRead(filename)
            df_sim = toDataFrames(raw_data)[0]
            
            # 2. Bereken alle beschikbare gm's
            gm_results = calculate_gm(df_sim)
            return pd.Series(gm_results)
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            return pd.Series(dtype=float)
        

def run_etc(dir, df, force=False):
    # Filter on the etc sims
    etc_indices = df[df["sim_type"] == "etc"].index

    if df[df["sim_type"] == "etc"].empty:
        print("No extreme corner simulation was found.")
        return pd.DataFrame

    print("Processing gm for extreme corner runs...")
    for idx in etc_indices:
        filename = df.at[idx, "filename"]
        if pd.isna(df.loc[idx].get("gm_v1")) or force:
            metrics = process_gm_row(filename)
            for col, val in metrics.items():
                df.at[idx, col] = val

def run_mc(dir, df, force=False):
    # Filter on Monte Carlo sims
    mc_indices = df[df["sim_type"] == "mc"].index

    if df[df["sim_type"] == "mc"].empty:
        print("No Monte Carlo simulation was found.")
        return pd.DataFrame

    print("Processing gm for Monte Carlo runs...")
    for idx in mc_indices:
        filename = df.at[idx, "filename"]
        if pd.isna(df.loc[idx].get("gm_v1")) or force:
            metrics = process_gm_row(filename)
            for col, val in metrics.items():
                df.at[idx, col] = val

    df_mc = df[df["sim_type"] == "mc"].copy()
    gm_cols = [c for c in df_mc.columns if c.startswith("gm_")]
    # Group by VDD to get statistics
    stats = df_mc.groupby("vdd")[gm_cols].agg(["mean", "std"]).reset_index()
    return stats, gm_cols