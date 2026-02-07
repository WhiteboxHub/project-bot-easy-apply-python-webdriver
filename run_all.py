import os
import subprocess
import sys

def run_all_candidates():
    # Path to candidates directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    candidates_dir = os.path.join(project_root, "assets", "candidates")
    
    if not os.path.exists(candidates_dir):
        print(f"❌ Candidates directory not found: {candidates_dir}")
        return

    # Find all yaml/yml files
    candidate_files = [f for f in os.listdir(candidates_dir) if f.endswith((".yaml", ".yml"))]
    
    if not candidate_files:
        print("❌ No candidate profiles found in assets/candidates/")
        return

    print(f"🚀 Found {len(candidate_files)} candidates. Starting batch run...\n")

    for candidate in candidate_files:
        print(f"--- Processing Candidate: {candidate} ---")
        try:
            # Run main.py with the candidate file as an argument
            # We use sys.executable to ensure we use the same python interpreter (and venv)
            result = subprocess.run([sys.executable, "main.py", candidate], check=False)
            
            if result.returncode == 0:
                print(f"✅ Finished {candidate} successfully.\n")
            else:
                print(f"⚠️ {candidate} finished with return code {result.returncode}.\n")
                
        except Exception as e:
            print(f"❌ Error running {candidate}: {e}\n")

    print("🏁 Batch run completed for all candidates.")

if __name__ == "__main__":
    run_all_candidates()
