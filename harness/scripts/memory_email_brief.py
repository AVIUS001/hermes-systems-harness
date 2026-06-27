#!/usr/bin/env python3
"""Create or send the Hermes memory briefing email."""

from __future__ import annotations

import argparse
import json
import os
import smtplib
import ssl
from datetime import date, datetime, timedelta
from email.message import EmailMessage
from pathlib import Path

VAULT = Path(__file__).resolve().parents[2]
MEMORY_DIR = VAULT / "memory"
GRAPH_PATH = VAULT / "harness" / "graph" / "graph.json"
OUTBOX = VAULT / "harness" / "outbox"
WEEKLY_DIR = VAULT / "harness" / "updates" / "weekly"
OVERNIGHT_DIR = VAULT / "harness" / "updates" / "overnight"
DEFAULT_RECIPIENT = os.environ.get("HERMES_BRIEF_RECIPIENT", "you@example.com")
DEFAULT_ENV_FILE = VAULT / "harness" / "config" / "email.env"
ENV_EXAMPLE_FILE = VAULT / "harness" / "config" / "email.env.example"


def resolve_env_file(path: Path) -> Path:
    path = path.expanduser()
    if path.is_absolute():
        return path
    for candidate in (Path.cwd() / path, VAULT / path):
        if candidate.exists():
            return candidate.resolve()
    return (VAULT / path).resolve()


def load_env_file(path: Path) -> None:
    resolved = resolve_env_file(path)
    if not resolved.exists():
        hint = ""
        if ENV_EXAMPLE_FILE.exists():
            hint = (
                f"\nCopy {ENV_EXAMPLE_FILE.relative_to(VAULT)} to "
                f"{DEFAULT_ENV_FILE.relative_to(VAULT)} and fill in SMTP credentials."
            )
        raise SystemExit(f"SMTP env file not found: {resolved}{hint}")
    path = resolved
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def read_text(path: Path, max_chars: int = 3500) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n\n[truncated]"


def latest_file(directory: Path, glob: str = "*.md") -> Path | None:
    if not directory.exists():
        return None
    files = sorted(directory.glob(glob), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def graph_todos(limit: int = 20) -> list[dict]:
    if not GRAPH_PATH.exists():
        return []
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    statuses = {"blocked": 0, "review_required": 1, "revision_needed": 2, "stale": 3}
    candidates = [
        {
            "id": n["id"],
            "type": n.get("type", "unknown"),
            "title": n.get("title", n["id"]),
            "status": n.get("status", "unknown"),
            "owner": n.get("owner", "systems_engineer"),
        }
        for n in graph.get("nodes", [])
        if n.get("status") in statuses
    ]
    candidates.sort(key=lambda n: (statuses.get(n["status"], 99), n["type"], n["title"]))
    return candidates[:limit]


def memory_section(day: date) -> tuple[str, str]:
    path = MEMORY_DIR / f"{day.isoformat()}.md"
    rel = path.relative_to(VAULT)
    if path.exists():
        body = read_text(path, max_chars=2500)
        return f"`{rel}`", body or "_File exists but is empty._"
    return f"`{rel}`", "_No memory file exists for this date._"


def build_brief(recipient: str, mode: str) -> tuple[str, str]:
    today = date.today()
    yesterday = today - timedelta(days=1)
    today_link, today_body = memory_section(today)
    yesterday_link, yesterday_body = memory_section(yesterday)
    weekly = latest_file(WEEKLY_DIR)
    overnight = latest_file(OVERNIGHT_DIR)
    todos = graph_todos()

    subject = f"Hermes Memory Brief - {today.isoformat()}"
    lines = [
        f"# Hermes Memory Brief - {today.isoformat()}",
        "",
        f"To: {recipient}",
        f"Mode: {mode}",
        "",
        "## Memory Links",
        "",
        f"- Today: {today_link}",
        f"- Yesterday: {yesterday_link}",
        "",
        "## Today",
        "",
        today_body,
        "",
        "## Yesterday",
        "",
        yesterday_body,
        "",
        "## Weekly Summary",
        "",
    ]
    if weekly:
        lines.append(f"Source: `{weekly.relative_to(VAULT)}`")
        lines.extend(["", read_text(weekly, max_chars=3000)])
    else:
        lines.append("_No weekly summary found._")

    lines.extend(["", "## Latest Overnight Health", ""])
    if overnight:
        lines.append(f"Source: `{overnight.relative_to(VAULT)}`")
        lines.extend(["", read_text(overnight, max_chars=2500)])
    else:
        lines.append("_No overnight health report found yet._")

    lines.extend(["", "## To Do List", ""])
    if todos:
        for item in todos:
            lines.append(f"- [{item['status']}] {item['title']} (`{item['id']}`, {item['type']}, owner: {item['owner']})")
    else:
        lines.append("- No graph-derived review/stale/blocked items found.")

    lines.extend([
        "",
        "## Agent Boundary",
        "",
        "This briefing was generated from local vault files. Sending requires explicit SMTP configuration and `--send --yes`.",
        "",
    ])
    return subject, "\n".join(lines)


def write_draft(subject: str, body: str) -> Path:
    OUTBOX.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    path = OUTBOX / f"{stamp}-hermes-memory-brief.md"
    path.write_text(f"Subject: {subject}\n\n{body}\n", encoding="utf-8")
    return path


def send_email(recipient: str, subject: str, body: str) -> None:
    host = os.environ.get("HERMES_SMTP_HOST")
    port = int(os.environ.get("HERMES_SMTP_PORT", "587"))
    username = os.environ.get("HERMES_SMTP_USER")
    password = os.environ.get("HERMES_SMTP_PASSWORD")
    from_addr = os.environ.get("HERMES_SMTP_FROM") or username
    missing = [
        name for name, value in {
            "HERMES_SMTP_HOST": host,
            "HERMES_SMTP_USER": username,
            "HERMES_SMTP_PASSWORD": password,
            "HERMES_SMTP_FROM or HERMES_SMTP_USER": from_addr,
        }.items()
        if not value
    ]
    if missing:
        raise SystemExit(f"Missing SMTP configuration: {', '.join(missing)}")

    msg = EmailMessage()
    msg["From"] = from_addr
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)

    context = ssl.create_default_context()
    with smtplib.SMTP(host, port, timeout=30) as smtp:
        smtp.starttls(context=context)
        smtp.login(username, password)
        smtp.send_message(msg)


def main() -> int:
    parser = argparse.ArgumentParser(description="Draft or send Hermes memory briefing email")
    parser.add_argument("--recipient", default=DEFAULT_RECIPIENT)
    parser.add_argument("--env-file", help="Load SMTP variables from a private env file before sending")
    parser.add_argument("--write", action="store_true", help="Write outbox draft")
    parser.add_argument("--send", action="store_true", help="Send via SMTP environment variables")
    parser.add_argument("--yes", action="store_true", help="Required with --send")
    args = parser.parse_args()

    if args.env_file:
        load_env_file(Path(args.env_file))
    elif args.send and DEFAULT_ENV_FILE.exists():
        load_env_file(DEFAULT_ENV_FILE)

    mode = "send" if args.send else "draft"
    subject, body = build_brief(args.recipient, mode)
    draft_path = write_draft(subject, body) if (args.write or not args.send) else None

    sent = False
    if args.send:
        if not args.yes:
            raise SystemExit("Refusing to send without --yes")
        send_email(args.recipient, subject, body)
        sent = True

    print(json.dumps({
        "recipient": args.recipient,
        "subject": subject,
        "draft": str(draft_path) if draft_path else None,
        "sent": sent,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
