
## Code structure
cornerstone/
├── pyproject.toml
└── src/
    └── cornerstone/
        ├── __init__.py
        ├── cli.py
        ├── core/
        │   ├── __init__.py
        │   ├── io.py
        │   └── parser.py
        └── scripts/
            ├── __init__.py
            ├── gm_analysis.py
            └── gain_analysis.py

Main idea: one centralised dataframe is created, collecting all the relevant results
The visualiser can afterwards filter through this dataframe
Example table:
path,type,corner,temp,vdd,mc_iter,gm,gain
...raw,etc,Kff,Th,190,None,1.2e-4,15.2
...raw,mc,Kttmm,Tt,110,1,0.8e-4,12.1
...raw,mc,Kttmm,Tt,110,2,0.82e-4,12.3