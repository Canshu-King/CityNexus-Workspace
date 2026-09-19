# codex-chatgpt-web setup notes for the CityNexus workstation

Target reviewed upstream:

```text
repository: miuuyy/codex-chatgpt-web
release: v5.0.4
platform: Windows x64
```

## Do not switch the route inside an active Codex task

`codex-chatgpt-web` becomes the owner of Codex's `openai_base_url`.  Install it
only after the current Codex task has produced its review package.

Before setup, preserve the existing Codex configuration:

```powershell
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backup = "D:\moodle\CityNexus-Tools\codex-route-backup-$stamp"
New-Item -ItemType Directory -Force -Path $backup | Out-Null

if (Test-Path "$env:USERPROFILE\.codex\config.toml") {
    Copy-Item "$env:USERPROFILE\.codex\config.toml" "$backup\config.toml"
}

git -C D:\moodle\CityNexus status --short | Out-File "$backup\citynexus-git-status.txt"
```

## Pinned launcher installation

Use the exact reviewed release instead of an unpinned `latest` install:

```powershell
$env:CODEX_WEB_GPT_VERSION = "5.0.4"
irm https://github.com/miuuyy/codex-chatgpt-web/releases/download/v5.0.4/install-launcher.ps1 | iex
```

The reviewed installer downloads the Windows x64 release binary, downloads
`checksums.txt`, verifies the binary SHA-256, installs per-user, and launches
Codex Web GPT.

## First-use recommendation

For CityNexus, start with **Zero Risk** rather than automatic browser control.

Reason: Zero Risk keeps the Codex harness available but requires you to choose
the ChatGPT model/effort and paste/send manually. It removes the risk specific
to automated manipulation of the ChatGPT page. It does not make every account
or network risk disappear.

Use the launcher's guided setup. The manual connector identity is:

```text
Codex Zero Risk
```

Automatic Full Harness uses:

```text
Codex Native2
```

Automatic and Zero Risk use separate tunnel/connector identities.

## CityNexus smoke test before write access

Use a fresh Codex task and a disposable test directory. Prove, in order:

1. the ChatGPT Web model row appears;
2. a read-only prompt completes;
3. the full harness can read one harmless local YAML file;
4. shell/Python read-only execution works;
5. Visio MCP can perform `list_shapes` / `read_shape_data` on a smoke-test file.

Only after all five pass should a Web-backed model be allowed to modify a copy
of a VSDX. Do not point the first write test at the frozen CityNexus baseline.

If setup must be removed, use the launcher's **Remove Codex integration**
before uninstalling so the previous Codex route is restored.
