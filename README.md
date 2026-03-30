---
title: IntelliStock AI Retail Intelligence
emoji: 📦
colorFrom: purple
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: Predictive Retail Intelligence powered by AI
---

# IntelliStock — Predictive Retail Intelligence Using AI

An AI-powered inventory management and retail analytics dashboard built with **Streamlit**.

## 🚀 Features

- 📊 **Real-time Dashboard** – KPIs, revenue charts, sales heatmaps
- 🤖 **AI Recommendations** – Smart reorder & discount suggestions
- 📈 **Demand Forecasting** – Statistical + ML-based forecasting
- 🔔 **Smart Alerts** – Overstock, low-stock, and price anomaly detection
- 🗂️ **Scenario Analysis** – What-if simulations for inventory decisions
- 👤 **Authentication** – Login / Register / Forgot Password with OTP

## 🔐 Demo Credentials

| Field    | Value                   |
|----------|-------------------------|
| Username | `Parthik`               |
| Password | `Parth@$1023`           |

## ⚙️ Environment Variables (Optional)

Set these in Hugging Face Space **Settings → Variables and secrets**:

| Variable       | Description                          |
|----------------|--------------------------------------|
| `DATABASE_URL` | PostgreSQL connection string         |
| `SMTP_SERVER`  | SMTP host for OTP e-mails            |
| `SMTP_PORT`    | SMTP port (default 587)              |
| `SMTP_USER`    | SMTP username / email                |
| `SMTP_PASS`    | SMTP password                        |

> If `DATABASE_URL` is not set, the app will try to connect to a local PostgreSQL instance. For a free cloud DB, use [Neon](https://neon.tech) or [Supabase](https://supabase.com).

## 🛠️ Local Development

```bash
git clone <repo-url>
cd <repo>
python -m pip install -r requirements.txt
# Set DATABASE_URL in .env or environment
python -m streamlit run backend/streamlit_app/app.py
```

## 📁 Project Structure

```
├── backend/
│   ├── streamlit_app/app.py   # Main Streamlit app
│   ├── services/              # Business logic services
│   ├── data/                  # CSV data files
│   ├── db.py                  # Database connection
│   └── models.py              # SQLAlchemy models
├── Dockerfile                 # HF Spaces deployment
├── requirements.txt
└── .streamlit/config.toml
```
