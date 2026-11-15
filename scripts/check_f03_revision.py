"""Verify editorial v3 and supplemental evidence; no Gen 3 execution is claimed."""
import json
from fractions import Fraction
from pathlib import Path
from package_f03_revision import probe_revision, sha, lf_sha

ROOT = Path(__file__).resolve().parents[1]
base = ROOT / 'web/evidence/f03'
folder = base / 'v3'
assert sha(folder / 'manifest.json') == 'debe2928d298bae74879f1855862e61bb7b8b38e971013c6de0779398d1e6d93'
manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
assert manifest['parent_manifest_sha256'] == sha(base / 'v2/manifest.json')
for item in manifest['files']:
    path = folder / item['path']
    assert path.parent == folder
    assert sha(path) == item['sha256'], item['path']
publication = json.loads((folder / 'publication.json').read_text(encoding='utf-8'))
assert publication['method_generation'] == 'gen2' and publication['parent'] == 'v2'
assert publication['new_run'] is False and publication['gen3_implemented'] is False
assert publication['review_status'] == 'awaiting_v3_review'
attribution = json.loads((base / 'source-attribution.json').read_text(encoding='utf-8'))
assert attribution['calculation_sha256'] == sha(base / 'v2/calculation.json')
assert attribution['input_sha256'] == sha(base / 'v2/f03-costs.csv')
probe = json.loads((ROOT / 'web/evidence/method-probe/results.json').read_text(encoding='utf-8'))
for method in attribution['methods']:
    current = lf_sha((ROOT / method['path']).read_bytes())
    assert current == method['sha256_lf']
    assert all(v == current for v in method['commit_blob_sha256_lf'].values())
    if method['path'] in probe['source_sha256_lf']:
        assert current == probe['source_sha256_lf'][method['path']]
assert json.loads((ROOT / 'web/evidence/method-probe/revision-1.json').read_text(encoding='utf-8')) == probe_revision()
c = json.loads((base / 'v2/calculation.json').read_text(encoding='utf-8'))
variance = Fraction(c['totals']['variance'])
volume = c['sensitivity']['effects']['units']
assert (variance - Fraction(volume['max']), variance - Fraction(volume['min'])) == (30500, 38750)
assert Fraction(c['totals']['flex_baseline']) - 100 * 20 == 186000
assert Fraction(c['totals']['actual']) - 186000 == 39300
print('PASS: v3 frozen; equivalent mappings and numeric invariants match; Gen 2 unchanged, Gen 3 design only.')
