# Slack to CSV

Convert a Slack export of JSON files to a single CSV file.

## Prerequisites

- Python 3.12

## Getting started

```command
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the script

If your Slack export is in a Zip file, extract it. Then run the script, passing it the path to the folder where the exported Slack data lives.

```command
python main.py path/to/folder
```

The script will output a file called `output.csv` in the same directory.
