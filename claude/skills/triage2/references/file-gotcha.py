#!/usr/bin/env python3
"""Central triage filing registry: tie each repo to its Gotchas.md and index runs.

The Gotcha BODY always lives in-repo at <root>/Gotchas.md (committed with the fix,
so it travels with the code). This registry is the host-level filing system that
*recognises which repo* a run belongs to and points at where its Gotchas live, so
findings can never be misattributed across repos.

Keyed by the canonical, worktree-safe repo key from repo-identity.sh
(normalized git origin, abs-path fallback).

Usage:
  file-gotcha.py record --key <repo_key> --root <repo_root> --gotchas <path> \
      --remote <url> --section "§11" --branch triage/<slug> --sha <sha> --issue "<text>"
  file-gotcha.py show   [--key <repo_key>]     # print the registry (optionally one repo)

Registry: ~/.triage/registry.json  (created on first record).
"""
import argparse, json, os, sys, datetime, fcntl

REG = os.path.expanduser("~/.triage/registry.json")


def _open_locked():
    os.makedirs(os.path.dirname(REG), exist_ok=True)
    f = open(REG, "a+")
    fcntl.flock(f, fcntl.LOCK_EX)
    f.seek(0)
    try:
        data = json.loads(f.read() or "{}")
    except json.JSONDecodeError:
        data = {}
    return f, data


def _write(f, data):
    f.seek(0)
    f.truncate()
    f.write(json.dumps(data, indent=2, sort_keys=True))
    f.flush()
    fcntl.flock(f, fcntl.LOCK_UN)
    f.close()


def record(a):
    if not a.key:
        sys.exit("refusing to file: empty repo key (identity resolution failed)")
    f, data = _open_locked()
    e = data.setdefault(a.key, {"root": a.root, "gotchas": a.gotchas,
                                "remote": a.remote, "runs": []})
    e["root"], e["gotchas"], e["remote"] = a.root, a.gotchas, a.remote
    e["runs"].append({
        "date": a.date or datetime.date.today().isoformat(),
        "section": a.section, "branch": a.branch, "sha": a.sha, "issue": a.issue,
    })
    _write(f, data)
    print(f"filed: {a.key} {a.section} -> {a.gotchas}")


def show(a):
    if not os.path.exists(REG):
        print("{}  (no runs filed yet)")
        return
    data = json.load(open(REG))
    print(json.dumps(data.get(a.key, "unknown repo key") if a.key else data,
                     indent=2, sort_keys=True))


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record")
    for flag in ("key", "root", "gotchas", "remote", "section", "branch", "sha", "issue", "date"):
        r.add_argument(f"--{flag}", default="")
    r.set_defaults(fn=record)
    s = sub.add_parser("show")
    s.add_argument("--key", default="")
    s.set_defaults(fn=show)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
