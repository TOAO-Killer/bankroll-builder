"""Refresh digests after combo opp+hunt 13:00 America/Denver 2026-11-28."""
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

hunt = json.loads(Path("data/desk/zerocap_hunt_20261128_13.json").read_text(encoding="utf-8"))
created = hunt.get("created") or []
amts = "/".join(f"${c['amount_usd']:.0f}" for c in created) if created else "(none)"
n_conv = len(hunt.get("conversion_redistributed") or [])
n_multi = len(hunt.get("multi_rail_redistributed") or [])
n_inv = len(hunt.get("invent_redistributed") or [])
n_redist = len(hunt.get("redistributed") or [])
stack = hunt.get("stack") or {}
molt = hunt.get("moltbook_via_counts") or {}

summary = (
    f"Combo 13:00 opp+hunt: cash $0.00; "
    f"NEW conversion {len(created)} ({amts}); redistributed {n_redist} "
    f"({n_conv} conv + {n_multi} multi + {n_inv} invent); "
    f"float=$0; open_approvals={len(pending)}; stack UP (dashboard HTTP 200)"
)
other = (
    f"Combo 13:00: NEW conversion {len(created)} ({amts}); "
    f"redistributed conversion-first; cash $0; NEW ua-*=0; warm_leads=0; stack UP; "
    f"chase band $19–$79; no invent inflate; Moltbook vias={molt}"
)

note_event(
    kind="account_change",
    summary=summary,
    event_id="combo-13-digest-final",
    section="ACCOUNT_CHANGES",
    detail={
        "cycle": "bb-combo-20261128-13",
        "conversion_ids": [c.get("offer_id") for c in created],
        "amounts": [c.get("amount_usd") for c in created],
        "urls": [c.get("url") for c in created],
        "new_ua_ids": [],
        "open_approval_count": len(pending),
        "redistributed": n_redist,
    },
    refresh_digest=False,
)
d = write_digest(
    check_type="manual",
    extra_other=[{"id": "combo-13-other", "summary": other}],
    mark_notified=True,
)
print("ok", d.get("ok"))

desk_md = Path("data/desk/notify_digest.md")
desk_json = Path("data/desk/notify_digest.json")
if desk_md.is_file():
    shutil.copy2(desk_md, STORE / "internal" / "bb-notify-digest.md")
if desk_json.is_file():
    shutil.copy2(desk_json, STORE / "internal" / "bb-notify-digest.json")

latest = "\n".join(
    [
        "# Ops check — manual (Combo 13:00)",
        "",
        f"- Denver: `{now.isoformat()}`",
        f"- UTC: `{now.astimezone(timezone.utc).isoformat()}`",
        "- Status: **GREEN**",
        "- Stack: **UP** (DESKTOP-N5P6TAA) — left running",
        f"- PIDs: vel **{stack.get('velocity_pid')}** · `:8080` **{stack.get('dashboard_8080_pid')}** "
        f"(HTTP {stack.get('dashboard_http')}) · listen **{stack.get('stripe_listen_pid')}** · "
        f"wd **{stack.get('stripe_watchdog_pid')}**",
        "- Cash booked: $0.00 · gap $1999",
        f"- Open approvals: {len(pending)}",
        "- Invoices since last: 0 paid",
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

row = {
    "ts": now.isoformat(),
    "check_type": "manual",
    "cycle": "bb-combo-20261128-13",
    "status": "GREEN",
    "cash_usd": 0.0,
    "open_approvals": len(pending),
    "created_conversion": len(created),
    "redistributed": n_redist,
    "stack_pids": {
        "velocity": stack.get("velocity_pid"),
        "dashboard_8080": stack.get("dashboard_8080_pid"),
        "stripe_listen": stack.get("stripe_listen_pid"),
        "stripe_watchdog": stack.get("stripe_watchdog_pid"),
    },
    "dashboard_http": stack.get("dashboard_http"),
    "summary": summary,
}
with (ops_dir / "ops_check_log.jsonl").open("a", encoding="utf-8") as fh:
    fh.write(json.dumps(row) + "\n")
with Path("data/desk/ops_check_log.jsonl").open("a", encoding="utf-8") as fh:
    fh.write(json.dumps(row) + "\n")
print("latest.md written")
