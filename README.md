# IntelliStock (Dev)

Developer helper: run `dev_auto_run.py` to automatically run tests and restart the Streamlit app when code changes are detected.

Usage:

- Install dev dependency: `pip install watchdog` (or `pip install -r requirements.txt`).
- Start watcher: `python dev_auto_run.py`

The watcher will run `pytest` on each change and restart the Streamlit server when tests pass.

## Local Postgres & DB setup (dev)

We've added automation to run a local Postgres, create tables, and load CSVs.

- Start everything via VS Code Task: **Run Task -> Setup Dev DB**
- Or run manually:
  - docker-compose up -d
  - cp .env.example .env  # update values if needed
  - python -m pip install -r requirements.txt
  - python -m backend.scripts.create_tables
  - python -m backend.scripts.load_csvs

Files added:
- `docker-compose.yml` — local Postgres service
- `backend/db.py`, `backend/models.py` — DB setup and models (includes users, registrations, OTPs)
- `backend/scripts/setup_dev_env.ps1` — automates the full setup on Windows (PowerShell)
- `.vscode/tasks.json` — adds "Setup Dev DB" task

## Web UI & Authentication

A simple Flask app serves the frontend and enforces login.

1. Ensure dependencies are installed (`pip install -r requirements.txt`).
2. Run the auth server from the project root:
   ```sh
   python -m backend.auth
   ```
3. Visit http://127.0.0.1:5000/login in your browser (include the port!)
4. Use the seeded user:
   - **Username / Email:** `Parthik` (or `parthikgohel754@gmail.com`)
   - **Password:** `Parth@$1023`

After successful login you are redirected to the main dashboard page.  

### Streamlit login

The Streamlit application now includes a built‑in login form.  When you start
it (`python -m streamlit run backend/streamlit_app/app.py`) you will see a
simple username/password screen.  Enter the seeded user (`Parthik` /
`Parth@$1023`) and the dashboard will load.  Until credentials are provided the
app stops at the login form, preventing unauthenticated access.

Forgot password? Select the "Forgot Password" option on the login form and
provide your username or email. An OTP is sent to your registered email; enter it
along with a new password (and confirmation) to reset your credentials.

*The mobile/SMS route was removed in the current build — only email delivery
is supported.*

By default OTPs are printed to the console for development.  To enable real
email delivery, set the following environment variables (you can use a
Gmail account, Mailgun, etc):

```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your.address@example.com
SMTP_PASS=supersecretpassword
```

The app will automatically use these values when sending the OTP.
> The Flask/`backend/auth.py` server remains available if you prefer a
> traditional web‑app entry point, but it is not required for the Streamlit
> front end.

The credentials logic is in the top of
`backend/streamlit_app/app.py`; it queries the `users` table just like the
Flask code.  You can add password hashing, role checks, or other rules there.


