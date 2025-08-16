# 💸 Rupee Intelligence Platform for Trade (RIPT)

RIPT is an AI-powered platform for INR-based cross-border transactions, showcasing the Rupee’s global dominance through secure, scalable, and intelligent trade infrastructure. Built as a proof-of-concept for RBI-compliant trade settlement systems.

---

## 🚀 Features

- **Transaction Processing**  
  Handles INR transactions via Special Rupee Vostro Accounts (SRVA) for trade corridors:
  - India–Russia
  - India–EU
  - India–UK
  - India–Singapore

- **Security**  
  Hybrid AES-256/RSA encryption, SafeDataVault, and privacy budget management.

- **Fraud Detection**  
  AI-driven anomaly detection using:
  - Isolation Forest
  - Random Forest
  - DBSCAN

- **Analytics**  
  Interactive dashboards powered by Plotly for transaction and risk analysis.

- **QR Payments**  
  Mobile payment integration with QR code generation and scanning.

- **Compliance**  
  RBI-compliant XML/CSV exports and audit logging.

---

## 🏗️ System Architecture

| Layer       | Description |
|------------|-------------|
| **Frontend** | Streamlit-based single-page app with tabbed navigation and custom CSS |
| **Backend**  | Modular API layer (SRVA Manager, Transaction Processor, Exchange Rates) |
| **Database** | Dual support: MySQL (production), SQLite (development) |
| **Security** | Field-level encryption, pseudonymization, re-identification risk analysis |
| **Analytics**| Real-time TPS monitoring, ML-powered fraud detection, statistical analysis |

---

## 🧰 Prerequisites

- **Python**: 3.11 or higher
- **Database**:
  - Development: SQLite (included with Python)
  - Production: MySQL 8.0+

- **System Dependencies**:
  - Ubuntu:  
    `sudo apt-get install libgl1-mesa-glx libglib2.0-0`
  - Windows/macOS:  
    Handled automatically by `pip`

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd rupee-intelligence-platform-trade
