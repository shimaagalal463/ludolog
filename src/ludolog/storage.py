import json
from pathlib import Path

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def save(path, data):
    Path(path).write_text(json.dumps(data), encoding='utf-8')
