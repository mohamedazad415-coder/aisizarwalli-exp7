const EXPERIMENT = "EXP-009";
const SOURCE = "moltbook_exp009";
const ALLOWED_ORIGIN = "https://mohamedazad415-coder.github.io";

const ALLOWED_EVENTS = new Set([
  "landing_page_view",
  "engaged_5s",
  "engaged_15s",
  "artwork_open",
]);
const ALLOWED_VARIANTS = new Set(["CONTROL", "TREATMENT"]);

function cors(origin) {
  const ok = origin === ALLOWED_ORIGIN;
  return {
    "Access-Control-Allow-Origin": ok ? origin : "null",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Vary": "Origin",
    "Cache-Control": "no-store",
  };
}
function json(body,status=200,headers={}) {
  return new Response(JSON.stringify(body),{
    status,
    headers:{"Content-Type":"application/json; charset=utf-8",...headers},
  });
}
function validSessionId(value) {
  return typeof value === "string" &&
    value.length >= 8 && value.length <= 128 &&
    /^[A-Za-z0-9-]+$/.test(value);
}
async function lifecycle(env) {
  let row = await env.DB.prepare(
    "SELECT status, launch_utc, maximum_end_utc FROM exp009_control WHERE experiment=?"
  ).bind(EXPERIMENT).first();

  if (!row) {
    return {status:"PRELAUNCH",launch_utc:null,maximum_end_utc:null};
  }

  if (row.status === "RUNNING") {
    const counts = await env.DB.prepare(
      `SELECT
        COUNT(DISTINCT CASE WHEN variant='CONTROL' AND event_name='landing_page_view' THEN session_id END) AS control_sessions,
        COUNT(DISTINCT CASE WHEN variant='TREATMENT' AND event_name='landing_page_view' THEN session_id END) AS treatment_sessions
       FROM exp009_events`
    ).first();

    const controlSessions = Number(counts?.control_sessions || 0);
    const treatmentSessions = Number(counts?.treatment_sessions || 0);
    const now = new Date();
    const end = row.maximum_end_utc ? Date.parse(row.maximum_end_utc) : NaN;

    let stopReason = null;
    if (controlSessions >= 12 && treatmentSessions >= 12) {
      stopReason = "SESSION_THRESHOLD_REACHED";
    } else if (Number.isFinite(end) && now.getTime() >= end) {
      stopReason = "MAXIMUM_DURATION_REACHED";
    }

    if (stopReason) {
      const closedAt = now.toISOString();
      await env.DB.prepare(
        "UPDATE exp009_control SET status='CLOSED', updated_at=? WHERE experiment=? AND status='RUNNING'"
      ).bind(closedAt,EXPERIMENT).run();

      await env.DB.prepare(
        `INSERT OR IGNORE INTO exp009_closure
         (experiment,stop_reason,closed_at,control_sessions,treatment_sessions)
         VALUES (?,?,?,?,?)`
      ).bind(
        EXPERIMENT,stopReason,closedAt,controlSessions,treatmentSessions
      ).run();

      row = await env.DB.prepare(
        "SELECT status, launch_utc, maximum_end_utc FROM exp009_control WHERE experiment=?"
      ).bind(EXPERIMENT).first();
    }
  }

  const closure = await env.DB.prepare(
    "SELECT stop_reason, closed_at, control_sessions, treatment_sessions FROM exp009_closure WHERE experiment=?"
  ).bind(EXPERIMENT).first();

  return closure ? {...row,...closure} : row;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const origin = request.headers.get("Origin") || "";
    const headers = cors(origin);

    if (request.method === "OPTIONS") {
      if (origin !== ALLOWED_ORIGIN) return new Response(null,{status:403,headers});
      return new Response(null,{status:204,headers});
    }

    if (url.pathname === "/health" && request.method === "GET") {
      const state = await lifecycle(env);
      return json({
        ok:true, experiment:EXPERIMENT, storage:"D1",
        deduplication:true, lifecycle:state
      },200,headers);
    }

    if (url.pathname === "/stats" && request.method === "GET") {
      const state = await lifecycle(env);
      const rows = await env.DB.prepare(
        `SELECT variant,
           COUNT(DISTINCT CASE WHEN event_name='landing_page_view' THEN session_id END) AS sessions,
           COUNT(DISTINCT CASE WHEN event_name='engaged_5s' THEN session_id END) AS engaged_5s,
           COUNT(DISTINCT CASE WHEN event_name='engaged_15s' THEN session_id END) AS engaged_15s,
           COUNT(DISTINCT CASE WHEN event_name='artwork_open' THEN session_id END) AS artwork_opens
         FROM exp009_events
         GROUP BY variant
         ORDER BY variant`
      ).all();
      const totals = await env.DB.prepare(
        "SELECT COUNT(*) AS total_events, MIN(received_at) AS first_event, MAX(received_at) AS last_event FROM exp009_events"
      ).first();
      return json({
        experiment:EXPERIMENT,
        aggregate_only:true,
        lifecycle:state,
        variants:rows.results || [],
        totals:totals || {}
      },200,headers);
    }

    if (url.pathname !== "/event" || request.method !== "POST") {
      return json({ok:false,error:"not_found"},404,headers);
    }
    if (origin !== ALLOWED_ORIGIN) {
      return json({ok:false,error:"origin_not_allowed"},403,headers);
    }

    const state = await lifecycle(env);
    if (state.status !== "RUNNING") {
      return json({ok:false,error:"experiment_not_running",status:state.status},409,headers);
    }

    let body;
    try { body = await request.json(); }
    catch { return json({ok:false,error:"invalid_json"},400,headers); }

    if (
      body?.experiment !== EXPERIMENT ||
      body?.source !== SOURCE ||
      !ALLOWED_VARIANTS.has(body?.variant) ||
      !ALLOWED_EVENTS.has(body?.event_name) ||
      !validSessionId(body?.session_id)
    ) {
      return json({ok:false,error:"invalid_event"},400,headers);
    }

    const clientTs =
      typeof body.client_ts === "string" && body.client_ts.length <= 64
        ? body.client_ts : null;

    const result = await env.DB.prepare(
      `INSERT OR IGNORE INTO exp009_events
       (experiment,variant,session_id,event_name,source,client_ts,received_at)
       VALUES (?,?,?,?,?,?,?)`
    ).bind(
      EXPERIMENT,body.variant,body.session_id,body.event_name,
      SOURCE,clientTs,new Date().toISOString()
    ).run();

    return json({ok:true,duplicate:result.meta?.changes === 0},200,headers);
  }
};
