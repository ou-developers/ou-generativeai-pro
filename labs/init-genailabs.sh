#!/bin/bash

# Define a log file for capturing all output
LOGFILE=/var/log/cloud-init-output.log
exec > >(tee -a $LOGFILE) 2>&1

# Marker file to ensure the script only runs once
MARKER_FILE="/home/opc/.init_done"

# Check if the marker file exists
if [ -f "$MARKER_FILE" ]; then
  echo "Init script has already been run. Exiting."
  exit 0
fi

echo "===== Starting Cloud-Init Script ====="

# Expand the boot volume
echo "Expanding boot volume..."
sudo /usr/libexec/oci-growfs -y

# Enable ol9_addons and install necessary development tools
echo "Installing required packages..."
sudo dnf config-manager --set-enabled ol9_addons
sudo dnf install -y podman git libffi-devel bzip2-devel ncurses-devel readline-devel wget make gcc zlib-devel openssl-devel

# Install the latest SQLite from source
echo "Installing latest SQLite..."
cd /tmp
wget https://www.sqlite.org/2023/sqlite-autoconf-3430000.tar.gz
tar -xvzf sqlite-autoconf-3430000.tar.gz
cd sqlite-autoconf-3430000
./configure --prefix=/usr/local
make
sudo make install

# Verify the installation of SQLite
echo "SQLite version:"
/usr/local/bin/sqlite3 --version

# Ensure the correct version is in the path and globally
export PATH="/usr/local/bin:$PATH"
export LD_LIBRARY_PATH="/usr/local/lib:$LD_LIBRARY_PATH"
echo 'export PATH="/usr/local/bin:$PATH"' >> /home/opc/.bashrc
echo 'export LD_LIBRARY_PATH="/usr/local/lib:$LD_LIBRARY_PATH"' >> /home/opc/.bashrc

# Set environment variables to link the newly installed SQLite with Python build globally
echo 'export CFLAGS="-I/usr/local/include"' >> /home/opc/.bashrc
echo 'export LDFLAGS="-L/usr/local/lib"' >> /home/opc/.bashrc

# Source the updated ~/.bashrc to apply changes globally
source /home/opc/.bashrc

# Create a persistent volume directory for Oracle data
echo "Creating Oracle data directory..."
sudo mkdir -p /home/opc/oradata
echo "Setting up permissions for the Oracle data directory..."
sudo chown -R 54321:54321 /home/opc/oradata
sudo chmod -R 755 /home/opc/oradata

# Run the Oracle Database Free Edition container
echo "Running Oracle Database container..."
sudo podman run -d \
    --name 23ai \
    --network=host \
    -e ORACLE_PWD=database123 \
    -v /home/opc/oradata:/opt/oracle/oradata:z \
    container-registry.oracle.com/database/free:latest

# Wait for Oracle Container to start
echo "Waiting for Oracle container to initialize..."
sleep 20

# --- Wait for CDB root (FREE) ---
# Checking if FREE (CDB root) is registered
echo "$(date '+%Y-%m-%d %H:%M:%S') Checking if FREE (CDB root) is registered..."
MAX_RETRIES=20
for i in $(seq 1 $MAX_RETRIES); do
  if sudo podman exec 23ai lsnrctl status | grep -q "FREE "; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') FREE service is registered with the listener."
    break
  fi
  echo "$(date '+%Y-%m-%d %H:%M:%S') [$i/$MAX_RETRIES] Waiting for FREE service..."
  sleep 10
done

if ! sudo podman exec 23ai lsnrctl status | grep -q "FREEPDB1"; then
  echo "$(date '+%Y-%m-%d %H:%M:%S') FREEPDB1 not registered after $MAX_RETRIES attempts. Forcing it open..."
  sudo podman exec 23ai bash -lc "echo exit | sqlplus -S / as sysdba <<EOF
  ALTER SYSTEM SET LOCAL_LISTENER = '(ADDRESS=(PROTOCOL=TCP)(HOST=127.0.0.1)(PORT=1521))' scope=both;
  ALTER SYSTEM REGISTER;
  ALTER PLUGGABLE DATABASE ALL OPEN;
  ALTER PLUGGABLE DATABASE ALL SAVE STATE;
  EXIT;
EOF"
  echo "$(date '+%Y-%m-%d %H:%M:%S') Forced FREEPDB1 open and saved state. Continuing setup..."
fi


# Run the SQL commands to configure the PDB
echo "Configuring Oracle database in PDB (freepdb1)..."
sudo podman exec -i 23ai bash <<EOF
sqlplus -S / as sysdba <<EOSQL
-- ensure PDB is open and switch context
-- ALTER PLUGGABLE DATABASE FREEPDB1 OPEN IF NOT EXISTS;
ALTER SESSION SET CONTAINER=FREEPDB1;
CREATE BIGFILE TABLESPACE tbs2 DATAFILE 'bigtbs_f2.dbf' SIZE 1G AUTOEXTEND ON NEXT 32M MAXSIZE UNLIMITED EXTENT MANAGEMENT LOCAL SEGMENT SPACE MANAGEMENT AUTO;
CREATE UNDO TABLESPACE undots2 DATAFILE 'undotbs_2a.dbf' SIZE 1G AUTOEXTEND ON RETENTION GUARANTEE;
CREATE TEMPORARY TABLESPACE temp_demo TEMPFILE 'temp02.dbf' SIZE 1G REUSE AUTOEXTEND ON NEXT 32M MAXSIZE UNLIMITED EXTENT MANAGEMENT LOCAL UNIFORM SIZE 1M;
CREATE USER vector IDENTIFIED BY vector DEFAULT TABLESPACE tbs2 QUOTA UNLIMITED ON tbs2;
GRANT DB_DEVELOPER_ROLE TO vector;
EXIT;
EOSQL
EOF

# Reconnect to CDB root to apply system-level changes
echo "Switching to CDB root for system-level changes..."
sudo podman exec -i 23ai bash <<EOF
sqlplus -S / as sysdba <<EOSQL
CREATE PFILE FROM SPFILE;
ALTER SYSTEM SET vector_memory_size = 512M SCOPE=SPFILE;
SHUTDOWN IMMEDIATE;
STARTUP;
-- Re-open PDBs after restart and save state again
ALTER PLUGGABLE DATABASE ALL OPEN;
ALTER PLUGGABLE DATABASE ALL SAVE STATE;
ALTER SYSTEM REGISTER;
EXIT;
EOSQL
EOF

echo "Final listener check:"
podman exec -i 23ai bash -lc "lsnrctl services"

# Wait for Oracle to restart and apply memory changes
sleep 10

echo "Skipping vector_memory_size check. Assuming it is set to 512M based on startup logs."

# Now switch to opc for user-specific tasks
sudo -u opc -i bash <<'EOF_OPC'

# Set environment variables
export HOME=/home/opc
export PYENV_ROOT="$HOME/.pyenv"
curl https://pyenv.run | bash

# Add pyenv initialization to ~/.bashrc for opc
cat << EOF >> $HOME/.bashrc
export PYENV_ROOT="\$HOME/.pyenv"
[[ -d "\$PYENV_ROOT/bin" ]] && export PATH="\$PYENV_ROOT/bin:\$PATH"
eval "\$(pyenv init --path)"
eval "\$(pyenv init -)"
eval "\$(pyenv virtualenv-init -)"
EOF

# Ensure .bashrc is sourced on login
cat << EOF >> $HOME/.bash_profile
if [ -f ~/.bashrc ]; then
   source ~/.bashrc
fi
EOF

# Source the updated ~/.bashrc to apply pyenv changes
source $HOME/.bashrc

# Export PATH to ensure pyenv is correctly initialized
export PATH="$PYENV_ROOT/bin:$PATH"

# Install Python 3.11.9 using pyenv with the correct SQLite version linked
CFLAGS="-I/usr/local/include" LDFLAGS="-L/usr/local/lib" LD_LIBRARY_PATH="/usr/local/lib" pyenv install 3.11.9

# Rehash pyenv to update shims
pyenv rehash

# Set up vectors directory and Python 3.11.9 environment
mkdir -p $HOME/labs
cd $HOME/labs
pyenv local 3.11.9

# Rehash again to ensure shims are up to date
pyenv rehash

# Verify Python version in the labs directory
python --version

# Adding the PYTHONPATH for correct installation and look up for the libraries
export PYTHONPATH=$HOME/.pyenv/versions/3.11.9/lib/python3.11/site-packages:$PYTHONPATH

# Install required Python packages
$HOME/.pyenv/versions/3.11.9/bin/pip install --no-cache-dir oci==2.129.1 oracledb sentence-transformers langchain==0.2.6 langchain-community==0.2.6 langchain-chroma==0.1.2 langchain-core==0.2.11 langchain-text-splitters==0.2.2 langsmith==0.1.83 pypdf==4.2.0 streamlit==1.36.0 python-multipart==0.0.9 chroma-hnswlib==0.7.3 chromadb==0.5.3 torch==2.5.0

# Download the model during script execution
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L12-v2')"

# Install JupyterLab
pip install --user jupyterlab

# Install OCI CLI
echo "Installing OCI CLI..."
curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh -o install.sh
chmod +x install.sh
./install.sh --accept-all-defaults

# Verify the installation
echo "Verifying OCI CLI installation..."
oci --version || { echo "OCI CLI installation failed."; exit 1; }

# Ensure all the binaries are added to PATH
echo 'export PATH=$PATH:$HOME/.local/bin' >> $HOME/.bashrc
source $HOME/.bashrc

# Copy files from the git repo labs folder to the labs directory in the instance
echo "Copying files from the 'labs' folder in the OU Git repository to the existing labs directory..."
REPO_URL="https://github.com/ou-developers/ou-generativeai-pro.git"
FINAL_DIR="$HOME/labs"  # Existing directory on your instance

# Initialize a new git repository
git init

# Add the remote repository
git remote add origin $REPO_URL

# Enable sparse-checkout and specify the folder to download
git config core.sparseCheckout true
echo "labs/*" >> .git/info/sparse-checkout

# Pull only the specified folder into the existing directory
git pull origin main  # Replace 'main' with the correct branch name if necessary

# Move the contents of the 'labs' subfolder to the root of FINAL_DIR, if necessary
mv labs/* . 2>/dev/null || true  # Move files if 'labs' folder exists

# Remove any remaining empty 'labs' directory and .git folder
rm -rf .git labs

echo "Files successfully downloaded to $FINAL_DIR"

EOF_OPC

# Create the marker file to indicate the script has been run
touch "$MARKER_FILE"

echo "===== Cloud-Init Script Completed Successfully ====="
exit 0
