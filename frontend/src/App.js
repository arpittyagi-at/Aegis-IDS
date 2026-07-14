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

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";
const WS_URL = `${API_BASE.replace(/^http/, "ws")}/stream`;

function App() {
  const [stats, setStats] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [streamData, setStreamData] = useState([]);
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [mode, setMode] = useState("normal");
  const [dataset, setDataset] = useState("ciciot");
  const [dataSource, setDataSource] = useState("generated");  // "generated" or "real"
  const [metrics, setMetrics] = useState(null);
  const [selectedAlert, setSelectedAlert] = useState(null);

  // Fetch stats and data source on load
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
    const fetchDataSource = async () => {
      try {
        const response = await axios.get(`${API_BASE}/data-source`);
        setDataSource(response.data.data_source);
      } catch (err) {
        console.error("Failed to fetch data source");
      }
    };
    fetchStats();
    fetchDataSource();
    const interval = setInterval(() => {
      fetchStats();
      fetchDataSource();
    }, 3000); // ← poll every 3 seconds
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
          index: data.timestamp,  // Already in milliseconds from backend
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
        const response = await axios.get(`${API_BASE}/metrics?dataset=${dataset}`);
        setMetrics(response.data);
      } catch (err) {
        console.error("Failed to fetch metrics");
      }
    };
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000);
    return () => clearInterval(interval);
  }, [dataset]);

  const handleModeChange = async (newMode) => {
    try {
      await axios.post(`${API_BASE}/mode`, { mode: newMode, dataset });
      setMode(newMode);
    } catch (err) {
      setError("Failed to change mode");
    }
  };

  const handleDatasetChange = async (newDataset) => {
    setDataset(newDataset);
    try {
      await axios.post(`${API_BASE}/mode`, { mode, dataset: newDataset });
    } catch (err) {
      setError("Failed to change dataset");
    }
  };

  const handleDataSourceChange = async (newSource) => {
    try {
      await axios.post(`${API_BASE}/data-source`, {
        source: newSource,
      });
      setDataSource(newSource);
      // Clear stream data when switching sources for fresh view
      setStreamData([]);
    } catch (err) {
      setError("Failed to change data source");
    }
  };

  if (loading) {
    return <div className="loading">Loading AEGIS IDS Dashboard...</div>;
  }


  const totalEvents = stats?.total_analyzed ?? 0;
  const alertsRaised = stats?.total_attacks ?? 0;
  const detectionRate = totalEvents ? (alertsRaised / totalEvents) * 100 : 0;

  const getShapColor = (value) => (value < 0 ? "#ff5f5f" : "#19e68c");

  return (
    <div className="app">
      <div className="header">
        <h1>🛡️ AEGIS IDS Dashboard</h1>
        <p>
          Adaptive Explainable Generalized Intrusion Detection System with SHAP Explanations
        </p>
        <p style={{ fontSize: "12px", color: "#888", marginTop: "4px", letterSpacing: "0.05em" }}>
          Built by <span style={{ color: "#00d4ff", fontWeight: "bold" }}>Arpit Tyagi</span>
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
              <XAxis
                dataKey="index"
                stroke="#cccccc"
                tickFormatter={(v) => new Date(v).toLocaleTimeString()}
                interval="preserveStartEnd"
                tick={{ fontSize: 10 }}
              />
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
                      (stats?.total_analyzed || 0) - (stats?.total_attacks || 0),
                    fill: "#00ff88",
                  },
                  {
                    name: "Anomaly",
                    value: stats?.total_attacks || 0,
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
              <strong>Alert #{idx + 1}</strong> | Severity:{" "}
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
                            color: getShapColor(info.shap),
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
                            background: getShapColor(info.shap),
                            borderRadius: 3,
                          }}
                        />
                      </div>
                      <small style={{ color: "#888" }}>
                        raw value: {info.value}
                      </small>
                    </div>
                  ))}
                {/* Plain-English interpretation of the top SHAP feature */}
                {selectedAlert.shap_vals && Object.keys(selectedAlert.shap_vals).length > 0 && (() => {
                  const topFeatureName = Object.keys(selectedAlert.shap_vals)[0];
                  const topFeatureInfo = Object.values(selectedAlert.shap_vals)[0];
                  const rawVal = topFeatureInfo?.value;
                  const shapVal = topFeatureInfo?.shap;
                  const direction = topFeatureInfo?.direction;
                  const isAttack = direction === "attack";
                  return (
                    <div style={{
                      marginTop: 16,
                      padding: '12px 14px',
                      background: 'rgba(255,255,255,0.05)',
                      borderRadius: 6,
                      border: '1px solid rgba(255,107,107,0.3)',
                      fontSize: 13,
                      color: '#cccccc',
                      lineHeight: 1.6,
                    }}>
                      <strong style={{ color: '#00ff88' }}>📋 Interpretation: </strong>
                      The top signal was{' '}
                      <span style={{ color: '#00d4ff', fontFamily: 'monospace' }}>
                        {topFeatureName.replace(/_/g, ' ')}
                      </span>
                      {rawVal !== undefined && rawVal !== null ? (
                        <> with a raw value of{' '}
                          <span style={{ color: '#ffaa44', fontWeight: 'bold' }}>{rawVal}</span>
                        </>
                      ) : null}
                      {' '}(SHAP:{' '}
                      <span style={{ color: getShapColor(shapVal), fontWeight: 'bold' }}>
                        {shapVal >= 0 ? '+' : ''}{shapVal?.toFixed(4)}
                      </span>
                      ) — this feature strongly pushed the model toward an{' '}
                      <span style={{ color: '#ff6b6b', fontWeight: 'bold' }}>
                        {isAttack ? 'ATTACK' : 'NORMAL'}
                      </span>{' '}decision.
                      {' '}Model confidence:{' '}
                      <span style={{ color: '#ff6b6b', fontWeight: 'bold' }}>
                        {(selectedAlert.probability * 100).toFixed(1)}%
                      </span>
                      {' '}— above adaptive threshold of{' '}
                      <span style={{ color: '#ffaa44' }}>
                        {selectedAlert.threshold?.toFixed(3)}
                      </span>.
                    </div>
                  );
                })()}
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
          <label>Data Source:</label>
          <div style={{ display: "flex", gap: "10px", marginTop: "5px" }}>
            <button
              onClick={() => handleDataSourceChange("generated")}
              style={{ background: dataSource === "generated" ? "#00d4ff" : "#333", color: dataSource === "generated" ? "#000" : "#fff" }}
            >
              🤖 GENERATED ATTACKS
            </button>
            <button
              onClick={() => handleDataSourceChange("real")}
              style={{ background: dataSource === "real" ? "#00d4ff" : "#333", color: dataSource === "real" ? "#000" : "#fff" }}
            >
              📊 REAL DATASETS
            </button>
          </div>
        </div>

        <div className="control-group">
          <label>Traffic Mode (Generated Only):</label>
          <div style={{ display: "flex", gap: "10px", marginTop: "5px" }}>
            <button
              onClick={() => handleModeChange("normal")}
              style={{ background: mode === "normal" ? "#00ff88" : "#333", color: mode === "normal" ? "#000" : "#fff", opacity: dataSource === "generated" ? 1 : 0.5 }}
              disabled={dataSource === "real"}
            >
              🟢 NORMAL
            </button>
            <button
              onClick={() => handleModeChange("ddos")}
              style={{ background: mode === "ddos" ? "#ff6b6b" : "#333", color: mode === "ddos" ? "#fff" : "#fff", opacity: dataSource === "generated" ? 1 : 0.5 }}
              disabled={dataSource === "real"}
            >
              🔴 DDOS
            </button>
            <button
              onClick={() => handleModeChange("portscan")}
              style={{ background: mode === "portscan" ? "#ffaa44" : "#333", color: mode === "portscan" ? "#000" : "#fff", opacity: dataSource === "generated" ? 1 : 0.5 }}
              disabled={dataSource === "real"}
            >
              🟠 PORTSCAN
            </button>
            <button
              onClick={() => handleModeChange("mixed")}
              style={{ background: mode === "mixed" ? "#aa44ff" : "#333", color: "#fff", opacity: dataSource === "generated" ? 1 : 0.5 }}
              disabled={dataSource === "real"}
            >
              🟣 MIXED
            </button>
          </div>
        </div>

        <div className="control-group">
          <label htmlFor="dataset-select">Dataset:</label>
          <select
            id="dataset-select"
            value={dataset}
            onChange={(e) => handleDatasetChange(e.target.value)}
            style={{
              background: "rgba(0,0,0,0.4)",
              color: "#00d4ff",
              border: "1px solid #00d4ff",
              padding: "8px 12px",
              borderRadius: 5,
              fontSize: 13,
            }}
          >
            <option value="ciciot">CICIoT 2023 (IoT)</option>
            <option value="nslkdd">NSL-KDD (Classic)</option>
            <option value="unswnb15">UNSW-NB15 (Mixed)</option>
            <option value="cicids2017">CIC-IDS 2017 (Enterprise)</option>
          </select>
          {metrics?.metrics?.length > 0 && (
            <small style={{ color: "#cccccc", marginLeft: 12 }}>
              Best: {metrics.metrics[0].model} | F1 {metrics.metrics[0].f1}%
            </small>
          )}
        </div>

        <button onClick={() => window.location.reload()} style={{ marginTop: "15px" }}>
          🔄 Refresh Dashboard
        </button>
      </div>

      <div style={{
        textAlign: "center",
        padding: "20px",
        color: "#555",
        fontSize: "12px",
        borderTop: "1px solid rgba(255,255,255,0.07)",
        marginTop: "20px",
      }}>
        AEGIS IDS &mdash; Designed &amp; Built by{" "}
        <span style={{ color: "#00d4ff", fontWeight: "600" }}>Arpit Tyagi</span>
        {" "}| &copy; {new Date().getFullYear()}
      </div>
    </div>
  );
}

export default App;
