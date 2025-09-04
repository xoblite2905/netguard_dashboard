# backend/app/services/port_scanner.py

import logging
import nmap
from datetime import datetime, timezone
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from app.database import SessionLocal
from app.models import Host, NetworkPort

logger = logging.getLogger(__name__)

def scan_ports():
    nm = nmap.PortScanner()
    db = SessionLocal()

    try:
        stmt = select(Host).where(Host.status == 'up').options(joinedload(Host.ports))
        hosts = db.scalars(stmt).unique().all()

        for host in hosts:
            logger.info(f"🔍 Scanning ports on {host.ip_address}...")
            try:
                nm.scan(hosts=host.ip_address, arguments='-sS -sU -T4 -Pn --top-ports 100')
                
                # Check if host results exist before trying to access them
                if host.ip_address not in nm.all_hosts():
                    logger.warning(f"No scan results for {host.ip_address}. It might be down.")
                    continue

                # --- THIS IS THE FIX ---
                # Changed nm.get() to the correct dictionary access nm[]
                result = nm[host.ip_address]
                tcp_ports = result.get('tcp', {})
                udp_ports = result.get('udp', {})

                existing_ports = {(p.port_number, p.protocol): p for p in host.ports}

                def process_ports(ports_dict, protocol):
                    for port_num_str, data in ports_dict.items():
                        if data.get('state') != 'open':
                            continue
                        
                        port_num = int(port_num_str)
                        service = f"{data.get('product', '')} {data.get('version', '')}".strip() or data.get('name', 'unknown')
                        
                        if (port_num, protocol) not in existing_ports:
                            new_port = NetworkPort(
                                port_number=port_num,
                                protocol=protocol,
                                service_name=service,
                                timestamp=datetime.now(timezone.utc),
                                host_id=host.id
                            )
                            db.add(new_port)
                        else:
                            existing_port = existing_ports[(port_num, protocol)]
                            existing_port.timestamp = datetime.now(timezone.utc)
                
                process_ports(tcp_ports, 'tcp')
                process_ports(udp_ports, 'udp')

                db.commit()
                logger.info(f"✅ Port scan complete for {host.ip_address}")

            except Exception as e:
                logger.error(f"Error scanning ports for {host.ip_address}: {e}", exc_info=True)
                db.rollback()
    finally:
        db.close()