"""Pytest 共享 fixture：FastAPI 应用与 TestClient。"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """FastAPI 应用 TestClient，用于集成测试。"""
    return TestClient(app)
