## Instructions
### Setup venv

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Install compatible version of qupath (only needed for scripts)
```bash
mkdir qupath_install qupath_download
paquo get_qupath --install-path qupath_install --download-path
qupath_download 0.3.2
# Do as command says, export env to get qupath for paquo to work
export PAQUO_QUPATH_DIR="..."

### Run script
```bash
ipython domore_to_qupath.py -- --src-dir "/path/to/data"
# ... open QuPath and look!
```

### Export from QuPath
```bash
ipython qupath_to_itn.py
# ... files are in "annotations" folder that is now created
```