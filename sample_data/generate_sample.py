"""
Pre-generate sample Excel data file for instant testing.
"""

import os
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from excel_handler import create_sample_excel_template

def main():
    os.makedirs("sample_data", exist_ok=True)
    sample_bytes = create_sample_excel_template()
    target_path = os.path.join("sample_data", "sample_interns_tasks.xlsx")
    with open(target_path, "wb") as f:
        f.write(sample_bytes)
    print(f"Sample Excel file generated at: {target_path}")

if __name__ == "__main__":
    main()
