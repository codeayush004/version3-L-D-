from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import (
    auth, batches, interns, subjects, scores, feedback, reports, excel, chat, debug, manager_sheet, attempts, settings
)

app = FastAPI(title="L&D Platform API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(batches.router)
app.include_router(interns.router)
app.include_router(subjects.router)
app.include_router(scores.router)
app.include_router(feedback.router)
app.include_router(reports.router)
app.include_router(excel.router)
app.include_router(chat.router)
app.include_router(debug.router)
app.include_router(manager_sheet.router)
app.include_router(attempts.router)
app.include_router(settings.router)

@app.get("/")
async def index():
    return {"status": "ok", "message": "L&D Platform API is live."}

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "Backend is running with modular architecture"}
