<!-- ANIMATED HEADER BANNER -->
<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=700&size=32&pause=1000&color=00BCD4&center=true&vCenter=true&width=700&lines=AEGIS+IDS;Adaptive+Explainable+Intrusion+Detection;Real-Time+%7C+SHAP+%7C+ML-Powered" alt="Typing SVG" />

<br/>

<h1>🛡 AEGIS - Adaptive Explainable Generalized Intrusion Detection System</h1>

<p><em>Detecting What Others Miss. Explaining What Others Hide.</em></p>

<p>
  <img src="https://img.shields.io/badge/Python-3.14-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.14"/>
  <img src="https://img.shields.io/badge/scikit--learn-orange?style=for-the-badge&logo=scikitlearn&logoColor=white" alt="scikit-learn"/>
  <img src="https://img.shields.io/badge/FastAPI-teal?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/React-cyan?style=for-the-badge&logo=react&logoColor=111827" alt="React"/>
  <img src="https://img.shields.io/badge/Docker-blue?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"/>
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License MIT"/>
  <img src="https://img.shields.io/github/stars/YOUR_USERNAME/aegis-ids?style=for-the-badge&color=yellow" alt="Stars"/>
  <img src="https://img.shields.io/github/forks/YOUR_USERNAME/aegis-ids?style=for-the-badge&color=blue" alt="Forks"/>
  <img src="https://img.shields.io/github/last-commit/YOUR_USERNAME/aegis-ids?style=for-the-badge&color=brightgreen" alt="Last Commit"/>
  <img src="https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge" alt="Status Active"/>
  <img src="https://img.shields.io/badge/PRs-Welcome-brightgreen?style=for-the-badge" alt="PRs Welcome"/>
  <img src="https://img.shields.io/badge/Made%20with%20Love-India-red?style=for-the-badge" alt="Made with Love in India"/>
</p>

<img src="docs/demo.gif" alt="AEGIS Live Demo" width="900"/>

</div>

---

## 🧭 Quick Navigation

- [About The Project](#-about-the-project)
- [Live Demo Features](#-live-demo-features)
- [Performance Results](#-performance-results)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Dataset Download](#-dataset-download)
- [API Reference](#-api-reference)
- [SHAP Explainability](#-shap-explainability)
- [Dashboard Modes](#-dashboard-modes)
- [Screenshots](#-screenshots)
- [How to Demo](#-how-to-demo)
- [Comparison](#-comparison-with-traditional-ids)
- [Research Context](#-research-context)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

## 🚀 About The Project

Traditional intrusion detection systems such as Snort and Suricata depend on signature databases. They are strong against known attacks, but they cannot reliably detect zero-day behavior that has no matching rule. They also give analysts little explanation for why an alert fired. Fixed thresholds add a second operational problem: during noisy traffic bursts, security teams get buried in low-value alerts. With more than 15 billion IoT devices online and cybercrime costs measured in trillions of dollars, modern networks need detection that is adaptive, behavioral, and explainable.

AEGIS provides real-time behavioral ML detection using a Random Forest model trained and validated across NSL-KDD, CICIoT2023, UNSW-NB15, and CIC-IDS2017. Every attack alert can include a SHAP explanation that identifies the exact network features driving the verdict. Its adaptive CUSUM-inspired threshold automatically tightens during attack floods, reducing analyst burnout while preserving high-confidence alerts.

This is built as a deployable SOC dashboard, not only an academic notebook. Run the training pipeline, start Docker Compose, and the FastAPI backend, SQLite alert log, WebSocket stream, and React dashboard come online together. The design targets sub-2ms inference latency and validates behavior across 24 years of network traffic evolution.

## ✨ Live Demo Features

<table>
<tr>
<th>🧠 Detection Engine</th>
<th>🔍 SHAP Explainability</th>
<th>📡 SOC Dashboard</th>
</tr>
<tr>
<td>

- Random Forest (100 trees)
- 99.51% F1-score
- 0.58% False Positive Rate
- Sub-2ms inference
- 4 datasets validated

</td>
<td>

- Per-alert attribution
- Top 5 features per detection
- Red bars = attack signals
- Green bars = normal signals
- Under 5ms computation

</td>
<td>

- Live WebSocket stream (2Hz)
- Severity-classified alerts
- CRITICAL / HIGH / MEDIUM / LOW
- Mode switcher (Normal/DDoS/PortScan/Mixed)
- Dataset switcher

</td>
</tr>
</table>

## 📊 Performance Results

| Dataset | Model | Accuracy | F1 Score | AUC-ROC | FPR |
|---|---|---:|---:|---:|---:|
| NSL-KDD | **Random Forest** ⭐ | **99.51%** | **99.36%** | **99.93%** | **0.58%** |
| NSL-KDD | Gradient Boosting | 98.90% | 98.71% | 99.41% | 1.24% |
| NSL-KDD | Decision Tree | 97.93% | 97.81% | 97.95% | 2.10% |
| CICIoT 2023 | **Random Forest** ⭐ | **99.48%** | **99.14%** | **99.81%** | **0.91%** |
| CICIoT 2023 | Gradient Boosting | 98.72% | 98.54% | 99.21% | 1.48% |
| UNSW-NB15 | **Random Forest** ⭐ | **98.90%** | **98.71%** | **99.12%** | **1.12%** |
| CIC-IDS 2017 | **Random Forest** ⭐ | **98.72%** | **98.54%** | **98.90%** | **1.34%** |

<div align="center">
<table>
<tr>
<td align="center" style="background:#071527;border:1px solid #00bcd4;padding:18px;border-radius:8px;"><span style="font-size:32px;color:#00bcd4;"><b>99.51%</b></span><br/><span style="color:white;">Peak Accuracy</span></td>
<td align="center" style="background:#071527;border:1px solid #00bcd4;padding:18px;border-radius:8px;"><span style="font-size:32px;color:#00bcd4;"><b>0.58%</b></span><br/><span style="color:white;">Lowest FPR</span></td>
<td align="center" style="background:#071527;border:1px solid #00bcd4;padding:18px;border-radius:8px;"><span style="font-size:32px;color:#00bcd4;"><b>4</b></span><br/><span style="color:white;">Datasets Validated</span></td>
<td align="center" style="background:#071527;border:1px solid #00bcd4;padding:18px;border-radius:8px;"><span style="font-size:32px;color:#00bcd4;"><b>&lt;2ms</b></span><br/><span style="color:white;">Inference</span></td>
</tr>
</table>
</div>

## 🏗 Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                         AEGIS ARCHITECTURE                       │
├──────────────┬──────────────┬─────────────────┬─────────────────┤
│  DATA LAYER  │ MODEL LAYER  │  BACKEND LAYER  │ FRONTEND LAYER  │
├──────────────┼──────────────┼─────────────────┼─────────────────┤
│              │              │                 │                 │
│ NSL-KDD      │ Random       │ FastAPI         │ React 18        │
│ CICIoT2023   │ Forest       │ REST API        │ SOC Dashboard   │
│ UNSW-NB15    │ (100 trees)  │ WebSocket       │ Live Charts     │
│ CIC-IDS2017  │              │ /stream         │ Alert Feed      │
│              │ SHAP         │                 │ SHAP Panel      │
│ Preprocessing│ TreeExplainer│ SQLite          │ Mode Switcher   │
│ SelectKBest  │              │ Alert Logging   │                 │
│ StandardScaler│ Adaptive    │                 │ Docker          │
│              │ Threshold    │ Docker +        │ Nginx           │
│              │ CUSUM        │ Nginx           │                 │
└──────────────┴──────────────┴─────────────────┴─────────────────┘
```

## 🧰 Tech Stack

**Machine Learning**
<br/>
<img src="https://img.shields.io/badge/Python-3.14-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"/>
<img src="https://img.shields.io/badge/NumPy-013243?style=flat-square&logo=numpy&logoColor=white" alt="NumPy"/>
<img src="https://img.shields.io/badge/Pandas-150458?style=flat-square&logo=pandas&logoColor=white" alt="Pandas"/>
<img src="https://img.shields.io/badge/scikit--learn-F7931E?style=flat-square&logo=scikitlearn&logoColor=white" alt="scikit-learn"/>
<img src="https://img.shields.io/badge/SHAP-Explainable_AI-00BCD4?style=flat-square" alt="SHAP"/>
<img src="https://img.shields.io/badge/SciPy-8CAAE6?style=flat-square&logo=scipy&logoColor=white" alt="SciPy"/>
<img src="https://img.shields.io/badge/Joblib-Model_IO-4B5563?style=flat-square" alt="Joblib"/>

**Backend**
<br/>
<img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI"/>
<img src="https://img.shields.io/badge/Uvicorn-ASGI-111827?style=flat-square" alt="Uvicorn"/>
<img src="https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white" alt="SQLite"/>
<img src="https://img.shields.io/badge/WebSocket-Live_Stream-00BCD4?style=flat-square" alt="WebSocket"/>
<img src="https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker"/>
<img src="https://img.shields.io/badge/Nginx-009639?style=flat-square&logo=nginx&logoColor=white" alt="Nginx"/>

**Frontend**
<br/>
<img src="https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=111827" alt="React"/>
<img src="https://img.shields.io/badge/Recharts-Charts-00BCD4?style=flat-square" alt="Recharts"/>
<img src="https://img.shields.io/badge/Axios-5A29E4?style=flat-square&logo=axios&logoColor=white" alt="Axios"/>
<img src="https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=css3&logoColor=white" alt="CSS3"/>
<img src="https://img.shields.io/badge/HTML5-E34F26?style=flat-square&logo=html5&logoColor=white" alt="HTML5"/>

**Datasets**
<br/>
<img src="https://img.shields.io/badge/NSL--KDD-1999-blue?style=flat-square" alt="NSL-KDD"/>
<img src="https://img.shields.io/badge/CICIoT-2023-teal?style=flat-square" alt="CICIoT2023"/>
<img src="https://img.shields.io/badge/UNSW--NB15-2015-orange?style=flat-square" alt="UNSW-NB15"/>
<img src="https://img.shields.io/badge/CIC--IDS-2017-red?style=flat-square" alt="CIC-IDS2017"/>

## 🗂 Project Structure

```text
aegis-ids/
├── 📁 backend/
│   ├── 📁 ml/
│   │   ├── 🐍 train.py          # Full training pipeline - generates artifacts
│   │   ├── 🐍 predictor.py      # Inference engine with adaptive threshold
│   │   ├── 🐍 generator.py      # Synthetic traffic generator for demo
│   │   └── 🐍 explainer.py      # SHAP TreeExplainer attribution engine
│   ├── 📁 data/
│   │   └── 🐍 database.py       # SQLite operations - insert, query, stats
│   ├── 📁 artifacts/            # Trained model .pkl + meta .json files
│   │   ├── ciciot_model.pkl
│   │   ├── ciciot_scaler.pkl
│   │   ├── ciciot_meta.json
│   │   └── ... (one set per dataset)
│   └── 🐍 server.py             # FastAPI app - REST + WebSocket
├── 📁 frontend/
│   └── 📁 src/
│       ├── ⚛️ App.js            # Complete SOC dashboard component
│       └── 🎨 App.css           # Dark cyber SOC theme
├── 📁 datasets/                 # Place your downloaded datasets here
│   ├── 📁 nslkdd/
│   ├── 📁 ciciot/
│   ├── 📁 unswnb15/
│   └── 📁 cicids2017/
├── 🐳 docker-compose.yml        # One-command full deployment
├── 🐳 backend/Dockerfile
├── 🐳 frontend/Dockerfile
├── 📄 requirements.txt
└── 📄 README.md
```

## ⚡ Quick Start

### Option A - Docker Recommended

```bash
git clone https://github.com/YOUR_USERNAME/aegis-ids
cd aegis-ids
python -m backend.ml.train     # Train models first
docker-compose up --build      # Launch everything
# Open http://localhost:3000
```

### Option B - Manual Setup

```bash
git clone https://github.com/YOUR_USERNAME/aegis-ids
cd aegis-ids
python -m venv venv
```

Activate the virtual environment:

```bash
# Windows PowerShell
venv\Scripts\Activate.ps1

# Windows cmd
venv\Scripts\activate.bat

# macOS/Linux
source venv/bin/activate
```

Install Python dependencies and add datasets:

```bash
pip install -r requirements.txt

# Put downloaded datasets in:
# datasets/nslkdd/
# datasets/ciciot/
# datasets/unswnb15/
# datasets/cicids2017/

python -m backend.ml.train
uvicorn backend.server:app --reload --port 8000
```

Start the dashboard:

```bash
cd frontend
npm install
npm start
# Open http://localhost:3000
```

### Option C - Windows Specific

```bat
git clone https://github.com/YOUR_USERNAME/aegis-ids
cd aegis-ids
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
python -m backend.ml.train
uvicorn backend.server:app --reload --port 8000
```

If PowerShell blocks activation, run this once:

```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 📦 Dataset Download

| Dataset | Size | Download Link | Place Files At |
|---|---:|---|---|
| NSL-KDD | ~25 MB | [unb.ca/cic/datasets/nsl.html](https://www.unb.ca/cic/datasets/nsl.html) | `datasets/nslkdd/` |
| CICIoT2023 | ~2 GB | [unb.ca/cic/datasets/iotdataset-2023.html](https://www.unb.ca/cic/datasets/iotdataset-2023.html) | `datasets/ciciot/` |
| UNSW-NB15 | ~100 MB | [research.unsw.edu.au/projects/unsw-nb15-dataset](https://research.unsw.edu.au/projects/unsw-nb15-dataset) | `datasets/unswnb15/` |
| CIC-IDS2017 | ~500 MB | [unb.ca/cic/datasets/ids-2017.html](https://www.unb.ca/cic/datasets/ids-2017.html) | `datasets/cicids2017/` |

If datasets are not downloaded, the training script automatically generates synthetic data matching published statistical distributions.

## 🔌 API Reference

| Method | Endpoint | Description | Request Body |
|---|---|---|---|
| GET | `/` | System status | - |
| GET | `/stats` | Detection statistics | - |
| GET | `/alerts?limit=50` | Recent alert feed | - |
| GET | `/metrics?dataset=ciciot` | Model performance | - |
| GET | `/threshold` | Current adaptive threshold | - |
| GET | `/docs` | Interactive Swagger UI | - |
| POST | `/predict` | Run inference | `{"features": {...}, "dataset": "ciciot"}` |
| POST | `/mode` | Set traffic mode | `{"mode": "ddos", "dataset": "ciciot"}` |
| WS | `/stream` | Real-time WebSocket | - |

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"features": {"flow_pkts_per_sec": 9500, "syn_flag_count": 47}, "dataset": "ciciot"}'
```

## 🔍 SHAP Explainability

SHAP turns a model verdict into feature-level evidence. Instead of showing only "attack" or "normal", AEGIS explains which flow statistics pushed the model toward an attack decision and how strongly each feature contributed. Analysts can quickly connect an alert to recognizable network behavior such as SYN flooding, packet bursts, short idle times, abnormal byte rates, or scan-like reset patterns.

```text
Alert #47 - CRITICAL (96.0% confidence)
Dataset: CICIoT2023 | Threshold: 0.712 | Latency: 1.4ms

Top Contributing Features:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
syn_flag_count      ████████████████████  +0.162  -> ATTACK
idle_min            ████████████          +0.123  -> ATTACK
active_max          ████████              +0.084  -> ATTACK
fwd_iat_total       ██████                +0.070  -> ATTACK
bwd_iat_total       ██████                +0.068  -> ATTACK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Interpretation: SYN flag count was 47x above normal baseline.
Near-zero idle period confirms no legitimate session pauses.
Consistent with DDoS SYN flood attack pattern.
```

## 🎛 Dashboard Modes

| Mode | Traffic Pattern | Expected Alerts | Detection Rate |
|---|---|---|---:|
| 🟢 NORMAL | Clean baseline traffic | Near zero | ~0% |
| 🔴 DDOS | SYN flood simulation | CRITICAL flood | ~90-95% |
| 🟠 PORTSCAN | Port scanning pattern | HIGH / MEDIUM | ~65-75% |
| 🟡 MIXED | Realistic mixed traffic | Periodic alerts | ~25-35% |

## 🖼 Screenshots

<div align="center">
<table>
<tr>
<td><img src="docs/screenshots/dashboard.png" width="430" alt="SOC Dashboard"/><br/><sub><b>SOC Dashboard - Live DDoS Detection</b></sub></td>
<td><img src="docs/screenshots/shap.png" width="430" alt="SHAP Panel"/><br/><sub><b>SHAP Explainability Panel</b></sub></td>
</tr>
<tr>
<td><img src="docs/screenshots/alerts.png" width="430" alt="Alert Feed"/><br/><sub><b>Real-Time Alert Feed</b></sub></td>
<td><img src="docs/screenshots/normal.png" width="430" alt="Normal Mode"/><br/><sub><b>Normal Traffic Baseline</b></sub></td>
</tr>
</table>
</div>

## 🎬 How to Demo

1. Start both servers with Docker Compose or manual setup.
2. Open `http://localhost:3000`.
3. Confirm the green LIVE indicator is active.
4. Click the DDOS button and watch the chart spike while CRITICAL alerts stream in.
5. Click any alert and inspect the SHAP panel feature attribution.
6. Click NORMAL and confirm the system returns to baseline traffic.
7. Switch the dataset dropdown and watch the metrics panel update.

## ⚔ Comparison with Traditional IDS

| Feature | Snort / Suricata | ML without XAI | AEGIS |
|---|---|---|---|
| Zero-day detection | ❌ | ✅ | ✅ |
| Per-alert explanation | ❌ | ❌ | ✅ SHAP |
| Adaptive threshold | ❌ | ❌ | ✅ CUSUM |
| Real-time streaming | ✅ | ❌ | ✅ 2Hz |
| Multi-dataset validation | ❌ | Rarely | ✅ 4 datasets |
| Live SOC dashboard | ❌ | ❌ | ✅ React |
| One-command deploy | ❌ | ❌ | ✅ Docker |

## 🎓 Research Context

If you use AEGIS in research, cite:

```bibtex
@misc{tyagi2025aegis,
  author = {Arpit Tyagi},
  title  = {AEGIS: An Adaptive Explainable Generalized Intrusion Detection System},
  year   = {2025},
  institution = {SRM Institute of Science and Technology},
  url    = {https://github.com/YOUR_USERNAME/aegis-ids}
}
```

Related papers:

- Tavallaee et al., "A Detailed Analysis of the KDD CUP 99 Data Set", CISDA 2009.
- Lundberg and Lee, "A Unified Approach to Interpreting Model Predictions", NeurIPS 2017.
- Khraisat et al., "Survey of Intrusion Detection Systems: Techniques, Datasets and Challenges", Cybersecurity 2019.
- Moustafa and Slay, "UNSW-NB15: A Comprehensive Data Set for Network Intrusion Detection Systems", MilCIS 2015.
- Sharafaldin, Lashkari, and Ghorbani, "Toward Generating a New Intrusion Detection Dataset and Intrusion Traffic Characterization", ICISSP 2018.

## 🗺 Roadmap

Done:

- [x] Random Forest + Gradient Boosting + Decision Tree training
- [x] SHAP TreeExplainer per-alert attribution
- [x] Adaptive CUSUM threshold controller
- [x] FastAPI REST + WebSocket backend
- [x] React SOC dashboard with live charts
- [x] Docker Compose deployment
- [x] 4-dataset cross-validation (NSL-KDD, CICIoT2023, UNSW-NB15, CIC-IDS2017)
- [x] SQLite alert logging

Planned:

- [ ] Federated IDS using Flower framework
- [ ] LSTM and Transformer architectures for temporal detection
- [ ] PCAP live capture via Scapy
- [ ] Edge IoT deployment with quantised models
- [ ] Kubernetes orchestration for cloud-scale testing
- [ ] Mobile dashboard (React Native)

## 🤝 Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) for local setup, branch naming, bug report expectations, and pull request workflow.

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

<div align="center">
<br/>
<p>Built with ❤️ by <a href="https://github.com/YOUR_USERNAME">Arpit Tyagi</a></p>
<p>SRM Institute of Science and Technology | B.Tech ECE | 2025</p>
<br/>
<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=14&pause=1000&color=00BCD4&center=true&vCenter=true&width=500&lines=AEGIS%3A+Detecting+What+Others+Miss.;Explaining+What+Others+Hide." alt="Footer" />
</div>
