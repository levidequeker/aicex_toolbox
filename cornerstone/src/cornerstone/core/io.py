# Reproduced from Carsten Wulff's CICSIM project: https://github.com/wulffern/cicsim

import os
import numpy as np
import pandas as pd
from pathlib import Path

RESULT_DIR = "cornerstone_plots"
BSIZE_SP = 512
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


def makeResultDirectory(path: str, sim: str, subsim=None):
    """Checks if the required result directory structure is present. If not, the required folders are made."""
    result_root = Path(os.path.join(Path(path), RESULT_DIR))
    # Check if root result directory exists
    if not os.path.isdir(result_root):
        os.mkdir(result_root)

    # Check if simulation directory exists within results directory
    sim_dir = Path(os.path.join(result_root, sim))
    destination = sim_dir
    if not os.path.isdir(sim_dir):
        os.mkdir(sim_dir)
        destination = sim_dir
    
    # Optional: user can make subdirectory within sim directory. Useful when sorting on different parameters
    # Check if subsimulation directory exists within simulation directory
    if subsim is not None:
        subsim_dir = Path(os.path.join(sim_dir, subsim))
        destination = subsim_dir
        if not os.path.isdir(sim_dir):
            os.mkdir(sim_dir)
    
    return destination
            

