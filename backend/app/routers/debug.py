from fastapi import APIRouter, BackgroundTasks
from app.services import evasive_scanner, host_discovery, port_scanner

router = APIRouter()

@router.get("/scan_ports_manual")
def scan_ports_manual():
    port_scanner.scan_ports()
    return {"status": "Scan triggered"}

@router.post("/test/ids/{host_ip}")
def trigger_ids_evasion_test(host_ip: str, background_tasks: BackgroundTasks):
    """
    SAFE ENDPOINT for running an IDS/IPS evasion stress test on a target.
    This runs in the background and does not interfere with normal alert displays.
    """
    background_tasks.add_task(evasive_scanner.run_evasive_scan, host_ip)
    return {"message": f"Evasive IDS scan has been launched against {host_ip}. Monitor app logs for results."}