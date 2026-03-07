import os
import pytest
from fastapi.testclient import TestClient
from dotenv import load_dotenv

# ✅ Ensure .env is loaded BEFORE app import
load_dotenv()

from app.main import app
from app.db.init_db import init_db
from app.db.session import DATABASE_URL


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """
    Ensure tests use the SAME database as the app
    and tables exist before tests run.
    """
    print(f"\n[TEST DB] Using DATABASE_URL = {DATABASE_URL}\n")

    init_db()


@pytest.fixture(scope="function")
def client():
    return TestClient(app)
