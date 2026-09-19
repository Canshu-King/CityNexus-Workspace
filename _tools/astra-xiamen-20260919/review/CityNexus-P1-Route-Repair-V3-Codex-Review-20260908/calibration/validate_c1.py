"""Validate only the freshly rendered Renderer v0.3.1 C1 calibration."""
import json
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

import yaml


HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(HERE, 'out')
VSDX = os.path.join(OUT, 'C1_Font_Style.vsdx')
SVG = os.path.join(OUT, 'C1_Font_Style.raw.svg')
REPORT = os.path.join(OUT, 'C1_Font_Style-report.json')
SAMPLES = {
    'C1-ACTOR-H': 'actorHuman',
    'C1-ACTOR-E': 'actorExternal',
    'C1-UC-DEFAULT': 'useCaseDefault',
    'C1-UC-PLANNING': 'useCasePlanning',
    'C1-UC-COMMERCE': 'useCaseCommerce',
    'C1-CLASS-DEFAULT': 'classDefault',
    'C1-CLASS-JOURNEY': 'classJourney',
    'C1-CLASS-PROJECTION': 'classProjection',
    'C1-CLASS-PLANNING': 'classPlanning',
    'C1-CLASS-COMMERCE': 'classCommerce',
    'C1-CLASS-EVENT': 'classEvent',
}
NS = {'v': 'http://schemas.microsoft.com/office/visio/2012/main'}


def colour(value):
    return str(value).strip().lower()


def expected_style(tokens, ref):
    raw = tokens['shapeStyles'][ref]
    colors = tokens['colors']
    return {
        'fill': colour(colors.get(raw['fill'], raw['fill'])),
        'stroke': colour(colors.get(raw['stroke'], raw['stroke'])),
        'text': colour(colors.get(raw.get('text', 'text'), raw.get('text', 'text'))),
    }


def cell(shape, name):
    node = shape.find("v:Cell[@N='%s']" % name, NS)
    return None if node is None else node.get('V')


def prop(shape, name):
    node = shape.find("v:Section[@N='Property']/v:Row[@N='%s']/v:Cell[@N='Value']" % name, NS)
    return None if node is None else node.get('V')


def font(shape):
    node = shape.find("v:Section[@N='Character']/v:Row[@IX='0']/v:Cell[@N='Font']", NS)
    return None if node is None else node.get('V')


def main():
    tokens = yaml.safe_load(open(os.path.join(ROOT, 'visio-spec', 'style-tokens.yaml'), encoding='utf8'))
    failures = []
    samples = {}
    if not (os.path.exists(VSDX) and os.path.exists(SVG)):
        failures.append('C1 artifacts missing')
    else:
        with zipfile.ZipFile(VSDX) as archive:
            root_xml = archive.read('visio/pages/page1.xml').decode('utf8', 'ignore')
            root = ET.fromstring(root_xml.encode('utf8'))
        shapes = root.findall('.//v:Shape', NS)
        for sid, ref in SAMPLES.items():
            shape = next((s for s in shapes if prop(s, 'SpecId') == sid), None)
            expected = expected_style(tokens, ref)
            actual = {} if shape is None else {
                'styleRef': prop(shape, 'StyleRef'),
                'fill': colour(cell(shape, 'FillForegnd')),
                'stroke': colour(cell(shape, 'LineColor')),
                'text': colour(shape.find("v:Section[@N='Character']/v:Row[@IX='0']/v:Cell[@N='Color']", NS).get('V')) if shape is not None and shape.find("v:Section[@N='Character']/v:Row[@IX='0']/v:Cell[@N='Color']", NS) is not None else None,
                'font': font(shape),
            }
            sample_failures = []
            if actual.get('styleRef') != ref: sample_failures.append('styleRef')
            for key in ('fill', 'stroke', 'text'):
                if actual.get(key) != expected[key]: sample_failures.append(key)
            if actual.get('font') not in ('Segoe UI', 'Aptos'): sample_failures.append('font')
            samples[sid] = {'expected': {'styleRef': ref, **expected}, 'actual': actual, 'failures': sample_failures}
            if sample_failures: failures.append('%s: %s' % (sid, ', '.join(sample_failures)))
        svg = open(SVG, encoding='utf8', errors='ignore').read()
        # Resolve CSS class font-family declarations only for visible text nodes.
        css={m.group(1):m.group(2).strip() for m in re.finditer(r'\.(st\d+)\s*\{[^}]*font-family:([^;}]*)',svg,re.I|re.S)}
        for tm in re.finditer(r'<text[^>]*class="([^"]+)"[^>]*>(.*?)</text>',svg,re.I|re.S):
            family=css.get(tm.group(1).split()[0],'')
            if family and family.lower() not in ('segoe ui','aptos'): failures.append('visible forbidden font '+family)
        for token in ('<linearGradient','<filter','#VALUE!','#REF!'):
            if token.lower() in svg.lower() or token.lower() in root_xml.lower(): failures.append('forbidden '+token)
    result = {
        'calibration': 'C1',
        'artifact': {'vsdx': VSDX, 'svg': SVG},
        'samples': samples,
        'matched': sum(not value['failures'] for value in samples.values()),
        'required': len(SAMPLES),
        'status': 'PASS' if not failures and len(samples) == len(SAMPLES) else 'FAIL',
        'failures': failures,
    }
    with open(REPORT, 'w', encoding='utf8') as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
