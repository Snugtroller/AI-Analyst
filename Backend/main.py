from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from .report_service import ReportRequest, build_report


load_dotenv()

app = FastAPI(title="AI Report Generator API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post(
    "/api/report",
    responses={
        400: {"description": "Bad Request"},
        500: {"description": "Internal Server Error"},
    },
)
def create_report(request: ReportRequest) -> dict[str, Any]:
    try:
        report = build_report(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {exc}") from exc

    return report


@app.get("/api/report/download")
def download_report(topic: str) -> Response:
    report = build_report(ReportRequest(prompt=topic))
    filename = report["download_filename"]
    content = report["report_markdown"]
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=content, media_type="text/markdown; charset=utf-8", headers=headers)
