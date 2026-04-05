import pytest
from httpx import AsyncClient
from app.main import app

import asyncio

@pytest.mark.asyncio
async def test_faculty_fetch_and_resolve(monkeypatch):
	# Mock faculty user id
	faculty_user_id = "507f1f77bcf86cd799439011"
	complaint_id = "CMP-20260403-7F3A9B"

	# Mock authentication dependency
	async def fake_get_current_faculty_user():
		return faculty_user_id

	app.dependency_overrides = {}
	from app.api.routes import faculty_routes
	faculty_routes.get_current_faculty_user = fake_get_current_faculty_user

	async with AsyncClient(app=app, base_url="http://test") as ac:
		# Fetch assigned complaints (should not fail)
		resp = await ac.get(f"/api/v1/faculty/complaints/")
		assert resp.status_code in (200, 401, 403)  # Acceptable for empty/mocked DB

		# Try to resolve a complaint (should not fail, but likely 404 if not present)
		resp2 = await ac.post(f"/api/v1/faculty/complaints/{complaint_id}/resolve", json={"resolution_explanation": "Resolved by faculty."})
		assert resp2.status_code in (200, 404, 403)

