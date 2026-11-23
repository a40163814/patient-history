const API_BASE = '/api/v1';

export async function loginPatient(phoneNumber, language = 'en') {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone_number: phoneNumber, language, otp: '123456' })
  });
  if (!res.ok) throw new Error('Login failed');
  return res.json();
}

export async function submitConsent(payload) {
  const res = await fetch(`${API_BASE}/intake/consent`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to record consent');
  return res.json();
}

export async function updatePatientLanguage(patientToken, language) {
  const res = await fetch(
    `${API_BASE}/intake/language?patient_token=${encodeURIComponent(patientToken)}&language=${encodeURIComponent(language)}`,
    { method: 'POST' }
  );
  if (!res.ok) throw new Error('Failed to update language');
  return res.json();
}

export async function submitVitals(patientToken, heightCm, weightKg, ayushSystem = 'allopathy', sessionId = null) {
  const res = await fetch(`${API_BASE}/intake/vitals`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      patient_token: patientToken,
      session_id: sessionId,
      height_cm: parseFloat(heightCm),
      weight_kg: parseFloat(weightKg),
      ayush_system: ayushSystem
    })
  });
  if (!res.ok) throw new Error('Failed to save vitals');
  return res.json();
}

export async function fetchNextQuestion(patientToken, sessionId, failures = 0) {
  const res = await fetch(
    `${API_BASE}/intake/question?patient_token=${encodeURIComponent(patientToken)}&session_id=${encodeURIComponent(sessionId)}&consecutive_failures=${failures}`
  );
  if (!res.ok) {
    if (res.status === 403 || res.status === 404) {
      throw new Error('SESSION_EXPIRED');
    }
    throw new Error('Failed to fetch question');
  }
  return res.json();
}

export async function recordAnswer(payload) {
  const res = await fetch(`${API_BASE}/intake/answer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to record answer');
  return res.json();
}

export async function skipOrAdvanceSection(patientToken, sessionId) {
  const res = await fetch(
    `${API_BASE}/intake/skip-or-advance?patient_token=${encodeURIComponent(patientToken)}&session_id=${encodeURIComponent(sessionId)}`,
    { method: 'POST' }
  );
  if (!res.ok) throw new Error('Failed to advance section');
  return res.json();
}

export async function fetchPatientReview(patientToken, sessionId) {
  const res = await fetch(
    `${API_BASE}/intake/review?patient_token=${encodeURIComponent(patientToken)}&session_id=${encodeURIComponent(sessionId)}`
  );
  if (!res.ok) throw new Error('Failed to load review data');
  return res.json();
}

export async function submitFinalIntake(patientToken, sessionId) {
  const res = await fetch(
    `${API_BASE}/intake/submit?patient_token=${encodeURIComponent(patientToken)}&session_id=${encodeURIComponent(sessionId)}`,
    { method: 'POST' }
  );
  if (!res.ok) throw new Error('Failed to submit intake');
  return res.json();
}

export async function uploadReportFile(patientToken, sessionId, file) {
  const formData = new FormData();
  formData.append('patient_token', patientToken);
  formData.append('session_id', sessionId);
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/reports/upload`, {
    method: 'POST',
    body: formData
  });
  if (!res.ok) throw new Error('Report upload failed');
  return res.json();
}

export async function uploadMultipleReportFiles(patientToken, sessionId, files) {
  const formData = new FormData();
  formData.append('patient_token', patientToken);
  formData.append('session_id', sessionId);
  for (let i = 0; i < files.length; i++) {
    formData.append('files', files[i]);
  }

  const res = await fetch(`${API_BASE}/reports/upload-batch`, {
    method: 'POST',
    body: formData
  });
  if (!res.ok) throw new Error('Batch report upload failed');
  return res.json();
}

export async function fetchDoctorQueue() {
  const res = await fetch(`${API_BASE}/doctor/queue`);
  if (!res.ok) throw new Error('Failed to load doctor queue');
  return res.json();
}

export async function fetchCaseSheet(sessionId) {
  const res = await fetch(`${API_BASE}/doctor/case/${sessionId}`);
  if (!res.ok) throw new Error('Failed to fetch case sheet');
  return res.json();
}

export async function editCaseField(sessionId, fieldId, newValue, reason = 'Doctor edit') {
  const res = await fetch(`${API_BASE}/doctor/case/${sessionId}/field`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ field_id: fieldId, new_value: newValue, reason })
  });
  if (!res.ok) throw new Error('Failed to edit field');
  return res.json();
}

export async function approveCaseSheet(sessionId, notes, aiSummary) {
  const res = await fetch(`${API_BASE}/doctor/case/${sessionId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      doctor_id: 'DOC-AYUSH-101',
      doctor_notes: notes,
      ai_summary: aiSummary
    })
  });
  if (!res.ok) throw new Error('Failed to approve case sheet');
  return res.json();
}

export async function resetAndSeedDemo() {
  const res = await fetch(`${API_BASE}/seed/reset`, { method: 'POST' });
  if (!res.ok) throw new Error('Database reset failed');
  return res.json();
}
