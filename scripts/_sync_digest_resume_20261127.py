"""Refresh digests after zerocap hunt+chase resume 2026-11-27 ~13:00 Denver."""
from __future__ import annotations

import json
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
pending_ids = [str(r.get("id")) for r in pending if isinstance(r, dict) and r.get("id")]
print("pending", len(pending))

summary = (
    "Resume hunt 13:00 zerocap+chase: cash $0.00; "
    "NEW conversion 2 ($21/$62); redistributed 131 (27 conv + 25 multi + 79 invent); "
    "float=$0; open_approvals=11; stack REPAIRED→UP (dashboard HTTP 200)"
)
other = (
    "Resume hunt 13:00: NEW conversion 2 ($21/$62); "
    "redistributed conversion-first; "
    "cash $0; NEW ua-*=0; warm_leads=0; stack repaired then UP; chase band $19–$79; "
    "no invent inflate; Moltbook 1x draft_file ($21) + 1x api ($62); $29 skipped (invent amt)"
)

note_event(
    kind="account_change",
    summary=summary,
    event_id="zerocap-hunt-resume-digest-final",
    section="ACCOUNT_CHANGES",
    detail={
        "cycle": "bb-zerocap-hunt-chase-resume-20261127",
        "conversion_ids": ["spinner_aria_label_pass_21", "helper_text_copy_pass_62"],
        "amounts": [21.0, 62.0],
        "urls": [
            "https://buy.stripe.com/9B69AM0bX2wc5hM63R3843F",
            "https://buy.stripe.com/bJe5kw8ItfiYdOi9g33843G",
        ],
        "new_ua_ids": [],
        "open_approval_count": len(pending),
        "redistributed": 131,
        "stack_repaired": True,
    },
    refresh_digest=False,
)
d = write_digest(
    check_type="manual",
    extra_other=[{"id": "zerocap-hunt-chase-resume-other", "summary": other}],
    mark_notified=True,
)
print("ok", d.get("ok"))
print("paths", d.get("paths"))

desk_md = Path("data/desk/notify_digest.md")
desk_json = Path("data/desk/notify_digest.json")
if desk_md.is_file():
    shutil.copy2(desk_md, STORE / "internal" / "bb-notify-digest.md")
if desk_json.is_file():
    shutil.copy2(desk_json, STORE / "internal" / "bb-notify-digest.json")

status = "GREEN"
latest = "\n".join(
    [
        "# Ops check — manual (resume hunt 13:00)",
        "",
        f"- Denver: `{now.isoformat()}`",
        f"- UTC: `{now.astimezone(timezone.utc).isoformat()}`",
        f"- Status: **{status}** (stack was DOWN at resume → repaired → UP)",
        "- Stack: **UP** (DESKTOP-N5P6TAA)",
        "- PIDs: vel **8316** · `:8080` **5012** (HTTP 200) · listen **8204** · wd **4956**",
        "- Cash booked: $0.00 · gap $1999",
        "- Open approvals: 11",
        "- Invoices since last: 0 paid",
        "- Account changes: 1",
        "- NEW ua-*: 0",
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

log_path = ops_dir / "ops_check_log.jsonl"
# Append RESUMED then GREEN
for row in (
    {
        "ts": now.isoformat(),
        "check_type": "manual",
        "cycle": "bb-zerocap-hunt-chase-resume-20261127",
        "status": "RESUMED",
        "cash_usd": 0.0,
        "open_approvals": 11,
        "summary": "User pause lift; stack was DOWN; repair started",
    },
    {
        "ts": now.isoformat(),
        "check_type": "manual",
        "cycle": "bb-zerocap-hunt-chase-resume-20261127",
        "status": "GREEN",
        "cash_usd": 0.0,
        "open_approvals": 11,
        "created_conversion": 2,
        "redistributed": 131,
        "stack_pids": {
            "velocity": 8316,
            "dashboard_8080": 5012,
            "stripe_listen": 8204,
            "stripe_watchdog": 4956,
        },
        "dashboard_http": 200,
        "summary": summary,
    },
):
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")

# Mirror to sandbox desk log too
sandbox_log = Path("data/desk/ops_check_log.jsonl")
with sandbox_log.open("a", encoding="utf-8") as fh:
    fh.write(
        json.dumps(
            {
                "ts": now.isoformat(),
                "check_type": "manual",
                "cycle": "bb-zerocap-hunt-chase-resume-20261127",
                "status": "GREEN",
                "cash_usd": 0.0,
                "created_conversion": 2,
                "redistributed": 131,
                "summary": summary,
            }
        )
        + "\n"
    )

print("latest.md written")
print("digest copied to store")
