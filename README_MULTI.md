# LinkedIn EasyApply Bot 2.0 - Multi-Candidate Edition

A robust, stealthy, and modular bot to automate LinkedIn Easy Apply applications with **multi-candidate support** and **rotating residential proxies**.

## 🚀 New Features (Multi-Candidate Edition)

### 👥 Multi-Candidate Support
*   **Multiple Profiles**: Manage unlimited candidates with separate configurations
*   **Individual Settings**: Each candidate has their own resume, search criteria, and preferences
*   **Chrome Profile Isolation**: Separate browser profiles for each candidate
*   **Database Tracking**: Track applications per candidate with detailed analytics

### 🌐 Rotating Proxy Support
*   **Multiple Providers**: Support for Bright Data, Oxylabs, Smartproxy, and custom proxies
*   **Rotation Strategies**: Per-session, per-application, time-based, or per-candidate
*   **Health Checking**: Automatic proxy health monitoring and failover
*   **Authentication**: Built-in support for proxy authentication

### 🛡️ Anti-Detection & Human Behavior
*   **Undetected Chromedriver**: Uses `undetected-chromedriver` to bypass Selenium detection
*   **Variable Fingerprinting**: Uses `selenium-stealth` to randomize WebGL, Canvas, and other browser fingerprints
*   **Natural Human Jitter**:
    *   **Mouse**: Moves cursor in Bezier curves using `humancursor` to mimic physical hand movement
    *   **Scrolling**: Natural "stuttering" scrolling with random pauses and micro-reversals
*   **Profile Persistence**: Loads your real Chrome profile to maintain cookies and session state

### ⚡ Reliability & Safeguards
*   **Stale Element Guard**: Automatically detects and recovers from DOM changes (StaleElementReferenceException) without crashing
*   **Scroll Tracking**: Robust pagination and scroll tracking to prevent infinite loops
*   **Selector Fallbacks**: Primary and fallback selectors for critical elements
*   **Execution Safeguards**:
    *   **Max Applications**: Stops after a configurable number of submissions (per candidate)
    *   **Cooldown**: Random sleep between applications (configurable per candidate)
*   **Dry Run Mode**: Test flows securely without submitting (`dry_run: true`)

### 💾 Data & Security
*   **DuckDB Integration**: Local high-performance SQL database with multi-candidate tracking
*   **Secure Credentials**: Loads sensitive data from `.env` file with per-candidate support
*   **Run Tracking**: Detailed tracking of each run with candidate, proxy, and system information

### 🧩 Architecture
*   **Modular Design**: Code is split into `bot/core`, `bot/discovery`, `bot/application`, and `bot/persistence`
*   **Structured Logging**: Machine-parseable logs with `job_id`, `step`, and `event`
*   **Metrics**: Prints a session summary (Attempted, Submitted, Failed, Skipped) at the end of every run

---

## 🛠️ Setup

### 1. Prerequisites
*   Python 3.10+
*   Google Chrome installed

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Candidates (config/candidates.yaml)
Create your candidate profiles:
```yaml
candidates:
  - id: candidate_001
    name: "John Doe"
    enabled: true
    
    credentials:
      email: "john.doe@example.com"
      password: ""  # Use .env for security
      phone: "1234567890"
    
    uploads:
      Resume: ./assets/candidates/candidate_001/resume.pdf
      Cover Letter: ./assets/candidates/candidate_001/cover_letter.pdf
    
    search:
      positions:
        - Software Engineer
      locations:
        - Remote
      salary: 80000
    
    preferences:
      max_applications_per_run: 15
      cooldown_seconds: 120
```

### 4. Configure Credentials (.env)
```ini
# Candidate passwords
CANDIDATE_001_PASSWORD=your_password

# Proxy credentials (optional)
PROXY_BRIGHTDATA_PASSWORD=your_proxy_password
```

### 5. Configure Proxies (Optional - config/proxy_config.yaml)
```yaml
proxy:
  enabled: true
  provider: "brightdata"
  
  rotation:
    strategy: "per_session"  # or per_application, time_based, per_candidate
  
  pools:
    - name: "brightdata_residential_us"
      host: "brd.superproxy.io"
      port: 22225
      username: "your_username"
      password: "{PROXY_BRIGHTDATA_PASSWORD}"
```

---

## ▶️ Execution

### Run the Bot
**IMPORTANT**: Close all Google Chrome windows before running.

```bash
# List all candidates
python main_multi.py --list-candidates

# Run for specific candidate
python main_multi.py --candidate candidate_001

# Run for all enabled candidates
python main_multi.py --all

# Dry run mode
python main_multi.py --candidate candidate_001 --dry-run

# Show proxy statistics
python main_multi.py --proxy-stats
```

### Legacy Mode (Single Candidate)
The original `main.py` still works for backward compatibility:
```bash
python main.py
```

---

## 📊 Multi-System Deployment

### Running on Multiple Systems

1. **Copy the project** to each system
2. **Configure different candidates** on each system
3. **Run independently** or use the orchestrator (optional)

Example setup:
- **System 1**: Runs candidate_001, candidate_002
- **System 2**: Runs candidate_003, candidate_004
- **System 3**: Runs candidate_005, candidate_006

### Database Synchronization (Optional)

For centralized tracking, you can:
1. Use a shared network drive for `data/bot_data.duckdb`
2. Export data periodically and merge
3. Use the orchestrator API (advanced)

---

## 📂 Project Structure
```
.
├── main.py                  # Legacy entry point (single candidate)
├── main_multi.py            # NEW: Multi-candidate entry point
├── config/
│   ├── candidates.yaml      # NEW: Multi-candidate configuration
│   └── proxy_config.yaml    # NEW: Proxy pool configuration
├── .env                     # Secrets (per-candidate passwords, proxy credentials)
├── bot/
│   ├── core/
│   │   ├── browser.py              # Browser with proxy support
│   │   ├── session.py              # LinkedIn authentication
│   │   ├── candidate_manager.py    # NEW: Candidate management
│   │   ├── proxy_manager.py        # NEW: Proxy rotation
│   │   ├── execution_guard.py      # Application rate limiting
│   │   ├── metrics.py              # Session statistics
│   │   └── dry_run.py              # Test mode controller
│   ├── discovery/           # Job search & discovery
│   ├── application/         # Application workflow
│   ├── persistence/         # Data storage (DuckDB)
│   └── utils/               # Shared utilities
├── data/
│   └── bot_data.duckdb     # Database with multi-candidate tracking
└── assets/
    └── candidates/          # NEW: Per-candidate resumes/cover letters
        ├── candidate_001/
        │   ├── resume.pdf
        │   └── cover_letter.pdf
        └── candidate_002/
            └── resume.pdf
```

---

## 🔍 Database Schema

### Applications Table
```sql
CREATE TABLE applications (
    timestamp TIMESTAMP,
    job_id VARCHAR,
    job VARCHAR,
    company VARCHAR,
    attempted BOOLEAN,
    result BOOLEAN,
    candidate_id VARCHAR,  -- NEW
    proxy_used VARCHAR     -- NEW
)
```

### Candidates Table (NEW)
```sql
CREATE TABLE candidates (
    candidate_id VARCHAR PRIMARY KEY,
    name VARCHAR,
    email VARCHAR,
    created_at TIMESTAMP
)
```

### Runs Table (NEW)
```sql
CREATE TABLE runs (
    run_id VARCHAR PRIMARY KEY,
    candidate_id VARCHAR,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    applications_submitted INTEGER,
    applications_failed INTEGER,
    proxy_used VARCHAR,
    system_id VARCHAR
)
```

---

## 🎯 Use Cases

### Scenario 1: Single User, Multiple Profiles
Run different job searches with different resumes/preferences:
- **Profile A**: Senior positions, high salary
- **Profile B**: Mid-level positions, broader locations

### Scenario 2: Recruitment Agency
Manage multiple clients' job applications:
- Each client has their own candidate profile
- Separate tracking and reporting per client
- Different proxies per client for IP diversity

### Scenario 3: Distributed Team
Run on multiple systems for higher throughput:
- System 1: Handles candidates 1-5
- System 2: Handles candidates 6-10
- Centralized database for analytics

---

## 🔐 Security Best Practices

1. **Never commit `.env`** - It's gitignored by default
2. **Use environment variables** for all passwords
3. **Rotate proxies regularly** - Use per_session or per_application strategy
4. **Monitor for rate limits** - Adjust cooldown_seconds if needed
5. **Use separate Chrome profiles** - Prevents session conflicts

---

## 📈 Monitoring & Analytics

### Query Applications by Candidate
```sql
SELECT candidate_id, COUNT(*) as total_applications, 
       SUM(CASE WHEN result THEN 1 ELSE 0 END) as successful
FROM applications
GROUP BY candidate_id;
```

### Query Proxy Usage
```sql
SELECT proxy_used, COUNT(*) as applications
FROM applications
WHERE proxy_used IS NOT NULL
GROUP BY proxy_used;
```

### Query Run History
```sql
SELECT * FROM runs
ORDER BY started_at DESC
LIMIT 10;
```

---

## 🐛 Troubleshooting

### "No candidates configured"
- Create `config/candidates.yaml` from the example
- Ensure at least one candidate has `enabled: true`

### "Candidate password required"
- Add password to `.env` as `CANDIDATE_XXX_PASSWORD=your_password`
- Or add directly to `candidates.yaml` (not recommended)

### Proxy connection failed
- Check proxy credentials in `config/proxy_config.yaml`
- Verify proxy is enabled: `enabled: true`
- Test proxy health: `python main_multi.py --proxy-stats`

### Chrome profile in use
- Close all Chrome windows before running
- Use different profile paths for each candidate

---

## 📝 Migration from Old Version

If you're upgrading from the single-candidate version:

1. **Keep `main.py`** - It still works for backward compatibility
2. **Create `config/candidates.yaml`** - Move your config there
3. **Update `.env`** - Add `CANDIDATE_001_PASSWORD`
4. **Run database migration** - Happens automatically on first run
5. **Test with dry-run** - `python main_multi.py --candidate candidate_001 --dry-run`

---

*Multi-Candidate Edition - Built for scale and stealth*
