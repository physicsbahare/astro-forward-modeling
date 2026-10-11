import ast,json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import pandas as pd
import run_corrected_four_stage as driver
class ResumeTests(unittest.TestCase):
    def test_existing_context_error_is_never_retried(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);bundle=root/'bundle';bundle.mkdir();out=root/'out'
            (bundle/'input_manifest.json').write_text(json.dumps({'inputs':{},'fingerprint':'synthetic_unit_fixture'}))
            (bundle/'models.json').write_text(json.dumps([{'source_id':123,'status':'OK','frozen_context':{'tile':'A1','context_id':1}}]))
            old=pd.DataFrame(columns=['source_id','context_tile','context_id'])
            contexts=pd.DataFrame([{'tile':'A1','context_id':1}])
            hist=pd.DataFrame(columns=['source_id','context_tile','context_id','evolution'])
            def tables(path,*args,**kwargs):
                name=Path(path).name
                return contexts if name=='context_manifest.csv' else hist if name=='real_background_pilot.csv' else old
            with patch.object(driver.pd,'read_csv',side_effect=tables),patch.object(driver,'adapters',return_value={'FIT_DIR':out/'fit_products'}),patch.object(driver,'context_psf',side_effect=AssertionError('Do not retry failed context')) as psf:
                run=driver.run
                if os.environ.get('OLD_CONTEXT_DRIVER'):
                    tree=ast.parse(Path(os.environ['OLD_CONTEXT_DRIVER']).read_text());env=dict(driver.__dict__)
                    exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run'],type_ignores=[]),'old_driver','exec'),env);run=env['run']
                run(root,bundle,out,[])
                fp=json.loads((out/'run_manifest.json').read_text())['fingerprint']
                receipt=out/'ID123_CONTEXT.json';receipt.write_text(json.dumps({'source_id':123,'status':'ERROR','fingerprint':fp}))
                original=receipt.read_bytes();run(root,bundle,out,[123])
                psf.assert_not_called();self.assertEqual(original,receipt.read_bytes())
if __name__=='__main__':unittest.main()
