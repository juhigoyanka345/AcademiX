import os
import sys

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-xai-student-key-2026'
    DATABASE = os.path.join(BASE_DIR, 'instance', 'database.sqlite')
    MODEL_PATH = os.path.join(BASE_DIR, 'models', 'student_model.pkl')
    SCALER_PATH = os.path.join(BASE_DIR, 'models', 'scaler.pkl')
    EXPLAINER_PATH = os.path.join(BASE_DIR, 'models', 'explainer.pkl')
