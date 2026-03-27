# Start Postgres, install deps, wait for DB, create tables, and load CSVs
$ErrorActionPreference = "Stop"

Write-Host "Starting Postgres via docker-compose..."
docker-compose up -d

Write-Host "Installing Python dependencies..."
python -m pip install -r requirements.txt

# Wait for DB to be ready (tries for up to 60 seconds)
Write-Host "Waiting for Postgres to accept connections..."
$max=60
for ($i=0; $i -lt $max; $i++) {
    try {
        python - <<'PY'
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('DATABASE_URL')
if not url:
    raise SystemExit('DATABASE_URL not set')
engine = create_engine(url)
with engine.connect() as conn:
    conn.execute('SELECT 1')
print('ok')
PY
        Write-Host "Postgres ready"
        break
    } catch {
        Start-Sleep -Seconds 1
    }
}

Write-Host "Creating DB tables (if missing)..."
python -m backend.scripts.create_tables

Write-Host "Loading CSVs into DB..."
python -m backend.scripts.load_csvs

Write-Host "Dev DB setup complete."
