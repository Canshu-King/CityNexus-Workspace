# CityNexus preview operations — fixed entry

This branch replaces quick-tunnel URL roulette with one named Cloudflare Tunnel and one recorded public hostname.

## Boundary

This repository contains no Cloudflare token, tunnel credential JSON, Basic-auth secret, AI key, or private database.

A one-time Cloudflare-account bootstrap must be executed on the machine/account that owns the tunnel:

cloudflared tunnel login
cloudflared tunnel create citynexus-preview
cloudflared tunnel route dns citynexus-preview <fixed-preview-hostname>

Then copy preview-ops/cloudflared.named-tunnel.example.yml to a local, untracked config path and fill in the tunnel UUID, credentials-file path, and fixed hostname.

Do not use trycloudflare.com for the Mission 003 user preview.

## Runtime chain

fixed hostname -> named cloudflared tunnel -> 127.0.0.1:4782 auth proxy -> 127.0.0.1:4781 production preview -> 127.0.0.1:8781 backend

There must be exactly one public tunnel process for this preview.

## Start

powershell -ExecutionPolicy Bypass -File preview-ops/start-named-tunnel.ps1 -ConfigPath "D:\\moodle\\run\\cloudflared-citynexus.yml" -PublicHost "preview.example.com"

The launcher refuses a second tunnel when its PID file points to a live cloudflared process. It records the active public hostname in run/preview_endpoint.txt, so handoff never depends on memory.

## Stop

powershell -ExecutionPolicy Bypass -File preview-ops/stop-named-tunnel.ps1

The stop script kills only the PID written by the launcher. It never enumerates multiple cloudflared processes and guesses which one belongs to the user.

## Health gate

powershell -ExecutionPolicy Bypass -File preview-ops/check-preview.ps1

Expected anonymous status for /api/v1/health, /v8/live, and /manifest.webmanifest is 401. Anonymous 200 is a security regression. Transport failure means the preview is down.

Authenticated 200 checks remain a runtime-operator action because credentials are intentionally absent from this repository.

## Single-entry rule

Do not open a second public ingress for the same preview credentials. If the fixed hostname changes, update the local tunnel config and run/preview_endpoint.txt together, then retire the old route before declaring the replacement active.

## Ownership

GitHub is the source of truth for scripts and runbook. The local Commander remains the execution hand for starting/stopping the process because this GitHub-side environment has no access to the user's Windows process table or Cloudflare account. That is an environment boundary, not a request to keep manually managing URLs.