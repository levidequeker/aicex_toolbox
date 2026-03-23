import re
import numpy as np

def parse_filename(name):
    """Extracts metadata from filename."""
    # Pattern: tran_SchGt <Corner> <Temp> V <Voltage[mV]> _ <MC_Iter> .raw
    pattern = r"tran_SchGt(?P<corner>[a-zA-Z]+)(?P<temp>T[tlh])V(?P<vdd>\d+)(?:_(?P<mc>\d+))?"
    match = re.search(pattern, name)
    
    if not match:
        return None
        
    return {
        "filename": name,
        "corner": match.group("corner"),
        "temp": match.group("temp"),
        "vdd": int(match.group("vdd")),
        "mc_iter": int(match.group("mc")) if match.group("mc") else None,
        "gm": np.nan,
        "Av": np.nan,
    }