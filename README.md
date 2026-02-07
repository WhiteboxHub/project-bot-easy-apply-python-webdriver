# LinkedIn AI Auto Job Applier 🤖

This bot automates job applications on LinkedIn. It supports multi-candidate profiles, automated form filling, and detailed logging.

## ⚙️ Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
- Copy `.env.example` to a new file named `.env`.
- Fill in your LinkedIn credentials and (optional) AI API keys:
  ```env
  LINKEDIN_USERNAME=your_email@example.com
  LINKEDIN_PASSWORD=your_password
  LLM_API_KEY=your_key_here
  ```

### 3. Candidate Profiles & Resumes
- **Profiles**: Create your profile YAML files in `assets/candidates/`.
- **Resumes**: Place your resume PDF in the folder specified in your YAML configuration (e.g., `assets/resumes/resume.pdf`).

## 🚀 How to Run

- **Select Profile Manually**: `python main.py`
- **Run Specific Profile**: `python main.py candidate_name.yaml`
- **Run All Profiles**: `python run_all.py`

## 📊 View Results
- **CSV Logs**: Check `output/applied_jobs.csv` for application history.
- **Detailed History**: Run `python app.py` and visit `http://localhost:5000`.

## 📁 More Information
For a deep dive into advanced features, architecture, and project history, see [PROJECT_ANALYSIS.md](PROJECT_ANALYSIS.md).

## 🆘 Support
Join the Discord server for assistance: [https://discord.gg/fFp7uUzWCY](https://discord.gg/fFp7uUzWCY)
