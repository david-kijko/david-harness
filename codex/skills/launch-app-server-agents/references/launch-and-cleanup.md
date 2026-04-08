# Launch And Cleanup

## Check The Port First

```bash
ssh -i /home/david/.ssh/kijko_deploy_key -o BatchMode=yes root@157.90.215.60 \
  'ss -ltnp | grep 48765 || true'
```

If the port is busy, either stop the old listener first or pick a new loopback port.

## Start The Listener

Run the listener in its own SSH PTY session:

```bash
ssh -tt -i /home/david/.ssh/kijko_deploy_key -o BatchMode=yes root@157.90.215.60 \
  'sudo -u david bash -lc "codex app-server --listen ws://127.0.0.1:48765"'
```

Expected banner:

- `codex app-server (WebSockets)`
- `listening on: ws://127.0.0.1:48765`
- `readyz: http://127.0.0.1:48765/readyz`
- `healthz: http://127.0.0.1:48765/healthz`

## Health Check

```bash
ssh -i /home/david/.ssh/kijko_deploy_key -o BatchMode=yes root@157.90.215.60 \
  'curl -fsS http://127.0.0.1:48765/readyz && printf "\n" && curl -fsS http://127.0.0.1:48765/healthz'
```

## Start A Remote Client Session

For a real interactive client:

```bash
ssh -tt -i /home/david/.ssh/kijko_deploy_key -o BatchMode=yes root@157.90.215.60 \
  'sudo -u david bash -lc "cd /home/david && codex --remote ws://127.0.0.1:48765 --no-alt-screen \"<prompt>\""'
```

Notes:

- `codex exec` does not support `--remote`
- remote interactive sessions require a PTY
- expect update prompts and terminal control noise

## Clean Up

Stop the temporary client and listener with `Ctrl-C`, then verify the port is clear:

```bash
ssh -i /home/david/.ssh/kijko_deploy_key -o BatchMode=yes root@157.90.215.60 \
  'ss -ltnp | grep 48765 || true'
```

No output means the listener is gone.
