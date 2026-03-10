#!/usr/bin/env python3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from rawread import ngRawRead, toDataFrames


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


def main():

    RAW_FILE = "tran_SchGtKttTtVt_LVT_VDD100.raw"

    VIN = "v(vin)"
    VOUT = "v(vout)"

    GAIN_THRESHOLD = 1


    df = toDataFrames(ngRawRead(RAW_FILE))[0]

    vin = df[VIN].values
    vout = df[VOUT].values

    # In simulation: VIN VIN VSS pwl 0 0 50u {VDDA} 100u 0
    # So Vin ramps up and then back down. Must be split in two parts so it does not mess with the derivative
    # Split sweep at maximum Vin into two branches: up and down
    peak = np.argmax(vin)

    vin_up = vin[:peak]
    vout_up = vout[:peak]

    vin_down = vin[peak:]
    vout_down = vout[peak:]


    vin_up, gain_up, res_up = analyze_branch(vin_up, vout_up, GAIN_THRESHOLD)
    vin_down, gain_down, res_down = analyze_branch(vin_down, vout_down, GAIN_THRESHOLD)


    table = pd.DataFrame([

        {"branch":"forward", **res_up},
        {"branch":"reverse", **res_down}

    ])

    table.to_csv("gain_metrics.csv", index=False)

    print("\nGain Metrics\n")
    print(table.to_string(index=False))


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

    plt.savefig("gain_curve.png", dpi=300)
    plt.close()


if __name__ == "__main__":
    main()