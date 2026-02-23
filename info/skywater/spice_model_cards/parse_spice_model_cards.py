import os
import re
import pandas as pd

# Path to your .pm3.spice file
spice_file = os.path.join("/opt/pdk/share/pdk/sky130A/libs.ref/sky130_fd_pr/spice","sky130_fd_pr__nfet_01v8_lvt.pm3.spice")

# Regular expression to match a model line with Lmin, Lmax, Wmin, Wmax
model_regex = re.compile(
    r'^\.model\s+(\S+)\s+.*Lmin=([\d\.Ee+-]+).*Lmax=([\d\.Ee+-]+).*Wmin=([\d\.Ee+-]+).*Wmax=([\d\.Ee+-]+)',
    re.IGNORECASE
)

models = []

with open(spice_file, 'r') as f:
    for line in f:
        line = line.strip()
        match = model_regex.search(line)
        if match:
            model_name = match.group(1)
            lmin = float(match.group(2))
            lmax = float(match.group(3))
            wmin = float(match.group(4))
            wmax = float(match.group(5))
            models.append({
                "Model": model_name,
                "Lmin (µm)": lmin,
                "Lmax (µm)": lmax,
                "Wmin (µm)": wmin,
                "Wmax (µm)": wmax
            })

# Convert to DataFrame for easy display
df = pd.DataFrame(models)

# Optional: save to CSV
df.to_csv("nfet_01v8_lvt_models.csv", index=False)

# Print table
print(df)
