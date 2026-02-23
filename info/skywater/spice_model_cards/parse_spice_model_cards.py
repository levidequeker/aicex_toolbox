import os
import re
import pandas as pd

# Path to your .pm3.spice file
spice_file = "sky130_fd_pr__pfet_01v8.pm3.spice"
spice_path = os.path.join("/opt/pdk/share/pdk/sky130A/libs.ref/sky130_fd_pr/spice",spice_file)

# Regular expression to match a model line with Lmin, Lmax, Wmin, Wmax
model_regex = re.compile(
    r'__model\.[0-9]*\s.*\n',
    re.IGNORECASE
)
dimensions_regex = re.compile(r'\+\sLmin=([\d\.Ee+-]+).*Lmax=([\d\.Ee+-]+).*Wmin=([\d\.Ee+-]+).*Wmax=([\d\.Ee+-]+) ', re.IGNORECASE)
models = []
dimensions_line_ctr = 0
with open(spice_path, 'r') as f:
    for line in f:
        match = model_regex.search(line)
        if match:
            print(line)
            model_name = re.findall(r'model\.[0-9]*', line)
            dimensions_line_ctr = 3
        if dimensions_line_ctr == 1:
            lmin = re.findall(r'lmin\s=\s\d*\.\d*e-\d*', line)[0][7:]
            lmax = re.findall(r'lmax\s=\s\d*\.\d*e-\d*', line)[0][7:]
            wmin = re.findall(r'wmin\s=\s\d*\.\d*e-\d*', line)[0][7:]
            wmax = re.findall(r'wmax\s=\s\d*\.\d*e-\d*', line)[0][7:]
            models.append({
                "Model": model_name,
                "Lmin (µm)": lmin,
                "Lmax (µm)": lmax,
                "Wmin (µm)": wmin,
                "Wmax (µm)": wmax
            })
        if dimensions_line_ctr > 0:
            dimensions_line_ctr -= 1

# Convert to DataFrame for easy display
df = pd.DataFrame(models)

# Optional: save to CSV
df.to_csv("output/" + spice_file[:-10] + "_models"  + ".csv", index=False)

pd.set_option('display.max_rows', None)

# Print table
print(df)
