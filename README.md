# Frame Notes

Frame Notes is designed as a workflow tool for photographers working across planning, shooting, editing, and darkroom experimentation.

**Status:** Early development — homepage and project scaffold in place.

---

## Stack
- Python 3
- Django
- SQLite (development)

---

## Local Setup

```bash
git clone https://github.com/amandallaz/frame_notes.git
cd frame_notes
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

---

## v1 Roadmap
- [ ] Projects CRUD
- [ ] Film rolls and frame notes
- [ ] Selects and dashboard
- [ ] Deploy to production

---

## Data Model
<img width="657" height="315" alt="Screenshot 2026-05-19 at 4 05 41 PM" src="https://github.com/user-attachments/assets/61b8552b-3322-42de-a17c-5add4b0eae64" />


