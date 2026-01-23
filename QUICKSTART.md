# Quick Start Guide - Multi-Candidate Bot

## 1. Install Dependencies
```bash
pip install -r requirements.txt
```

## 2. Create Your First Candidate

### Edit `config/candidates.yaml`:
```yaml
candidates:
  - id: candidate_001
    name: "Your Name"
    enabled: true
    
    credentials:
      email: "your.email@example.com"
      password: ""  # Will use .env
      phone: "1234567890"
    
    uploads:
      Resume: ./assets/candidates/candidate_001/resume.pdf
    
    search:
      positions:
        - Software Engineer
      locations:
        - Remote
      salary: 80000
    
    preferences:
      max_applications_per_run: 10
      cooldown_seconds: 90
      dry_run: true  # Start with dry-run!
```

### Create `.env`:
```ini
CANDIDATE_001_PASSWORD=your_linkedin_password
```

### Add Your Resume:
```bash
# Place your resume here:
assets/candidates/candidate_001/resume.pdf
```

## 3. Test Run (Dry Mode)
```bash
python main_multi.py --candidate candidate_001 --dry-run
```

## 4. Live Run
Once dry-run works, set `dry_run: false` in candidates.yaml and run:
```bash
python main_multi.py --candidate candidate_001
```

## 5. Add More Candidates
Just copy the candidate block in `candidates.yaml` and change:
- `id` (e.g., candidate_002)
- `name`, `email`, `phone`
- Resume path
- Search preferences

## 6. Enable Proxies (Optional)

### Edit `config/proxy_config.yaml`:
```yaml
proxy:
  enabled: true
  
  pools:
    - name: "my_proxy"
      host: "proxy.example.com"
      port: 8080
      username: "user"
      password: "{PROXY_PASSWORD}"
```

### Add to `.env`:
```ini
PROXY_PASSWORD=your_proxy_password
```

## Common Commands

```bash
# List all candidates
python main_multi.py --list-candidates

# Run specific candidate
python main_multi.py --candidate candidate_001

# Run all enabled candidates
python main_multi.py --all

# Check proxy status
python main_multi.py --proxy-stats

# Dry run (safe testing)
python main_multi.py --candidate candidate_001 --dry-run
```

## Troubleshooting

**"No candidates configured"**
- Make sure `config/candidates.yaml` exists
- Check that at least one candidate has `enabled: true`

**"Password required"**
- Add `CANDIDATE_XXX_PASSWORD` to `.env` file

**Chrome profile error**
- Close ALL Chrome windows before running
- Or specify a different profile path in candidates.yaml

**Resume not found**
- Check the path in `uploads.Resume`
- Make sure the PDF file exists at that location

## Next Steps

1. Start with ONE candidate in dry-run mode
2. Verify it finds jobs and fills forms correctly
3. Disable dry-run for live applications
4. Add more candidates as needed
5. Enable proxies for better stealth (optional)
6. Run on multiple systems for scale (optional)

See `README_MULTI.md` for full documentation.
