# GPT Review Package

先阅读 `GPT-OPINION.md`，再查看 `visio-renderer/calibration/out/P1_UC_ROUTE_REPAIR-WORKLIST.json`。

验证命令：

```powershell
cd visio-renderer
python -m pytest .\tests -q
python .\calibration\validate_p1_route_candidate_v3.py
```

包内 `MANIFEST.json` 为每个文件记录相对路径、大小和 SHA-256。
