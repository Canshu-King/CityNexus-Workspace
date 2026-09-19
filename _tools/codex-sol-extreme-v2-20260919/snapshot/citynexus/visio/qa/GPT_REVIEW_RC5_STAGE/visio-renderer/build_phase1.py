"""Build a fresh Phase 1 RC5 document; RC4 is never opened or used as a base."""
import os, sys, subprocess, shutil
HERE=os.path.dirname(__file__); ROOT=os.path.abspath(os.path.join(HERE,'..'))
OUT=os.path.join(ROOT,'visio','CityNexus_Visio_Model_Baseline_v1.0.4_RC5.vsdx')
def main():
    os.makedirs(os.path.dirname(OUT),exist_ok=True)
    tmp=OUT+'.new'
    if os.path.exists(tmp): os.remove(tmp)
    for p in ('00_style_guide','p1_uc_overview','p1_domain_overview'):
        subprocess.check_call([sys.executable,os.path.join(HERE,'render_phase1.py'),'--page',p,'--output',tmp],cwd=ROOT)
    os.replace(tmp,OUT)
    print(OUT)
if __name__=='__main__': main()
