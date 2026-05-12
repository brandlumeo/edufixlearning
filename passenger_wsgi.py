import os
import sys

# Add project directory to sys.path
sys.path.insert(0, os.path.dirname(__file__))

# Import the Django WSGI application
from edufix_lms.wsgi import application
