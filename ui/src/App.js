import { useState, useEffect, useCallback } from 'react';
import './App.css';
import { api } from './api';

const IPL_TEAMS = [
  'Mumbai Indians', 'Chennai Super Kings', 'Royal Challengers Bengaluru',
  'Kolkata Knight Riders', 'Delhi Capitals', 'Sunrisers Hyderabad',
  'Rajasthan Royals', 'Punjab Kings', 'Lucknow Super Giants', 'Gujarat Titans',
];
const IPL_VENUES = [
  'Wankhede Stadium', 'M. A. Chidambaram Stadium', 'Eden Gardens',
  'M. Chinnaswamy Stadium', 'Arun Jaitley Stadium', 'Rajiv Gandhi Intl. Stadium',
  'Sawai Mansingh Stadium', 'Punjab Cricket Association Stadium',
  'BRSABV Ekana Cricket Stadium', 'Narendra Modi Stadium',
];
const FIFA_GROUPS = {
  A:['Mexico','South Africa','Korea Republic','Czechia'],
  B:['Canada','Bosnia Herzegovina','Qatar','Switzerland'],
  C:['Brazil','Morocco','Haiti','Scotland'],
  D:['USA','Paraguay','Australia','Turkey'],
  E:['Germany','Curacao','Cote dIvoire','Ecuador'],
  F:['Netherlands','Japan','Sweden','Tunisia'],
  G:['Belgium','Egypt','IR Iran','New Zealand'],
  H:['Spain','Cabo Verde','Saudi Arabia','Uruguay'],
  I:['France','Senegal','Iraq','Norway'],
  J:['Argentina','Algeria','Austria','Jordan'],
  K:['Portugal','Congo DR','Uzbekistan','Colombia'],
  L:['England','Croatia','Ghana','Panama'],
};
const FIFA_TEAMS  = Object.values(FIFA_GROUPS).flat().sort();
const FIFA_STAGES = ['group','round_of_32','round_of_16','quarterfinal','semifinal','final'];
const IPL_STAGES  = ['league','qualifier_1','eliminator','qualifier_2','final'];

function ProbBars({ data, sport }) {
  return (
    <div className="prob-bars">
      {Object.entries(data).map(([label, val]) => {
        const pct = Math.round(val * 100);
        const cls = sport === 'fifa'
          ? (label==='win' ? 'win' : label==='draw' ? 'draw' : 'loss')
          : (label===Object.keys(data)[0] ? 'ipl-t1' : 'ipl-t2');
        return (
          <div className="prob-row" key={label}>
            <div className="prob-meta">
              <span className="prob-name">{label}</span>
              <span className="prob-val">{pct}%</span>
            </div>
            <div className="prob-bar">
              <div className={`prob-fill ${cls}`} style={{ width:`${pct}%` }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
function Spinner() { return <span className="loading" />; }
function ErrorMsg({ msg }) { return msg ? <div className="error-msg">⚠ {msg}</div> : null; }

// ── IPL Predict ───────────────────────────────────────────────────────────────
function IPLPredict() {
  const [team1,setTeam1]   = useState('Mumbai Indians');
  const [team2,setTeam2]   = useState('Chennai Super Kings');
  const [venue,setVenue]   = useState(IPL_VENUES[0]);
  const [stage,setStage]   = useState('league');
  const [result,setResult] = useState(null);
  const [loading,setLoading] = useState(false);
  const [error,setError]   = useState('');

  async function predict() {
    if (team1===team2) { setError('Teams must be different'); return; }
    setLoading(true); setError(''); setResult(null);
    try { setResult(await api.predictIPL(team1,team2,venue,stage)); }
    catch(e) { setError(e.message); }
    finally { setLoading(false); }
  }

  return (
    <div>
      <div className="card">
        <div className="card-title">Match Details</div>
        <div className="form-row">
          <div className="field">
            <label>Team 1 (Batting First)</label>
            <select value={team1} onChange={e=>setTeam1(e.target.value)}>
              {IPL_TEAMS.map(t=><option key={t}>{t}</option>)}
            </select>
          </div>
          <div className="field">
            <label>Team 2 (Bowling First)</label>
            <select value={team2} onChange={e=>setTeam2(e.target.value)}>
              {IPL_TEAMS.map(t=><option key={t}>{t}</option>)}
            </select>
          </div>
        </div>
        <div className="form-row three">
          <div className="field">
            <label>Venue</label>
            <select value={venue} onChange={e=>setVenue(e.target.value)}>
              {IPL_VENUES.map(v=><option key={v}>{v}</option>)}
            </select>
          </div>
          <div className="field">
            <label>Stage</label>
            <select value={stage} onChange={e=>setStage(e.target.value)}>
              {IPL_STAGES.map(s=><option key={s}>{s}</option>)}
            </select>
          </div>
          <div className="field" style={{justifyContent:'flex-end'}}>
            <label>&nbsp;</label>
            <button className="btn btn-ipl" onClick={predict} disabled={loading}>
              {loading ? <Spinner /> : '⚡ Predict'}
            </button>
          </div>
        </div>
        <ErrorMsg msg={error} />
      </div>
      {result && (
        <div className="result-card ipl">
          <div className="result-label">Predicted Winner</div>
          <div className="result-winner ipl">{result.winner}</div>
          <ProbBars data={result.probabilities} sport="ipl" />
          <div style={{marginTop:'0.75rem',fontSize:'0.72rem',color:'var(--muted)',fontFamily:'var(--font-mono)'}}>
            match_id: {result.match_id}
          </div>
        </div>
      )}
    </div>
  );
}

// ── FIFA Predict ──────────────────────────────────────────────────────────────
function FIFAPredict() {
  const [home,setHome]     = useState('Brazil');
  const [away,setAway]     = useState('France');
  const [stage,setStage]   = useState('group');
  const [result,setResult] = useState(null);
  const [loading,setLoading] = useState(false);
  const [error,setError]   = useState('');

  async function predict() {
    if (home===away) { setError('Teams must be different'); return; }
    setLoading(true); setError(''); setResult(null);
    try { setResult(await api.predictFIFA(home,away,stage)); }
    catch(e) { setError(e.message); }
    finally { setLoading(false); }
  }

  return (
    <div>
      <div className="card">
        <div className="card-title">Match Details</div>
        <div className="form-row">
          <div className="field">
            <label>Home Team</label>
            <select value={home} onChange={e=>setHome(e.target.value)}>
              {FIFA_TEAMS.map(t=><option key={t}>{t}</option>)}
            </select>
          </div>
          <div className="field">
            <label>Away Team</label>
            <select value={away} onChange={e=>setAway(e.target.value)}>
              {FIFA_TEAMS.map(t=><option key={t}>{t}</option>)}
            </select>
          </div>
        </div>
        <div className="form-row three">
          <div className="field">
            <label>Stage</label>
            <select value={stage} onChange={e=>setStage(e.target.value)}>
              {FIFA_STAGES.map(s=><option key={s}>{s}</option>)}
            </select>
          </div>
          <div className="field" style={{justifyContent:'flex-end',gridColumn:'span 2'}}>
            <label>&nbsp;</label>
            <button className="btn btn-fifa" onClick={predict} disabled={loading}>
              {loading ? <Spinner /> : '⚡ Predict'}
            </button>
          </div>
        </div>
        <ErrorMsg msg={error} />
      </div>
      {result && (
        <div className="result-card fifa">
          <div className="result-label">Predicted Outcome (Home Team)</div>
          <div className="result-winner fifa">{result.outcome.toUpperCase()}</div>
          <ProbBars data={result.probabilities} sport="fifa" />
          <div style={{marginTop:'0.75rem',fontSize:'0.72rem',color:'var(--muted)',fontFamily:'var(--font-mono)'}}>
            match_id: {result.match_id}
          </div>
        </div>
      )}
    </div>
  );
}

// ── IPL Simulate — own component, own state ───────────────────────────────────
function IPLSimulate() {
  const [result,setResult]   = useState(null);
  const [loading,setLoading] = useState(false);
  const [error,setError]     = useState('');

  async function simulate() {
    setLoading(true); setError(''); setResult(null);
    try { const r = await api.simulateIPL(); setResult(r.simulation ?? r); }
    catch(e) { setError(e.message); }
    finally { setLoading(false); }
  }

  return (
    <div>
      <div className="card">
        <div className="card-title">IPL 2026 Playoff Qualification</div>
        <p style={{fontSize:'0.85rem',color:'var(--muted)',marginBottom:'1.2rem'}}>
          Monte Carlo simulation — each team's probability of finishing top 4 and
          winning the title. Results vary slightly each run (that's expected).
        </p>
        <button className="btn btn-ipl" onClick={simulate} disabled={loading}>
          {loading ? <><Spinner />&nbsp;Simulating...</> : '▶ Run IPL Simulation'}
        </button>
        <ErrorMsg msg={error} />
      </div>

      {result && (
        <div className="card" style={{animation:'fadeUp 0.3s ease'}}>
          <div className="card-title">
            Playoff Qualification Odds
            <span style={{float:'right',fontFamily:'var(--font-mono)',fontSize:'0.7rem',color:'var(--muted)'}}>
              n={result.simulations_run?.toLocaleString()} sims
            </span>
          </div>
          <table className="sim-table">
            <thead>
              <tr><th>#</th><th>Team</th><th>Playoff %</th><th>Win Title %</th></tr>
            </thead>
            <tbody>
              {Object.entries(result.playoff_probabilities || {})
                .sort((a,b) => b[1]-a[1])
                .map(([team,prob],i) => {
                  // handle both key variants from API
                  const winProb =
                    result.champion_probabilities?.[team] ??
                    result.champion_probability?.[team] ?? 0;
                  return (
                    <tr key={team}>
                      <td><span className={`rank-badge rank-${Math.min(i+1,3)}`}>{i+1}</span></td>
                      <td style={{fontWeight:500}}>{team}</td>
                      <td>
                        <div>{(prob*100).toFixed(1)}%</div>
                        <div className="mini-bar" style={{
                          background:`linear-gradient(90deg,var(--ipl) ${prob*100}%,var(--border2) ${prob*100}%)`
                        }}/>
                      </td>
                      <td style={{fontFamily:'var(--font-mono)',fontSize:'0.82rem',color:'var(--ipl)'}}>
                        {(winProb*100).toFixed(1)}%
                      </td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ── FIFA Simulate — own component, own state ──────────────────────────────────
function FIFASimulate() {
  const [result,setResult]   = useState(null);
  const [loading,setLoading] = useState(false);
  const [error,setError]     = useState('');

  async function simulate() {
    setLoading(true); setError(''); setResult(null);
    try { const r = await api.simulateFIFA(); setResult(r.simulation ?? r); }
    catch(e) { setError(e.message); }
    finally { setLoading(false); }
  }

  return (
    <div>
      <div className="card">
        <div className="card-title">FIFA World Cup 2026 Tournament Simulation</div>
        <p style={{fontSize:'0.85rem',color:'var(--muted)',marginBottom:'1.2rem'}}>
          Simulates the full tournament — group stage through the final.
          Results vary slightly each run.
        </p>
        <button className="btn btn-fifa" onClick={simulate} disabled={loading}>
          {loading ? <><Spinner />&nbsp;Simulating...</> : '▶ Run FIFA Simulation'}
        </button>
        <ErrorMsg msg={error} />
      </div>

      {result && (
        <div className="card" style={{animation:'fadeUp 0.3s ease'}}>
          <div className="card-title">
            Tournament Win Probabilities
            <span style={{float:'right',fontFamily:'var(--font-mono)',fontSize:'0.7rem',color:'var(--muted)'}}>
              n={result.simulations_run?.toLocaleString()} sims
            </span>
          </div>
          <table className="sim-table">
            <thead>
              <tr><th>#</th><th>Team</th><th>Group Advance %</th><th>Win Tournament %</th></tr>
            </thead>
            <tbody>
              {Object.entries(result.group_qualification || {})
                .sort((a,b) => b[1]-a[1])
                .slice(0,20)
                .map(([team,prob],i) => {
                  const winProb =
                    result.champion_probability?.[team] ??
                    result.champion_probabilities?.[team] ?? 0;
                  return (
                    <tr key={team}>
                      <td><span className={`rank-badge rank-${Math.min(i+1,3)}`}>{i+1}</span></td>
                      <td style={{fontWeight:500}}>{team}</td>
                      <td>
                        <div>{(prob*100).toFixed(1)}%</div>
                        <div className="mini-bar" style={{
                          background:`linear-gradient(90deg,var(--fifa) ${prob*100}%,var(--border2) ${prob*100}%)`
                        }}/>
                      </td>
                      <td style={{fontFamily:'var(--font-mono)',fontSize:'0.82rem',color:'var(--fifa)'}}>
                        {(winProb*100).toFixed(1)}%
                      </td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ── Simulate Tab — sport switcher only ────────────────────────────────────────
function SimulateTab() {
  const [sport,setSport] = useState('ipl');
  return (
    <div>
      <div className="sport-tabs">
        <button className={`sport-tab ${sport==='ipl'?'active-ipl':''}`}
          onClick={()=>setSport('ipl')}>🏏 IPL</button>
        <button className={`sport-tab ${sport==='fifa'?'active-fifa':''}`}
          onClick={()=>setSport('fifa')}>⚽ FIFA 2026</button>
      </div>
      {sport==='ipl'  && <IPLSimulate />}
      {sport==='fifa' && <FIFASimulate />}
    </div>
  );
}

// ── Accuracy Tab ──────────────────────────────────────────────────────────────
function AccuracyTab() {
  const [data,setData]       = useState(null);
  const [loading,setLoading] = useState(true);
  const [error,setError]     = useState('');

  const load = useCallback(async () => {
    setLoading(true); setError('');
    try { const r = await api.accuracy(); setData(r.stats); }
    catch(e) { setError(e.message); }
    finally { setLoading(false); }
  },[]);

  useEffect(()=>{ load(); },[load]);

  const fmt = item => {
    if (!item) return { pct:'—', sub:'no data' };
    const pct = item.accuracy!=null ? `${(parseFloat(item.accuracy)*100).toFixed(1)}%` : '—';
    return { pct, sub:`${item.correct??0} / ${item.total??0}` };
  };

  const statKeys = [
    {key:'overall',label:'Overall'},{key:'group_stage',label:'Group Stage'},
    {key:'round_of_16',label:'Round of 16'},{key:'quarterfinal',label:'QF'},
    {key:'semifinal',label:'SF'},{key:'final',label:'Final'},
  ];

  return (
    <div>
      <div className="card">
        <div className="card-title" style={{display:'flex',justifyContent:'space-between'}}>
          Model Accuracy
          <button className="btn btn-ghost" style={{padding:'4px 12px',fontSize:'0.78rem'}} onClick={load}>
            ↻ Refresh
          </button>
        </div>
        {loading && <p style={{color:'var(--muted)',fontSize:'0.85rem'}}>Loading...</p>}
        <ErrorMsg msg={error} />
        {data && !loading && (
          <>
            <div className="acc-grid">
              {statKeys.map(({key,label}) => {
                const {pct,sub} = fmt(data[key]);
                return (
                  <div className="acc-item" key={key}>
                    <div className="acc-label">{label}</div>
                    <div className="acc-pct" style={{
                      color:pct==='—'?'var(--muted)':parseFloat(pct)>=60?'var(--green)':'var(--text)'
                    }}>{pct}</div>
                    <div className="acc-sub">{sub}</div>
                  </div>
                );
              })}
            </div>
            {!data.overall && (
              <p style={{fontSize:'0.83rem',color:'var(--muted)',marginTop:'1rem'}}>
                No results recorded yet.
              </p>
            )}
          </>
        )}
      </div>
      <ManualResult />
    </div>
  );
}

function ManualResult() {
  const [sport,setSport]     = useState('ipl');
  const [matchId,setMatchId] = useState('');
  const [outcome,setOutcome] = useState('team1_wins');
  const [done,setDone]       = useState(false);
  const [loading,setLoading] = useState(false);
  const [error,setError]     = useState('');

  async function submit() {
    if (!matchId.trim()) { setError('Enter a match_id from a prediction'); return; }
    setLoading(true); setError(''); setDone(false);
    try { await api.submitResult(matchId.trim(),outcome,sport); setDone(true); setMatchId(''); }
    catch(e) { setError(e.message); }
    finally { setLoading(false); }
  }

  return (
    <div className="card">
      <div className="card-title">Submit Actual Result</div>
      <p style={{fontSize:'0.83rem',color:'var(--muted)',marginBottom:'1rem'}}>
        After each match, paste the match_id and enter the real outcome to track accuracy.
      </p>
      <div className="form-row three">
        <div className="field">
          <label>Sport</label>
          <select value={sport} onChange={e=>setSport(e.target.value)}>
            <option value="ipl">IPL</option><option value="fifa">FIFA</option>
          </select>
        </div>
        <div className="field">
          <label>Match ID</label>
          <input value={matchId} onChange={e=>setMatchId(e.target.value)}
            placeholder="e.g. IPL_MI_CSK_league"/>
        </div>
        <div className="field">
          <label>Actual Outcome</label>
          <select value={outcome} onChange={e=>setOutcome(e.target.value)}>
            {sport==='ipl'
              ? <><option value="team1_wins">Team 1 Won</option><option value="team2_wins">Team 2 Won</option></>
              : <><option value="win">Home Win</option><option value="draw">Draw</option><option value="loss">Away Win</option></>
            }
          </select>
        </div>
      </div>
      <button className="btn btn-ghost" onClick={submit} disabled={loading} style={{marginTop:'4px'}}>
        {loading ? <Spinner /> : 'Submit Result'}
      </button>
      {done && <div style={{color:'var(--green)',fontSize:'0.83rem',marginTop:'10px'}}>✓ Result recorded</div>}
      <ErrorMsg msg={error} />
    </div>
  );
}

// ── App shell ─────────────────────────────────────────────────────────────────
const TABS = [
  {id:'predict-ipl', label:'🏏 IPL',      cls:'ipl'},
  {id:'predict-fifa',label:'⚽ FIFA',      cls:'fifa'},
  {id:'simulate',    label:'📊 Simulate', cls:''},
  {id:'accuracy',    label:'🎯 Accuracy', cls:''},
];

export default function App() {
  const [tab,setTab] = useState('predict-ipl');
  const pageTitle = {
    'predict-ipl':  {main:'IPL',       accent:'ipl',  sub:'Predict the winner of any IPL 2026 match'},
    'predict-fifa': {main:'FIFA 2026', accent:'fifa', sub:'Predict match outcomes for the World Cup'},
    'simulate':     {main:'Simulate',  accent:'',     sub:'Monte Carlo playoff & qualification odds'},
    'accuracy':     {main:'Accuracy',  accent:'',     sub:'Track how well the model is doing'},
  }[tab];

  return (
    <div className="app">
      <header className="header">
        <div className="header-logo">◈ <span>IPL</span> × <em>FIFA</em></div>
        <nav className="nav">
          {TABS.map(t=>(
            <button key={t.id}
              className={`nav-btn ${tab===t.id?`active ${t.cls}`:''}`}
              onClick={()=>setTab(t.id)}>
              {t.label}
            </button>
          ))}
        </nav>
      </header>
      <main className="main">
        <div className="page-title">
          <span className={pageTitle.accent?`accent-${pageTitle.accent}`:''}>
            {pageTitle.main}
          </span>
        </div>
        <p className="page-sub">{pageTitle.sub}</p>
        {tab==='predict-ipl'  && <IPLPredict />}
        {tab==='predict-fifa' && <FIFAPredict />}
        {tab==='simulate'     && <SimulateTab />}
        {tab==='accuracy'     && <AccuracyTab />}
      </main>
    </div>
  );
}