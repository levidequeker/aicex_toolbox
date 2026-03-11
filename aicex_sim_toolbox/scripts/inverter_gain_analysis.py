#!/usr/bin/env python3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
from pathlib import Path
import glob

BSIZE_SP = 512 # Max size of a line of data; we don't want to read the
               # whole file to find a line, in case file does not have
               # expected structure.
MDATA_LIST = [b'title', b'date', b'plotname', b'flags', b'no. variables',
              b'no. points', b'dimensions', b'command', b'option']
def ngRawRead(fname: str):
    """Read ngspice binary raw files. Return tuple of the data, and the
    plot metadata. The dtype of the data contains field names. This is
    not very robust yet, and only supports ngspice.
    >>> darr, mdata = rawread('test.py')
    >>> darr.dtype.names
    >>> plot(np.real(darr['frequency']), np.abs(darr['v(out)']))
    """
    # Example header of raw file
    # Title: rc band pass example circuit
    # Date: Sun Feb 21 11:29:14  2016
    # Plotname: AC Analysis
    # Flags: complex
    # No. Variables: 3
    # No. Points: 41
    # Variables:
    #         0       frequency       frequency       grid=3
    #         1       v(out)  voltage
    #         2       v(in)   voltage
    # Binary:
    fp = open(fname, 'rb')
    plot = {}
    count = 0
    arrs = []
    plots = []
    names = dict()
    ind = 0
    while (True):
        try:
            mdata = fp.readline(BSIZE_SP).split(b':', maxsplit=1)
        except:
            raise
        if len(mdata) == 2:
            if mdata[0].lower() in MDATA_LIST:
                plot[mdata[0].lower()] = mdata[1].strip()
            if mdata[0].lower() == b'variables':
                nvars = int(plot[b'no. variables'])
                npoints = int(plot[b'no. points'])
                plot['varnames'] = []
                plot['varunits'] = []
                for varn in range(nvars):

                    varspec = (fp.readline(BSIZE_SP).strip()
                               .decode('ascii').split())
                    assert(varn == int(varspec[0]))

                    #- Skup duplicated variables
                    if(varspec[1] not in names):
                        names[varspec[1]] = 1
                    else:
                        varspec[1] += str(ind)
                        ind +=1
                    plot['varnames'].append(varspec[1])
                    plot['varunits'].append(varspec[2])
            if mdata[0].lower() == b'binary':
                rowdtype = np.dtype({'names': plot['varnames'],
                                     'formats': [np.complex128 if b'complex'
                                                 in plot[b'flags']
                                                 else np.float64]*nvars})
                # We should have all the metadata by now
                arrs.append(np.fromfile(fp, dtype=rowdtype, count=npoints))
                plots.append(plot)
                fp.readline() # Read to the end of line
        else:
            break

    return (arrs, plots)

def toDataFrames(ngarr):
    (arrs,plots) = ngarr

    dfs = list()
    for i in range(0,len(plots)):
        df = pd.DataFrame(data=arrs[0],columns=plots[0]['varnames'])
        dfs.append(df)
    return dfs

def compute_gain(vin, vout):

    order = np.argsort(vin)
    vin = vin[order]
    vout = vout[order]

    gain = np.gradient(vout, vin)

    return vin, vout, gain


def largest_continuous_region(vin, gain, threshold):

    mask = np.abs(gain) > threshold

    # Check if it is above threshold somewhere
    if not np.any(mask): 
        return np.nan, np.nan, np.nan

    regions = []
    start = None

    for i, m in enumerate(mask):
        
        if m and start is None:
            # Beginning of window
            start = i
        elif not m and start is not None:
            # End of window
            regions.append((start, i-1))
            start = None

    if start is not None:
        # End of window not reached at end of sim --> save up until end of sim as window
        regions.append((start, len(mask)-1))

    # Select largest window as best window
    best = None
    best_width = 0

    for s,e in regions:
        # s = start, e = end
        width = vin[e] - vin[s]

        if width > best_width:
            best_width = width
            best = (s,e)

    s,e = best

    vin_min = vin[s]
    vin_max = vin[e]

    return vin_min, vin_max, vin_max - vin_min


def analyze_branch(vin, vout, threshold):

    vin, vout, gain = compute_gain(vin, vout)

    max_gain = np.max(np.abs(gain))

    vin_min, vin_max, width = largest_continuous_region(vin, gain, threshold)

    if np.isnan(width):

        v_bias = np.nan
        small_signal_gain = np.nan

    else:

        v_bias = (vin_min + vin_max)/2

        idx = np.argmin(np.abs(vin - v_bias))

        small_signal_gain = gain[idx]

    results = {
        "max_gain": max_gain,
        "vin_min_gain_window": vin_min,
        "vin_max_gain_window": vin_max,
        "vin_gain_window": width,
        "bias_point": v_bias,
        "small_signal_gain_at_bias": small_signal_gain
    }

    return vin, gain, results

def analyze_file(filename, vdd):
    GAIN_THRESHOLD = 1

    df = toDataFrames(ngRawRead(filename))[0]
    vin = df["v(vin)"].values
    vout = df["v(vout)"].values
    time = df["time"].values

    # In simulation, VDD starts at 0, because I let all nodes initialize at 0 V
    # I let VDD sweep up in the first 10 ns, leading to a non-realistic transient. 
    # Must remove this transient so it does not spoil the gain measurement
    timestep = time[1] - time[0]
    transient_steps = 100e-9 // timestep # Remove the first 100 ns

    # In simulation: VIN VIN VSS pwl 0 0 50u {VDDA} 100u 0
    # So Vin ramps up and then back down. Must be split in two parts so it does not mess with the derivative
    # Split sweep at maximum Vin into two branches: up and down
    peak = np.argmax(vin)
 
    vin_up = vin[transient_steps:peak]
    vout_up = vout[transient_steps:peak]

    vin_down = vin[peak:]
    vout_down = vout[peak:]


    vin_up, gain_up, res_up = analyze_branch(vin_up, vout_up, GAIN_THRESHOLD)
    vin_down, gain_down, res_down = analyze_branch(vin_down, vout_down, GAIN_THRESHOLD)

    # Plot gain curve
    plt.figure()

    plt.plot(vin_up, gain_up, label="Forward sweep")
    plt.plot(vin_down, gain_down, label="Reverse sweep")

    plt.axhline(1, linestyle="--")
    plt.axhline(-1, linestyle="--")

    plt.xlabel("Vin [V]")
    plt.ylabel("Gain dVout/dVin")
    plt.title("Voltage Gain vs Vin")

    plt.grid(True)
    plt.legend()

    plt.savefig(f"iga/gain_curve_VDD{vdd}.png", dpi=300)
    plt.close()

    return res_up, res_down


def main():


    VIN = "v(vin)"
    VOUT = "v(vout)"
    GAIN_THRESHOLD = 1

    raw_files = sorted(glob.glob("*.raw"))
    results = []
    for file in raw_files:
        match = re.findall(r"[0-9]+", file) # Extract VDD from filename
        if match is not None:
            vdd = int(match)
            res_up, res_down = analyze_file(file, vdd)

            res_up["branch"] = "forward"
            res_down["branch"] = "reverse"

            res_up["vdd"] = vdd
            res_down["vdd"] = vdd

            results.append(res_up)
            results.append(res_down)

    if len(results) == 0:
        print("No file found that corresponds to the naming convention tran_<type of test>_<technology>_VDD<number>.raw")
        return 0
        
    table = pd.DataFrame(results)
    table = table.sort_values(["vdd", "branch"])
    table.to_csv("gain_overview.csv", index=False)

    with open("gain_overview.txt", "w") as f:

        f.write("GAIN ANALYSIS OVERVIEW\n")
        f.write("=====================\n\n")

        for vdd in sorted(table["vdd"].unique()):

            f.write(f"VDD = {vdd:.3f} V\n")

            sub = table[table["vdd"] == vdd]

            f.write(sub.to_string(index=False))
            f.write("\n\n")


    print("\nFull overview:\n")
    print(table)

    


if __name__ == "__main__":
    main()