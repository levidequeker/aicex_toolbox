import subprocess
import re
from pathlib import Path

TEMPLATE = Path("tran_SchGtKttTtVt.spi")

# Voltage sweep (0.30 → 0.03 V in steps of 0.01V)
voltages = [round(v/1000, 3) for v in range(280, 210, -20)]


def make_netlist(vdd):
    """Create a modified netlist with updated AVDD parameter and corresponding filename."""
    content = TEMPLATE.read_text()

    # Replace AVDD value
    new_content = re.sub(
        r"\.param\s+AVDD\s*=.*",
        f".param AVDD = {vdd}",
        content
    )

    # filename suffix in mV (0.30 → 300)
    mv = int(vdd * 1000)

    # Replace write command in the control section
    new_content = re.sub(
        r"write.*",
        f"write tran_SchGtKttTtVt_LVT_VDD{mv}.raw",
        new_content
    )

    # output file name
    outfile = Path(f"tran_SchGtKttTtVt_VDD{mv}.spi")
    outfile.write_text(new_content)
    return outfile, mv


def run_ngspice(netfile, mv):
    """Execute NGspice."""
    rawfile = f"tran_SchGtKttTtVt_LVT_VDD{mv}.raw"
    logfile = f"tran_SchGtKttTtVt_LVT_VDD{mv}.log"

    cmd = f"ngspice {netfile} -r {rawfile} 2>&1 | tee {logfile}"
    print(f"Running: {cmd}")
    subprocess.run(cmd, shell=True, check=True)


def main():
    for v in voltages:
        net, mv = make_netlist(v)
        run_ngspice(net, mv)


if __name__ == "__main__":
    main()


