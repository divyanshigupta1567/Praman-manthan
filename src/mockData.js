// mockData.js
// Shape-accurate placeholder data. Every field name here matches the locked
// schema contract exactly — swap these for real fetch calls (see api.js)
// without touching any component.

export const mockComplaints = [
  {
    complaint_id: "PRM-1320",
    complaint_text: "Streetlight has been out for 2 weeks near the bus stop.",
    category: "Streetlight",
    predicted_category: "Streetlight",
    confidence: 0.94,
    latitude: 27.4924,
    longitude: 77.6737,
    locality: "Vrindavan Road",
    timestamp: "2026-09-14T18:20:00Z",
    status: "Open",
    image_url: null,
    user_id: null,
  },
  {
    complaint_id: "PRM-1171",
    complaint_text: "Garbage not collected on Krishna Nagar main road for 4 days.",
    category: "Sanitation",
    predicted_category: "Sanitation",
    confidence: 0.88,
    latitude: 27.4931,
    longitude: 77.6702,
    locality: "Krishna Nagar",
    timestamp: "2026-09-15T09:05:00Z",
    status: "Pending Verification",
    image_url: null,
    user_id: null,
  },
  {
    complaint_id: "PRM-1217",
    complaint_text: "Open manhole cover, dangerous for two-wheelers at night.",
    category: "Roads",
    predicted_category: "Roads",
    confidence: 0.81,
    latitude: 27.4918,
    longitude: 77.6759,
    locality: "Vrindavan Road",
    timestamp: "2026-09-16T21:40:00Z",
    status: "In Progress",
    image_url: null,
    user_id: null,
  },
];

export const mockIncidents = [
  {
    incident_id: "INC-004",
    category: "Sanitation",
    locality: "Krishna Nagar",
    centroid_lat: 27.4931,
    centroid_lng: 77.6702,
    cluster_radius_km: 0.6,
    complaint_count: 14,
    similar_complaint_count: 9,
    unresolved_count: 11,
    first_seen: "2026-09-10T08:00:00Z",
    last_seen: "2026-09-17T10:30:00Z",
    baseline: 3.2,
    current_volume: 14,
    z_score: 3.8,
    insufficient_history: false,
    spike_pct: 337.5,
    pressure_score: 0.91,
    severity_band: "High Pressure",
    auto_escalated: true,
    sample_complaint_ids: ["PRM-1171", "PRM-1180", "PRM-1183"],
  },
  {
    incident_id: "INC-011",
    category: "Roads",
    locality: "Vrindavan Road",
    centroid_lat: 27.4918,
    centroid_lng: 77.6759,
    cluster_radius_km: 0.9,
    complaint_count: 7,
    similar_complaint_count: 4,
    unresolved_count: 5,
    first_seen: "2026-09-13T12:00:00Z",
    last_seen: "2026-09-17T21:40:00Z",
    baseline: 2.0,
    current_volume: 7,
    z_score: 1.9,
    insufficient_history: false,
    spike_pct: 250,
    pressure_score: 0.58,
    severity_band: "Emerging",
    auto_escalated: false,
    sample_complaint_ids: ["PRM-1217", "PRM-1220"],
  },
  {
    incident_id: "INC-013",
    category: "Streetlight",
    locality: "Chaitanya Vihar",
    centroid_lat: 27.4956,
    centroid_lng: 77.6641,
    cluster_radius_km: 0.4,
    complaint_count: 2,
    similar_complaint_count: 1,
    unresolved_count: 2,
    first_seen: "2026-09-16T06:00:00Z",
    last_seen: "2026-09-17T08:00:00Z",
    baseline: 0,
    current_volume: 2,
    z_score: 0,
    insufficient_history: true,
    spike_pct: "N/A (new activity)",
    pressure_score: 0.22,
    severity_band: "Normal",
    auto_escalated: false,
    sample_complaint_ids: ["PRM-1320"],
  },
];

export const mockHotspots = mockIncidents.map((i) => ({
  incident_id: i.incident_id,
  centroid_lat: i.centroid_lat,
  centroid_lng: i.centroid_lng,
  severity_band: i.severity_band,
  category: i.category,
  locality: i.locality,
}));

export const mockMetrics = {
  total_complaints: 231,
  active_incidents: 3,
  emerging_incidents: 1,
  auto_escalated_incidents: 1,
};

export const mockTrends = [
  { date: "2026-09-13", category: "Sanitation", locality: "Krishna Nagar", complaint_count: 4, baseline: 3.2 },
  { date: "2026-09-14", category: "Sanitation", locality: "Krishna Nagar", complaint_count: 5, baseline: 3.2 },
  { date: "2026-09-15", category: "Sanitation", locality: "Krishna Nagar", complaint_count: 9, baseline: 3.2 },
  { date: "2026-09-16", category: "Sanitation", locality: "Krishna Nagar", complaint_count: 12, baseline: 3.2 },
  { date: "2026-09-17", category: "Sanitation", locality: "Krishna Nagar", complaint_count: 14, baseline: 3.2 },
];

export const mockBriefing = {
  generated_at: "2026-09-18T06:00:00Z",
  summary_text:
    "One incident has been auto-escalated overnight: sanitation reports in Krishna Nagar are running well above baseline. One additional cluster in Vrindavan Road is trending upward and worth watching today.",
  highlighted_incident_ids: ["INC-004", "INC-011"],
};

export const mockModelMetrics = {
  baseline_model: { name: "Logistic Regression", accuracy: 0.87, precision: 0.84, recall: 0.81, f1: 0.82 },
  comparison_model: { name: "Linear SVM", accuracy: 0.89, precision: 0.86, recall: 0.85, f1: 0.85 },
};
