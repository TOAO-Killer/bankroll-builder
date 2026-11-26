"""Fix digest ACCOUNT_CHANGES/OTHER for hunt 06 after shell $ escaping mangled text."""
from __future__ import annotations

from grokfreakit.paths import load_env_files

load_env_files()
from bankroll.env_aliases import apply_env_aliases

apply_env_aliases()

from bankroll.velocity.ops_notify import note_event, write_digest

summary = (
    "Hunt 06:00 zerocap+chase: cash $0.00; "
    "NEW conversion 2 ($22/$32); redistributed 122 (18 conv + 25 multi + 79 invent); "
    "float=$0; open_approvals=11; stack UP (no restart)"
)
other = (
    "Hunt 06:00: NEW conversion 2 ($22/$32); "
    "redistributed 18 conv + 25 multi + 79 invent; "
    "cash $0; NEW ua-*=0; warm_leads=0; stack UP; chase band $19–$79; no invent inflate"
)

note_event(
    kind="account_change",
    summary=summary,
    event_id="zerocap-hunt-06-final-v2",
    section="ACCOUNT_CHANGES",
    detail={
        "cycle": "bb-zerocap-hunt-chase-20261126-06",
        "conversion_ids": ["nav_link_label_pass_22", "empty_state_copy_pass_32"],
        "amounts": [22.0, 32.0],
        "urls": [
            "https://buy.stripe.com/fZu00c6Al1s89y2gIv3843v",
            "https://buy.stripe.com/6oU14g5whb2IbGa3VJ3843w",
        ],
        "new_ua_ids": [],
    },
    refresh_digest=False,
)
d = write_digest(
    check_type="manual",
    extra_other=[{"id": "zerocap-hunt-chase-06-final-v2", "summary": other}],
    mark_notified=True,
)
print("ok", d.get("ok"))
print("paths", d.get("paths"))
md = d.get("markdown") or ""
for section in ("ACCOUNT_CHANGES", "OTHER"):
    i = md.find("## " + section)
    if i >= 0:
        print(md[i : i + 520])
        print("---")
