# backend/app/services/evasive_scanner.py
import subprocess
import logging
from datetime import datetime, timezone

# --- ADDITIONS FOR AUTOMATION START ---
import time
import threading
import random
from app.state import app_state
# --- ADDITIONS FOR AUTOMATION END ---

from . import ids_query_service

logger = logging.getLogger(__name__)


def run_evasive_scan(target_ip: str):
    """
    Runs a special Nmap scan designed to bypass IDS and test its effectiveness.
    Uses the new ids_query_service to check for alerts.
    """
    logger.warning(f"⚠️  Starting IDS Evasion Test against {target_ip}. This scan is INTENTIONALLY noisy and deceptive.")

    command = [
        "nmap", "-sS", "--script=vuln", "-f", "--mtu", "16", "-D", "RND:10",
        "--source-port", "53", "--data-length", "25", "-T2", "-Pn", target_ip
    ]

    logger.info(f"Executing Evasive Scan Command: {' '.join(command)}")
    scan_start_time = datetime.now(timezone.utc)

    try:
        # Give the scan a generous timeout of 30 minutes
        subprocess.run(command, capture_output=True, text=True, timeout=1800)
    except subprocess.TimeoutExpired:
        logger.error(f"Evasive scan against {target_ip} timed out.")
    finally:
        scan_end_time = datetime.now(timezone.utc)
        logger.info(f"Evasive scan on {target_ip} complete. Checking for IDS alerts...")
        _check_for_ids_alerts(target_ip, scan_start_time, scan_end_time)


def _check_for_ids_alerts(target_ip: str, start_time: datetime, end_time: datetime):
    """
    Queries Elasticsearch via the new service to see if Suricata logged any alerts.
    """
    alerts = ids_query_service.query_alerts_by_ip_and_time(target_ip, start_time, end_time)

    if alerts:
        alert_signatures = {alert.get('alert', {}).get('signature', 'N/A') for alert in alerts}
        logger.info(f"✅ EVASION FAILED (GOOD!): Suricata detected the scan. {len(alerts)} alerts generated. Signatures: {alert_signatures}")
    else:
        logger.error(f"❌ EVASION SUCCESSFUL (BAD!): Suricata did NOT detect the evasive scan against {target_ip}. Your IDS has a blind spot or there's a pipeline delay.")

# --- ADDITIONS FOR AUTOMATION START ---

def start_automated_evasion_scanner():
    """
    Initializes and starts the periodic evasive scanner in a separate, daemonized thread.
    """
    def evasion_scanner_loop():
        # A brief pause at startup to allow host discovery to run first
        time.sleep(120) 
        while True:
            active_ips = app_state.active_host_ips
            if not active_ips:
                logger.info("Automated Evasion Scan: No active hosts found to target. Skipping this cycle.")
            else:
                target_ip = random.choice(active_ips)
                logger.info(f"Automated Evasion Scan: Randomly selected '{target_ip}' for IDS/IPS stress test.")
                run_evasive_scan(target_ip)

            # Sleep for 4 hours before the next automated scan
            logger.info("Automated evasion scanner is sleeping for 4 hours.")
            time.sleep(14400) # 4 hours * 60 minutes * 60 seconds

    logger.info("Initializing automated IDS/IPS evasion scanner thread...")
    scanner_thread = threading.Thread(target=evasion_scanner_loop, daemon=True)
    scanner_thread.start()
    logger.info("✅ Automated evasion scanner thread is now running.")
# --- ADDITIONS FOR AUTOMATION END ---