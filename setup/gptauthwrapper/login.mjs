#!/usr/bin/env node
/**
 * GPTAuthWrapper independent login — performs device-code OAuth against OpenAI
 * and writes tokens to its own auth file (not shared with Codex CLI).
 *
 * Usage: node scripts/login.mjs [--auth-path /path/to/auth.json]
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';

const OAUTH_CLIENT_ID = 'app_EMoamEEZ73f0CkXaXp7hrann';
const OAUTH_ISSUER = 'https://auth.openai.com';
const DEFAULT_AUTH_PATH = path.join(os.homedir(), '.gptauthwrapper', 'auth.json');

const authPath = (() => {
  const idx = process.argv.indexOf('--auth-path');
  return idx !== -1 && process.argv[idx + 1] ? process.argv[idx + 1] : DEFAULT_AUTH_PATH;
})();

async function deviceCodeGrant() {
  // Step 1: Request device code
  const dcResponse = await fetch(`${OAUTH_ISSUER}/oauth/device/code`, {
    method: 'POST',
    headers: { 'content-type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      client_id: OAUTH_CLIENT_ID,
      scope: 'openid profile email offline_access',
      audience: 'https://api.openai.com/v1',
    }),
  });

  if (!dcResponse.ok) {
    const text = await dcResponse.text();
    console.error(`Failed to get device code: ${dcResponse.status} ${text}`);
    process.exit(1);
  }

  const dc = await dcResponse.json();
  console.log('\n=== GPTAuthWrapper Login ===\n');
  console.log(`1. Open: ${dc.verification_uri_complete || dc.verification_uri}`);
  console.log(`2. Enter code: ${dc.user_code}`);
  console.log(`\n   Expires in ${Math.floor(dc.expires_in / 60)} minutes\n`);

  // Step 2: Poll for completion
  const interval = (dc.interval || 5) * 1000;
  const deadline = Date.now() + dc.expires_in * 1000;

  while (Date.now() < deadline) {
    await new Promise((r) => setTimeout(r, interval));

    const tokenResponse = await fetch(`${OAUTH_ISSUER}/oauth/token`, {
      method: 'POST',
      headers: { 'content-type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        grant_type: 'urn:ietf:params:oauth:grant-type:device_code',
        client_id: OAUTH_CLIENT_ID,
        device_code: dc.device_code,
      }),
    });

    if (tokenResponse.ok) {
      return tokenResponse.json();
    }

    const err = await tokenResponse.json().catch(() => ({}));
    if (err.error === 'authorization_pending') continue;
    if (err.error === 'slow_down') {
      await new Promise((r) => setTimeout(r, 5000));
      continue;
    }

    console.error(`Token exchange failed: ${JSON.stringify(err)}`);
    process.exit(1);
  }

  console.error('Device code expired. Run again.');
  process.exit(1);
}

function extractAccountId(tokens) {
  for (const token of [tokens.id_token, tokens.access_token].filter(Boolean)) {
    try {
      const claims = JSON.parse(Buffer.from(token.split('.')[1], 'base64url').toString('utf8'));
      const accountId =
        claims?.chatgpt_account_id ||
        claims?.['https://api.openai.com/auth']?.chatgpt_account_id ||
        claims?.organizations?.[0]?.id;
      if (accountId) return accountId;
    } catch {}
  }
}

const tokens = await deviceCodeGrant();

const authData = {
  auth_mode: 'chatgpt',
  tokens: {
    id_token: tokens.id_token || null,
    access_token: tokens.access_token,
    refresh_token: tokens.refresh_token,
    account_id: extractAccountId(tokens),
  },
  last_refresh: new Date().toISOString(),
};

await fs.mkdir(path.dirname(authPath), { recursive: true });
await fs.writeFile(authPath, JSON.stringify(authData, null, 2), { mode: 0o600 });

console.log(`\nTokens written to: ${authPath}`);
console.log(`Account: ${authData.tokens.account_id || 'unknown'}`);
console.log('\nGPTAuthWrapper will use this file independently from Codex CLI.');
