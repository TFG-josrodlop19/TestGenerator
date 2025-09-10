import sqlite3
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

DATABASE_NAME = os.getenv("DATABASE_NAME", "mibase.db")
DB_PATH = PROJECT_ROOT / DATABASE_NAME

conexion = sqlite3.connect(str(DB_PATH))

cursor = conexion.cursor()