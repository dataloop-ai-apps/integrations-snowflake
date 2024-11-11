FROM dataloopai/dtlpy-agent:cpu.py3.10.opencv

RUN pip install --user pandas snowflake-connector-python dtlpy
