"""Core entry point retained as a small, deterministic wrapper around native COM renderer."""
import os, subprocess, sys
def render_pages(renderer, pages, output):
    for p in pages:
        subprocess.check_call([sys.executable,renderer,'--page',p,'--output',output],cwd=os.path.dirname(os.path.dirname(renderer)))
