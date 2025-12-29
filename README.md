# 🧠 Decision-Making AI Agent (FastAPI + Streamlit)

A lightweight decision assistant that helps freelancers, independent consultants, and small teams **evaluate business opportunities** and decide:
✅ **ACCEPT** / ❌ **REJECT** / 🟡 **NEEDS_INFO**

This project combines:
- a **FastAPI backend** for structured evaluation logic,
- a **Streamlit UI** dashboard for rich user interaction,
- and a **simple CRM-style memory + CSV export** to track decision history.

---

## 🚀 Features

- 📡 **FastAPI backend** with auto-generated `/docs` API documentation
- 🤖 **Rule-based decision evaluation**
  - ROI (return on investment)
  - Feasibility
  - Client risk
  - Motivation
- 💾 **Memory logging** of all decisions (stored as JSON lines)
- 📊 **Streamlit UI dashboard** for interactive evaluation
- 📁 **CSV export** for historical decision tracking (CRM-style)

---

## 📸 Screenshots

> **Backend (FastAPI docs)**  
![API Docs](assets/api.png)

> **Streamlit UI**  
![UI](assets/ui.png)

*(Add these images to `assets/` and update the paths if you use different names.)*

---

## 🛠️ Tech Stack

| Component | Tech |
|-----------|------|
| Backend API | Python + FastAPI + Uvicorn |
| Frontend UI | Streamlit |
| Models & Validation | Pydantic |
| Persistence | JSONL (memory/decisions.jsonl) |
| CLI / Export | Python CSV export script |

---

## 📦 Installation & Run (Local)

### 1️⃣ Clone the repository
```bash
git clone https://github.com/Ali-Abdulqawi/Decision-Making-AI-Agent.git
cd Decision-Making-AI-Agent

