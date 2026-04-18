# WSGI Configuration for PythonAnywhere
import sys
import os

# Add your project directory to the sys.path
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Disable bytecode to avoid issues on PythonAnywhere
sys.dont_write_bytecode = True

# Import Flask application
from app import app as application

# For debugging
if __name__ == "__main__":
    application.run()
