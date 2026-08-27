import os
import logging

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", os.path.abspath(os.path.join(BASE_DIR, "storage", "uploads")))
PROJECTS_DIR = os.environ.get("PROJECTS_DIR", os.path.abspath(os.path.join(BASE_DIR, "storage", "projects")))

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROJECTS_DIR, exist_ok=True)
logger.info(f"Storage directory resolved to: {UPLOAD_DIR}")
logger.info(f"Projects directory resolved to: {PROJECTS_DIR}")
