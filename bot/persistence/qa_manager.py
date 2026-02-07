import csv
import os
import re

class QAManager:
    def __init__(self, file_path="data/qa.csv"):
        self.file_path = file_path
        self._ensure_file()
        self.data = self._load()

    def _ensure_file(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['question', 'answer'])

    def _clean_text(self, text):
        # Remove common LinkedIn UI noise like "Required", "Multiple choice", "Select an option", etc.
        noise = [
            r"Required", r"required",
            r"Multiple choice", r"multiple choice",
            r"Select an option", r"select an option",
            r"Yes\s*No", r"yes\s*no",
            r"Please make a selection",
            r"\d+ applicants",
            r"\(Optional\)",
            r"\s+"
        ]
        text = str(text).replace('\n', ' ').strip()
        for pattern in noise:
            text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
        return ' '.join(text.split()).lower()

    def _load(self):
        qa_dict = {}
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    q = self._clean_text(row['question'])
                    if q:
                        qa_dict[q] = row['answer']
        except: pass
        return qa_dict

    def find_answer(self, question_text):
        q_clean = self._clean_text(question_text)
        # 1. Exact match
        if q_clean in self.data:
            return self.data[q_clean]
        
        # 2. Partial match (if a stored question is inside the new question)
        for stored_q, answer in self.data.items():
            if stored_q in q_clean or q_clean in stored_q:
                # Only use if it's long enough to be meaningful
                if len(stored_q) > 10:
                    return answer
        return None

    def save_answer(self, question, answer):
        q_clean = self._clean_text(question)
        if q_clean in self.data and self.data[q_clean] == answer:
            return # Already saved
        
        self.data[q_clean] = answer
        with open(self.file_path, 'a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([question.replace('\n', ' ').strip(), answer])

    def cleanup_file(self):
        """Removes duplicates and cleans noise from existing file."""
        unique_qa = {}
        with open(self.file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                q = self._clean_text(row['question'])
                if q and q not in unique_qa:
                    unique_qa[q] = (row['question'].strip().replace('\n', ' '), row['answer'])

        with open(self.file_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['question', 'answer'])
            for q, (original, answer) in unique_qa.items():
                writer.writerow([original, answer])
        self.data = self._load()
