"""Check the published v2 bundle, its source figures and preserved version boundary."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.gen2_analysis import analyze

folder = ROOT / 'web/evidence/f03/v2'
manifest_path = folder / 'manifest.json'
EXPECTED_MANIFEST = 'd5a635a55e67513133fa90bff5978df1e2e6ef574dfd12bde101f885f5d56477'
assert hashlib.sha256(manifest_path.read_bytes()).hexdigest() == EXPECTED_MANIFEST, 'Frozen v2 manifest changed'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
for item in manifest['files']:
    file = folder / item['path']
    assert file.parent == folder
    assert hashlib.sha256(file.read_bytes()).hexdigest() == item['sha256'], file.name
assert (folder / 'f03-costs.csv').read_bytes() == (ROOT / 'web/evidence/f03/v1/f03-costs.csv').read_bytes()
calculation = json.loads((folder / 'calculation.json').read_text(encoding='utf-8'))
assert calculation == analyze(folder / 'f03-costs.csv'), 'Published calculation differs from source'
publication = json.loads((folder / 'publication.json').read_text(encoding='utf-8'))
assert publication['calculation'] == calculation
assert publication['proposal_version'] == 'v2' and publication['generation'] == 'gen2'
assert publication['review_status'] == 'awaiting_claude_rereview'
assert publication['completed_handoffs'] == publication['submissions'] == 6
assert publication['rejections'] == 0
assert publication['adjustment'] == 'request_evidence'
assert publication['unseen_test'] is False and publication['model_cost'] is None
assert calculation['totals']['non_volume_variance'] == '37300'
print('PASS: frozen v2, unchanged input, public figures and awaiting re-review state.')
