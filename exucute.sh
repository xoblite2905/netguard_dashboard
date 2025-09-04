#!/bin/bash
# Exit immediately if a command exits with a non-zero status.
set -e

# --- (The update_env_var function and ASCII art are unchanged) ---
update_env_var() {
  local var_name=$1
  local var_value=$2
  if ! grep -q "^${var_name}=" .env; then
    echo "${var_name}=${var_value}" >> .env
  else
    sed -i "/^${var_name}=/c\\${var_name}=${var_value}" .env
  fi
}
# --- (ASCII art section) ---
clear
figlet -c "Welcome"
figlet -c "To"
toilet -f big -F gay "CybReon"
echo ">>> Disrupt. Expose. Prevail. <<<"

# --- Stage 1: System Configuration ---
echo "--- Stage 1: Configuring System Environment ---"
> .env
echo "INFO: Cleared previous .env file."

INTERFACE=$(ip -4 route ls | grep default | grep -Po '(?<=dev )(\S+)' | head -1)
[ -z "$INTERFACE" ] && { echo "ERROR: Could not automatically detect network interface. Exiting."; exit 1; }
update_env_var "IFACE" "$INTERFACE"
echo "INFO: Network interface configured as ${INTERFACE}."

# --- ADD THE FOLLOWING BLOCK ---
echo "INFO: Dynamically setting interface in suricata.yaml to '${INTERFACE}'..."
# This command replaces the value of 'interface:' in suricata.yaml
sed -i "s/^\(\s*interface:\s*\).*/\1${INTERFACE}/" suricata.yaml
echo "INFO: suricata.yaml has been updated."
# --- END OF NEW BLOCK ---

SCAN_TARGET_CIDR=$(ip -o -f inet addr show "$INTERFACE" | awk '/scope global/ {print $4}' | head -1)
[ -z "$SCAN_TARGET_CIDR" ] && { echo "ERROR: Could not automatically detect network CIDR. Exiting."; exit 1; }
update_env_var "SCAN_TARGET_CIDR" "$SCAN_TARGET_CIDR"
echo "INFO: LAN scan target automatically configured as ${SCAN_TARGET_CIDR}."


# --- Stage 2: Unified Credentials and App Configuration ---
echo ""
echo "--- Stage 2: Unified Credentials and App Configuration ---"
DB_USER="netguard_user"
DB_NAME="netguard_db"

read -s -p "Create the MASTER password for PostgreSQL & MISP Databases: " MASTER_PASSWORD
echo ""
read -s -p "Confirm the MASTER password: " MASTER_PASSWORD_CONFIRM
echo ""
[ "$MASTER_PASSWORD" != "$MASTER_PASSWORD_CONFIRM" ] && { echo "ERROR: Passwords do not match. Please run again."; exit 1; }

echo "INFO: Saving ALL required configuration to .env file..."
update_env_var "POSTGRES_USER" "$DB_USER"
update_env_var "POSTGRES_DB" "$DB_NAME"
update_env_var "POSTGRES_PASSWORD" "$MASTER_PASSWORD"

update_env_var "DB_HOST" "postgres_db"
update_env_var "DB_PORT" "5432"
update_env_var "DB_DRIVER" "pg8000"
update_env_var "ELASTICSEARCH_URI" "http://elasticsearch:9200"

ENCODED_PASSWORD=$(echo "$MASTER_PASSWORD" | sed -e 's|%|%25|g' -e 's|:|%3A|g' -e 's|/|%2F|g' -e 's|?|%3F|g' -e 's|&|%26|g' -e 's|=|%3D|g' -e 's|+|%2B|g' -e 's| |%20|g' -e 's|#|%23|g' -e 's|@|%40|g')
DATABASE_URL_VALUE="postgresql+pg8000://${DB_USER}:${ENCODED_PASSWORD}@postgres_db:5432/${DB_NAME}"
update_env_var "DATABASE_URL" "$DATABASE_URL_VALUE"


# --- Host Preparation Stage ---
echo ""
echo "--- Preparing Host System ---"
echo "INFO: Checking for and disabling any conflicting host services..."
if command -v systemctl &> /dev/null; then
    sudo systemctl disable --now suricata || true
fi
sudo pkill -f suricata || true
echo "INFO: Host is clean."


# --- Stages 3 & 4: Cleaning and preparing Docker environment ---
echo ""
echo "--- Stages 3 & 4: Cleaning and preparing Docker environment... ---"
if ! docker-compose --env-file .env down -v --remove-orphans; then
    echo "Notice: 'docker-compose down' reported an error. This is normal on the first run."
fi
docker volume prune -f
echo "--- Stage 4.5: Ensuring a clean packet stream directory... ---"
rm -rf ./packet_stream && mkdir -p ./packet_stream


# --- Stage 5: Building and starting all Docker services ---
echo ""
echo "--- Stage 5: Starting services in sequence to ensure stability ---"
export COMPOSE_HTTP_TIMEOUT=180

# Step 1: Start dependencies.
echo "INFO: Starting database and Elasticsearch services..."
docker-compose --env-file .env up -d db elasticsearch

# Step 2: Wait for dependencies to be healthy. This is the corrected loop.
echo "INFO: Waiting for dependencies to initialize (this may take up to a minute)..."
while [ -z "$(docker-compose ps -a | grep 'postgres_db' | grep '(healthy)')" ] || [ -z "$(docker-compose ps -a | grep 'elasticsearch' | grep '(healthy)')" ]; do
    printf "."
    sleep 5
done
echo ""
echo "✅ SUCCESS: Database and Elasticsearch are healthy."

# Step 3: Force-rebuild the custom services to bypass any broken cache.
echo "INFO: Force-rebuilding custom services to bypass cache..."
docker-compose --env-file .env build --no-cache zeek netguard_app packet-streamer

# Step 4: Start all remaining services.
# The '--no-build' flag prevents an unnecessary second build.
echo "INFO: Starting all remaining application services..."
if ! docker-compose --env-file .env up -d --no-build; then
    echo "ERROR: Docker Compose failed to start the main application stack. Please check the logs."
    exit 1
fi

echo ""
echo "✅✅✅ Deployment complete! Suricata and Zeek are running in parallel."