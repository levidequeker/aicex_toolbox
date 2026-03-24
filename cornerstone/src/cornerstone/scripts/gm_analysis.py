import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from cornerstone.core.io import ngRawRead, toDataFrames, makeResultDirectory
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

def generate_mc_plots(df_mc, stats, gm_cols, result_path, plot=False):
    for col in gm_cols:
        print(f"Provide the title for the plot of column {col}:")
        col_title = input()
        plt.figure(figsize=(10, 6))
        
        # Plot A: De 'Wolk' (Mean + Shading)
        # Multi-index kolommen van stats aanspreken: stats[(col, 'mean')]
        x = stats["vdd"]
        mu = stats[(col, "mean")]
        sigma = stats[(col, "std")]

        plt.plot(x, mu, label=f"Mean {col}", color='blue', lw=2)
        plt.fill_between(x, mu - 3*sigma, mu + 3*sigma, color='blue', alpha=0.2, label='3-sigma range')
        plt.scatter(df_mc["vdd"], df_mc[col], color='black', s=5, alpha=0.3, label='Raw MC data')

        plt.title(f"Monte Carlo Analysis: {col_title}")
        plt.xlabel("VDD [mV]")
        plt.ylabel("gm [S]")
        plt.grid(True, which='both', linestyle='--', alpha=0.5)
        plt.legend()
        
        plot_name = result_path / f"mc_shading_{col}.png"
        plt.savefig(plot_name)
        if plot:
            plt.show()

        # Plot B: Distributie per VDD (Histogram)
        plt.figure(figsize=(10, 6))
        sns.histplot(data=df_mc, x=col, hue="vdd", kde=True, palette="viridis")
        plt.title(f"Distribution of {col_title} across VDD steps")
        plt.savefig(result_path / f"mc_distro_{col}.png")
        if plot:
            plt.show()

def generate_etc_plots(df_etc, gm_cols, result_path, plot=False):
    for col in gm_cols:
        print(f"Provide the title for the plot of column {col}:")
        col_title = input()
        plt.figure(figsize=(10, 6))
        for c in ["Kss","Kff","Ksf","Kfs"]:
            subset = df_etc[df_etc["corner"] == c]
            plt.scatter(subset["vdd"], subset[col], label=c)
        plt.title(f"Extreme corner analysis: {col_title}")
        plt.xlabel("VDD [mV]")
        plt.ylabel("gm [S]")
        plt.grid(True, which='both', linestyle='--', alpha=0.5)
        plt.legend()
        
        plot_name = result_path / f"etc_corners_{col}.png"
        plt.savefig(plot_name)
        if plot:
            plt.show()


def run_etc(path, df, force=False, plot=False):
    # Filter on the etc sims
    etc_indices = df[df["sim_type"] == "etc"].index

    if df[df["sim_type"] == "etc"].empty:
        print("No extreme corner simulation was found.")
        return pd.DataFrame

    print("Processing gm for extreme corner runs...")
    for idx in etc_indices:
        filename = df.at[idx, "filename"]
        if pd.isna(df.loc[idx].get("gm_v1")) or force:
            metrics = process_gm_row(filename, force)
            for col, val in metrics.items():
                df.at[idx, col] = val
    df_etc = df[df["sim_type"] == "etc"].copy()
    gm_cols = [c for c in df_etc.columns if c.startswith("gm_")]
    result_path = makeResultDirectory(path=path, sim="etc")
    generate_etc_plots(df_etc, gm_cols, result_path, plot)
    

def run_mc(path, df, force=False, plot=False):
    # Filter on Monte Carlo sims
    mc_indices = df[df["sim_type"] == "mc"].index

    if df[df["sim_type"] == "mc"].empty:
        print("No Monte Carlo simulation was found.")
        return df, []

    print("Processing gm for Monte Carlo runs...")
    for idx in mc_indices:
        filename = df.at[idx, "filename"]
        if pd.isna(df.loc[idx].get("gm_v1")) or force:
            metrics = process_gm_row(filename, force)
            for col, val in metrics.items():
                df.at[idx, col] = val

    df_mc = df[df["sim_type"] == "mc"].copy()
    gm_cols = [c for c in df_mc.columns if c.startswith("gm_")]
    # Group by VDD to get statistics
    stats = df_mc.groupby("vdd")[gm_cols].agg(["mean", "std"]).reset_index()

    print(stats)
    # Ensure simulation dir exists
    result_path = makeResultDirectory(path=path, sim="mc")
    stats.to_csv(result_path / "mc_gm_stats.csv", index=False)
    generate_mc_plots(df_mc, stats, gm_cols, result_path, plot)

    return stats, gm_cols