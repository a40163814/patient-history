import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.models import init_db_async

@pytest.mark.asyncio
async def test_full_api_intake_and_doctor_lifecycle():
    await init_db_async()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health check
        res = await client.get("/api/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"

        # 2. Seed reset
        res = await client.post("/api/v1/seed/reset")
        assert res.status_code == 200
        assert res.json()["status"] == "success"

        # 3. Doctor queue should show 3 seeded patients (with Vijay Patil at top due to Red Flag)
        q_res = await client.get("/api/v1/doctor/queue")
        assert q_res.status_code == 200
        queue_data = q_res.json()["queue"]
        assert len(queue_data) >= 3
        # Top entry must have red flag
        assert queue_data[0]["has_red_flag"] is True

        # 4. New Patient Login
        login_res = await client.post("/api/v1/auth/login", json={
            "phone_number": "9998887776",
            "language": "en"
        })
        assert login_res.status_code == 200
        pat_data = login_res.json()
        token = pat_data["patient_token"]
        session_id = pat_data["session_id"]
        assert token.startswith("AYUSH-")

        # 5. Consent Submission
        consent_res = await client.post("/api/v1/intake/consent", json={
            "patient_token": token,
            "consent_given": True,
            "preferred_language": "en"
        })
        assert consent_res.status_code == 200

        # 6. Vitals Submission
        vitals_res = await client.post("/api/v1/intake/vitals", json={
            "patient_token": token,
            "height_cm": 165.0,
            "weight_kg": 60.0
        })
        assert vitals_res.status_code == 200
        v_data = vitals_res.json()
        assert v_data["bmi"] == 22.0
        assert v_data["bmi_category"] == "Normal"
        assert v_data["vitals_label"] == "self-reported"

        # 7. Get First Question (Should be symptoms / chief complaint)
        q_res = await client.get(f"/api/v1/intake/question?patient_token={token}&session_id={session_id}")
        assert q_res.status_code == 200
        q1 = q_res.json()
        assert q1["section_id"] == "symptoms"
        assert q1["field_key"] == "chief_complaint"

        # 8. Answer chief complaint
        ans_res = await client.post("/api/v1/intake/answer", json={
            "patient_token": token,
            "session_id": session_id,
            "section_id": "symptoms",
            "field_key": "chief_complaint",
            "value": "Mild fever and throat irritation",
            "source": "patient_said"
        })
        assert ans_res.status_code == 200
        assert ans_res.json()["status"] == "success"

        # 9. Get Next Question (symptom_duration)
        q_res2 = await client.get(f"/api/v1/intake/question?patient_token={token}&session_id={session_id}")
        assert q_res2.status_code == 200
        q2 = q_res2.json()
        assert q2["section_id"] == "symptoms"
        assert q2["field_key"] == "symptom_duration"

        # 10. Answer symptom duration
        await client.post("/api/v1/intake/answer", json={
            "patient_token": token,
            "session_id": session_id,
            "section_id": "symptoms",
            "field_key": "symptom_duration",
            "value": "3 days",
            "source": "patient_said"
        })

        # 11. Patient Review Screen
        rev_res = await client.get(f"/api/v1/intake/review?patient_token={token}&session_id={session_id}")
        assert rev_res.status_code == 200
        assert "symptoms" in rev_res.json()["sections"]

        # 12. Submit Intake to Queue
        sub_res = await client.post(f"/api/v1/intake/submit?patient_token={token}&session_id={session_id}")
        assert sub_res.status_code == 200
        assert sub_res.json()["status"] == "completed"

        # 13. Doctor Review Case Sheet
        cs_res = await client.get(f"/api/v1/doctor/case/{session_id}")
        assert cs_res.status_code == 200
        cs = cs_res.json()
        assert cs["vitals_label"] == "self-reported"
        field_id = cs["sections"]["symptoms"][0]["id"]

        # 14. Doctor Inline Edit
        edit_res = await client.put(f"/api/v1/doctor/case/{session_id}/field", json={
            "field_id": field_id,
            "doctor_id": "DOC-SENIOR-1",
            "new_value": "Acidity (Amlapitta), no other chronic diseases",
            "reason": "Clarified during physical examination"
        })
        assert edit_res.status_code == 200

        # 15. Doctor Approval & PDF Generation
        appr_res = await client.post(f"/api/v1/doctor/case/{session_id}/approve", json={
            "doctor_id": "DOC-SENIOR-1",
            "doctor_notes": "Patient advised Sutshekhar Ras and pathya diet."
        })
        assert appr_res.status_code == 200
        assert appr_res.json()["status"] == "approved"
        pdf_url = appr_res.json()["pdf_download_url"]

        # 16. Verify PDF Download
        pdf_res = await client.get(pdf_url)
        assert pdf_res.status_code == 200
        assert pdf_res.headers["content-type"] == "application/pdf"
        assert len(pdf_res.content) > 1000
