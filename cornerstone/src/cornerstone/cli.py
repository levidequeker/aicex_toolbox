import argparse
import sys
from pathlib import Path
from cornerstone.scripts import gm_analysis, gain_analysis
from cornerstone.core.database import make_dataframe

DB_FILE = "cornerstone_results.csv"

def main():
    # 1. Base parser
    parser = argparse.ArgumentParser(prog="cornerstone", description="IC Design Post-Processing")
    subparsers = parser.add_subparsers(dest="command", help="Available analysis types")

    # 2. GM Command
    gm_parser = subparsers.add_parser("gm", help="Transconductance analysis")
    gm_sub = gm_parser.add_subparsers(dest="mode", help="Simulation mode")
    
    # gm etc
    etc_parser = gm_sub.add_parser("etc", help="Extreme corner analysis")
    etc_parser.add_argument("--path", default=".", help="Directory with .raw files")
    
    # gm mc
    mc_parser = gm_sub.add_parser("mc", help="Monte Carlo statistical analysis")
    mc_parser.add_argument("--path", default=".", help="Directory with .raw files")

    # 3. GAIN Command (Repeat the logic)
    gain_parser = subparsers.add_parser("gain", help="Gain/VTC analysis")
    # ... you can add sub-modes here too if needed ...

    # Parse arguments
    args = parser.parse_args()

    # Create or update dataframe
    df = make_dataframe(args.path, DB_FILE)

    # Routing logic
    if args.command == "gm":
        if args.mode == "etc":
            gm_analysis.run_etc(args.path, df)
            df.to_csv(Path(args.path) / DB_FILE, index=False)
        elif args.mode == "mc":
            gm_analysis.run_mc(args.path, df)
            df.to_csv(Path(args.path) / DB_FILE, index=False)
        else:
            gm_parser.print_help()

    elif args.command == "gain":
        gain_analysis.main(args.path)
        df.to_csv(Path(args.path) / DB_FILE, index=False)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()