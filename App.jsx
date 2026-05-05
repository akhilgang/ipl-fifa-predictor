import { useState, useEffect, useCallback } from "react";

const API_URL = process.env.REACT_APP_API_URL || "https://asfuo5zeki.execute-api.ap-south-1.amazonaws.com";

/* ── IPL teams for testing ── */
const IPL_TEAMS = [
  "Mumbai Indians", "Chennai Super Kings", "Royal Challengers Bangalore",
  "Kolkata Knight Riders", "Delhi Capitals", "Rajasthan Royals",
  "Punjab Kings", "Sunrisers Hyderabad", "Gujarat Titans", "Lucknow Super Giants",
];

const STAGES = ["League Stage", "Qualifier 1", "Eliminator", "Qualifier 2", "Final"];

const OUTCOME_COLORS = {
  win:  { bar: "#1D9E75", bg: "#E1F5EE", text: "#085041", label: "Win" },
  draw: { bar: "#BA7517", bg: "#FAEEDA", text: "#412402", label: "Draw" },
  loss: { bar: "#D85A30", bg: "#FAECE7", text: "#4A1B0C", label: "Loss" },
};

/* ── Mock for offline testing ── */
function mockPredict(home, away) {
  const seed = (home + away).split("").reduce((a, c) => a + c.charCodeAt(0), 0);
  const r = (n) => ((seed * 9301 + 49297) % 233280) / 233280;
  const raw = [r(), r() * 0.3, r() * 0.3];
  const sum = raw.reduce((a, b) => a + b, 0);
  const [win, draw, loss] = raw.map((v) => +(v / sum).toFixed(3));
  const outcome = win > draw && win > loss ? "win" : draw > loss ? "draw" : "loss";
  return { outcome, probabilities: [win, draw, loss] };
}

/* ── Probability bar ── */
function ProbBar({ label, value, color }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
        <span style={{ fontSize: 13, color: "var(--color-text-secondary)" }}>{label}</span>
        <span style={{ fontSize: 13, fontWeight: 500 }}>{(value * 100).toFixed(1)}%</span>
      </div>
      <div style={{ height: 8, background: "var(--color-background-secondary)", borderRadius: 4, overflow: "hidden" }}>
        <div style={{ width: `${value * 100}%`, height: "100%", background: color, borderRadius: 4, transition: "width 0.6s cubic-bezier(.4,0,.2,1)" }} />
      </div>
    </div>
  );
}

/* ── Prediction card ── */
function ResultCard({ result, home, away }) {
  if (!result) return null;
  const [win, draw, loss] = result.probabilities;
  const o = OUTCOME_COLORS[result.outcome];
  return (
    <div style={{ background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)", borderRadius: "var(--border-radius-lg)", padding: "1.25rem", marginTop: 16 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
        <div style={{ background: o.bg, color: o.text, borderRadius: "var(--border-radius-md)", padding: "4px 14px", fontSize: 13, fontWeight: 500 }}>
          {o.label}
        </div>
        <span style={{ fontSize: 14, color: "var(--color-text-secondary)" }}>
          {home} vs {away}
        </span>
      </div>
      <ProbBar label="Home win" value={win} color={OUTCOME_COLORS.win.bar} />
      <ProbBar label="Draw / No result" value={draw} color={OUTCOME_COLORS.draw.bar} />
      <ProbBar label="Away win" value={loss} color={OUTCOME_COLORS.loss.bar} />
    </div>
  );
}

/* ── Predict tab ── */
function PredictTab() {
  const [home, setHome] = useState(IPL_TEAMS[0]);
  const [away, setAway] = useState(IPL_TEAMS[1]);
  const [stage, setStage] = useState(STAGES[0]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [useMock, setUseMock] = useState(false);

  const predict = useCallback(async () => {
    if (home === away) { setError("Home and away teams must be different."); return; }
    setError("");
    setLoading(true);
    setResult(null);
    try {
      if (useMock) {
        await new Promise((r) => setTimeout(r, 600));
        setResult(mockPredict(home, away));
      } else {
        const res = await fetch(`${API_URL}/predict`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ home, away, stage }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        setResult(await res.json());
      }
    } catch (e) {
      setError(`API error: ${e.message}. Enable mock mode to test offline.`);
    } finally {
      setLoading(false);
    }
  }, [home, away, stage, useMock]);

  const selectStyle = {
    width: "100%", padding: "10px 12px", fontSize: 14,
    border: "0.5px solid var(--color-border-secondary)",
    borderRadius: "var(--border-radius-md)",
    background: "var(--color-background-primary)",
    color: "var(--color-text-primary)",
  };

  return (
    <div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
        <div>
          <label style={{ display: "block", fontSize: 12, color: "var(--color-text-secondary)", marginBottom: 6 }}>Home team</label>
          <select value={home} onChange={(e) => setHome(e.target.value)} style={selectStyle}>
            {IPL_TEAMS.map((t) => <option key={t}>{t}</option>)}
          </select>
        </div>
        <div>
          <label style={{ display: "block", fontSize: 12, color: "var(--color-text-secondary)", marginBottom: 6 }}>Away team</label>
          <select value={away} onChange={(e) => setAway(e.target.value)} style={selectStyle}>
            {IPL_TEAMS.map((t) => <option key={t}>{t}</option>)}
          </select>
        </div>
      </div>
      <div style={{ marginBottom: 16 }}>
        <label style={{ display: "block", fontSize: 12, color: "var(--color-text-secondary)", marginBottom: 6 }}>Stage</label>
        <select value={stage} onChange={(e) => setStage(e.target.value)} style={selectStyle}>
          {STAGES.map((s) => <option key={s}>{s}</option>)}
        </select>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
        <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: "var(--color-text-secondary)", cursor: "pointer" }}>
          <input type="checkbox" checked={useMock} onChange={(e) => setUseMock(e.target.checked)} />
          Mock mode (test without live API)
        </label>
      </div>

      <button
        onClick={predict}
        disabled={loading}
        style={{ width: "100%", padding: "10px 0", fontSize: 14, fontWeight: 500, cursor: loading ? "wait" : "pointer", opacity: loading ? 0.6 : 1 }}
      >
        {loading ? "Predicting…" : "Predict outcome"}
      </button>

      {error && (
        <div style={{ marginTop: 12, padding: "10px 14px", background: "var(--color-background-danger)", color: "var(--color-text-danger)", borderRadius: "var(--border-radius-md)", fontSize: 13 }}>
          {error}
        </div>
      )}
      <ResultCard result={result} home={home} away={away} />
    </div>
  );
}

/* ── Accuracy tab ── */
function AccuracyTab() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [useMock, setUseMock] = useState(false);

  const fetch_ = useCallback(async () => {
    setLoading(true);
    try {
      if (useMock) {
        await new Promise((r) => setTimeout(r, 500));
        setData({ total: 24, correct: 17, accuracy: 0.708, last_updated: new Date().toISOString() });
      } else {
        const res = await fetch(`${API_URL}/accuracy`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        setData(await res.json());
      }
    } catch { setData(null); }
    finally { setLoading(false); }
  }, [useMock]);

  useEffect(() => { fetch_(); }, [fetch_]);

  const statCard = (label, value) => (
    <div style={{ background: "var(--color-background-secondary)", borderRadius: "var(--border-radius-md)", padding: "1rem", textAlign: "center" }}>
      <div style={{ fontSize: 12, color: "var(--color-text-secondary)", marginBottom: 6 }}>{label}</div>
      <div style={{ fontSize: 24, fontWeight: 500 }}>{value}</div>
    </div>
  );

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
        <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: "var(--color-text-secondary)", cursor: "pointer" }}>
          <input type="checkbox" checked={useMock} onChange={(e) => { setUseMock(e.target.checked); }} />
          Mock mode
        </label>
        <button onClick={fetch_} disabled={loading} style={{ fontSize: 13 }}>
          {loading ? "Loading…" : "Refresh"}
        </button>
      </div>

      {data ? (
        <>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: 20 }}>
            {statCard("Accuracy", `${(data.accuracy * 100).toFixed(1)}%`)}
            {statCard("Correct", data.correct)}
            {statCard("Total", data.total)}
          </div>
          <div style={{ height: 12, background: "var(--color-background-secondary)", borderRadius: 6, overflow: "hidden", marginBottom: 12 }}>
            <div style={{ width: `${data.accuracy * 100}%`, height: "100%", background: "#1D9E75", borderRadius: 6, transition: "width 0.7s ease" }} />
          </div>
          <div style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>
            Last updated: {new Date(data.last_updated).toLocaleString()}
          </div>
        </>
      ) : (
        <div style={{ fontSize: 14, color: "var(--color-text-secondary)" }}>
          {loading ? "Loading stats…" : "No data yet. Enable mock mode or check the API."}
        </div>
      )}
    </div>
  );
}

/* ── Testing guide tab ── */
function TestingTab() {
  const steps = [
    { step: "1", title: "Enable mock mode", detail: "Toggle "Mock mode" on the Predict tab to get realistic responses without hitting AWS. Great for UI dev and Amplify deploys." },
    { step: "2", title: "Use IPL data locally", detail: "Download match data from cricsheet.org (JSON format, free). Write a small Python script to map it to your feature schema and call your Lambda directly via boto3 or cURL." },
    { step: "3", title: "Test Lambda with cURL", detail: 'curl -X POST https://your-api-id.execute-api.ap-south-1.amazonaws.com/predict \\\n  -H "Content-Type: application/json" \\\n  -d \'{"home":"MI","away":"CSK","stage":"League Stage"}\'' },
    { step: "4", title: "Seed DynamoDB manually", detail: "Use the AWS console or a script to PUT fake match items with actual_outcome=null. Then run your result-updater Lambda manually to test the accuracy flow." },
    { step: "5", title: "Use football-data.org sandbox", detail: "football-data.org's free tier gives historical World Cup data. Train on past tournaments, test predictions against known outcomes — you'll have ground truth for accuracy measurement without waiting for 2026." },
    { step: "6", title: "Switch to World Cup 2026 when ready", detail: "The tournament starts June 11, 2026. Your EventBridge trigger will start fetching live results automatically. Just swap IPL_TEAMS for WC nations in this frontend." },
  ];

  return (
    <div>
      {steps.map(({ step, title, detail }) => (
        <div key={step} style={{ display: "flex", gap: 16, marginBottom: 20 }}>
          <div style={{ flexShrink: 0, width: 28, height: 28, borderRadius: "50%", background: "var(--color-background-secondary)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, fontWeight: 500 }}>
            {step}
          </div>
          <div>
            <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 4 }}>{title}</div>
            <pre style={{ margin: 0, fontSize: 12, color: "var(--color-text-secondary)", whiteSpace: "pre-wrap", fontFamily: "var(--font-mono)", background: detail.startsWith("curl") ? "var(--color-background-secondary)" : "none", padding: detail.startsWith("curl") ? "10px 12px" : 0, borderRadius: detail.startsWith("curl") ? "var(--border-radius-md)" : 0 }}>
              {detail}
            </pre>
          </div>
        </div>
      ))}
    </div>
  );
}

/* ── Root app ── */
export default function App() {
  const [tab, setTab] = useState("predict");

  const tabs = [
    { id: "predict", label: "Predict" },
    { id: "accuracy", label: "Accuracy" },
    { id: "testing", label: "Testing guide" },
  ];

  return (
    <div style={{ minHeight: "100vh", background: "var(--color-background-tertiary, #f5f4f0)", padding: "2rem 1rem" }}>
      <div style={{ maxWidth: 560, margin: "0 auto" }}>
        {/* Header */}
        <div style={{ marginBottom: 32 }}>
          <h1 style={{ fontSize: 22, fontWeight: 500, margin: "0 0 4px" }}>Match Predictor</h1>
          <p style={{ fontSize: 14, color: "var(--color-text-secondary)", margin: 0 }}>
            ML inference · AWS Lambda · DynamoDB
          </p>
        </div>

        {/* Tabs */}
        <div style={{ display: "flex", gap: 4, marginBottom: 24, borderBottom: "0.5px solid var(--color-border-tertiary)", paddingBottom: 0 }}>
          {tabs.map(({ id, label }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              style={{
                background: "none", border: "none", borderBottom: tab === id ? "2px solid var(--color-text-primary)" : "2px solid transparent",
                padding: "8px 14px", fontSize: 14, fontWeight: tab === id ? 500 : 400,
                color: tab === id ? "var(--color-text-primary)" : "var(--color-text-secondary)",
                cursor: "pointer", borderRadius: 0, marginBottom: -1,
              }}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Tab body */}
        <div style={{ background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)", borderRadius: "var(--border-radius-lg)", padding: "1.5rem" }}>
          {tab === "predict" && <PredictTab />}
          {tab === "accuracy" && <AccuracyTab />}
          {tab === "testing" && <TestingTab />}
        </div>

        <p style={{ marginTop: 20, fontSize: 12, color: "var(--color-text-secondary)", textAlign: "center" }}>
          Currently testing with IPL 2026 · World Cup mode active Jun 11
        </p>
      </div>
    </div>
  );
}
