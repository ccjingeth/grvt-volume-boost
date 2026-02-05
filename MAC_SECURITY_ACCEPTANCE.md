# macOS Security Acceptance

## 1) Environment setup

```bash
./scripts/macos_client.sh setup
```

## 2) Preflight doctor

```bash
./scripts/macos_client.sh doctor
```

Pass criteria:
- Two accounts detected
- Two browser state files detected
- Cookie refresh succeeds for both accounts
- API connectivity succeeds
- Security checks all pass (permissions + endpoint host checks)

## 3) QR login flow (screenshot capture)

In GUI (`./scripts/macos_client.sh run`):
- `Setup Account` -> `Capture QR`
- macOS native screenshot crosshair appears
- Select QR region
- QR decode succeeds
- Login succeeds (with email verification if prompted)

## 4) Functional parity checklist

- Env switch works (`PROD` / `TESTNET`)
- Account1/Account2 login + subaccount selection works
- All trading modes run:
  - Open & Instant Close
  - Build, Hold & Close
  - Build & Hold
  - Close Existing
- Monitor window updates positions/order state correctly
- External fill / single-leg risk prompt appears and handles continue/stop

## 5) Packaging and launch

```bash
./scripts/macos_client.sh build
open dist/GRVTVolumeBoost.app
```

Pass criteria:
- App launches and can complete QR login + one dry test cycle in TESTNET.

