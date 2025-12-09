'''
===========================================================
StrokeCare Web Application — Secure Software Development
Author: Vishvapriya Sangvikar

Course: COM7033 – MSc Data Science & Artificial Intelligence
Student ID: 2415083
Institution: Leeds Trinity University
Assessment: Assessment 1 – Software Artefact (70%)
AI Statement: Portions of this file were drafted or refined using
    generative AI for planning and editing only,
    as permitted in the module brief.
===========================================================
'''

# tests/test_patients.py
from __future__ import annotations


def test_patient_list_route_requires_login(client):
    """
    /admin/patients should NOT be directly accessible without login.
    Flask-Login's @login_required should return a 302 redirect to /auth/login.
    """
    resp = client.get("/admin/patients")

    # Anonymous users should be redirected to the sign-in page
    assert resp.status_code == 302
    location = resp.headers.get("Location", "")
    assert "/auth/login" in location
