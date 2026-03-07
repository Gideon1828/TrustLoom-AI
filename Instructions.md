# TrustLoom AI — Developer Commands

## Project Structure

```
TrustLoom-AI/
├── frontend/          → React (Vite) UI
├── api/               → FastAPI backend
├── main.js            → Electron entry point
├── preload.js         → Electron preload script
├── package.json       → Electron + builder config
└── release/win-unpacked/  → Built .exe output
```

---

## 1. Frontend Changes (React UI)

After editing any file inside `frontend/src/`:

```powershell
# Step 1: Rebuild the frontend
cd frontend
npm run build

# Step 2: Run the Electron app (from project root)
cd ..
npm start
```

**One-liner:**

```powershell
cd "D:\IVth Year Project\TrustLoom-AI\frontend"; npm run build; cd ..; npm start
```

> **Note:** You must rebuild (`npm run build`) every time you change frontend code.
> The Electron app loads from `frontend/dist/`, not the live source.

---

## 2. Backend Changes (FastAPI)

After editing any file inside `api/`:

```powershell
# Just restart the backend server — no build step needed
cd "D:\IVth Year Project\TrustLoom-AI"
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

> With `--reload`, the server auto-restarts on file changes.
> No Electron restart or frontend rebuild needed for backend-only changes.

---

## 3. Electron Changes (main.js / preload.js)

After editing `main.js` or `preload.js`:

```powershell
# Just restart Electron — no build needed
cd "D:\IVth Year Project\TrustLoom-AI"
npm start
```

> These files are read directly by Electron at startup. No build step required.

---

## 4. Running the Full Application

You need **two terminals** running simultaneously:

**Terminal 1 — Backend:**

```powershell
cd "D:\IVth Year Project\TrustLoom-AI"
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — Electron App:**

```powershell
cd "D:\IVth Year Project\TrustLoom-AI"
npm start
```

---

## 5. Building the .exe (Desktop Release)

> **Important:** The `.exe` is a snapshot. After making **any** changes (frontend, backend, or Electron), you must rebuild the `.exe` to see those changes in the packaged app. Running `npm start` only previews changes in development mode — it does **not** update the `.exe`.

**Quick rebuild command (run from project root):**

```powershell
cd "D:\IVth Year Project\TrustLoom-AI\frontend"; npm run build; cd ..; $env:CSC_IDENTITY_AUTO_DISCOVERY = "false"; npx electron-builder --win; node -e "const { rcedit } = require('rcedit'); rcedit('release\\win-unpacked\\TrustLoom AI.exe', { icon: 'frontend\\public\\logo.ico' }).then(() => console.log('Icon set!'))"
```

### Step 1: Rebuild frontend

```powershell
cd "D:\IVth Year Project\TrustLoom-AI\frontend"
npm run build
```

### Step 2: Build the Electron .exe

```powershell
cd "D:\IVth Year Project\TrustLoom-AI"
$env:CSC_IDENTITY_AUTO_DISCOVERY = "false"
npx electron-builder --win
```

### Step 3: Stamp custom icon (if needed)

```powershell
node -e "const { rcedit } = require('rcedit'); rcedit('release\\win-unpacked\\TrustLoom AI.exe', { icon: 'frontend\\public\\logo.ico' }).then(() => console.log('Icon set!'))"
```

Output: `release\win-unpacked\TrustLoom AI.exe`

---

## Quick Reference

| What changed | Commands needed |
|---|---|
| Frontend (`frontend/src/`) | `cd frontend && npm run build` → `npm start` |
| Backend (`api/`) | Restart uvicorn (auto with `--reload`) |
| Electron (`main.js`, `preload.js`) | `npm start` |
| Frontend + Electron | `cd frontend && npm run build` → `cd .. && npm start` |
| Build .exe | `cd frontend && npm run build` → `cd .. && npx electron-builder --win` |
