"""Check the frozen F03 v1 record; revisions belong in a new directory."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
folder = root / 'web/evidence/f03/v1'
manifest = folder / 'manifest.json'
EXPECTED_MANIFEST = 'f20fb4b385bc7c2d4179ac0eb7ae8bea1836eec7220c7b3abc01b9492be43026'
assert hashlib.sha256(manifest.read_bytes()).hexdigest() == EXPECTED_MANIFEST, 'Frozen manifest changed; create a new version instead'
record = json.loads(manifest.read_text(encoding='utf-8'))
assert record['review_status'] == 'awaiting_claude'
for entry in record['files']:
    path = folder / entry['path']
    assert path.parent == folder
    assert hashlib.sha256(path.read_bytes()).hexdigest() == entry['sha256'], f'Frozen file changed: {path.name}'
print('PASS: F03 v1 manifest and all frozen documents are intact.')
