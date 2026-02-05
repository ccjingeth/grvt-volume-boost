# GRVT Volume Boost Tool

Self-trade volume boost tool for GRVT perpetuals. It uses two accounts to place opposing trades (hedged) to generate volume while aiming to stay market-neutral.

This repo contains both a GUI and CLI. Authentication is via QR-login sessions (no API keys in `.env`).

## Disclaimer

Trading is risky. Self-trading / wash trading may violate exchange rules and/or local regulations. Use at your own risk.

## Quickstart

### 1) Install

Python 3.10+ recommended.

```bash
pip install -r requirements.txt
python -m playwright install
```

### 2) Run the GUI

```bash
python volume_boost_gui.py
```

## Windows EXE (one-click)

For Windows users, download the latest `GRVTVolumeBoost-windows-x64.zip` from GitHub Releases, unzip it, then run:

- `GRVTVolumeBoost.exe`

The release build bundles Playwright Chromium, so QR login / cookie refresh works without extra setup.

## macOS app (.app bundle)

### Build locally (recommended)

On macOS, you can build and run a native `.app` client:

```bash
./scripts/build_macos.sh
open dist/GRVTVolumeBoost.app
```

Notes:
- First launch may be blocked by Gatekeeper for unsigned apps. Right-click the app and choose `Open`.
- The build script bundles Playwright Chromium into the app so QR login works out of the box.
- On macOS, `Capture QR` uses the native screenshot tool (`screencapture -i`) for region capture.
- On first `Capture QR`, macOS may ask for Screen Recording permission. Allow it and relaunch the app.

### One-command client run (no manual dependency steps)

```bash
./scripts/macos_client.sh run
```

Optional commands:
- `./scripts/macos_client.sh setup`: install dependencies and Chromium only
- `./scripts/macos_client.sh build`: build `.app`
- `./scripts/macos_client.sh doctor`: run preflight checks (accounts, cookies, API, security)
- Double-click `scripts/macos_client.command`: same as `run`

### GitHub Release artifact

This repo now includes a `macos-release` GitHub Actions workflow. Tag builds generate:
- `GRVTVolumeBoost-macos-arm64.zip`
- `GRVTVolumeBoost-macos-x64.zip`

## Chinese

See `README.md`.

### 3) Configure accounts (QR)

- Click `Setup Account`
- For Account 1 and 2, use `Capture QR` (or `Select Image...`) and then `Login`
- If GRVT asks for email verification, the app will prompt you to enter the code

Sessions are saved locally under:
- PROD: `session/`
- TESTNET: `session_testnet/`

These are ignored by git.

## Security Notes

- Do not share `session/`, `session_testnet/`, or `grvt_cookie_cache*.json` (they contain authentication material).
- If you publish logs/screenshots, redact any cookies/session identifiers first.

## Security Hardening (2026-02)

- Session directories are created with user-only permissions (`700`).
- Cookie cache, browser state, and debug logs are restricted to user read/write (`600`).
- Login success messages no longer display cookie prefixes.
- QR capture images are not persisted by default; set `GRVT_SAVE_QR_DEBUG=1` only for troubleshooting.
- Pre-launch acceptance checklist: `MAC_SECURITY_ACCEPTANCE.md`

## Environments (PROD / TESTNET)

The GUI has an `Env` switch (top bar). Switching env restarts the app and uses separate session directories.

Defaults:
- PROD: `trades.grvt.io`, `market-data.grvt.io`, `edge.grvt.io`
- TESTNET: `trades.testnet.grvt.io`, `market-data.testnet.grvt.io`, `edge.testnet.grvt.io`

## Configuration

Copy `.env.example` to `.env` (optional). Most users can run with defaults.

## Notes

- Cookies are refreshed automatically from the stored browser state.
- Orders are signed with an EIP-712 session key stored in `localStorage['grvt_ss_on_chain']` after successful login.

## Developer

- Author: ccjing
- Twitter: <https://x.com/ccjing_eth>
- GRVT referral: <https://grvt.io/?ref=ccjing> (35% fee rebate + 1.3x points)
- Telegram group: <https://t.me/+VAhPSvs7jrxjYTY1>
