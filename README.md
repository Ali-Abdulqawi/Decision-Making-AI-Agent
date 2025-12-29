# 🧠 Decision-Making AI Agent (FastAPI + Streamlit)

A lightweight decision assistant that helps freelancers/teams evaluate business opportunities and decide:
✅ ACCEPT / ❌ REJECT / 🟡 NEEDS_INFO

It uses a deterministic scoring system (ROI, feasibility, risk, motivation) + saves every evaluation to memory (JSONL) and can export decisions to CSV (CRM-style history).

---

## 🚀 Features
- FastAPI backend endpoint: `/evaluate`
- Decision output: ACCEPT / REJECT / NEEDS_INFO + confidence + reasons + risks + next actions
- Memory logging (JSONL): `memory/decisions.jsonl`
- Streamlit UI dashboard
- Export decisions to CSV

---

## 🧱 Tech Stack
- Python
- FastAPI + Uvicorn
- Streamlit
- Pydantic

---

## ▶️ Run Locally

### 1) Create and activate virtual env
```bash
python3 -m venv .venv
source .venv/bin/activate
