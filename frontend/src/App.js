import React, { useState, useEffect } from "react";
import "./App.css";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from "recharts";
import axios from "axios";

function App() {
  const [stats, setStats] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [streamData, setStreamData] = useState([]);
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [mode, setMode] = useState("online");
  const [dataset, setDataset] = useState("unsw-nb15");
  const [metrics, setMetrics] = useState(null);
  const [selectedAlert, setSelectedAlert] = useState(null);

  const API_BASE = "http://localhost:8000";
  const WS_URL = "ws://localhost:8000/stream";

  // Fetch stats on load
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await axios.get(`${API_BASE}/stats`);
        setStats(response.data);
        setLoading(false);
        setError(null);
      } catch (err) {
        setError("Failed to connect to backend");
        setLoading(false);
      }
    };
    fetchStats();
    const interval = setInterval(fetchStats, 3000); // ← poll every 3 seconds
    return () => clearInterval(interval);
  }, []);

  // WebSocket connection for streaming data
  useEffect(() => {
    let ws;
    try {
      ws = new WebSocket(WS_URL);
      ws.onopen = () => {
        setConnected(true);
        setError(null);
      };
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        // Normalize data fields to match chart expectations
        const normalized = {
          ...data,
          index: Date.now(),
          prediction: data.probability,
          alert: data.is_attack,
        };

        setStreamData((prev) => [...prev.slice(-19), normalized]);

        if (normalized.alert) {
          setAlerts((prev) => [normalized, ...prev].slice(0, 10));
        }
      };
      ws.onerror = () => {
        setConnected(false);
      };
      ws.onclose = () => {
        setConnected(false);
      };
    } catch (err) {
      setConnected(false);
    }
    return () => ws && ws.close();
  }, []);

  // Fetch metrics
  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await axios.get(`${API_BASE}/metrics`);
        setMetrics(response.data);
      } catch (err) {
        console.error("Failed to fetch metrics");
      }
    };
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleModeChange = async (newMode) => {
    try {
      await axios.post(`${API_BASE}/mode`, { mode: newMode });
      setMode(newMode);
    } catch (err) {
      setError("Failed to change mode");
    }
  };

  const handleThresholdChange = async (value) => {
    try {
      await axios.post(`${API_BASE}/threshold`, {
        threshold: parseFloat(value),
      });
    } catch (err) {
      setError("Failed to update threshold");
    }
  };

  if (loading) {
    return <div className="loading">Loading AEGIS IDS Dashboard...</div>;
  }


  const totalEvents = stats?.total_analyzed ?? 0;
  const alertsRaised = stats?.total_attacks ?? 0;
  const detectionRate = totalEvents ? (alertsRaised / totalEvents) * 100 : 0;

  return (
    <div className="app">
      <div className="header">
        <h1>🛡️ AEGIS IDS Dashboard</h1>
        <p>
          Adaptive Engagement Guard for Intrusion Detection with SHAP
          Explanations
        </p>
        <div style={{ marginTop: "10px" }}>
          <span
            className="status-indicator"
            style={{ backgroundColor: connected ? "#00ff88" : "#ff4444" }}
            title={connected ? "Connected" : "Disconnected"}
          ></span>
          <span style={{ color: connected ? "#00ff88" : "#ff4444" }}>
            {connected ? "Live Streaming" : "Disconnected"}
          </span>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      <div className="stats-grid">
        <div className="stat-card">
          <h4>Total Events</h4>
          <p className="stat-value">{totalEvents}</p>
        </div>
        <div className="stat-card">
          <h4>Alerts Raised</h4>
          <p className="stat-value" style={{ color: "#ff6b6b" }}>
            {alertsRaised}
          </p>
        </div>
        <div className="stat-card">
          <h4>Detection Rate</h4>
          <p className="stat-value" style={{ color: "#00ff88" }}>
            {detectionRate.toFixed(2)}%
          </p>
        </div>
        <div className="stat-card">
          <h4>Threshold</h4>
          <p className="stat-value">
            {streamData.length > 0 && streamData[streamData.length - 1].threshold ? streamData[streamData.length - 1].threshold.toFixed(3) : "N/A"}
          </p>
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="chart-container">
          <h3>📊 Prediction Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={streamData}>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(255,255,255,0.1)"
              />
              <XAxis dataKey="index" stroke="#cccccc" />
              <YAxis stroke="#cccccc" />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1a1a1a",
                  border: "1px solid #00d4ff",
                }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="prediction"
                stroke="#00d4ff"
                dot={false}
                isAnimationActive={false}
              />
              <Line
                type="monotone"
                dataKey="threshold"
                stroke="#ff6b6b"
                dot={false}
                strokeDasharray="5 5"
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-container">
          <h3>🚨 Alert Status</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={[
                {
                  name: "Normal",
                  value:
                    (stats?.total_analyzed || 0) - (stats?.total_attacks || 0),
                },
                { name: "Anomaly", value: stats?.total_attacks || 0 },
              ]}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(255,255,255,0.1)"
              />
              <XAxis dataKey="name" stroke="#cccccc" />
              <YAxis stroke="#cccccc" />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1a1a1a",
                  border: "1px solid #00d4ff",
                }}
              />
              <Bar dataKey="value" fill="#00d4ff">
                {[
                  {
                    name: "Normal",
                    value:
                      (stats?.total_events || 0) - (stats?.alerts_raised || 0),
                    fill: "#00ff88",
                  },
                  {
                    name: "Anomaly",
                    value: stats?.alerts_raised || 0,
                    fill: "#ff6b6b",
                  },
                ].map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="alerts-panel">
        <h3>🚨 Recent Alerts ({alerts.length})</h3>
        {alerts.length === 0 ? (
          <p style={{ color: "#cccccc" }}>
            No alerts yet. System running smoothly!
          </p>
        ) : (
          alerts.map((alert, idx) => (
            <div
              key={idx}
              className={`alert-item ${alert.severity || "high"}`}
              onClick={() => setSelectedAlert(alert)}
              style={{ cursor: "pointer" }}
            >
              <strong>Alert #{alerts.length - idx}</strong> | Severity:{" "}
              {alert.severity?.toUpperCase() || "HIGH"}
              <br />
              <small>
                Risk: {alert.prediction?.toFixed(3) || "N/A"} | Threshold:{" "}
                {alert.threshold?.toFixed(3) || "N/A"}
              </small>
            </div>
          ))
        )}
      </div>

      {selectedAlert && (
        <div className="shap-panel">
          <h3>
            🔍 SHAP Explanation (Alert #{alerts.indexOf(selectedAlert) + 1})
          </h3>
          <button onClick={() => setSelectedAlert(null)}>Close</button>
          <div style={{ marginTop: "15px" }}>
            {selectedAlert.shap_vals ? (
              <>
                <div className="shap-explanation">
                  <strong>Prediction Value:</strong>{" "}
                  {selectedAlert.prediction?.toFixed(4) || "N/A"}
                  <br />
                  <strong>Threshold:</strong>{" "}
                  {selectedAlert.threshold?.toFixed(4) || "N/A"}
                  <br />
                  <strong>Alert Status:</strong>{" "}
                  {selectedAlert.alert ? "🔴 ANOMALY DETECTED" : "🟢 Normal"}
                </div>
                <h4 style={{ color: "#00ff88", marginTop: "15px" }}>
                  Top Contributing Features:
                </h4>
                {Object.entries(selectedAlert.shap_vals)
                  .slice(0, 5)
                  .map(([name, info], idx) => (
                    <div
                      key={idx}
                      className="shap-explanation"
                      style={{ marginTop: "8px" }}
                    >
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          marginBottom: 4,
                        }}
                      >
                        <span
                          style={{ color: "#00d4ff", fontFamily: "monospace" }}
                        >
                          {name.replace(/_/g, " ")}
                        </span>
                        <span
                          style={{
                            color:
                              info.direction === "attack"
                                ? "#ff6b6b"
                                : "#00ff88",
                            fontWeight: "bold",
                          }}
                        >
                          {info.shap >= 0 ? "+" : ""}
                          {info.shap?.toFixed(4)}
                        </span>
                      </div>
                      <div
                        style={{
                          background: "rgba(255,255,255,0.1)",
                          borderRadius: 3,
                          height: 6,
                        }}
                      >
                        <div
                          style={{
                            width: `${Math.abs(info.shap) * 300}%`,
                            maxWidth: "100%",
                            height: "100%",
                            background:
                              info.direction === "attack"
                                ? "#ff6b6b"
                                : "#00ff88",
                            borderRadius: 3,
                          }}
                        />
                      </div>
                      <small style={{ color: "#888" }}>
                        raw value: {info.value}
                      </small>
                    </div>
                  ))}
              </>
            ) : (
              <p style={{ color: "#cccccc" }}>
                No SHAP explanation available for this alert.
              </p>
            )}
          </div>
        </div>
      )}

      <div className="controls-panel">
        <div className="control-group">
          <label>Traffic Mode:</label>
          <div style={{ display: "flex", gap: "10px", marginTop: "5px" }}>
            <button
              onClick={() => handleModeChange("normal")}
              style={{ background: mode === "normal" ? "#00ff88" : "#333", color: mode === "normal" ? "#000" : "#fff" }}
            >
              🟢 NORMAL
            </button>
            <button
              onClick={() => handleModeChange("ddos")}
              style={{ background: mode === "ddos" ? "#ff6b6b" : "#333", color: mode === "ddos" ? "#fff" : "#fff" }}
            >
              🔴 DDOS
            </button>
            <button
              onClick={() => handleModeChange("portscan")}
              style={{ background: mode === "portscan" ? "#ffaa44" : "#333", color: mode === "portscan" ? "#000" : "#fff" }}
            >
              🟠 PORTSCAN
            </button>
          </div>
        </div>

        <div className="control-group">
          <label htmlFor="dataset-select">Dataset:</label>
          <select
            id="dataset-select"
            value={dataset}
            onChange={(e) => {
              setDataset(e.target.value);
              axios.post(`${API_BASE}/mode`, { mode, dataset: e.target.value });
            }}
          >
            <option value="ciciot">CICIoT 2023</option>
            <option value="nslkdd">NSL-KDD</option>
          </select>
        </div>

        <button onClick={() => window.location.reload()} style={{ marginTop: "15px" }}>
          🔄 Refresh Dashboard
        </button>
      </div>
    </div>
  );
}

export default App;
