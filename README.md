# SmileCare Dental: Bolna appointment-confirmation demo

A dummy dental-clinic booking site and CRM. When a patient books, the front desk clicks **📞 Confirm call**. A Bolna voice agent ("Priya") then calls the patient to confirm, reschedule or cancel. The CRM updates the status, and a **simulated WhatsApp** message goes out.

```
Patient books ──► CRM (browser)  ──"Confirm call"──►  /api/call  ──►  Bolna places the call
                       ▲                                                  │
                       └──── /api/execution (polled every 3 s) ◄──────────┘
                                 transcript + extracted outcome
                       → status: confirmed / reschedule / cancelled / no answer
                       → WhatsApp message (simulated phone panel)
```

- **Deploy on Vercel:** see [DEPLOY_VERCEL.md](DEPLOY_VERCEL.md)
- **Run locally:** `cp .env.example .env`, add the key, then `python3 run_local.py` and open http://localhost:8000
- **No key?** It runs in DEMO mode with a simulated call.

## Bolna agent
- `SmileCare Dental · Appointment Confirmation (Priya)`, ID `106ac92f-41e1-4e2e-9c7f-dca769d5bcb6`
- Deepgram nova-3 (en) → azure/gpt-4.1-mini → ElevenLabs turbo v2.5, Vobiz telephony
- Per-call variables: `patient_name, treatment, doctor_name, appointment_date, appointment_time`
- Extracted: `appointment_status`, `new_preferred_time`, `patient_notes`

## Security
- The Bolna key is read only by the server function `api/index.py`, from env vars. It is never sent to the browser.
- `.env` is git-ignored and is not part of the shared zip.
- Set `ACCESS_CODE` on any public deployment so strangers can't place calls.
