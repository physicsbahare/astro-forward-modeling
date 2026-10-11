"""Explicit semantic compatibility for unchanged numerical truth controls.

Retain original checkpoint paths/hashes and original code snapshots. Only truth
rendering invariance, identical geometry/context and unchanged raw PSFs permit
reuse. Fitting-code improvements cannot silently recalculate science receipts.
"""
from pathlib import Path
import ast,json,hashlib
from gold91_recovery_audit import sha,atomic_json
FIELDS=('source_id','model','theta','z_source','tile','x_image','y_image','single_native_ref_band','bd_native_ref_band','frozen_context')
def geometry_equal(a,b):
    return all(a.get(k)==b.get(k) for k in FIELDS)
def definitions(path,names):
    tree=ast.parse(Path(path).read_text())
    return {n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names}
def inherit(project,previous,bundle,controls,out):
    project=Path(project);previous=Path(previous);bundle=Path(bundle);controls=Path(controls);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    repo=project/'astro-forward-modeling';old=json.loads((previous/'input_manifest.json').read_text());new=json.loads((bundle/'input_manifest.json').read_text())
    for p,digest in old['inputs'].items():
        if Path(p).suffix in {'.psf','.h5','.fits','.csv','.ipynb','.txt'} and new['inputs'].get(p)!=digest:raise RuntimeError(f'Raw/control dependency changed: {p}')
    snapshot=previous/'source_snapshots'
    kernel=snapshot/'corrected_four_stage.py';driver=snapshot/'run_corrected_four_stage.py'
    for archived in [kernel,driver]:
        if sha(archived)!=old['inputs'][str(repo/'scripts'/archived.name)]:raise RuntimeError('Original code snapshot does not match manifest')
    if definitions(kernel,{'render_truth','adaptive_numerics'})!=definitions(repo/'scripts/corrected_four_stage.py',{'render_truth','adaptive_numerics'}):raise RuntimeError('Truth rendering changed')
    if definitions(driver,{'native_psf'})!=definitions(repo/'scripts/run_corrected_four_stage.py',{'native_psf'}):raise RuntimeError('Native PSF construction changed')
    prev={r['source_id']:r for r in json.loads((previous/'models.json').read_text())};cur={r['source_id']:r for r in json.loads((bundle/'models.json').read_text())}
    source=json.loads((controls/'sampling_manifest.json').read_text())
    if source['models_sha256']!=sha(previous/'models.json'):raise RuntimeError('Source sampling model identity mismatch')
    code=repo/'scripts/check_truth_sampling.py'
    fp=hashlib.sha256(json.dumps(dict(models_sha=sha(bundle/'models.json'),code_sha=sha(code),inputs=new['fingerprint']),sort_keys=True).encode()).hexdigest()
    header=out/'sampling_manifest.json'
    if header.exists() and json.loads(header.read_text())['fingerprint']!=fp:raise RuntimeError('Destination identity changed')
    atomic_json(header,dict(fingerprint=fp,models_sha256=sha(bundle/'models.json'),code_sha256=sha(code)))
    receipts=[]
    for p in sorted(controls.glob('sampling_ID*.json')):
        saved=json.loads(p.read_text())
        if saved['fingerprint']!=source['fingerprint']:raise RuntimeError('Stale original control')
        oid=saved['rows'][0]['source_id']
        if not geometry_equal(prev[oid],cur[oid]):raise RuntimeError(f'Source geometry/context changed: {oid}')
        dest=out/p.name
        if dest.exists():continue
        saved['original_fingerprint']=saved['fingerprint'];saved['fingerprint']=fp
        saved['inherited_checkpoint']=dict(path=str(p),sha256=sha(p),reason='Unchanged rendering/PSFs/geometry; frozen-context lookup adds previously absent cases only; fit instrumentation does not enter truth image generation')
        atomic_json(dest,saved);receipts.append(dict(source_id=oid,original_path=str(p),original_sha256=sha(p)))
    audit=out/'compatibility_receipt.json'
    history=json.loads(audit.read_text()).get('inheritance_batches',[]) if audit.exists() else []
    history.append(receipts)
    atomic_json(audit,dict(fingerprint=fp,source_bundle=str(previous),source_controls=str(controls),rendering_AST_identical=True,native_PSF_AST_identical=True,inheritance_batches=history))
    print('INHERITED',len(receipts),'numerical controls; no fitting or rendering repeated')
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--project',type=Path,required=True);p.add_argument('--previous',type=Path,required=True);p.add_argument('--bundle',type=Path,required=True);p.add_argument('--controls',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();inherit(a.project,a.previous,a.bundle,a.controls,a.output)
