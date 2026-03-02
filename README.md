# L&D Portal

A premium dashboard for L&D managers to track intern performance, manage scores via Excel, and get insights from an AI assistant.

## Tech Stack
- **Frontend**: React (Vite), Vanilla CSS, Lucide icons.
- **Backend**: FastAPI (Python), MongoDB, Groq AI SDK.

## Quick Start (New Device)

If you are setting this up for the first time after cloning:

1.  **Run the Setup Script**:
    ```bash
    chmod +x setup.sh
    ./setup.sh
    ```
2.  **Configure Environment**:
    - Update `backend/.env` with your `MONGO_URI` and `GROQ_API_KEY`.
3.  **Start the Application**:
    - **Backend**: `cd backend && ./venv/bin/python run.py`
    - **Frontend**: `cd frontend && npm run dev`

---

## Manual Setup (If Script Fails)

### Backend
1. Navigate to `backend/`
2. Create virtual environment: `python3 -m venv venv`
3. Activate & Install: `source venv/bin/activate && pip install -r requirements.txt`
4. Create `.env` from template.
5. Run: `python run.py`

### Frontend
1. Navigate to `frontend/`
2. Install: `npm install`
3. Run: `npm run dev`

## Key Features
- **Intern Upload**: Bulk create intern profiles via Excel.
- **Dynamic Score Grid**: Real-time score updates and RAG assessments.
- **External Sync**: Automated feedback extraction from linked Google Sheets.
- **AI Assistant**: Natural language insights based on intern data.
