# Python Installation Guide for Windows

## Problem
Python is not installed or not in your system PATH. You're seeing errors like:
- "Python was not found"
- "pip is not recognized"

## Solution: Install Python

### Step 1: Download Python

1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Click **"Download Python 3.11.x"** (or latest 3.10+)
3. Save the installer

### Step 2: Install Python

1. **Run the installer** (python-3.11.x-amd64.exe)
2. **IMPORTANT:** Check ✅ **"Add python.exe to PATH"** at the bottom
3. Click **"Install Now"**
4. Wait for installation to complete
5. Click **"Close"**

### Step 3: Verify Installation

Open a **NEW** PowerShell window and run:

```powershell
python --version
```

Should show: `Python 3.11.x`

```powershell
pip --version
```

Should show: `pip 23.x.x from ...`

### Step 4: Install Backend Dependencies

```powershell
cd "d:\Final Year Project\trading-software\backend"
pip install -r requirements.txt
```

---

## Alternative: Use Python Launcher

If you have Python installed but `python` command doesn't work, try:

```powershell
py -3 --version
py -3 -m pip install -r requirements.txt
```

---

## Troubleshooting

### "Python was not found"
- Python is not installed
- Solution: Follow Step 1-2 above

### "pip is not recognized"
- Python was installed without adding to PATH
- Solution: Reinstall Python and check "Add to PATH"

### Multiple Python Versions
If you have multiple Python versions:

```powershell
# Use specific version
py -3.11 -m pip install -r requirements.txt
```

---

## After Python is Installed

### Backend Setup

1. **Create virtual environment** (recommended):
```powershell
cd "d:\Final Year Project\trading-software\backend"
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. **Configure environment**:
```powershell
copy .env.example .env
# Edit .env with your Telegram credentials
```

3. **Run backend**:
```powershell
python main.py
```

### Frontend Setup (Already Working)

The frontend is already set up and working! Just run:

```powershell
cd "d:\Final Year Project\trading-software\frontend"
npm run dev
```

---

## Quick Start After Python Installation

```powershell
# Terminal 1 - Backend
cd "d:\Final Year Project\trading-software\backend"
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Edit .env with Telegram credentials
python main.py

# Terminal 2 - Frontend
cd "d:\Final Year Project\trading-software\frontend"
npm run dev
```

Then open: http://localhost:3000

---

## Need Help?

1. **Python not installing?**
   - Make sure you have admin rights
   - Disable antivirus temporarily
   - Download from official python.org only

2. **Still getting errors?**
   - Restart your computer after installing Python
   - Open a NEW terminal window
   - Check Windows Store for Python app conflicts

3. **Want to skip backend for now?**
   - You can run just the frontend to see the UI
   - Backend is needed for actual market scanning
