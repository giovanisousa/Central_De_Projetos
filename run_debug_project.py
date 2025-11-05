"""
Non-interactive runner for debug_single_project.comparar_projeto
Usage: python run_debug_project.py <project_id> <db_url>
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from debug_single_project import comparar_projeto

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python run_debug_project.py <project_id> <db_url>")
        sys.exit(1)
    project_id = sys.argv[1]
    db_url = sys.argv[2]
    comparar_projeto(project_id, db_url)
