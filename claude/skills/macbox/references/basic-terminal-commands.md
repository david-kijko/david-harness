# Basic Terminal Commands for MacBox

## 1) Navigation and discovery

```bash
pwd
ls -la
cd /home/devuser/macos-intent
find . -maxdepth 2 -type f | head -n 50
```

## 2) Docker container checks

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
docker logs --tail 100 macos-intent
docker inspect macos-intent --format '{{json .Config.Env}}' | jq .
```

## 3) Container lifecycle actions

```bash
cd /home/devuser/macos-intent
docker compose up -d
docker compose restart
docker compose down
```

## 4) noVNC access verification

```bash
curl -I http://127.0.0.1:8006/
curl -s -u "$NOVNC_USER:$NOVNC_PASS" http://127.0.0.1:8006/ | head -n 40
```

Expected pattern:
- unauthenticated request returns `401` when auth is enabled
- authenticated request returns `200`

## 5) Credential readout

```bash
cd /home/devuser/macos-intent
grep -E '^(NOVNC_USER|NOVNC_PASS)=' .env
```

## 6) Paste/clipboard troubleshooting checks

```bash
curl -s -u "$NOVNC_USER:$NOVNC_PASS" http://127.0.0.1:8006/ | grep -n 'hardening.js\|clipboard'
```

If custom shortcut support is expected, confirm the page includes the script.

## 7) QEMU monitor quick checks (via container)

```bash
docker exec macos-intent sh -lc "echo 'info status' | nc -w 1 127.0.0.1 7100"
```

## 8) Safe command habits

- Confirm target before changes: `docker ps`, `pwd`
- Snapshot config before edits: `cp file file.bak.$(date +%s)`
- Verify after every action with an observable check
