# waterpix-backend

## IMPORTANT
**waterpix-backend** and **waterpix-frontend** repositories are working together, make sure you download them both locally to your home directory.
## Configuration steps:
1. Create and activate virtual environment with conda:

`conda env create -f environment.yml`

`conda activate py39waterpix`

If you want to install any new package:
- install it with conda e.g. `conda install -c conda-forge black`
- update `environment.yml`

`conda env export | findstr -v "prefix" > environment.yml`

- update virtual environment with .yml file

`conda env update --file environment.yml --prune`

2. Configure `settings.py` file

3. Create PostgreSQL database (you must have it locally installed):

`python -m tools.create_database`

4. Start API: 
- if you want to **develop our API**:

`python -m tools.start_api -dev`

- if you want to **use it for other services**:

`python -m tools.start_api -prod`

## Formatting files
For formatting your files, please use black library e.g. `black .\tools\create_database\cli.py`
