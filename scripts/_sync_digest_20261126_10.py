"""Refresh digests after zerocap hunt+chase 10:00."""
from __future__ import annotations

import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _pyc_bootstrap  # noqa: F401

from grokfreakit.paths import load_env_files

load_env_files()
from bankroll.env_aliases import apply_env_aliases

apply_env_aliases()

from bankroll.velocity.ops_notify import note_event, write_digest
from bankroll.velocity.user_approvals import list_items

STORE = Path(
    r"C:\Users\marcu\AppData\Local\Cursor\AgentStores\cursor_agent_stores"
    r"\bc-899940a3-e674-4ea2-b08d-d777f13df5d9\files"
)

DENVER = timezone(timedelta(hours=-7), name="America/Denver")
now = datetime.now(DENVER)

pending = list_items(status="pending")
print("pending", len(pending))

summary = (
    "Hunt 10:00 zerocap+chase: cash $0.00; "
    "NEW conversion 2 ($20/$23); redistributed 130 (26 conv + 25 multi + 79 invent); "
    "float=$0; open_approvals=11; stack UP (dashboard HTTP 200)"
)
other = (
    "Hunt 10:00: NEW conversion 2 ($20/$23); "
    "redistributed conversion-first; "
    "cash $0; NEW ua-*=0; warm_leads=0; stack UP; chase band $19–$79; no invent inflate; "
    "Moltbook 1x api + 1x draft_file (429)"
)

note_event(
    kind="account_change",
    summary=summary,
    event_id="zerocap-hunt-10-digest-final",
    section="ACCOUNT_CHANGES",
    detail={
        "cycle": "bb-zerocap-hunt-chase-20261126-10",
        "conversion_ids": ["loading_state_copy_pass_20", "hover_hint_copy_pass_23"],
        "amounts": [20.0, 23.0],
        "urls": [
            "https://buy.stripe.com/00wfZa6Al6Ms6lQeAn3843D",
            "https://buy.stripe.com/6oUcMY4sd3Ag9y23VJ3843E",
        ],
        "new_ua_ids": [],
        "open_approval_count": len(pending),
        "redistributed": 130,
    },
    refresh_digest=False,
)
d = write_digest(
    check_type="manual",
    extra_other=[{"id": "zerocap-hunt-chase-10-other", "summary": other}],
    mark_notified=True,
)
print("ok", d.get("ok"))
print("paths", d.get("paths"))
md = d.get("markdown") or ""
for section in ("OPEN_APPROVALS", "ACCOUNT_CHANGES", "OTHER"):
    i = md.find("## " + section)
    if i >= 0:
        print(md[i : i + 420])
        print("---")

desk_md = Path("data/desk/notify_digest.md")
desk_json = Path("data/desk/notify_digest.json")
if desk_md.is_file():
    shutil.copy2(desk_md, STORE / "internal" / "bb-notify-digest.md")
if desk_json.is_file():
    shutil.copy2(desk_json, STORE / "internal" / "bb-notify-digest.json")

pending_ids = [str(r.get("id")) for r in pending if isinstance(r, dict) and r.get("id")]
latest = "\n".join(
    [
        "# Ops check — manual (hunt 10:00)",
        "",
        f"- Denver: `{now.isoformat()}`",
        f"- UTC: `{now.astimezone(timezone.utc).isoformat()}`",
        "- Stack: **UP** (DESKTOP-N5P6TAA)",
        "- Cash booked: $0.00",
        "- Open approvals: 11",
        "- Invoices since last: 0 paid (digest queued-outbound rows = SMTP-unset redistrib posts, not Stripe receipts)",
        "- Account changes: 1",
        "",
        "## Open approval ids",
        "",
        *[f"- `{x}`" for x in pending_ids],
        "",
        "## Account changes",
        "",
        f"- {summary}",
        "",
        "## Other",
        "",
        f"- {other}",
        "",
    ]
)
ops_dir = STORE / "internal" / "bb-ops-log"
ops_dir.mkdir(parents=True, exist_ok=True)
(ops_dir / "latest.md").write_text(latest, encoding="utf-8")

# Append a compact ops log line into project store jsonl if present.
log_path = ops_dir / "ops_check_log.jsonl"
import json

row = {
    "ts": now.isoformat(),
    "check_type": "manual",
    "cycle": "bb-zerocap-hunt-chase-20261126-10",
    "cash_usd": 0.0,
    "open_approvals": 11,
    "created_conversion": 2,
    "redistributed": 130,
    "summary": summary,
}
with log_path.open("a", encoding="utf-8") as fh:
    fh.write(json.dumps(row) + "\n")
print("latest.md written")
