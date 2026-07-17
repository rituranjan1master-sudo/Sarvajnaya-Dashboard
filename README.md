# Sarvajnaya-Dashboard
A simple Streamlit + SQLite dashboard for tracking clients and prospects.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
streamlit run sarvajnaya_dashboard.py
```

This opens the app in your browser (usually http://localhost:8501).
A `sarvajnaya.db` SQLite file is created automatically in the same folder on first run.

## Views

- **Overview** — quick stats (total clients, active contracts, open payments, open prospects) and a 7-day reminder list.
- **Clients** — search/filter clients, update payment status & reminder date, delete a client.
- **Prospects** — view the follow-up pipeline, update status/next follow-up, delete a prospect.
- **Add Client** — form to add a new client (GMB profile, socials, service dates, payment info, reminder).
- **Add Prospect** — form to add a new lead (name, phone, source, follow-up date, remark, status).
- **Settings** — export clients/prospects to CSV.

## Backup

Just copy the `sarvajnaya.db` file to back up all your data.

## Notes on changes from the original draft

- Payment/reminder updates and status updates now use a dropdown of existing clients/prospects (by ID + name) instead of a free-typed ID, so you can't accidentally update the wrong record.
- Added delete actions (with a confirmation checkbox) for both clients and prospects.
- Forms now `st.rerun()` after a successful update/delete so the table refreshes immediately.
- CSV export buttons work directly (previously nested inside an `st.button`, which breaks in Streamlit since a second click was needed).
- Name/phone search is cast to string first so it doesn't crash on empty/NaN values.
