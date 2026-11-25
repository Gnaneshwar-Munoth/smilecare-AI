# Deploying SmileCare CRM on Vercel

Takes about 10 minutes. You need a free Vercel account and the **Bolna API key**, which you'll get separately. The key is deliberately **not** in this zip.

---

## What's in the zip

```
smilecare-crm/
├── public/index.html     ← the whole UI (booking form, CRM, WhatsApp mockup)
├── api/index.py          ← the server: /api/config, /api/call, /api/execution
├── vercel.json           ← routes /api/* to api/index.py
├── requirements.txt      ← empty on purpose (standard library only)
├── .env.example          ← list of settings (no secrets)
├── run_local.py           ← optional: run locally without Vercel
└── README.md
```

The Bolna key lives **only** in Vercel's encrypted environment variables. The Python functions read it on the server, so it never reaches the browser.

---

## Option A: Vercel website (no terminal)

1. **Unzip** the file.
2. **Push it to GitHub:** create a new **private** repo and upload the contents of the `smilecare-crm` folder, so `public/`, `api/` and `vercel.json` are at the repo root. The included `.gitignore` already blocks `.env`.
3. Go to **vercel.com → Add New… → Project**, then import the repo.
4. On the configure screen:
   - **Framework Preset:** `Other`
   - **Root Directory:** `./` (the folder that contains `api/` and `public/`)
   - Leave the Build and Output settings at their defaults.
5. Open **Environment Variables** and add:

   | Name | Value | Required? |
   |---|---|---|
   | `BOLNA_API_KEY` | *(the key you were sent privately)* | yes, for real calls |
   | `BOLNA_AGENT_ID` | `106ac92f-41e1-4e2e-9c7f-dca769d5bcb6` | yes |
   | `ACCESS_CODE` | any password, e.g. `smile2026` | **strongly recommended** |
   | `BOLNA_FROM_NUMBER` | a number on the Bolna account, e.g. `+9180…` | optional |

6. Click **Deploy**. After about 1 minute you get a URL like `https://smilecare-crm-xxxx.vercel.app`.

> If you add or change environment variables after deploying, go to **Deployments → ⋯ → Redeploy**. Vercel only picks up new values on a fresh deploy.

## Option B: Vercel CLI

```bash
npm i -g vercel
cd smilecare-crm
vercel                     # log in, accept the defaults (framework: Other)
vercel env add BOLNA_API_KEY production        # paste the key when prompted
vercel env add BOLNA_AGENT_ID production       # 106ac92f-41e1-4e2e-9c7f-dca769d5bcb6
vercel env add ACCESS_CODE production          # pick a password
vercel --prod
```

---

## Check that it works

1. Open `https://<your-app>.vercel.app/api/config`. You should see:
   ```json
   {"mode": "live", "agent_id": "106ac92f-…", "access_required": true}
   ```
   - If it says `"demo"`, the key isn't set. Add it, then redeploy.
2. Open the app. The top-right badge should say **LIVE · Bolna**. If you set `ACCESS_CODE`, type it into the box next to the badge.
3. Book an appointment with **your own mobile number** in `+91XXXXXXXXXX` format, then click **📞 Confirm call**.
4. Your phone rings, and "Priya" from SmileCare Dental confirms the appointment.
5. During the call, the transcript fills in live. When it ends, the status updates and a WhatsApp message appears in the phone mockup.

---

## Good to know

- **Demo mode:** if `BOLNA_API_KEY` is missing, the app still works and simulates the call in the browser. That's handy for showing it without spending credits.
- **Data** (appointments, calls) is stored in each visitor's browser (localStorage). Different browsers see their own data. **Reset demo data** restores the sample rows.
- **Each real call costs Bolna credits.** Keep `ACCESS_CODE` set on a public URL, so random visitors can't trigger calls.
- **Phone numbers** must be in international format (`+91…`). A 10-digit Indian number gets `+91` added automatically.
- **WhatsApp** is simulated in the UI; no real WhatsApp message is sent.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Badge says DEMO on Vercel | `BOLNA_API_KEY` is missing in Vercel env vars, or you didn't redeploy after adding it |
| "Wrong or missing access code" | Type the `ACCESS_CODE` value into the box at the top right |
| "Bolna rejected the call (401/403)" | The key is wrong or revoked. Ask for a fresh one |
| "Bolna rejected the call (4xx) … number" | The phone format is wrong, or the account has no calling number. Set `BOLNA_FROM_NUMBER` |
| Build failed: "No python entrypoint found" | You have an old copy with `api/call.py`, `config.py`, `execution.py`. Use the new zip: `api/` must contain only `index.py` |
| 404 on `/api/...` | `api/` must be at the repo root, next to `public/` and `vercel.json` |
| Call placed but the transcript never shows | Wait about 10 s after hang-up. Bolna finishes processing, then the page picks it up on its next 3-second check |

## Run locally (optional, no Vercel)

```bash
cp .env.example .env     # put the key in .env
python3 run_local.py        # http://localhost:8000 (Python 3.9+, nothing to install)
```
