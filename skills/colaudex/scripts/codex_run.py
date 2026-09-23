#!/usr/bin/env python3
"""The only way colaudex calls Codex. Stdlib only.

  codex_run.py preflight
  codex_run.py exec   --tier T [--kind code|paper] --prompt FILE --out PREFIX [--cwd DIR] [--resume THREAD_ID]
  codex_run.py review --tier T --prompt FILE --out PREFIX [--cwd DIR]
  codex_run.py validate FILE        # check a review JSON (for example one written by a Claude reviewer)
  codex_run.py stats [COLAB_DIR]    # one row per run from all *.result.json (Codex and Claude)
  codex_run.py describe --combo A|B|C|D [--kind code|paper]   # per tier: the exact models that combo would use

Writes PREFIX.jsonl / .err / .last.md / .result.json (review also PREFIX.json) and prints the result JSON.
Exit code 0 = Codex finished (check "status"/"error_class"); 1 = infra failure or invalid review.
"""
import argparse, json, os, re, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "config.json").read_text())
SCHEMA = ROOT / "schemas" / "review.schema.json"
WORKER_RULES = ROOT / "templates" / "worker-rules.md"
SEVERITIES = {"blocker", "major", "minor", "nit"}
FINDING_KEYS = ("id", "severity", "location", "evidence", "problem", "suggestion")


def pick(role, tier, kind):
    paper = role == "exec" and kind == "paper" and tier != "test"  # test tier stays cheap even for paper
    m = CFG["paper_exec"]["codex"] if paper else CFG["tiers"][tier][role]["codex"]
    if m["model"] not in CFG["codex"]["allowed_models"]:
        sys.exit(f"model {m['model']} not in allowed_models")
    return m


def build_cmd(role, m, cwd, last, resume, kind="code"):
    cmd = ["codex", "exec", "-m", m["model"], "-c", f'model_reasoning_effort="{m["effort"]}"',
           "-c", 'approval_policy="never"', "--sandbox", "workspace-write" if role == "exec" else "read-only",
           "--disable", "multi_agent", "--disable", "memories", "--skip-git-repo-check",
           "-C", cwd, "--json", "-o", last]
    if role == "review":
        cmd += ["--output-schema", str(SCHEMA)]
        if kind == "paper":  # citation checks need the web, whatever the user's config says
            cmd += ["-c", 'web_search="live"']
    return cmd + (["resume", resume, "-"] if resume else ["-"])


def run(cmd, prompt, jsonl, err):
    """Run with a watchdog: kill when no output for stale_seconds or total > max_seconds."""
    stale, limit = CFG["codex"]["stale_seconds"], CFG["codex"]["max_seconds"]
    with open(jsonl, "w") as fo, open(err, "w") as fe:
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=fo, stderr=fe, text=True)
        p.stdin.write(prompt)
        p.stdin.close()
        start = last_change = time.time()
        seen, killed = -1, None
        while p.poll() is None:
            time.sleep(2)
            size = os.path.getsize(jsonl) + os.path.getsize(err)
            now = time.time()
            if size != seen:
                seen, last_change = size, now
            killed = "stale" if now - last_change > stale else "timeout" if now - start > limit else None
            if killed:
                p.terminate()
                try:
                    p.wait(10)
                except subprocess.TimeoutExpired:
                    p.kill()
                break
    return p.wait(), killed, round(time.time() - start)


def parse_events(jsonl):
    thread_id, usage, errors, denied = None, None, [], False
    for line in Path(jsonl).read_text().splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        t = e.get("type", "")
        if t == "thread.started":
            thread_id = e.get("thread_id")
        elif t == "turn.completed":
            usage = e.get("usage")
        elif t in ("error", "turn.failed"):
            errors.append(str(e.get("message") or e.get("error"))[:300])
        item = e.get("item") or {}
        if item.get("type") == "command_execution" and "Operation not permitted" in str(item.get("aggregated_output", "")):
            denied = True
    return thread_id, usage, errors, denied


def validate_review(data):
    """Return a list of problems; an empty list means valid."""
    if not isinstance(data, dict):
        return ["not a JSON object"]
    bad = []
    if data.get("verdict") not in ("pass", "fix", "reject"):
        bad.append("verdict must be pass|fix|reject")
    if not isinstance(data.get("summary"), str):
        bad.append("summary missing")
    findings = data.get("findings")
    if not isinstance(findings, list):
        return bad + ["findings must be a list"]
    for i, f in enumerate(findings):
        missing = [k for k in FINDING_KEYS if not isinstance(f, dict) or not isinstance(f.get(k), str)]
        if missing:
            bad.append(f"finding {i}: missing {missing}")
        elif f["severity"] not in SEVERITIES:
            bad.append(f"finding {i}: bad severity {f['severity']}")
        elif not f["evidence"].strip():
            bad.append(f"finding {i}: empty evidence")
    return bad


def load_json_loose(text):
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    return json.loads(text)


def cmd_run(a, role):
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    jsonl, err, last = f"{out}.jsonl", f"{out}.err", f"{out}.last.md"
    Path(last).unlink(missing_ok=True)
    m = pick(role, a.tier, a.kind)
    prompt = Path(a.prompt).read_text()
    if role == "exec":
        prompt = WORKER_RULES.read_text() + "\n" + prompt
    rc, killed, secs = run(build_cmd(role, m, a.cwd, last, getattr(a, "resume", None), a.kind), prompt, jsonl, err)
    thread_id, usage, errors, denied = parse_events(jsonl)
    msg = Path(last).read_text() if Path(last).exists() else ""
    errtext = Path(err).read_text()
    r = {"role": role, "backend": "codex", "tier": a.tier, "model": m["model"], "effort": m["effort"], "rc": rc, "seconds": secs,
         "thread_id": thread_id, "usage": usage, "sandbox_denied": denied, "errors": errors,
         "error_class": None, "status": None}
    if killed or rc != 0 or not msg.strip():
        r["error_class"] = "INFRA_FAIL"
        r["detail"] = killed or ("rate_limited" if re.search(r"429|rate.?limit", errtext + " ".join(errors), re.I)
                                 else (errors[-1] if errors else errtext.strip()[-300:]))
    elif role == "exec":
        found = re.findall(r"STATUS:\s*(DONE|PARTIAL|BLOCKED)", msg)
        r["status"] = found[-1] if found else "UNKNOWN"
    else:
        try:
            data = load_json_loose(msg)
            problems = validate_review(data)
        except ValueError as e:
            data, problems = None, [f"invalid JSON: {e}"]
        if problems:
            r["error_class"], r["detail"] = "INVALID_REVIEW", problems
        else:
            Path(f"{out}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2))
            r["status"] = data["verdict"]
            r["counts"] = {s: sum(f["severity"] == s for f in data["findings"]) for s in SEVERITIES}
    Path(f"{out}.result.json").write_text(json.dumps(r, ensure_ascii=False, indent=2))
    print(json.dumps(r, ensure_ascii=False))
    return 1 if r["error_class"] else 0


def cmd_validate(a):
    try:
        problems = validate_review(load_json_loose(Path(a.file).read_text()))
    except ValueError as e:
        problems = [f"invalid JSON: {e}"]
    print(json.dumps({"valid": not problems, "problems": problems}, ensure_ascii=False))
    return 1 if problems else 0


def cmd_stats(a):
    rows = []
    for f in sorted(Path(a.dir).glob("*/*.result.json")):
        r = json.loads(f.read_text())
        u = r.get("usage") or {}
        rows.append([f.name.removesuffix(".result.json"), r.get("role", "?"), r.get("backend", "codex"), r.get("tier", "?"),
                     f'{r.get("model")}/{r.get("effort", "-")}', r.get("seconds", "?"),
                     u.get("input_tokens", r.get("tokens", "?")), u.get("cached_input_tokens", "-"), u.get("output_tokens", "-"),
                     r.get("error_class") or r.get("status")])
    rows.sort(key=lambda x: (x[0], x[1] != "exec"))
    head = ["run", "role", "backend", "tier", "model", "secs", "in_tok", "cached", "out_tok", "outcome"]
    print("\t".join(head))
    for row in rows:
        print("\t".join(map(str, row)))
    return 0


COMBOS = {"A": ("claude", "claude"), "B": ("claude", "codex"), "C": ("codex", "claude"), "D": ("codex", "codex")}


def model_label(backend, m):
    if backend == "codex":
        return f"Codex {m['model']} ({m['effort']})"
    return f"Claude {m['model']} ({m['agent'].rsplit('-', 1)[1]})"  # effort lives in the agent name


def cmd_describe(a):
    exec_b, review_b = COMBOS[a.combo]
    out = {}
    for tier, t in CFG["tiers"].items():
        ex = CFG["paper_exec"] if a.kind == "paper" and tier != "test" else t["exec"]
        n = 2 if t.get("second_reviewer") else 1
        out[tier] = {"exec": model_label(exec_b, ex[exec_b]),
                     "review": model_label(review_b, t["review"][review_b]) + (f" x{n}" if n > 1 else "")}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


def cmd_preflight(_):
    try:
        ver = subprocess.run(["codex", "--version"], capture_output=True, text=True, timeout=20).stdout.strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        print(json.dumps({"ok": False, "detail": f"codex not runnable: {e}"}))
        return 1
    cmd = ["codex", "exec", "-m", "gpt-6-luna", "-c", 'model_reasoning_effort="low"', "-c", 'approval_policy="never"',
           "--sandbox", "read-only", "--disable", "multi_agent", "--disable", "memories", "--skip-git-repo-check", "--json", "-"]
    try:
        p = subprocess.run(cmd, input="reply OK", capture_output=True, text=True, timeout=180)
        ok = p.returncode == 0 and '"agent_message"' in p.stdout
        detail = "" if ok else (p.stderr.strip()[-300:] or p.stdout[-300:])
    except subprocess.TimeoutExpired:
        ok, detail = False, "timeout after 180s"
    print(json.dumps({"ok": ok, "version": ver, "detail": detail}))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("preflight")
    v = sub.add_parser("validate")
    v.add_argument("file")
    d = sub.add_parser("describe")
    d.add_argument("--combo", required=True, choices=list("ABCD"))
    d.add_argument("--kind", default="code", choices=["code", "paper"])
    st = sub.add_parser("stats")
    st.add_argument("dir", nargs="?", default=".colab")
    for role in ("exec", "review"):
        s = sub.add_parser(role)
        s.add_argument("--tier", required=True, choices=list(CFG["tiers"]))
        s.add_argument("--kind", default="code", choices=["code", "paper"])
        s.add_argument("--prompt", required=True)
        s.add_argument("--out", required=True)
        s.add_argument("--cwd", default=os.getcwd())
        if role == "exec":
            s.add_argument("--resume")
    a = ap.parse_args()
    if a.cmd == "preflight":
        return cmd_preflight(a)
    if a.cmd == "validate":
        return cmd_validate(a)
    if a.cmd == "stats":
        return cmd_stats(a)
    if a.cmd == "describe":
        return cmd_describe(a)
    return cmd_run(a, a.cmd)


if __name__ == "__main__":
    sys.exit(main())
