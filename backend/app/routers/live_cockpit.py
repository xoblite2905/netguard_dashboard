# backend/app/routers/live_cockpit.py (FINAL CORRECTED VERSION)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict, Any
from elasticsearch import Elasticsearch

from app import models
from app import schemas
from app.database import SessionLocal
from app.config import settings

try:
    es = Elasticsearch(settings.ELASTICSEARCH_URI)
    if not es.ping():
        raise ConnectionError("Could not connect to Elasticsearch")
except Exception as e:
    print(f"CRITICAL: Elasticsearch connection failed. API will not work. Error: {e}")
    es = None

# --- ROUTING FIX: REMOVED the prefix from here. main.py will handle it. ---
router = APIRouter(
    tags=["Live Cockpit"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Note: The path is now relative. It will be prefixed by /api/v1/cockpit in main.py
@router.get("/bandwidth", response_model=List[Dict[str, Any]])
def get_live_bandwidth_from_es():
    # ... (function content is unchanged and correct) ...
    if not es: raise HTTPException(status_code=503, detail="Elasticsearch service is not available.")
    query = { "size": 0, "query": { "bool": { "filter": [ { "term": { "log_source": "zeek" } }, { "exists": { "field": "uid" } }, { "range": { "@timestamp": { "gte": "now-60s", "lte": "now" } } } ] } }, "aggs": { "bandwidth_over_time": { "date_histogram": { "field": "@timestamp", "fixed_interval": "1s", "min_doc_count": 0, "extended_bounds": { "min": "now-60s", "max": "now" } }, "aggs": { "ingress_bytes": { "sum": { "field": "resp_ip_bytes" } }, "egress_bytes": { "sum": { "field": "orig_ip_bytes" } } } } } }
    try:
        response = es.search(index="netguard-zeek-*", body=query)
        buckets = response.get('aggregations', {}).get('bandwidth_over_time', {}).get('buckets', [])
        if not buckets: return []
        chart_data = []
        for bucket in buckets:
            ts_seconds = bucket['key'] // 1000
            ingress = bucket.get('ingress_bytes', {}).get('value', 0)
            egress = bucket.get('egress_bytes', {}).get('value', 0)
            chart_data.append({"time": ts_seconds, "in": ingress or 0, "out": egress or 0})
        return chart_data
    except Exception as e:
        print(f"Error querying Elasticsearch for bandwidth: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve bandwidth data from Elasticsearch")

@router.get("/security-posture", response_model=Dict[str, Any])
def get_security_posture():
    # ... (function content is unchanged and correct) ...
    if not es: raise HTTPException(status_code=503, detail="Elasticsearch service is not available.")
    query = { "query": { "bool": { "must": [ { "term": { "log_source": "suricata" } }, { "term": { "suricata.alert.severity": 1 } }, { "range": { "@timestamp": { "gte": "now-24h", "lte": "now" } } } ] } } }
    try:
        response = es.count(index="netguard-suricata-*", body=query)
        critical_alert_count = response.get('count', 0)
        final_score = max(0, 100 - (critical_alert_count * 5))
        return {"health_score": final_score, "critical_alerts_24h": critical_alert_count}
    except Exception as e:
        print(f"Error querying Elasticsearch for security posture: {e}")
        return {"health_score": 100, "critical_alerts_24h": "N/A"}

# I have removed the /hosts and /alerts endpoints from this file as they belong 
# in their respective routers (hosts.py, security.py) according to your main.py file.
# This prevents duplicate API routes.