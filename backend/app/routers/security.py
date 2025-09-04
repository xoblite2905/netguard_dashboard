# backend/app/routers/security.py
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.dependencies import get_db
from app import models, schemas
from app.services import evasive_scanner



router = APIRouter()

@router.get("/alerts", response_model=List[schemas.SecurityAlertSchema])
def get_all_security_alerts(db: Session = Depends(get_db)):
    """Retrieve all security alert records from the database."""
    alerts = db.query(models.SecurityAlert).order_by(models.SecurityAlert.timestamp.desc()).limit(100).all()
    return alerts


@router.post("/scan/evasive/{target_ip}")
def start_evasive_scan(target_ip: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Triggers a special Nmap scan with evasion techniques to test IDS/IPS.
    This is a non-blocking background task.
    """
    background_tasks.add_task(evasive_scanner.run_evasive_scan, target_ip)
    return {"message": "IDS Evasion Test initiated in background. Check service logs for results.", "target": target_ip}