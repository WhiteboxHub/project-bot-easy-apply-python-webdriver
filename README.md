# LinkedIn EasyApply Bot 2.0

A robust, stealthy, and modular bot to automate LinkedIn Easy Apply applications.

## 🚀 New Features

### 🛡️ Anti-Detection & Human Behavior
*   **Undetected Chromedriver**: Uses `undetected-chromedriver` to bypass Selenium detection.
*   **Variable Fingerprinting**: Uses `selenium-stealth` to randomize WebGL, Canvas, and other browser fingerprints.
*   **Natural Human Jitter**:
    *   **Mouse**: Moves cursor in Bezier curves using `humancursor` to mimic physical hand movement.
    *   **Scrolling**: Natural "stuttering" scrolling with random pauses and micro-reversals.
*   **Profile Persistence**: Loads your real Chrome profile to maintain cookies and session state.

### ⚡ Reliability & Safeguards
*   **Stale Element Guard**: Automatically detects and recovers from DOM changes (StaleElementReferenceException) without crashing.
*   **Scroll Tracking**: Robust pagination and scroll tracking to prevent infinite loops.
*   **Execution Safeguards**:
    *   **Max Applications**: Stops after a configurable number of submissions (default: 10).
    *   **Cooldown**: Random sleep between applications (default: 90s).
*   **Dry Run Mode**: Test flows securely without submitting (`dry_run: true`).

### 💾 Data & Security
*   **DuckDB Integration**: Replaced CSVs with a local high-performance SQL database (`data/bot_data.duckdb`).
*   **Secure Credentials**: Loads sensitive data (`username`, `password`) from a `.env` file instead of `config.yaml`.
*   **Automatic Migration**: Automatically imports legacy CSV data on first run.

### 🧩 Architecture
*   **Modular Design**: Code is split into `bot/core`, `bot/discovery`, `bot/application`, and `bot/persistence` for maintainability.
*   **Manual Intervention Mode**: If the bot encounters a field it cannot fill, it will **pause indefinitely**, allowing you to fill it manually in the browser. It resumes automatically once the error is cleared.
*   **Multi-Candidate Support**: Capable of handling multiple profiles via `config/candidates.yaml` and `main_multi.py`.
*   **Structured Logging**: Machine-parseable logs with `job_id`, `step`, and `event` for easier debugging.

---

## 🛠️ Setup

### 1. Prerequisites
*   Python 3.10+
*   Google Chrome installed

### 2. Install Dependencies
```bash
pip install -r requirements.txt
pip install tabulate  # Optional: For viewing database results
```

### 3. Configure Credentials (.env)
Rename `.env.example` to `.env` and add your details. This file is ignored by Git to keep your data safe.
```ini
LINKEDIN_USERNAME=your_email@example.com
LINKEDIN_PASSWORD=your_password
PHONE_NUMBER=1234567890
```

### 4. Configure Bot (config.yaml)
Edit `config.yaml` for job search parameters and execution speed.
```yaml
execution:
  max_applications_per_run: 10
  cooldown_seconds: 5  # Time to wait between applications
  dry_run: true       # Set to false to actually apply
```
*Note: Place your resume and cover letter in the `assets/` folder.*

---

## ▶️ Execution

### Run the Bot
**IMPORTANT**: Close all Google Chrome windows before running.

```bash
python main.py
```

### Checking Logs
Logs are printed to the console in a structured format:
```
2024-01-20 12:00:00 INFO job_id=12345 step=apply event=success message=Application Submitted
```

### Session Summary
When the bot finishes (or is interrupted), it prints a summary:
```
================ SESSION SUMMARY ================
Attempted:  12
Submitted:  5
Skipped:    6
Failed:     1
=================================================
```

---

## 📂 Project Structure
```
.
├── main.py              # Entry point
├── config.yaml          # Configuration
├── .env                 # Secrets (ignored by git)
├── bot/                 # Source code
│   ├── core/            # Browser, Session, Metrics, Guard
│   ├── discovery/       # Search, Scroll, Job Identity
│   ├── application/     # Workflow, Form Filler
│   ├── persistence/     # Store (DuckDB)
│   └── utils/           # Jitter, Logger, Retry
├── data/                # Database (bot_data.duckdb) & Outputs
├── assets/              # Input PDFs (Resume, CL)
└── archive/             # Old files
```
