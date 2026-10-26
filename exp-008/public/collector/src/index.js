const EXPERIMENT = "EXP-008";
const ALLOWED_ORIGIN = "__EXP008_ALLOWED_ORIGIN__";

const ALLOWED_EVENTS = new Set([
  "page_view",
  "engaged_5s",
  "engaged_15s",
  "acquisition_details_click",
  "collector_intent_confirm",
  "collector_intent_decline",
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

function json(body, status = 200, headers = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      ...headers,
    },
  });
}

function validSessionId(value) {
  return typeof value === "string" &&
    value.length >= 8 &&
    value.length <= 128 &&
    /^[A-Za-z0-9-]+$/.test(value);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const origin = request.headers.get("Origin") || "";
    const headers = cors(origin);

    if (request.method === "OPTIONS") {
      if (origin !== ALLOWED_ORIGIN) {
        return new Response(null, { status: 403, headers });
      }
      return new Response(null, { status: 204, headers });
    }

    if (url.pathname === "/health" && request.method === "GET") {
      return json({
        ok: true,
        experiment: EXPERIMENT,
        storage: "D1",
        deduplication: true,
      }, 200, headers);
    }

    if (url.pathname === "/stats" && request.method === "GET") {
      const rows = await env.DB.prepare(
        `SELECT variant,
           COUNT(DISTINCT CASE WHEN event_name='page_view' THEN session_id END) AS sessions,
           COUNT(DISTINCT CASE WHEN event_name='acquisition_details_click' THEN session_id END) AS acquisition_details_clicks,
           COUNT(DISTINCT CASE WHEN event_name='collector_intent_confirm' THEN session_id END) AS collector_intent_confirms,
           COUNT(DISTINCT CASE WHEN event_name='collector_intent_decline' THEN session_id END) AS collector_intent_declines
         FROM exp008_events
         GROUP BY variant
         ORDER BY variant`
      ).all();

      return json({
        experiment: EXPERIMENT,
        aggregate_only: true,
        variants: rows.results || [],
      }, 200, headers);
    }

    if (url.pathname !== "/event" || request.method !== "POST") {
      return json({ ok: false, error: "not_found" }, 404, headers);
    }

    if (origin !== ALLOWED_ORIGIN) {
      return json({ ok: false, error: "origin_not_allowed" }, 403, headers);
    }

    let body;
    try {
      body = await request.json();
    } catch {
      return json({ ok: false, error: "invalid_json" }, 400, headers);
    }

    if (
      body?.experiment !== EXPERIMENT ||
      !ALLOWED_VARIANTS.has(body?.variant) ||
      !ALLOWED_EVENTS.has(body?.event_name) ||
      !validSessionId(body?.session_id)
    ) {
      return json({ ok: false, error: "invalid_event" }, 400, headers);
    }

    const clientTs =
      typeof body.client_ts === "string" && body.client_ts.length <= 64
        ? body.client_ts
        : null;

    const receivedAt = new Date().toISOString();

    const result = await env.DB.prepare(
      `INSERT OR IGNORE INTO exp008_events
       (experiment, variant, session_id, event_name, client_ts, received_at)
       VALUES (?, ?, ?, ?, ?, ?)`
    )
      .bind(
        EXPERIMENT,
        body.variant,
        body.session_id,
        body.event_name,
        clientTs,
        receivedAt
      )
      .run();

    return json({
      ok: true,
      duplicate: result.meta?.changes === 0,
    }, 200, headers);
  },
};
