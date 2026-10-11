"""Publication diagnostics with explicit numerical-rejection scope."""
from pathlib import Path
import pandas as pd,numpy as np,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from gold91_recovery_audit import atomic_json,sha

def plot(bundle):
    bundle=Path(bundle);root=bundle/'identifiability/ID732291';out=bundle/'figures';out.mkdir(exist_ok=True)
    data=pd.read_csv(root/'fitted_numerics/fitted_component_numerics.csv')
    points=pd.read_csv(root/'same_data_structure_comparison.csv')
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for index,color,label in [(0,'#2166ac','Disk'),(1,'#b2182b','Bulge')]:
        a=data.loc[data.component==index]
        axes[0].scatter(a.minor_radius_arcsec,a.relative_l2_32_vs_128,color=color,label=label,s=42)
    axes[0].axhline(.001,color='black',ls=':',label='Frozen numerical tolerance')
    axes[0].set(xscale='log',yscale='log',xlabel='Fitted minor-axis radius (arcsec)',ylabel='Relative component-image error (32 vs 128)')
    axes[0].legend(fontsize=8)
    axes[1].scatter(points.bt_after_same_data_linear_solve,points.delta_chi2_to_best_saved_structure,color='#b2182b',marker='x',s=70)
    axes[1].axvline(.5,color='black',ls=':');axes[1].set(xlabel='Point B/T on the same scene',ylabel=r'$\Delta\chi^2$ to best saved structure',title='Numerically rejected solutions')
    fig.suptitle('ID732291: fitted bulge sampling failure, not a physical class change',fontsize=11);fig.tight_layout()
    for ext in ['pdf','png']:fig.savefig(out/f'ID732291_numerical_rejection.{ext}',dpi=300,bbox_inches='tight')
    plt.close(fig)
    atomic_json(out/'figure_manifest.json',dict(input_paths={str(p):sha(p) for p in [root/'fitted_numerics/fitted_component_numerics.csv',root/'same_data_structure_comparison.csv']},code_sha256=sha(Path(__file__)),
        caption='Four saved decompositions, with linear amplitudes re-solved on one analytic-total scene. Bulge component images fail the frozen numerical tolerance by factors520–947 at32 sampling. Delta-chi2 values on that grid are not confidence intervals; none of these B/T values is promoted into a validated class. Disk components are substantially more stable.'))
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--bundle',type=Path,required=True);a=p.parse_args();plot(a.bundle)
