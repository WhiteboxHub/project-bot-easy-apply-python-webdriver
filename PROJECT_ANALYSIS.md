# Project Analysis: LinkedIn AI Auto Job Applier

This document provides a technical overview and detailed analysis of the project's structure, features, and historical context.

## 🏗️ Technical Architecture

The bot is built as a modular Python application using Selenium for browser automation.

### Core Components
- `main.py`: Entry point for single-candidate runs. Supports CLI arguments.
- `run_all.py`: Batch runner for processing all candidate YAML files in sequence.
- `bot/core/`: Logic for browser initialization, candidate management, and session handling.
- `bot/application/`: Form filling logic, workflow management, and resume handling.
- `bot/discovery/`: Job search logic, location filtering, and job detail extraction.
- `bot/persistence/`: Data storage handlers for DuckDB, JSON counts, and CSV logs.
- `bot/utils/`: Shared utilities for logging, delays, and dynamic selector management.

### Data Storage
- **DuckDB (`output/applications.db`)**: Primary storage for detailed application history.
- **JSON (`data/counts.json`)**: Daily application metrics and candidate-specific counters.
- **CSV (`output/applied_jobs.csv`)**: Human-readable log of successful applications.
- **QA CSV (`data/qa.csv`)**: Knowledge base for form field automation.

---

## 🤩 Detailed Feature List

### General Features
- **Auto Login**: Persistent browser profiles per candidate.
- **Dynamic Filtering**: Apply filters for Salary, Company, and Experience Level via YAML.
- **Intelligent Form Filling**: Automatically answers application questions using a stored knowledge base.
- **Experience Filtering**: Automatically skips jobs requiring more experience than defined.
- **Blacklist/Whitelist**: Skips jobs based on company names or keywords in the description.
- **Headless Mode**: Option to run in the background.

### Stealth Features
- **Undetected Chromedriver**: Bypasses typical anti-bot detection.
- **Randomized Delays**: Human-like interaction timing.
- **Smooth Scrolling**: Scrolls elements into view before interaction.

---

## 🏛️ Historical Context & Contributors

This project originated as a community-driven tool to automate the tedious parts of job searching. Major updates included moving from Python-based configs to YAML for better security and flexibility, and adding multi-candidate support.

### Major Updates
- **Dec 2024**: YAML-based configuration migration.
- **Feb 2026**: Multi-candidate batch runner (`run_all.py`) and automated CSV logging.

---

## 📜 Terms and Conditions
*Refer to the primary repository for full licensing (GNU Affero General Public License v3.0).*
- **LinkedIn Policies**: User is responsible for compliance with LinkedIn terms.
- **No Warranties**: Provided "as-is" without guarantees of success or account safety.
