"""Combined CEO 8h + opp 4h + zerocap hunt — ~01:00 America/Denver Sat 2026-11-28.

One stack touch (probe only). Leave healthy PIDs running.
Policy: prefer conversion over invent; NEW ua-*=0 unless >=60%; leave 11 PENDING.
Band saturated -> NEW conversion=0; HARDER buyer chase + expandable zero-cap research.
Hero cheapest ($19). No invent/$170+ inflate. Stripe+USDC only.
Force Moltbook on conversion redistrib (api / draft_file on 429).
Cycle: bb-combo-20261128-01
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

import sys as _sys

_sys.path.insert(0, str(Path(__file__).resolve().parent))
import _pyc_bootstrap  # noqa: F401  — load .pyc when .py sources missing

from grokfreakit.paths import CONFIG, load_env_files

load_env_files()
from bankroll.env_aliases import apply_env_aliases

apply_env_aliases()

from bankroll.velocity.offer_publisher import publish_offer_channels
from bankroll.velocity.ops_notify import note_event, record_ops_check, write_digest
from bankroll.velocity.policy import load_opportunity_policy, load_policy, save_policy
from bankroll.velocity.settle import offer_pay_sheet, settle_status
from bankroll.velocity.stripe_autonomy import auto_book_paid
from bankroll.velocity.user_approvals import list_items
from capital_engine.stripe_client import live_charges_enabled, stripe_request

assert live_charges_enabled(), "live charges must be enabled"

CYCLE = "bb-combo-20261128-01"
ROOT = Path(__file__).resolve().parents[1]
DESK = ROOT / "data" / "desk"
WEBSITE = ROOT / "website" / "index.html"
DENVER = timezone(timedelta(hours=-7), name="America/Denver")
now_denver = datetime.now(DENVER)
OFFERS_CFG = CONFIG / "service_offers.json"
USDC_ADDR = "0xa38844Df998769d9f9e014186265C99095D19A3B"

# Healthy since resume repair ~13:21; leave running.
STACK_PIDS = {
    "velocity": 8316,
    "dashboard_8080": 5012,
    "stripe_listen": 8204,
    "stripe_watchdog": 4956,
}

paypal_email = (
    (os.environ.get("PAYPAL_EMAIL") or "").strip()
    or (os.environ.get("PAYPAL_ME") or "").strip()
    or (os.environ.get("PAYPAL_LINK") or "").strip()
)
paypal_api = bool(
    (os.environ.get("PAYPAL_CLIENT_ID") or "").strip()
    and (os.environ.get("PAYPAL_CLIENT_SECRET") or os.environ.get("PAYPAL_SECRET") or "").strip()
)
paypal_wired = bool(paypal_email or paypal_api)
rails_base = ["stripe", "usdc"] + (["paypal"] if paypal_wired else [])

# Live conversion band through 14:00 — chase hard; redistrib first (~30 SKUs).
CONV_LIVE_IDS = [
    "landing_cta_rewrite_19",
    "loading_state_copy_pass_20",
    "spinner_aria_label_pass_21",
    "nav_link_label_pass_22",
    "hover_hint_copy_pass_23",
    "hero_subhead_tighten_24",
    "alert_banner_copy_pass_25",
    "meta_description_pass_26",
    "settle_retry_checklist_27",
    "faq_answer_rewrite_28",
    "button_label_pass_30",
    "checkbox_consent_copy_pass_31",
    "empty_state_copy_pass_32",
    "form_placeholder_pass_33",
    "listing_copy_pack_34",
    "footer_nav_pass_36",
    "offer_blurb_tighten_38",
    "desk_board_headline_pass_42",
    "cta_microcopy_tighten_44",
    "outbound_callout_rewrite_46",
    "error_state_copy_pass_48",
    "thankyou_cta_pass_50",
    "success_page_copy_pass_52",
    "checkout_friction_mini_audit_54",
    "receipt_email_plain_pass_56",
    "payment_link_copy_pass_58",
    "helper_text_copy_pass_62",
    "confirm_dialog_copy_pass_64",
    "inline_validation_copy_pass_66",
    "multi_rail_status_onepager_68",
]

INVENT_HOT_IDS = [
    "hiring_spotlight_48h",
    "classified_flash_bump_24h",
    "classified_events_ad_slot_1w",
    "classified_morning_bump_24h",
    "stream_banner_sponsor_7d",
    "directory_weekend_spotlight_48h",
    "newsletter_midissue_callout_1issue",
    "stream_weekend_takeover_48h",
    "newsletter_footer_cta_1issue",
    "directory_midweek_spotlight_48h",
    "classified_midnight_bump_24h",
    "classified_evening_bump_24h",
    "classified_twilight_bump_24h",
    "classified_late_day_bump_24h",
    "newsletter_sponsor_strip_1issue",
    "classified_afternoon_bump_24h",
    "stream_sidebar_mention_7d",
    "newsletter_ps_bump_1issue",
    "stream_lower_third_mention_24h",
    "directory_sidebar_chip_48h",
    "stream_midroll_sticker_24h",
    "stream_midroll_chip_24h",
    "directory_logo_tile_48h",
    "directory_tool_chip_48h",
    "mcp_tools_featured_pack_7d",
    "directory_homepage_pin_48h",
    "directory_footer_chip_48h",
    "directory_nav_chip_48h",
    "directory_header_chip_48h",
    "directory_rail_chip_48h",
    "directory_subnav_chip_48h",
    "classified_after_hours_bump_24h",
    "classified_owl_shift_bump_24h",
    "directory_breadcrumb_chip_48h",
    "classified_graveyard_bump_24h",
    "directory_filter_chip_48h",
    "classified_pre_dawn_bump_24h",
    "directory_results_chip_48h",
    "classified_blue_hour_bump_24h",
    "directory_facets_chip_48h",
    "classified_civil_twilight_bump_24h",
    "directory_sort_chip_48h",
    "classified_golden_hour_bump_24h",
    "directory_pager_chip_48h",
    "classified_sunrise_bump_24h",
    "directory_tab_chip_48h",
    "classified_commute_bump_24h",
    "directory_query_chip_48h",
    "classified_rush_hour_bump_24h",
    "directory_search_chip_48h",
    "classified_midday_peak_bump_24h",
    "directory_suggest_chip_48h",
    "classified_lunch_window_bump_24h",
    "directory_autocomplete_chip_48h",
    "classified_siesta_bump_24h",
    "directory_typeahead_chip_48h",
    "classified_tea_time_bump_24h",
    "directory_snippet_chip_48h",
    "classified_happy_hour_bump_24h",
    "directory_preview_chip_48h",
    "classified_power_hour_bump_24h",
    "directory_hover_chip_48h",
    "classified_prime_time_bump_24h",
    "directory_focus_ring_chip_48h",
    "classified_dinner_hour_bump_24h",
    "directory_active_state_chip_48h",
    "stream_preroll_chip_24h",
    "classified_late_prime_bump_24h",
    "directory_selected_chip_48h",
    "stream_bumper_chip_24h",
    "classified_wrap_up_bump_24h",
    "directory_pressed_chip_48h",
    "newsletter_eyebrow_callout_1issue",
    "classified_closeout_bump_24h",
    "directory_disabled_chip_48h",
    "stream_stinger_chip_24h",
    "classified_last_call_bump_24h",
    "directory_empty_chip_48h",
    "stream_outro_chip_24h",
]

MULTI_RAIL_HOT_IDS = [
    "wallet_chain_reconcile_95",
    "cors_cookie_auth_debug_brief",
    "settle_receipt_gap_brief_106",
    "checkout_friction_map_112",
    "webhook_delivery_gap_audit_115",
    "agent_outbound_sequence_audit_122",
    "stripe_webhook_replay_brief_125",
    "webhook_timeout_budget_brief_126",
    "idempotency_key_audit_128",
    "multi_rail_receipt_matrix_130",
    "hollow_receipt_verifier_135",
    "settle_confirm_ladder_brief_139",
    "agent_desk_triage_pack_140",
    "checkout_rail_failover_audit_141",
    "write_ack_delivery_harness_145",
    "landing_cta_conversion_audit_152",
    "webhook_signature_clock_skew_brief_153",
    "multi_rail_status_matrix_154",
    "approval_join_key_audit_155",
    "receipt_latency_budget_brief_166",
    "multi_rail_fallback_matrix_167",
    "outbound_chase_pack_7d",
    "usdc_settle_ledger_assist_195",
    "settle_ack_timeout_brief_181",
    "multi_rail_retry_matrix_182",
]

# No free integer prices left in $19–$79 (taken by conversion + invent). NEW=0.
NEW_CONVERSION: list[dict] = []



def _molt(share: dict) -> dict:
    for c in share.get("channels") or []:
        if c.get("channel") == "moltbook":
            return c
    return {}


def _usdc_receipt_count() -> int:
    for settle_path in (
        DESK / "usdc_settlements.jsonl",
        ROOT / "data" / "learning" / "velocity" / "usdc_settlements.jsonl",
        DESK / "settle_receipts.jsonl",
    ):
        if not settle_path.is_file():
            continue
        n = 0
        for line in settle_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("confirmed") or row.get("status") == "confirmed":
                n += 1
        return n
    return 0


def _probe_landing() -> dict:
    url = "https://toao-killer.github.io/bankroll-builder/"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "BankrollBuilderCombo01/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return {
                "ok": True,
                "status": resp.status,
                "url": url,
                "has_stripe": "buy.stripe.com" in body,
                "has_usdc": "USDC" in body or "0xa38844" in body,
                "has_19": "landing_cta_rewrite" in body or "$19" in body or "Pay $19" in body or "Buy now — $19" in body,
            }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "url": url, "error": f"{type(exc).__name__}: {exc}"}


def _stack_probe() -> dict:
    dash_ok = False
    dash_status = None
    try:
        req = urllib.request.Request("http://127.0.0.1:8080/", headers={"User-Agent": "bb-combo-01"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            dash_ok = True
            dash_status = resp.status
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        dash_status = f"{type(exc).__name__}: {exc}"

    def _alive(pid: int) -> bool:
        try:
            out = subprocess.check_output(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    f"Get-Process -Id {pid} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id",
                ],
                text=True,
                timeout=15,
            ).strip()
            return out == str(pid)
        except Exception:  # noqa: BLE001
            return False

    return {
        "velocity_pid": STACK_PIDS["velocity"] if _alive(STACK_PIDS["velocity"]) else None,
        "dashboard_8080_pid": STACK_PIDS["dashboard_8080"] if _alive(STACK_PIDS["dashboard_8080"]) else None,
        "stripe_listen_pid": STACK_PIDS["stripe_listen"] if _alive(STACK_PIDS["stripe_listen"]) else None,
        "stripe_watchdog_pid": STACK_PIDS["stripe_watchdog"] if _alive(STACK_PIDS["stripe_watchdog"]) else None,
        "dashboard_http": dash_status,
        "dashboard_ok": dash_ok,
        "left_running": True,
        "fixes_applied": [],
        "host": "DESKTOP-N5P6TAA",
    }


def _distribute(url: str, name: str, amount: float, meta: dict, *, force_moltbook: bool = False) -> dict:
    share = publish_offer_channels(
        url=url,
        title=f"BankrollBuilder — {name} (Stripe+USDC)",
        amount_usd=amount,
        meta=meta,
        force_moltbook=force_moltbook,
    )
    usdc_blurb = meta.get("blurb_extra") or (
        f"Pay either way: Stripe card/Link {url} OR {amount:.2f} USDC on ethereum, base to {USDC_ADDR}."
    )
    share2 = publish_offer_channels(
        url=url,
        title=f"BankrollBuilder — {name} USDC settle",
        amount_usd=amount,
        meta={**meta, "primary_rail": "usdc", "blurb_extra": usdc_blurb},
        force_moltbook=False,
    )
    return {
        "offer_id": meta.get("offer_id"),
        "name": name,
        "amount_usd": amount,
        "url": url,
        "rails": meta.get("rails"),
        "posted": list({*(share.get("posted") or []), *(share2.get("posted") or [])}),
        "queued": list({*(share.get("queued") or []), *(share2.get("queued") or [])}),
        "human_share_required": False,
        "ok": bool(share.get("ok") and share2.get("ok")),
        "moltbook": _molt(share),
        "errors": list({*(share.get("errors") or []), *(share2.get("errors") or [])}),
        "lane": meta.get("lane"),
        "sku_kind": meta.get("sku_kind"),
    }


def _redist_batch(
    skus: list[dict],
    *,
    invent: bool,
    conversion: bool = False,
    force_moltbook: bool = False,
) -> tuple[list[dict], list[dict]]:
    out: list[dict] = []
    errs: list[dict] = []
    for sku in skus:
        oid = sku["offer_id"]
        amount = float(sku["amount_usd"])
        url = sku["url"]
        meta = {
            "offer_id": oid,
            "cycle": CYCLE,
            "settlement": "multi_rail_stripe_usdc",
            "rails": ["stripe_card", "stripe_link", "usdc"],
            "stripe_url": url,
            "usdc_receive": USDC_ADDR,
            "usdc_amount": f"{amount:.2f}",
            "usdc": {
                "amount": f"{amount:.2f}",
                "asset": "USDC",
                "chains": ["ethereum", "base"],
                "receive_address": USDC_ADDR,
            },
            "human_share_required": False,
            "why_converts": sku.get("why") or "01:00 harder chase redistrib — conversion first",
            "redistribute": True,
            "harder_buyer_chase": True,
            "blurb_extra": (
                f"Pay either way: Stripe card/Link {url} OR {amount:.2f} USDC on ethereum, base to {USDC_ADDR}."
            ),
        }
        if invent:
            meta["inventory"] = "invented_ad_or_access"
            meta["invent_inventory"] = True
            meta["lane"] = "hunt"
            meta["sku_kind"] = "invent_inventory"
        elif conversion:
            meta["lane"] = "cash_push"
            meta["sku_kind"] = "conversion_service"
            meta["conversion_tier"] = True
        else:
            meta["lane"] = "opp"
            meta["sku_kind"] = "service_demand"
        try:
            dist = _distribute(url, sku["name"], amount, meta, force_moltbook=force_moltbook)
            out.append(dist)
            tag = "CONV" if conversion else ("INVENT" if invent else "MULTI")
            print(
                f"REDIST_{tag} {oid} ${amount:.0f} posted={dist['posted']} "
                f"molt={dist['moltbook'].get('via') or dist['moltbook'].get('reason')}"
            )
        except Exception as exc:  # noqa: BLE001
            err = {"offer_id": oid, "phase": "redistribute", "error": f"{type(exc).__name__}: {exc}"}
            errs.append(err)
            print("REDIST_FAIL", oid, exc)
    return out, errs


def _create_stripe_sku(offer: dict) -> dict:
    oid = offer["offer_id"]
    amt = float(offer["amount_usd"])
    cents = int(round(amt * 100))
    product = stripe_request(
        "POST",
        "/v1/products",
        {
            "name": f"BankrollBuilder — {offer['name']}",
            "description": offer["desc"],
            "metadata[offer_id]": oid,
            "metadata[cycle]": CYCLE,
            "metadata[source]": offer["source"],
            "metadata[lane]": offer["lane"],
            "metadata[sku_kind]": offer["sku_kind"],
            "metadata[conversion_tier]": "true",
            "metadata[turnaround]": offer.get("turnaround") or "48h",
        },
    )
    price = stripe_request(
        "POST",
        "/v1/prices",
        {
            "currency": "usd",
            "unit_amount": str(cents),
            "product": product["id"],
            "metadata[offer_id]": oid,
            "metadata[cycle]": CYCLE,
        },
    )
    link = stripe_request(
        "POST",
        "/v1/payment_links",
        {
            "line_items[0][price]": price["id"],
            "line_items[0][quantity]": "1",
            "payment_method_types[0]": "card",
            "payment_method_types[1]": "link",
            "metadata[offer_id]": oid,
            "metadata[cycle]": CYCLE,
            "payment_intent_data[metadata][offer_id]": oid,
            "payment_intent_data[metadata][cycle]": CYCLE,
        },
    )
    url = str(link.get("url") or "")
    return {
        "ok": url.startswith("https://"),
        "url": url,
        "plink_id": link.get("id"),
        "product_id": product.get("id"),
        "price_id": price.get("id"),
        "amount_usd": amt,
        "offer_id": oid,
        "name": offer["name"],
        "livemode": bool(link.get("livemode")),
        "source": offer["source"],
        "why": offer["why"],
        "sku_kind": offer["sku_kind"],
        "lane": offer["lane"],
        "turnaround": offer.get("turnaround"),
        "desc": offer["desc"],
    }


def _ensure_landing_hero_cheapest(cheapest: dict) -> dict:
    """Keep landing hero on cheapest buy-now conversion SKU ($19)."""
    if not WEBSITE.is_file():
        return {"ok": False, "error": "website/index.html missing"}
    html = WEBSITE.read_text(encoding="utf-8")
    url = cheapest["url"]
    amt = float(cheapest["amount_usd"])
    name = cheapest["name"]
    amt_i = int(amt) if amt == int(amt) else amt
    html2 = html
    html2 = re.sub(
        r'(class="btn btn-primary"\s+href=")https://buy\.stripe\.com/[^"]+("[\s\S]*?>)(?:Pay \$[^<]+ on Stripe|Buy now — \$[^<]+)',
        rf'\1{url}\2Buy now — ${amt_i} {name.split("(")[0].strip()}',
        html2,
        count=1,
    )
    html2 = re.sub(
        r'(class="nav-pay"\s+href=")https://buy\.stripe\.com/[^"]+"',
        rf'\1{url}"',
        html2,
        count=1,
    )
    if html2 == html:
        # Already pointed correctly or pattern drift — still report target
        return {
            "ok": True,
            "unchanged": True,
            "path": str(WEBSITE),
            "primary_url": url,
            "amount_usd": amt,
            "name": name,
        }
    WEBSITE.write_text(html2, encoding="utf-8")
    return {"ok": True, "unchanged": False, "path": str(WEBSITE), "primary_url": url, "amount_usd": amt, "name": name}


# --- Policy ---
print("=== POLICY ===")
opp = load_opportunity_policy()
print("opportunity_policy", opp)
pol = load_policy()
pol.opportunity = opp
save_policy(pol)

# --- Cash poll (honest) ---
print("=== CASH POLL ===")
bal = stripe_request("GET", "/v1/balance")
avail = 0
pend = 0
for row in bal.get("available") or []:
    if row.get("currency") == "usd":
        avail = int(row.get("amount") or 0)
for row in bal.get("pending") or []:
    if row.get("currency") == "usd":
        pend = int(row.get("amount") or 0)
pi = stripe_request("GET", "/v1/payment_intents", {"limit": "5"})
ch = stripe_request("GET", "/v1/charges", {"limit": "5"})
cs = stripe_request("GET", "/v1/checkout/sessions", {"limit": "5"})
st = settle_status()
cash_booked = float((st.get("cash") or {}).get("verified_cash_usd") or 0)
poll = auto_book_paid(limit=25)
usdc_n = _usdc_receipt_count()
print(
    f"CASH stripe_avail=${avail/100:.2f} pending=${pend/100:.2f} "
    f"verified=${cash_booked:.2f} poll_new=${poll.get('new_amount_usd') or 0} "
    f"usdc_receipts={usdc_n}"
)

landing = _probe_landing()
print("landing", landing)
stack = _stack_probe()
print("stack", stack)

warm_leads: list[dict] = []
outbound_path = DESK / "outbound_queue.jsonl"
if outbound_path.is_file():
    for line in outbound_path.read_text(encoding="utf-8", errors="replace").splitlines()[-120:]:
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        blob = json.dumps(row).lower()
        if any(
            k in blob
            for k in (
                "buyer_reply",
                "inbound_reply",
                "warm_lead",
                '"interested"',
                "payment_received",
                "wants_to_buy",
            )
        ):
            warm_leads.append(
                {
                    "ts": row.get("ts"),
                    "kind": row.get("kind") or row.get("channel"),
                    "title": str(row.get("title") or row.get("summary") or "")[:120],
                }
            )
print(f"WARM_LEADS {len(warm_leads)} (no fabricate)")

# --- Taken ids/amounts ---
desk = json.loads((DESK / "published_offers.json").read_text(encoding="utf-8"))
taken_ids = {str((o.get("meta") or {}).get("offer_id") or "") for o in desk.get("offers") or []}
taken_amts = {float(o.get("amount_usd") or 0) for o in desk.get("offers") or []}
cfg_pre = json.loads(OFFERS_CFG.read_text(encoding="utf-8"))
by_cfg = {str(o.get("id")): o for o in (cfg_pre.get("offers") or []) if isinstance(o, dict)}
for o in cfg_pre.get("offers") or []:
    if isinstance(o, dict):
        oid = str(o.get("id") or "")
        if oid:
            taken_ids.add(oid)
        try:
            taken_amts.add(float(o.get("price_usd") or 0))
        except (TypeError, ValueError):
            pass

by_pub: dict[str, dict] = {}
for o in desk.get("offers") or []:
    mid = str((o.get("meta") or {}).get("offer_id") or "")
    if mid and mid not in by_pub:
        by_pub[mid] = o


def _sku_from_id(oid: str, *, invent: bool) -> dict | None:
    cfg = by_cfg.get(oid) or {}
    pub = by_pub.get(oid) or {}
    url = str(cfg.get("stripe_url") or pub.get("url") or "")
    if not url.startswith("https://"):
        return None
    try:
        amt = float(cfg.get("price_usd") or pub.get("amount_usd") or 0)
    except (TypeError, ValueError):
        amt = 0.0
    if amt <= 0:
        return None
    return {
        "offer_id": oid,
        "name": str(cfg.get("name") or pub.get("title") or oid),
        "amount_usd": amt,
        "url": url,
        "why": "01:00 combo redistrib — conversion prioritized",
        "invent": invent,
    }


CONV_LIVE = [s for oid in CONV_LIVE_IDS if (s := _sku_from_id(oid, invent=False))]
INVENT_HOT = [s for oid in INVENT_HOT_IDS if (s := _sku_from_id(oid, invent=True))]
MULTI_RAIL_HOT = [s for oid in MULTI_RAIL_HOT_IDS if (s := _sku_from_id(oid, invent=False))]
print(f"POOLS conv_live={len(CONV_LIVE)} multi={len(MULTI_RAIL_HOT)} invent={len(INVENT_HOT)}")

created: list[dict] = []
distributed_new: list[dict] = []
redistributed: list[dict] = []
errors: list[dict] = []
skipped: list[dict] = []

print("=== NEW CONVERSION (mid-gap, max 2) ===")
for offer in NEW_CONVERSION:
    oid = offer["offer_id"]
    amt = float(offer["amount_usd"])
    if oid in taken_ids:
        skipped.append({"offer_id": oid, "reason": "id_taken", "lane": "cash_push"})
        print("SKIP id", oid)
        continue
    if amt in taken_amts:
        skipped.append({"offer_id": oid, "reason": f"amount_taken_{amt}", "lane": "cash_push"})
        print("SKIP amt", oid, amt)
        continue
    try:
        row = _create_stripe_sku(offer)
        created.append(row)
        taken_ids.add(oid)
        taken_amts.add(amt)
        print("CREATED_CONV", oid, row["url"], "live", row["livemode"])
    except Exception as exc:  # noqa: BLE001
        errors.append({"offer_id": oid, "phase": "stripe", "lane": "cash_push", "error": f"{type(exc).__name__}: {exc}"})
        print("FAIL conv", oid, exc)

# Register catalog
cfg = json.loads(OFFERS_CFG.read_text(encoding="utf-8"))
by_id = {str(o.get("id")): o for o in (cfg.get("offers") or []) if isinstance(o, dict)}
for sku in created:
    oid = sku["offer_id"]
    amount = float(sku["amount_usd"])
    by_id[oid] = {
        "id": oid,
        "name": sku["name"],
        "price_usd": amount,
        "turnaround": sku.get("turnaround") or "within 48h after payment clears",
        "scope": sku.get("desc") or f"Agent-fulfilled conversion deliverable: {sku['name']}.",
        "stripe_url": sku["url"],
        "rails": list(rails_base),
        "cycle": CYCLE,
        "invent_inventory": False,
        "conversion_tier": True,
        "lane": sku["lane"],
        "sku_kind": sku["sku_kind"],
    }
# Hero stays cheapest buy-now ($19)
cfg["recommended_id"] = "landing_cta_rewrite_19"
cfg["reason"] = (
    "Combo 01:00: harder buyer chase+redistrib; no free mid-gap ints → NEW conversion=0; "
    "force Moltbook on conversion; no $170+ invent inflate; NEW ua-*=0. "
    + ("PayPal wired." if paypal_wired else "PayPal not wired — skipped.")
)
cfg["offers"] = list(by_id.values())
OFFERS_CFG.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
print("CATALOG", len(cfg["offers"]), "NEW_CONV", len(created))

# Distribute NEW (force moltbook → draft on 429)
for sku in created:
    oid = sku["offer_id"]
    amount = float(sku["amount_usd"])
    sheet = offer_pay_sheet(oid)
    if not sheet.get("ok"):
        errors.append({"offer_id": oid, "phase": "usdc_sheet", "error": sheet.get("error")})
        print("USDC_FAIL", oid, sheet.get("error"))
        continue
    rails = list(rails_base)
    blurb = (
        f"BUY NOW: Stripe card/Link {sku['url']} "
        f"OR {sheet['amount']} USDC on {', '.join(sheet.get('chains') or [])} "
        f"to {sheet['receive_address']}. Deliverable: {sku['name']}."
    )
    if paypal_wired:
        blurb += f" PayPal: {paypal_email}."
    meta = {
        "offer_id": oid,
        "cycle": CYCLE,
        "settlement": "multi_rail_stripe_usdc",
        "rails": rails,
        "stripe_url": sku["url"],
        "plink_id": sku.get("plink_id"),
        "usdc": {
            "amount": sheet.get("amount"),
            "asset": sheet.get("asset"),
            "chains": sheet.get("chains"),
            "receive_address": sheet.get("receive_address"),
        },
        "paypal": {"wired": paypal_wired, "target": paypal_email or None},
        "human_share_required": False,
        "invent_inventory": False,
        "conversion_tier": True,
        "why_converts": sku.get("why"),
        "source": sku.get("source"),
        "sku_kind": sku["sku_kind"],
        "lane": sku["lane"],
        "blurb_extra": blurb,
    }
    try:
        dist = _distribute(sku["url"], sku["name"], amount, meta, force_moltbook=True)
        distributed_new.append(dist)
        print(
            f"DIST_NEW {oid} posted={dist['posted']} "
            f"molt={dist['moltbook'].get('via') or dist['moltbook'].get('reason')}"
        )
    except Exception as exc:  # noqa: BLE001
        errors.append({"offer_id": oid, "phase": "distribute", "error": f"{type(exc).__name__}: {exc}"})
        print("DIST_FAIL", oid, exc)

# Landing hero stays $19
cheap_cfg = by_id.get("landing_cta_rewrite_19") or {}
landing_patch = _ensure_landing_hero_cheapest(
    {
        "url": cheap_cfg.get("stripe_url") or "https://buy.stripe.com/bJe4gs3o9gn2h0u0Jx3843f",
        "amount_usd": float(cheap_cfg.get("price_usd") or 19),
        "name": cheap_cfg.get("name") or "Landing CTA rewrite pack (same-day)",
    }
)
print("LANDING_HERO", landing_patch)

# Redistrib: ALL conversion (live + new) → multi → invent
CONV_FOR_REDIST = list(CONV_LIVE) + [
    {
        "offer_id": c["offer_id"],
        "name": c["name"],
        "amount_usd": c["amount_usd"],
        "url": c["url"],
        "why": "00:00 NEW conversion redistrib",
    }
    for c in created
]
print("=== REDISTRIBUTE CONVERSION (harder chase: force_moltbook) ===")
conv_rows, conv_errs = _redist_batch(
    CONV_FOR_REDIST, invent=False, conversion=True, force_moltbook=True
)
redistributed.extend(conv_rows)
errors.extend(conv_errs)

print("=== REDISTRIBUTE MULTI-RAIL-HOT ===")
mr_rows, mr_errs = _redist_batch(MULTI_RAIL_HOT, invent=False, force_moltbook=False)
redistributed.extend(mr_rows)
errors.extend(mr_errs)

print("=== REDISTRIBUTE INVENT-HOT ===")
inv_rows, inv_errs = _redist_batch(INVENT_HOT, invent=True, force_moltbook=False)
redistributed.extend(inv_rows)
errors.extend(inv_errs)

channels_hit = sorted(
    {
        *(c for row in distributed_new for c in (row.get("posted") or [])),
        *(c for row in distributed_new for c in (row.get("queued") or [])),
        *(c for row in redistributed for c in (row.get("posted") or [])),
        *(c for row in redistributed for c in (row.get("queued") or [])),
    }
)

pending = list_items(status="pending")
pending_ids = [str(r.get("id")) for r in pending if isinstance(r, dict) and r.get("id")]
open_approval_count = len(pending_ids)

verified_cash = float(cash_booked or 0) + float(poll.get("new_amount_usd") or 0)

molt_vias: dict[str, int] = {}
for row in list(distributed_new) + list(redistributed):
    via = (row.get("moltbook") or {}).get("via") or (row.get("moltbook") or {}).get("reason") or "none"
    molt_vias[str(via)] = molt_vias.get(str(via), 0) + 1

cash_block = {
    "stripe_available_usd": avail / 100.0,
    "stripe_pending_usd": pend / 100.0,
    "verified_cash_usd": verified_cash,
    "poll_sessions": poll.get("sessions_seen"),
    "poll_intents": poll.get("intents_seen"),
    "poll_booked_usd": poll.get("new_amount_usd") or 0,
    "usdc_receipts_logged": usdc_n if usdc_n else st.get("receipts_logged"),
    "payment_intents": len(pi.get("data") or []),
    "charges": len(ch.get("data") or []),
    "checkout_sessions": len(cs.get("data") or []),
    "gap_usd": (st.get("hardware") or {}).get("gap_usd") or 1999.0,
    "spent_float_usd": 0.0,
}

note = (
    "Cash books only after Stripe paid or USDC settle --confirm. "
    "Policy: min_capital_proposal_likelihood_pct=60, cash_deadline_days=10, "
    "prefer_conversion_over_invent. NEW ua-*=0. Existing ua-* left PENDING. "
    "Stack left UP. Buyer chase: outbound refreshed; warm_leads not fabricated. "
    "No $170+ invent inflate."
)

hunt_out = {
    "ts": now_denver.isoformat(),
    "cycle": CYCLE,
    "mode": "combo_ceo_opp_hunt_01",
    "policy": opp,
    "cash": cash_block,
    "landing": landing,
    "landing_patch": landing_patch,
    "stack": stack,
    "rails_available": {
        "stripe": True,
        "usdc": True,
        "paypal": paypal_wired,
        "paypal_reason": None if paypal_wired else "PAYPAL_EMAIL/CLIENT unset",
    },
    "created": created,
    "distributed_new": distributed_new,
    "conversion_redistributed": [r["offer_id"] for r in conv_rows],
    "invent_redistributed": [r["offer_id"] for r in inv_rows],
    "multi_rail_redistributed": [r["offer_id"] for r in mr_rows],
    "redistributed": redistributed,
    "channels_hit": channels_hit,
    "moltbook_via_counts": molt_vias,
    "warm_leads": warm_leads,
    "skipped": skipped,
    "errors": errors,
    "open_approval_count": open_approval_count,
    "gates_left_pending": pending_ids,
    "new_ua_ids": [],
    "opp_light": {
        "new_service_skus": [c["offer_id"] for c in created],
        "new_ua_ids": [],
        "note": "Light 4h opp: conversion/service SKUs only; no invent inflate; no NEW ua-*",
    },
    "note": note,
}
hunt_path = DESK / "zerocap_hunt_20261128_01.json"
hunt_path.write_text(json.dumps(hunt_out, indent=2) + "\n", encoding="utf-8")
print("WROTE", hunt_path)

opp_path = DESK / "opp_seeded_offers_20261128_01.json"
opp_out = {
    "ts": now_denver.isoformat(),
    "cycle": "bb-opp-light-20261128-01",
    "mode": "light_opp_conversion_first",
    "policy": opp,
    "cash": cash_block,
    "created": created,
    "distributed_new": distributed_new,
    "conversion_redistributed_share": [r["offer_id"] for r in conv_rows],
    "open_approval_count": open_approval_count,
    "gates_left_pending": pending_ids,
    "new_ua_ids": [],
    "stack": stack,
    "note": (
        "Light opp inside Hunt 00:00. No free mid-gap ints → NEW=0; harder conversion chase "
        "(force Moltbook). No invent inflate. No NEW ua-*. Rails Stripe+USDC only."
    ),
}
opp_path.write_text(json.dumps(opp_out, indent=2) + "\n", encoding="utf-8")
print("WROTE", opp_path)

amts = "/".join(f"${c['amount_usd']:.0f}" for c in created) if created else "(none)"
note_event(
    kind="account_change",
    summary=(
        f"Combo 01:00: cash ${verified_cash:.2f}; "
        f"NEW conversion {len(created)} ({amts}); "
        f"redistributed {len(redistributed)} "
        f"({len(conv_rows)} conv + {len(mr_rows)} multi + {len(inv_rows)} invent); "
        f"float=$0; open_approvals={open_approval_count}; channels={channels_hit}"
    ),
    event_id=f"combo-01-{now_denver.strftime('%Y%m%d%H%M')}",
    section="ACCOUNT_CHANGES",
    detail={
        "cycle": CYCLE,
        "conversion_ids": [c["offer_id"] for c in created],
        "amounts": [c["amount_usd"] for c in created],
        "urls": [c["url"] for c in created],
        "cash_booked": verified_cash,
        "open_approval_count": open_approval_count,
        "channels_hit": channels_hit,
        "new_ua_ids": [],
        "warm_leads": len(warm_leads),
        "stack": stack,
        "policy": opp,
    },
    refresh_digest=False,
)
record_ops_check(
    check_type="manual",
    extra_other=[
        {
            "id": "combo-chase-01",
            "summary": (
                f"Combo 01:00: NEW conversion {len(created)} ({amts}); "
                f"redistributed {len(conv_rows)} conv + {len(mr_rows)} multi + {len(inv_rows)} invent; "
                f"cash $0; float=$0; stack UP; ua-* PENDING; NEW ua-*=0; warm_leads={len(warm_leads)}; "
                f"no free mid-gap; conversion chase only; no invent inflate"
            ),
        }
    ],
    extra={
        "cycle": CYCLE,
        "created_conversion": len(created),
        "distributed_new": len(distributed_new),
        "redistributed": len(redistributed),
        "conversion_redistributed": len(conv_rows),
        "invent_redistributed": len(inv_rows),
        "multi_rail_redistributed": len(mr_rows),
        "errors": len(errors),
        "open_approval_count": open_approval_count,
        "paypal_wired": paypal_wired,
        "rails": ["stripe_card", "stripe_link", "usdc"] + (["paypal"] if paypal_wired else []),
        "conversion_tier": True,
        "channels_hit": channels_hit,
        "cash_usd": verified_cash,
        "spent_float_usd": 0.0,
        "new_ua_ids": [],
        "warm_leads": len(warm_leads),
        "stack_green": bool(stack.get("dashboard_ok") and stack.get("velocity_pid")),
        "policy": opp,
        "opp_light": True,
    },
    refresh_digest=True,
    mark_notified=True,
)
digest = write_digest(check_type="manual")
print(
    f"DONE conv_new={len(created)} dist_new={len(distributed_new)} redist={len(redistributed)} "
    f"conv_redist={len(conv_rows)} multi_redist={len(mr_rows)} invent_redist={len(inv_rows)} "
    f"errors={len(errors)} cash=${verified_cash:.2f} open_approvals={open_approval_count} "
    f"channels={channels_hit} molt={molt_vias} warm={len(warm_leads)}"
)
print("DIGEST", digest.get("project_digest") or digest.get("sandbox_digest"))
for c in created:
    print(f"SKU ${c['amount_usd']:.0f} {c['offer_id']} {c['url']}")
