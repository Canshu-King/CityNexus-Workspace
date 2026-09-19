"""Compatibility shim; production builds are invoked only through build_phase1.py."""
from legacy.render_phase1_legacy import main
if __name__=='__main__': main()
