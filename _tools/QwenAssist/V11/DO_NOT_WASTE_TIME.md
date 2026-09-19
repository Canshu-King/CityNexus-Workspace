# What Qwen should NOT waste time on

Do not:
- rerun the entire backend test suite repeatedly;
- re-read old V1-V10 review archives unless needed for one concrete issue;
- generate a new product architecture;
- produce coursework slides/reports;
- create fake live-provider evidence;
- invent API credentials;
- re-document every endpoint;
- rewrite the frontend framework;
- generate huge prose reports where a CSV/table is better;
- modify Git history;
- commit anything;
- claim a GitHub project's license without checking if web/GitHub access is available.

Use the large token budget for breadth and completeness in:
- edge cases;
- test design;
- contract mapping;
- UI state inventory;
- code-location mapping;
- provider semantics;
- candidate helpers.

Codex is the integration engineer.
Qwen is the sidecar analyst/test/UI/research engineer.
