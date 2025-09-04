# backend/app/services/host_discovery.py

import logging
import os
import nmap
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import SessionLocal
from app.models import Host

logger = logging.getLogger(__name__)

def discover_hosts():
    if os.geteuid() != 0:
        logger.warning("Host discovery requires root privileges.")
        return

    cidr = os.environ.get("SCAN_TARGET_CIDR")
    if not cidr:
        logger.error("Environment variable SCAN_TARGET_CIDR is not set.")
        return

    logger.info(f"🔍 Discovering hosts in CIDR: {cidr}")
    nm = nmap.PortScanner()
    db = SessionLocal()
    
    try:
        # ### --- START OF CHANGES --- ###
        # Step 1: Mark all existing hosts as 'down' before the scan.
        # This acts as a reset, ensuring only hosts found in this scan will be 'up'.
        logger.info("Setting status of all hosts to 'down' before new scan.")
        db.query(Host).update({"status": "down"})
        # We don't commit yet; the whole scan will be one transaction.

        # Step 2: Run the nmap scan (unchanged)
        scan_args = '-O -T4 -Pn'
        nm.scan(hosts=cidr, arguments=scan_args)

        # Step 3: Fetch existing hosts into a dictionary for quick lookups (unchanged)
        stmt = select(Host)
        existing_hosts = {host.ip_address: host for host in db.scalars(stmt).all()}
        
        # Step 4: Process scan results. Update hosts found back to 'up' or create them.
        for ip in nm.all_hosts():
            host_data = nm[ip]
            hostname = host_data.hostname() or 'N/A'
            mac = host_data['addresses'].get('mac')
            vendor = next(iter(host_data.get('vendor', {}).values()), None)
            os_name = next((match['name'] for match in host_data.get('osmatch', []) if match.get('name')), "Unknown OS")

            host = existing_hosts.get(ip)
            if not host:
                # This is a brand new host
                host = Host(ip_address=ip, first_seen=datetime.now(timezone.utc))
                db.add(host)
            
            # Update details and, most importantly, set status back to 'up'
            host.hostname = hostname
            host.mac_address = mac
            host.vendor = vendor
            host.os_name = os_name
            host.status = 'up' # This host is confirmed to be online
            host.last_seen = datetime.now(timezone.utc)

        # The old comparison loop at the end is no longer needed.
        # ### --- END OF CHANGES --- ###

        db.commit()
        logger.info(f"✅ Host discovery complete. Found {len(nm.all_hosts())} active hosts.")

    except Exception as e:
        logger.error(f"Error during host discovery: {e}", exc_info=True)
        db.rollback() # Rollback all changes if an error occurs
    finally:
        db.close()