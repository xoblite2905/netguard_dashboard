#!/bin/bash

# Directory where Suricata drops PCAP files
PCAP_DIR="/pcaps"
# Directory to store Zeek logs
LOG_DIR="/opt/zeek/logs"
# Directory to move processed PCAPs to
PROCESSED_DIR="/pcaps/processed"

# THE FIX: Define the full path to the Zeek executable
ZEEK_CMD="/opt/zeek/bin/zeek"

echo "PCAP processing script started. Watching ${PCAP_DIR} for files..."

mkdir -p "${PROCESSED_DIR}"

while true; do
  echo "Scanning for completed PCAP files..."
  find "${PCAP_DIR}" -maxdepth 1 -type f -name "suricata.pcap.*" -mmin +0.25 -print0 | while IFS= read -r -d $'\0' file; do
    echo "Found PCAP file: ${file}"
    # Use the full path variable to run Zeek
    ${ZEEK_CMD} -r "${file}" local.zeek

    if [ $? -eq 0 ]; then
      echo "Successfully processed ${file} with Zeek."
      mv "${file}" "${PROCESSED_DIR}/"
    else
      echo "ERROR: Zeek failed to process ${file}. It will be moved to an 'errored' directory."
      mkdir -p "${PROCESSED_DIR}/errored"
      mv "${file}" "${PROCESSED_DIR}/errored/"
    fi
  done
  echo "Scan complete. Waiting for 15 seconds before the next scan."
  sleep 15
done