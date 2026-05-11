# Desktop Electron Build

## Development

```powershell
cd desktop-electron
npm install
npm start
```

Electron will:
- start Python backend (`run_waitress.py`) on `127.0.0.1:5000`
- open `http://127.0.0.1:5000/booking.html`

## Build Python runtime (no Python required on client)

```powershell
cd desktop-electron
npm run runtime:build
```

This creates bundled runtime at:
- `desktop-electron/runtime/python`

When packaged, this runtime is shipped into:
- `resources/python-runtime`

## Build Windows installer

```powershell
cd desktop-electron
npm install
npm run dist
```

For faster rebuild when runtime dependencies are unchanged:

```powershell
npm run dist:quick
```

Output:
- `desktop-electron/dist/PhongKhamDaiAnh-Setup-<version>.exe`

## Notes

- Installer now bundles Python runtime (`python-runtime`) and app source (`app-src`).
- If runtime is missing, app falls back to system Python in PATH.
