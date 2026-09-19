"""Build a fresh Phase 1 RC5 document; RC4 is never opened or used as a base."""
import os, sys, subprocess, shutil
import yaml
from presentation import rect_from_center
from routing import load_routes
from style_adapter import apply_style
from class_adapter import apply_class
HERE=os.path.dirname(__file__); ROOT=os.path.abspath(os.path.join(HERE,'..'))
RES=[os.path.join(ROOT,'visio-spec','style-tokens.yaml'),os.path.join(HERE,'render-config.yaml'),os.path.join(HERE,'native-master-map.json'),os.path.join(HERE,'phase1-routing.yaml')]
OUT=os.path.join(ROOT,'visio','CityNexus_Visio_Model_Baseline_v1.0.4_RC5.vsdx')
def main():
    missing=[p for p in RES if not os.path.exists(p)]
    if missing: raise RuntimeError('Renderer resources not loaded: '+', '.join(missing))
    # Startup assertion: all production resources parse successfully.
    yaml.safe_load(open(RES[0],encoding='utf8')); yaml.safe_load(open(RES[1],encoding='utf8')); yaml.safe_load(open(RES[3],encoding='utf8'))
    import json; json.load(open(RES[2],encoding='utf8'))
    os.makedirs(os.path.dirname(OUT),exist_ok=True)
    tmp=OUT+'.new'
    if os.path.exists(tmp): os.remove(tmp)
    for p in ('00_style_guide','p1_uc_overview','p1_domain_overview'):
        subprocess.check_call([sys.executable,os.path.join(HERE,'render_phase1.py'),'--page',p,'--output',tmp],cwd=ROOT)
    os.replace(tmp,OUT)
    print(OUT)
if __name__=='__main__': main()
