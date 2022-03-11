Pulling nodes metadata from iDRAC

* Initialize virtual environment and install necessary packages: `make init`

* Activate virtual environment: `source env/bin/activate`

* Add configurations in `config.yml`

* Pull nodes metadata: `python scanodes.py`. A nodes_metadata.csv will be generated in the current directory.
