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

def analyze_file(filename, vdd):
    df = toDataFrames(ngRawRead(filename))[0]
    time_tran = df["time"].values
    tran_idx = np.argmin(np.abs(time_tran - 400e-9))
    time = time_tran[tran_idx:]
    vin = df["v(vin)"].values[tran_idx:]
    iout = df["i(v.xdut.v1)"].values[tran_idx:]

    dvin = np.gradient(vin)
    diout = np.gradient(iout)

    epsilon = 5e-6
    valid = np.abs(dvin) > epsilon
    

    gm = diout[valid] / dvin[valid]
    time_valid = time[valid]

    """fig, (ax1,ax2, ax3) = plt.subplots(3, 1, figsize=(8,4), sharex=True)
    
    ax1.plot(time_valid, gm)
    ax1.set_ylabel("Gm [A/V]")
    ax1.set_title(f"Voltage gain & gm vs time (VDD={vdd})")
    ax1.grid(True)
    
    ax2.plot(time_valid, Av)
    ax2.set_ylabel("Av [-]")
    ax2.set_xlabel("time [s]")
    ax2.grid(True)

    ax3.plot(time_valid, vin[valid], label="Vin")
    ax3.plot(time_valid, vout[valid], label="Vout")
    ax3.set_ylabel("Voltage [V]")
    ax3.set_xlabel("time [s]")
    ax3.legend()
    ax3.grid(True)

    plt.tight_layout()
    plt.savefig(f"media/gm_VDD{vdd}.png", dpi=300)
    plt.close()"""

    return np.abs(np.mean(gm))


def main():
    raw_files = sorted(glob.glob("*.raw"))
    results = []
    for file in raw_files:
        match = re.findall(r"[0-9]+", file) # Extract VDD from filename
        if len(match) > 0:
            vdd = int(match[0])
            print(f"Analyzing {file}")
            gm = analyze_file(file, vdd)
            results.append(
                {
                    "vdd": vdd,
                    "gm": gm,
                }
            )

    table = pd.DataFrame(results)
    table = table.sort_values(["vdd"])
    table.to_csv("gm_overview.csv", index=False)

    with open("gm_overview.txt", "w") as f:

        f.write("Gm ANALYSIS OVERVIEW\n")
        f.write("=====================\n\n")

        for vdd in sorted(table["vdd"].unique()):

            f.write(f"VDD = {vdd:.3f} V\n")

            sub = table[table["vdd"] == vdd]

            f.write(sub.to_string(index=False))
            f.write("\n\n")


    print("\nFull overview:\n")
    print(table)

    # --- Plot gm vs VDD ---
    fig, (ax1) = plt.subplots(1, 1, figsize=(8, 6), sharex=True)

    # gm vs VDD
    ax1.plot(table["vdd"], table["gm"]*1e6, marker="o")
    ax1.set_ylabel(r"$g_m$ [$\mu S$]")
    ax1.set_xlabel(r"$V_{dd}$ [mV]")
    ax1.set_title(r"$g_m$ vs $V_{dd}$ (NVT schmitt trigger)")
    ax1.grid(True)

    plt.tight_layout()
    plt.savefig("media/gm_Av_vs_VDD.png", dpi=300)
    plt.close()
            



    


if __name__ == "__main__":
    main()
