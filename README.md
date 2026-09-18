**PRAMAN - Civic Incident Intelligence Platform**

Turning scattered citizen complaints into meaningful incidents and
actionable civic intelligence.

**📌 Overview**

PRAMAN is an intelligent civic incident analysis platform designed
to transform individual citizen complaints into structured,
evidence-based incident intelligence.

A single complaint may represent an isolated issue. However, when
multiple citizens report similar problems from the same locality within
a short period of time, those complaints can indicate a larger emerging
civic incident.

PRAMAN identifies these hidden patterns by combining:

🤖 Machine Learning

🔎 Natural Language Processing

📍 Geospatial Analysis

📈 Time-Series Analysis

🧩 Incident Clustering

⚡ Pressure Scoring

The platform goes beyond simply counting complaints. It analyzes what
is being reported, where it is being reported, when it is happening, and
whether the activity is increasing unusually.

🎯 Problem

Civic authorities receive complaints related to issues such as:

🕳️ Potholes

🗑️ Garbage

💧 Water Leakage

💡 Streetlights

🚰 Sewage

🚦 Traffic Hazards

The challenge is not only to classify these complaints. The more
important task is to determine whether multiple complaints are connected
to the same real-world civic issue.

For example:

"Large pothole near the market"

"Deep pothole causing traffic problems"

"Road damaged near the market"

"Several potholes reported near the market"

Instead of treating these as four independent complaints, PRAMAN
analyzes their category, textual similarity, location, and time to
determine whether they form a common incident.

This transforms:

Individual Complaints → Related Patterns → Incidents → Actionable
Intelligence

💡 Solution

PRAMAN creates an end-to-end intelligence pipeline:

👤 Citizen
    ↓
📝 Complaint Submission
    ↓
🤖 AI Classification
    ↓
🔎 Text Similarity
    ↓
📍 Geographic Proximity
    ↓
🧩 Incident Clustering
    ↓
📈 Spike Detection
    ↓
⚡ Pressure Score
    ↓
🚨 Auto-Escalation
    ↓
📊 Authority Dashboard

Each stage contributes evidence to the final incident-level result.

🔄 How PRAMAN Works

1. 📝 Citizen Complaint Submission

The workflow begins when a citizen submits a complaint.

Input

Complaint description

Latitude

Longitude

Timestamp

Optional photo

The citizen does not need to manually select a category. PRAMAN
automatically predicts the category from the complaint text.

2. 🤖 AI-Based Complaint Classification

PRAMAN classifies incoming complaints into six civic categories:

Category            Example

🕳️ Pothole          Large pothole near the main road
🗑️ Garbage          Garbage has not been collected
💧 Water Leakage    Water pipeline is leaking
💡 Streetlight      Streetlight is not working
🚰 Sewage           Sewage water is overflowing
🚦 Traffic Hazard   Broken divider is creating a traffic hazard

Classification Pipeline

Complaint Text
      ↓
TF-IDF Vectorization
      ↓
Machine Learning Classifier
      ↓
Predicted Category
      +
Confidence Score

Models

Baseline: TF-IDF + Logistic Regression

Comparison: TF-IDF + Linear SVM

The models are evaluated using actual train/test results with:

Accuracy

Precision

Recall

F1 Score

3. 🔎 Text Similarity

After classification, PRAMAN checks whether a complaint is similar to
other recent complaints within the same category.

The system uses:

TF-IDF + Cosine Similarity

Similarity Interpretation

Similarity ≥ 0.85
        ↓
🟠 Potential Duplicate

0.55 ≤ Similarity < 0.85
        ↓
🟡 Potentially Related

Similarity < 0.55
        ↓
⚪ Unrelated

This helps identify complaints that may describe the same underlying
civic issue.

4. 📍 Geographic Proximity

Text similarity alone is not enough.

Two complaints may describe similar problems but occur in completely
different parts of a city.

PRAMAN therefore calculates the geographic distance between complaints
using Haversine Distance.

Default Radius

2 km

The radius can be configured within the intended range.

5. 🧩 Incident Clustering

This is the core intelligence layer of PRAMAN.

Complaints are connected using four signals:

🏷️ Same Category
       +
🔎 Text Similarity
       +
📍 Geographic Proximity
       +
⏱️ Time Window
       ↓
🧩 Incident Cluster

Two complaints can be connected when:

They belong to the same category

Text similarity is at least 0.55

Geographic distance is within 2 km

Their timestamps are within 72 hours

Connected complaints are grouped into incident clusters.

A cluster must contain at least 3 complaints to become an incident.

🧠 Complaint vs Incident

This distinction is fundamental to PRAMAN.

Complaint

One citizen
    ↓
One report
    ↓
One individual observation

Incident

Multiple citizens
       ↓
Similar reports
       +
Nearby locations
       +
Similar time period
       ↓
Detected pattern
       ↓
🧩 Incident

For example:

25 Citizen Complaints
        ↓
Similarity + Location + Time
        ↓
Incident Clustering
        ↓
4 Meaningful Incidents

PRAMAN therefore focuses on discovering patterns, not simply
displaying complaint records.

6. 📈 Spike Detection

After incidents are identified, PRAMAN checks whether complaint activity
is increasing unusually.

For every:

Category + Locality

the system calculates a rolling 7-day baseline.

Analysis Flow

Historical Complaint Volume
            ↓
      Rolling Mean
            +
   Rolling Standard Deviation
            ↓
      Current Volume
            ↓
          Z-Score
            ↓
      Spike Detection

Z-Score

Z = (Current Volume - Rolling Mean)
    / Rolling Standard Deviation

The system handles insufficient historical data and zero standard
deviation cases safely.

It also calculates the percentage change from the baseline.

This allows PRAMAN to distinguish between normal complaint activity and
unusual increases.

7. ⚡ Pressure Score

Not every incident requires the same level of attention.

PRAMAN calculates a Pressure Score from 0 to 100 for every incident.

The score combines four signals:

Signal                   Weight

📈 Spike Magnitude          40%
🧩 Cluster Size             30%
⏱️ Incident Duration        20%
🔴 Unresolved Ratio         10%

Formula

Pressure Score =
    0.4 × Spike Magnitude
  + 0.3 × Cluster Size
  + 0.2 × Duration
  + 0.1 × Unresolved Ratio

Each component is normalized to a 0–100 scale before calculating the
final score.

8. 🚨 Severity & Auto-Escalation

The Pressure Score is converted into three severity levels:

0 – 59
🟢 NORMAL

60 – 79
🟡 EMERGING

80 – 100
🔴 HIGH PRESSURE
     ↓
🚨 AUTO-ESCALATED

High-pressure incidents are automatically surfaced on the dashboard so
that important patterns can be identified without manually reviewing
every complaint.

9. 🗺️ Hotspot Visualization

PRAMAN presents incident locations on an interactive map.

The map uses severity-based markers:

🟢 Normal

🟡 Emerging

🔴 High Pressure

This helps users quickly identify:

Areas with concentrated complaints

Emerging civic problems

High-pressure incidents

Geographic distribution of civic issues

10. 📊 Authority Dashboard

The final intelligence is presented through a centralized dashboard
designed for quick understanding.

Dashboard Components

┌───────────────────────────────────────────────┐
│                 📊 KEY METRICS                │
│                                               │
│ Total      Active       Emerging     Auto     │
│ Complaints Incidents    Incidents    Escalated│
│                                               │
├───────────────────────┬───────────────────────┤
│                       │                       │
│       🗺️ HOTSPOT      │ 🚨 TOP EMERGING       │
│          MAP          │      INCIDENTS        │
│                       │                       │
│    🟢  🟡  🔴         │    Incident A         │
│                       │    Incident B         │
│                       │    Incident C         │
│                       │                       │
├───────────────────────┴───────────────────────┤
│               📈 TREND ANALYSIS               │
├───────────────────────────────────────────────┤
│                📝 DAILY BRIEFING              │
└───────────────────────────────────────────────┘

Dashboard Provides

📊 Total Complaints

🚨 Active Incidents

🟡 Emerging Incidents

🔴 Auto-Escalated Incidents

🗺️ Geographic Hotspots

📈 Complaint and incident trends

📝 Daily Operations Briefing

🔍 Incident Evidence

🔍 Incident Evidence Panel

PRAMAN does not simply display an alert. It also provides the evidence
behind the detected incident.

When an incident is selected, the evidence panel displays:

🆔 Incident ID

🏷️ Category

📍 Area

📊 Number of Reports

📈 Baseline

⚡ Spike %

⏱️ Time Window

🔎 Potentially Related Reports

🔴 Unresolved Reports

📍 Cluster Radius

⚡ Pressure Score

🚦 Incident Status

📝 Sample Complaints

This makes the detected intelligence traceable and interpretable.

📝 Daily Operations Briefing

PRAMAN generates a concise operations briefing from the computed
incident data.

The briefing uses information such as:

Incident counts

Complaint volume

Spike information

Pressure scores

Severity levels

Geographic activity

Unresolved complaints

The objective is to provide a quick operational summary without
requiring the user to inspect every individual complaint.

🏗️ System Architecture

                         👤 CITIZEN
                             │
                             ▼
                   ┌──────────────────┐
                   │ Complaint Form   │
                   │     React        │
                   └────────┬─────────┘
                            │
                            ▼
                   ┌──────────────────┐
                   │   Flask REST API │
                   └────────┬─────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
        🤖 CLASSIFIER   🔎 SIMILARITY   📍 GEO
              │             │             │
              └─────────────┼─────────────┘
                            │
                            ▼
                    🧩 CLUSTERING
                            │
                            ▼
                   📈 ANOMALY DETECTION
                            │
                            ▼
                     ⚡ PRESSURE SCORE
                            │
                            ▼
                     🚨 ESCALATION
                            │
                            ▼
                   📊 DASHBOARD
                    /          \
                   /            \
              🗺️ HOTSPOTS    📈 TRENDS
                   \            /
                    \          /
                     📝 BRIEFING

🛠️ Technology Stack

🤖 Machine Learning

Python

Pandas

NumPy

Scikit-learn

TF-IDF

Logistic Regression

Linear SVM

Cosine Similarity

📍 Geospatial Analysis

Haversine Distance

Geographic proximity analysis

Location-based clustering

📈 Analytics

Pandas time-window aggregation

Rolling 7-day mean

Rolling standard deviation

Z-score

Spike percentage

Pressure Score

⚙️ Backend

Flask

REST APIs

JSON

🎨 Frontend

React

Leaflet.js

Recharts / Plotly

🔧 Development

Git

GitHub

VS Code

📂 Project Structure

PRAMAN/
│
├── 📂 frontend/
│   ├── src/
│   ├── components/
│   └── ...
│
├── 📂 backend/
│   ├── app.py
│   └── ...
│
├── 📂 ml/
│   ├── classifier.py
│   ├── similarity.py
│   ├── clustering.py
│   ├── anomaly.py
│   └── pressure.py
│
├── 📂 scripts/
│   └── generate_data.py
│
├── 📂 data/
│   └── complaints.csv
│
├── 📄 requirements.txt
├── 📄 README.md
└── 📄 AI_USAGE_LOG.md

🔌 API Endpoints

Complaints

GET  /api/complaints
POST /api/complaints

Incidents & Analytics

GET /api/incidents
GET /api/metrics
GET /api/hotspots
GET /api/trends
GET /api/briefing

Model Metrics

GET /api/model-metrics

📊 Data Pipeline

PRAMAN works with structured complaint records containing:

complaint_id
complaint_text
category
latitude
longitude
locality
timestamp
status

The development dataset contains:

Multiple civic categories

Multiple localities

Time-distributed complaints

Seeded complaint spikes

Near-duplicate complaints

The seeded patterns help validate whether the intelligence pipeline can
discover meaningful incidents.

🧪 Model Validation

PRAMAN follows a proper train/test evaluation workflow.

Classification Metrics

🎯 Accuracy
🎯 Precision
🎯 Recall
🎯 F1 Score

Model Comparison

TF-IDF + Logistic Regression
              VS
TF-IDF + Linear SVM

The metrics are calculated from actual model predictions rather than
hardcoded values.

🌟 Key Features

Feature                  Description

🤖 AI Classification     Automatically categorizes citizen complaints
🔎 Text Similarity       Detects duplicate and related complaints
📍 Geographic Analysis   Finds geographically related complaints
🧩 Incident Clustering   Groups related complaints into incidents
📈 Spike Detection       Detects unusual increases in activity
⚡ Pressure Score        Quantifies incident pressure
🚨 Auto-Escalation       Flags high-pressure incidents
🗺️ Hotspot Map           Visualizes incident concentration
🔍 Evidence Panel        Shows evidence behind each incident
📊 Trend Analysis        Tracks complaint activity over time
📝 Daily Briefing        Summarizes computed civic intelligence

🚀 Getting Started

1. Clone the Repository

git clone <repository-url>
cd PRAMAN

2. Create a Virtual Environment

python -m venv venv

macOS / Linux

source venv/bin/activate

Windows

venv\Scripts\activate

3. Install Dependencies

pip install -r requirements.txt

4. Generate the Dataset

python scripts/generate_data.py

5. Start the Backend

python backend/app.py

6. Start the Frontend

cd frontend
npm install
npm run dev

Open the local URL displayed by the frontend development server.

🔮 Future Enhancements

📸 Image Intelligence

Analyze uploaded photographs to provide additional evidence for civic
issues.

🧠 Semantic Embeddings

Use embedding-based semantic similarity to improve matching beyond
traditional TF-IDF.

📱 Mobile Application

Provide a dedicated mobile interface for citizen reporting.

🔔 Real-Time Alerts

Send alerts when an incident crosses a configurable pressure threshold.

🗺️ Advanced Geospatial Analytics

Analyze recurring hotspots and spatial patterns across larger geographic
regions.

📊 Historical Analytics

Track recurring civic issues and long-term complaint trends.

🏙️ Municipal System Integration

Connect PRAMAN with existing civic complaint-management systems.

⚠️ Limitations

The current implementation is designed around a controlled set of civic
categories and a synthetic complaint dataset.

Real-world deployment would require:

Larger and more diverse datasets

Real municipal complaint data

Continuous model evaluation

Robust geospatial infrastructure

Production-grade API infrastructure

Security and privacy controls

Human validation for operational decisions

💭 The Core Idea

Traditional complaint systems often answer:

"How many complaints did we receive?"

PRAMAN goes one step further:

"What larger incident is emerging from these complaints?"

Individual Reports
        ↓
🔎 Find Patterns
        ↓
🧩 Form Incidents
        ↓
📈 Detect Spikes
        ↓
⚡ Measure Pressure
        ↓
🚨 Surface Priority
        ↓
📊 Civic Intelligence

🏙️ PRAMAN

From Complaints → Patterns → Incidents → Intelligence

Making civic problems easier to detect, understand, and prioritize.

⭐ Built with Python 🐍 | Machine Learning 🤖 | Data 📊 | React ⚛️ | Flask ⚙️
