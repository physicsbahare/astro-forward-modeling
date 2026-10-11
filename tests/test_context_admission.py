import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from run_corrected_four_stage import context_admission

class ContextAdmissionTests(unittest.TestCase):
    def test_two_bad_pixels_are_masked_not_global_rejection(self):
        sci=np.zeros((51,51));err=np.ones_like(sci);seg=np.zeros_like(sci,int)
        sci[0,0]=np.nan;err[-1,-1]=0
        self.assertFalse(np.all(np.isfinite(sci)&np.isfinite(err)&(err>0)))
        result=context_admission(sci,err,seg)
        self.assertTrue(result['usable']);self.assertEqual(result['bad_pixels'],2)
    def test_invalid_center_and_insufficient_area_fail(self):
        sci=np.zeros((51,51));err=np.ones_like(sci);seg=np.zeros_like(sci,int)
        err[25,25]=0;self.assertFalse(context_admission(sci,err,seg)['usable'])
        err[:]=1;err[:4]=0;self.assertFalse(context_admission(sci,err,seg)['usable'])

if __name__=='__main__':unittest.main()
