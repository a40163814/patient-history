# Known System Limitations & Mitigation Strategies

While AyushIntake is engineered for reliability, several technical and environmental boundaries apply in real-world OPD settings:

---

## 1. Acoustic Noise in Public Hospital Corridors

- **Limitation:** Public Indian hospital OPD waiting areas typically exhibit high ambient noise (65–85 dB), crowd chatter, and loudspeaker announcements, which can degrade speech-to-text accuracy.
- **Mitigation:**
  - Browser audio capture enables hardware `echoCancellation`, `noiseSuppression`, and `autoGainControl`.
  - **Dual Failure Fallback:** If speech recognition fails twice consecutively, the system automatically surfaces large-icon touch inputs and text options, preventing patient lockup.
  - The patient can tap *"Use Tap Icons"* or *"Skip, Ask Doctor"* at any time.

---

## 2. Network Latency & Connectivity Boundaries

- **Limitation:** Live bidirectional speech streaming (Gemini Live API WebSocket) requires stable internet connectivity. Cellular networks in remote rural PHCs may experience packet loss or high latency (>2,000 ms).
- **Mitigation:**
  - **Graceful Adapter Fallback:** If the WebSocket drops, the application falls back immediately to `WebSpeechAdapter` or direct on-screen question prompts without losing already-saved answers.
  - The patient client is an installable PWA with service worker caching for application assets.

---

## 3. Optical Character Recognition (OCR) on Handwritten Slips

- **Limitation:** Handwritten clinical prescriptions and low-resolution mobile photographs of crumpled lab slips can yield uncertain character extraction.
- **Mitigation:**
  - The vision extraction service assigns explicit **confidence scores** (0.0 to 1.0) to every extracted biomarker and medicine candidate.
  - The original uploaded image is always displayed **side-by-side** with extracted values in the Doctor Dashboard, enabling immediate visual verification by the clinician.
  - Extraction is strictly non-diagnostic; no clinical interpretations are made automatically.

---

## 4. Multi-Dialect & Code-Mixing Nuances

- **Limitation:** Patients in semi-urban and rural areas frequently mix Hindi, Marathi, and regional English loanwords (e.g. *"mala chest pain ahe"* or *"sugar report aala"*).
- **Mitigation:**
  - Red-flag keyword definitions in `/config/red_flags.json` include common transliterated and code-mixed clinical phrases across English, Hindi, and Marathi.
  - Negation rules look for both English (`no`, `denies`) and Devanagari (`नहीं`, `नाही`) markers before or after danger keywords.
