const BASE = process.env.REACT_APP_API_URL || '';

async function call(path, method = 'GET', body = null) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : null,
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  const data = await res.json();

  return typeof data.body === 'string'
    ? JSON.parse(data.body)
    : data;
}

export const api = {
  predictIPL:  (team1, team2, venue, stage) =>
    call('/predict', 'POST', { sport: 'ipl', team1, team2, venue, stage }),

  predictFIFA: (home_team, away_team, stage) =>
    call('/predict', 'POST', { sport: 'fifa', home_team, away_team, stage }),

  simulateIPL: (points_table, remaining_fixtures) =>
    call('/simulate', 'POST', { sport: 'ipl', simulate: true, points_table, remaining_fixtures }),

  simulateFIFA: () =>
    call('/simulate', 'POST', { sport: 'fifa', simulate: true }),

  accuracy: () =>
    call('/accuracy', 'GET'),

  submitResult: (match_id, actual_outcome, sport) =>
    call('/result', 'POST', { match_id, actual_outcome, sport }),
};
