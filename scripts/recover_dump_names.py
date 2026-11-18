"""Create original-name copies of an existing Vol3 dumpfiles directory."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.artifact_manager import recover_dump_names

if __name__ == '__main__':
    result = recover_dump_names(sys.argv[1])
    print(json.dumps({key: value for key, value in result.items() if key != 'files'}, ensure_ascii=True))
