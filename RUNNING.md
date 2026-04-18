# How to Run Reverie Locally

## What you need installed first
- [Python 3.10+](https://www.python.org/downloads/)
- [VS Code](https://code.visualstudio.com/)
- [Live Server extension](https://marketplace.visualstudio.com/items?itemName=ritwickdey.LiveServer) for VS Code

---

## Step 1 — Clone or download the repo
If you downloaded the ZIP, unzip it and open the `reverie` folder in VS Code.

## Step 2 — Install Python dependencies
Open the VS Code terminal (Terminal → New Terminal) and run:
```bash
pip install -r backend/requirements.txt
```

## Step 3 — Add your API keys
Create a file called `.env` inside the `backend/` folder:
```
GEMINI_API_KEY=your_key_here
ELEVENLABS_API_KEY=your_key_here
```
Get your Gemini key free at: https://aistudio.google.com/app/apikey
Get your ElevenLabs key free at: https://elevenlabs.io

## Step 4 — Start the backend
In the VS Code terminal run:
```bash
uvicorn backend.main:app --reload
```
You should see: `Uvicorn running on http://127.0.0.1:8000`
Leave this terminal running.

## Step 5 — Open the frontend
Right-click `frontend/index.html` in the VS Code file explorer
→ click **"Open with Live Server"**

The app will open in your browser at `http://127.0.0.1:5500`

---

## You should now see:
- The Reverie home screen (night or morning mode depending on your time)
- The bottom nav bar linking to all pages
- The + button to log a dream (connects to Gemini once keys are set)

## If something isn't working
- Make sure the backend terminal is still running (Step 4)
- Make sure you saved your `.env` file with real keys
- Check the browser console (F12) for any error messages
