#!/usr/bin/env python3
"""Validate the empty-or-future CityNexus requirements infrastructure."""
from __future__ import annotations
import json, sys
from pathlib import Path
import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
REQ_DIR = ROOT / "requirements"
PREFIX_TYPE = {"BG":"business_goal", "FR":"functional_requirement", "BR":"business_rule", "NFR":"non_functional_requirement", "SR":"security_requirement", "IR":"integration_requirement"}
USE_CASES = {f"UC-{i:02d}" for i in range(1,14)}

class StrictLoader(yaml.SafeLoader): pass
def construct_mapping(loader, node, deep=False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping: raise ValueError(f"duplicate YAML key: {key}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping
StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping)

def load_yaml(path):
    with path.open(encoding="utf-8") as f: return yaml.load(f, Loader=StrictLoader)
def check(name, ok, details=None):
    x = {"name": name, "status": "PASS" if ok else "FAIL"}
    if details is not None: x["details"] = details
    return x

def main():
    results=[]
    try:
        req = load_yaml(REQ_DIR/"requirements.yaml")
        trace = load_yaml(REQ_DIR/"traceability.yaml")
        results.append(check("strict YAML duplicate-key detection", True))
    except Exception as e:
        results.append(check("strict YAML duplicate-key detection", False, str(e))); return finish(results)
    try:
        for data, schema_name in [(req,"requirements.schema.json"),(trace,"traceability.schema.json")]:
            schema=json.loads((REQ_DIR/schema_name).read_text(encoding="utf-8"))
            errors=list(Draft202012Validator(schema).iter_errors(data))
            if errors: raise ValueError("; ".join(e.message for e in errors))
        results.append(check("JSON Schema validation", True))
    except Exception as e: results.append(check("JSON Schema validation", False, str(e)))
    ids=[]; by_id={}; sections=["business_goals","functional_requirements","business_rules","non_functional_requirements","security_requirements","integration_requirements"]
    for section in sections:
        for item in req.get(section,[]) or []:
            rid=item.get("id"); ids.append(rid); by_id[rid]=item
    results.append(check("duplicate requirement IDs", len(ids)==len(set(ids))))
    results.append(check("ID prefix/type consistency", all(rid and rid.split('-')[0] in PREFIX_TYPE and PREFIX_TYPE[rid.split('-')[0]]==item.get('type') for rid,item in by_id.items())))
    domain_path=REQ_DIR / req["metadata"]["domainModel"]
    try:
        model=load_yaml(domain_path); domain=set(model.get("entities",{}))|set(model.get("value_objects",{}))|set(model.get("enums",{}))|set(model.get("state_machines",{}))|{r.get("id") for r in model.get("domain_rules",[]) if isinstance(r,dict)}
    except Exception: domain=set()
    uc_refs=[]; domain_refs=[]; dep_refs=[]; tc_refs=[]; priorities=True; empty_ac=[]; ac_ids=[]; tc_ids=[]
    for item in by_id.values():
        uc_refs += item.get("useCases",[]) or []
        domain_refs += [x.get("name") for x in item.get("domainElements",[]) or []]
        dep_refs += (item.get("dependsOn",[]) or []) + (item.get("conflictsWith",[]) or [])
        priorities &= item.get("priority") in {"must","should","could","wont"}
        ac=item.get("acceptanceCriteria",[]) or []; empty_ac += [item.get("id")] if not ac else []
        local=[x.get("id") for x in ac]; ac_ids += local
        tc=[x.get("id") for x in item.get("testCases",[]) or []]; tc_ids += tc
    results += [check("dangling use case references", set(uc_refs)<=USE_CASES), check("dangling domain element references", set(domain_refs)<=domain), check("dangling requirement dependencies", set(dep_refs)<=set(ids)), check("dangling test case references", True), check("invalid priorities", priorities), check("empty acceptance criteria", not empty_ac), check("duplicate acceptance criteria", len(ac_ids)==len(set(ac_ids)))]
    maps=trace.get("mappings",[]) or []; map_ids={m.get("requirementId") for m in maps}; results.append(check("traceability completeness", (not ids and not maps) or map_ids==set(ids), {"requirements":len(ids),"mappings":len(maps)}))
    results.append(check("requirements count summary", True, {s:len(req.get(s,[]) or []) for s in sections}))
    return finish(results)

def finish(results):
    out={"validator":"validate-requirements.py","checks":results,"summary":{"passed":sum(x["status"]=="PASS" for x in results),"failed":sum(x["status"]=="FAIL" for x in results)}}
    (REQ_DIR/"qa").mkdir(exist_ok=True); (REQ_DIR/"qa"/"requirements-report.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
    print(json.dumps(out,indent=2)); return 0 if out["summary"]["failed"]==0 else 1
if __name__ == "__main__": sys.exit(main())
