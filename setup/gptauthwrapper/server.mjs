#!/usr/bin/env node
import http from 'node:http';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

const HOME = os.homedir();
const AUTH_PATH = process.env.GPTAUTHWRAPPER_AUTH_PATH || process.env.CODEX_AUTH_PATH || path.join(HOME, '.codex', 'auth.json');
const HOST = process.env.GPTAUTHWRAPPER_HOST || process.env.CODEX_SHIM_HOST || '127.0.0.1';
const PORT = Number(process.env.GPTAUTHWRAPPER_PORT || process.env.CODEX_SHIM_PORT || 4141);
const OAUTH_CLIENT_ID = 'app_EMoamEEZ73f0CkXaXp7hrann';
const OAUTH_ISSUER = 'https://auth.openai.com';
const CODEX_API_ENDPOINT = 'https://chatgpt.com/backend-api/codex/responses';
const REFRESH_AFTER_MS = Number(process.env.GPTAUTHWRAPPER_REFRESH_AFTER_MS || 45 * 60 * 1000);
const DEFAULT_MODEL = process.env.GPTAUTHWRAPPER_DEFAULT_MODEL || 'gpt-5.4';
const DEFAULT_REASONING_EFFORT = process.env.GPTAUTHWRAPPER_DEFAULT_REASONING_EFFORT || '';
const DEFAULT_INSTRUCTIONS =
  process.env.GPTAUTHWRAPPER_DEFAULT_INSTRUCTIONS ||
  'You are a helpful assistant. Follow the user request exactly and keep the response concise.';
const EXPOSE_RAW_UPSTREAM = String(process.env.GPTAUTHWRAPPER_EXPOSE_RAW_UPSTREAM || '').toLowerCase() === 'true';
const EFFORT_MODEL_ALIASES = {
  'gpt-5.4-low': { baseModel: 'gpt-5.4', effort: 'low' },
  'gpt-5.4-medium': { baseModel: 'gpt-5.4', effort: 'medium' },
  'gpt-5.4-high': { baseModel: 'gpt-5.4', effort: 'high' },
  'gpt-5.4-xhigh': { baseModel: 'gpt-5.4', effort: 'xhigh' },
};
const SUPPORTED_MODELS = [
  'gpt-5.4',
  ...Object.keys(EFFORT_MODEL_ALIASES),
  'gpt-5.3-codex',
  'gpt-5.2',
  'gpt-5.2-codex',
  'gpt-5.1-codex',
  'gpt-5.1-codex-max',
  'gpt-5.1-codex-mini',
];

async function readAuth() {
  const raw = await fs.readFile(AUTH_PATH, 'utf8');
  return JSON.parse(raw);
}

async function writeAuth(data) {
  await fs.writeFile(AUTH_PATH, JSON.stringify(data, null, 2));
}

async function refreshAccessToken(refreshToken) {
  const body = new URLSearchParams({
    grant_type: 'refresh_token',
    refresh_token: refreshToken,
    client_id: OAUTH_CLIENT_ID,
  });

  const response = await fetch(`${OAUTH_ISSUER}/oauth/token`, {
    method: 'POST',
    headers: { 'content-type': 'application/x-www-form-urlencoded' },
    body,
  });

  if (!response.ok) {
    throw new Error(`Token refresh failed: ${response.status} ${await response.text()}`);
  }

  return response.json();
}

function decodeJwtClaims(token) {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return undefined;
    return JSON.parse(Buffer.from(parts[1], 'base64url').toString('utf8'));
  } catch {
    return undefined;
  }
}

function extractAccountId(tokens) {
  const candidates = [tokens?.id_token, tokens?.access_token].filter(Boolean);
  for (const token of candidates) {
    const claims = decodeJwtClaims(token);
    const accountId =
      claims?.chatgpt_account_id ||
      claims?.['https://api.openai.com/auth']?.chatgpt_account_id ||
      claims?.organizations?.[0]?.id;
    if (accountId) return accountId;
  }
}

function isAccessTokenUsable(accessToken) {
  const claims = decodeJwtClaims(accessToken);
  if (!claims?.exp) return false;
  // Usable if more than 60s before expiry
  return claims.exp > Math.floor(Date.now() / 1000) + 60;
}

let _lastAuthHealth = { ok: true, error: null, checkedAt: Date.now() };

function getAuthHealth() {
  return { ..._lastAuthHealth };
}

async function ensureAccessAuth() {
  const auth = await readAuth();
  if (!auth?.tokens?.access_token || !auth?.tokens?.refresh_token) {
    _lastAuthHealth = { ok: false, error: 'auth.json missing access_token/refresh_token', checkedAt: Date.now() };
    throw new Error('Codex auth.json does not contain access_token/refresh_token');
  }

  const lastRefresh = auth.last_refresh ? Date.parse(auth.last_refresh) : 0;
  const ageMs = lastRefresh ? Date.now() - lastRefresh : Number.POSITIVE_INFINITY;
  if (ageMs > REFRESH_AFTER_MS) {
    try {
      const refreshed = await refreshAccessToken(auth.tokens.refresh_token);
      auth.tokens.access_token = refreshed.access_token;
      auth.tokens.refresh_token = refreshed.refresh_token || auth.tokens.refresh_token;
      if (refreshed.id_token) auth.tokens.id_token = refreshed.id_token;
      auth.tokens.account_id = extractAccountId(refreshed) || auth.tokens.account_id;
      auth.last_refresh = new Date().toISOString();
      await writeAuth(auth);
      _lastAuthHealth = { ok: true, error: null, checkedAt: Date.now() };
    } catch (refreshErr) {
      // Race condition: another process (Codex CLI) may have already refreshed.
      // Re-read auth.json — it may now contain a valid token.
      const freshAuth = await readAuth();
      const freshLastRefresh = freshAuth.last_refresh ? Date.parse(freshAuth.last_refresh) : 0;
      if (freshLastRefresh > lastRefresh && isAccessTokenUsable(freshAuth.tokens.access_token)) {
        _lastAuthHealth = { ok: true, error: null, checkedAt: Date.now() };
        return {
          accessToken: freshAuth.tokens.access_token,
          accountId: freshAuth.tokens.account_id || extractAccountId(freshAuth.tokens),
        };
      }

      // Fallback: use existing access token if it hasn't expired yet
      if (isAccessTokenUsable(auth.tokens.access_token)) {
        console.error(`[GPTAuthWrapper] Refresh failed but access token still valid, using it: ${refreshErr.message}`);
        _lastAuthHealth = { ok: false, error: `refresh_failed_using_cached: ${refreshErr.message}`, checkedAt: Date.now() };
        return {
          accessToken: auth.tokens.access_token,
          accountId: auth.tokens.account_id || extractAccountId(auth.tokens),
        };
      }

      // No recovery possible — token is expired and refresh failed
      _lastAuthHealth = { ok: false, error: `refresh_failed_token_expired: ${refreshErr.message}`, checkedAt: Date.now() };
      throw new Error(`Token refresh failed and access token expired. Run 'codex login' to re-authenticate. Original error: ${refreshErr.message}`);
    }
  }

  _lastAuthHealth = { ok: true, error: null, checkedAt: Date.now() };
  return {
    accessToken: auth.tokens.access_token,
    accountId: auth.tokens.account_id || extractAccountId(auth.tokens),
  };
}

function mapChatMessages(messages = []) {
  const instructions = [];
  const input = [];

  for (const msg of messages) {
    if (msg?.role === 'system') {
      const text = Array.isArray(msg.content)
        ? msg.content.map((part) => part?.text || '').join('\n')
        : String(msg.content || '');
      if (text.trim()) instructions.push(text.trim());
      continue;
    }

    const contentParts = Array.isArray(msg.content)
      ? msg.content
      : [{ type: 'text', text: String(msg.content || '') }];

    const mappedParts = [];
    for (const part of contentParts) {
      if (typeof part === 'string') {
        if (part.trim()) mappedParts.push(msg.role === 'assistant'
          ? { type: 'output_text', text: part }
          : { type: 'input_text', text: part });
        continue;
      }
      if (part?.type === 'text' || part?.type === 'input_text') {
        if (part.text?.trim()) {
          mappedParts.push(msg.role === 'assistant'
            ? { type: 'output_text', text: part.text }
            : { type: 'input_text', text: part.text });
        }
        continue;
      }
      if (msg.role !== 'assistant' && part?.type === 'image_url' && part.image_url?.url) {
        mappedParts.push({
          type: 'input_image',
          image_url: part.image_url.url,
          detail: part.image_url.detail,
        });
      }
    }

    if (!mappedParts.length) continue;

    if (msg.role === 'assistant') {
      input.push({
        role: 'assistant',
        content: mappedParts,
      });
    } else {
      input.push({
        role: 'user',
        content: mappedParts,
      });
    }
  }

  return {
    instructions: instructions.join('\n\n'),
    input,
  };
}

function resolveReasoningConfig(body, aliasEffort = '') {
  const requestedEffort =
    body.reasoning_effort ||
    body.reasoningEffort ||
    body?.reasoning?.effort ||
    aliasEffort ||
    DEFAULT_REASONING_EFFORT;

  const requestedSummary = body.reasoning_summary || body?.reasoning?.summary;
  const requestedEnabled = body.reasoning_enabled;

  if (!requestedEffort && requestedSummary == null && requestedEnabled == null) {
    return body.reasoning;
  }

  return {
    ...(body.reasoning && typeof body.reasoning === 'object' ? body.reasoning : {}),
    ...(requestedEffort ? { effort: requestedEffort } : {}),
    ...(requestedSummary ? { summary: requestedSummary } : {}),
    ...(requestedEnabled != null ? { enabled: Boolean(requestedEnabled) } : {}),
  };
}

function mapIncomingRequest(body, endpointKind) {
  let input;
  let instructions;
  const requestedModel = body.model || DEFAULT_MODEL;
  const aliasConfig = EFFORT_MODEL_ALIASES[requestedModel];
  const model = aliasConfig?.baseModel || requestedModel;

  if (endpointKind === 'chat.completions') {
    const mapped = mapChatMessages(body.messages || []);
    input = mapped.input;
    instructions = mapped.instructions;
  } else {
    input = body.input ?? '';
    instructions = body.instructions || body.system || '';
  }

  if (typeof input === 'string') {
    input = [
      {
        role: 'user',
        content: [{ type: 'input_text', text: input }],
      },
    ];
  }

  if (!instructions) instructions = DEFAULT_INSTRUCTIONS;

  return {
    model,
    instructions,
    input,
    store: false,
    stream: true,
    reasoning: resolveReasoningConfig(body, aliasConfig?.effort),
    tools: body.tools,
    tool_choice: body.tool_choice,
    // Note: Codex backend rejects max_output_tokens — omit it entirely.
    // Clients (e.g. LiteLLM) may send max_output_tokens or max_tokens,
    // but the Codex API uses its own internal limits.
    // The Codex responses endpoint also rejects temperature entirely.
    // Some OpenAI-compatible clients send it by default (often as 1.0),
    // so we intentionally omit it here.
  };
}

function parseSseTranscript(raw) {
  const events = [];
  let eventName = 'message';
  let dataLines = [];

  const flush = () => {
    if (!dataLines.length) return;
    const dataText = dataLines.join('\n');
    let parsed;
    try {
      parsed = JSON.parse(dataText);
    } catch {
      parsed = dataText;
    }
    events.push({ event: eventName, data: parsed });
    eventName = 'message';
    dataLines = [];
  };

  for (const line of raw.split(/\r?\n/)) {
    if (!line.trim()) {
      flush();
      continue;
    }
    if (line.startsWith('event:')) {
      eventName = line.slice(6).trim();
      continue;
    }
    if (line.startsWith('data:')) {
      dataLines.push(line.slice(5).trim());
    }
  }
  flush();
  return events;
}

function extractUpstreamSummary(rawText) {
  const events = parseSseTranscript(rawText);
  let responseMeta;
  let outputText = '';
  let usage;

  for (const entry of events) {
    const payload = entry.data;
    if (payload?.response && !responseMeta) responseMeta = payload.response;
    if (payload?.type === 'response.output_text.delta' && typeof payload.delta === 'string') {
      outputText += payload.delta;
    }
    if (payload?.type === 'response.output_text.done' && typeof payload.text === 'string' && !outputText) {
      outputText = payload.text;
    }
    if (payload?.type === 'response.completed' && payload?.response) {
      responseMeta = payload.response;
      usage = payload.response.usage;
    }
  }

  return { events, responseMeta, outputText, usage };
}

function normalizeOutputText(data) {
  if (typeof data?.output_text === 'string') return data.output_text;
  if (Array.isArray(data?.output)) {
    const texts = [];
    for (const item of data.output) {
      if (item?.type === 'message' && Array.isArray(item?.content)) {
        for (const content of item.content) {
          if (content?.type === 'output_text' && typeof content?.text === 'string') {
            texts.push(content.text);
          }
        }
      }
    }
    if (texts.length) return texts.join('\n');
  }
  return '';
}

function toOpenAIishResponse(upstream) {
  const text = normalizeOutputText(upstream);
  return {
    id: upstream.id || `shim_${Date.now()}`,
    object: 'response',
    created_at: upstream.created_at || Math.floor(Date.now() / 1000),
    model: upstream.model || 'gpt-5.4',
    output_text: text,
    output: upstream.output || [
      {
        id: `msg_${Date.now()}`,
        type: 'message',
        role: 'assistant',
        content: [{ type: 'output_text', text }],
      },
    ],
    usage: upstream.usage,
    raw_upstream: upstream,
  };
}

function resolveResponseModel(requestedModel, upstreamModel) {
  if (requestedModel && EFFORT_MODEL_ALIASES[requestedModel]) return requestedModel;
  return upstreamModel || requestedModel || 'gpt-5.4';
}

function toChatCompletionsResponse(summary, model) {
  return {
    id: summary.responseMeta?.id || `chatcmpl_${Date.now()}`,
    object: 'chat.completion',
    created: summary.responseMeta?.created_at || Math.floor(Date.now() / 1000),
    model: resolveResponseModel(model, summary.responseMeta?.model),
    choices: [
      {
        index: 0,
        message: {
          role: 'assistant',
          content: summary.outputText,
        },
        finish_reason: 'stop',
      },
    ],
    usage: summary.usage,
  };
}

function toChatCompletionsSse(summary, model) {
  const id = summary.responseMeta?.id || `chatcmpl_${Date.now()}`;
  const created = summary.responseMeta?.created_at || Math.floor(Date.now() / 1000);
  const usedModel = resolveResponseModel(model, summary.responseMeta?.model);
  const chunks = [];

  for (const entry of summary.events) {
    const payload = entry.data;
    if (payload?.type === 'response.output_text.delta' && typeof payload.delta === 'string') {
      chunks.push(
        `data: ${JSON.stringify({
          id,
          object: 'chat.completion.chunk',
          created,
          model: usedModel,
          choices: [{ index: 0, delta: { content: payload.delta }, finish_reason: null }],
        })}\n\n`,
      );
    }
  }

  chunks.push(
    `data: ${JSON.stringify({
      id,
      object: 'chat.completion.chunk',
      created,
      model: usedModel,
      choices: [{ index: 0, delta: {}, finish_reason: 'stop' }],
    })}\n\n`,
  );
  chunks.push('data: [DONE]\n\n');
  return chunks.join('');
}

const server = http.createServer(async (req, res) => {
  try {
    if (req.method === 'GET' && req.url === '/health') {
      const authHealth = getAuthHealth();
      let tokenStatus = 'unknown';
      try {
        const auth = await readAuth();
        if (auth?.tokens?.access_token) {
          tokenStatus = isAccessTokenUsable(auth.tokens.access_token) ? 'valid' : 'expired';
        } else {
          tokenStatus = 'missing';
        }
      } catch { tokenStatus = 'unreadable'; }
      const healthy = authHealth.ok && tokenStatus !== 'expired' && tokenStatus !== 'missing';
      res.writeHead(healthy ? 200 : 503, { 'content-type': 'application/json' });
      res.end(JSON.stringify({
        ok: healthy,
        host: HOST,
        port: PORT,
        auth_path: AUTH_PATH,
        default_model: DEFAULT_MODEL,
        auth: {
          token_status: tokenStatus,
          last_refresh_ok: authHealth.ok,
          last_error: authHealth.error,
          checked_at: new Date(authHealth.checkedAt).toISOString(),
        },
      }));
      return;
    }

    if (req.method === 'GET' && req.url === '/v1/models') {
      res.writeHead(200, { 'content-type': 'application/json' });
      res.end(
        JSON.stringify({
          object: 'list',
          data: SUPPORTED_MODELS.map((id) => ({ id, object: 'model', owned_by: 'chatgpt-codex-oauth' })),
        }),
      );
      return;
    }

    if (req.method !== 'POST' || !['/v1/responses', '/v1/chat/completions'].includes(req.url)) {
      res.writeHead(404, { 'content-type': 'application/json' });
      res.end(JSON.stringify({ error: 'not found' }));
      return;
    }

    const chunks = [];
    for await (const chunk of req) chunks.push(chunk);
    const body = JSON.parse(Buffer.concat(chunks).toString('utf8'));
    const endpointKind = req.url === '/v1/chat/completions' ? 'chat.completions' : 'responses';

    const { accessToken, accountId } = await ensureAccessAuth();
    const mapped = mapIncomingRequest(body, endpointKind);

    const headers = {
      'content-type': 'application/json',
      authorization: `Bearer ${accessToken}`,
      origin: 'https://chatgpt.com',
      referer: 'https://chatgpt.com/',
    };

    if (accountId) headers['ChatGPT-Account-Id'] = accountId;

    const upstreamResponse = await fetch(CODEX_API_ENDPOINT, {
      method: 'POST',
      headers,
      body: JSON.stringify(mapped),
    });

    const text = await upstreamResponse.text();
    let json;
    try {
      json = JSON.parse(text);
    } catch {
      json = { raw_text: text };
    }

    if (!upstreamResponse.ok) {
      res.writeHead(upstreamResponse.status, { 'content-type': 'application/json' });
      res.end(JSON.stringify({ upstream_status: upstreamResponse.status, upstream: json }, null, 2));
      return;
    }

    const summary = json.raw_text ? extractUpstreamSummary(json.raw_text) : null;

    if (endpointKind === 'chat.completions') {
      if (body.stream) {
        res.writeHead(200, { 'content-type': 'text/event-stream; charset=utf-8' });
        res.end(toChatCompletionsSse(summary, body.model));
        return;
      }

      res.writeHead(200, { 'content-type': 'application/json' });
      res.end(JSON.stringify(toChatCompletionsResponse(summary, body.model), null, 2));
      return;
    }

    const payload = summary
        ? {
            id: summary.responseMeta?.id || `shim_${Date.now()}`,
            object: 'response',
            created_at: summary.responseMeta?.created_at || Math.floor(Date.now() / 1000),
            model: resolveResponseModel(body.model, summary.responseMeta?.model),
            output_text: summary.outputText,
          output: [
            {
              id: `msg_${Date.now()}`,
              type: 'message',
              role: 'assistant',
              content: [{ type: 'output_text', text: summary.outputText }],
            },
          ],
          usage: summary.usage,
          ...(EXPOSE_RAW_UPSTREAM ? { raw_upstream: json.raw_text } : {}),
        }
      : toOpenAIishResponse(json);

    res.writeHead(200, { 'content-type': 'application/json' });
    res.end(JSON.stringify(payload, null, 2));
  } catch (error) {
    res.writeHead(500, { 'content-type': 'application/json' });
    res.end(JSON.stringify({ error: String(error?.message || error) }, null, 2));
  }
});

server.listen(PORT, HOST, () => {
  console.log(`GPTAuthwrapper listening on http://${HOST}:${PORT}`);
  console.log(`Auth path: ${AUTH_PATH}`);

  // Proactive background refresh — keeps the token chain alive even with zero traffic.
  // Runs every REFRESH_AFTER_MS (default 45min). If the server sits idle for days,
  // the refresh token won't go stale because this timer keeps renewing it.
  const proactiveRefresh = async () => {
    try {
      await ensureAccessAuth();
      console.log(`[proactive-refresh] OK at ${new Date().toISOString()}`);
    } catch (err) {
      console.error(`[proactive-refresh] FAILED: ${err.message}`);
    }
  };
  setInterval(proactiveRefresh, REFRESH_AFTER_MS);
  // Also run once on startup after a short delay
  setTimeout(proactiveRefresh, 5000);
});
