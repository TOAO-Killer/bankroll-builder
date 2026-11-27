"""Add second mid-gap conversion SKU ($62) after resume hunt (amt $29 blocked by invent)."""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _pyc_bootstrap  # noqa: F401

from grokfreakit.paths import CONFIG, load_env_files

load_env_files()
from bankroll.env_aliases import apply_env_aliases

apply_env_aliases()

from bankroll.velocity.offer_publisher import publish_offer_channels
from capital_engine.stripe_client import live_charges_enabled, stripe_request
from bankroll.velocity.settle import offer_pay_sheet

assert live_charges_enabled()

CYCLE = "bb-zerocap-hunt-chase-resume-20261127"
ROOT = Path(__file__).resolve().parents[1]
DESK = ROOT / "data" / "desk"
OFFERS_CFG = CONFIG / "service_offers.json"
USDC_ADDR = "0xa38844Df998769d9f9e014186265C99095D19A3B"
DENVER = timezone(timedelta(hours=-7), name="America/Denver")
now = datetime.now(DENVER)

offer = {
    "offer_id": "helper_text_copy_pass_62",
    "name": "Helper text copy pass (same-day)",
    "amount_usd": 62.0,
    "turnaround": "same-day after payment clears",
    "desc": (
        "Agent-fulfilled: rewrite up to 8 form helper/hint paragraphs under inputs "
        "(≤110 chars each) on one page to reduce checkout/form friction, plus a one-line "
        "rationale table. Markdown same-day after payment clears. "
        "Fills mid-gap between $58 payment-link copy and $68 multi-rail status one-pager."
    ),
    "why": "Free mid-gap $62 inside $19–$79 chase; concrete helper-text deliverable agents can ship.",
    "source": "conversion_service",
    "sku_kind": "conversion_service",
    "lane": "cash_push",
}

cfg = json.loads(OFFERS_CFG.read_text(encoding="utf-8"))
taken_ids = {str(o.get("id") or "") for o in cfg.get("offers") or []}
taken_amts = {float(o.get("price_usd") or 0) for o in cfg.get("offers") or []}
oid = offer["offer_id"]
amt = float(offer["amount_usd"])
assert oid not in taken_ids, "id taken"
assert amt not in taken_amts, "amount taken"

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
        "metadata[turnaround]": offer["turnaround"],
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
assert url.startswith("https://"), url
print("CREATED", oid, url, "live", link.get("livemode"))

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

offers = list(cfg.get("offers") or [])
offers.append(
    {
        "id": oid,
        "name": offer["name"],
        "price_usd": amt,
        "turnaround": offer["turnaround"],
        "scope": offer["desc"],
        "stripe_url": url,
        "rails": list(rails_base),
        "cycle": CYCLE,
        "invent_inventory": False,
        "conversion_tier": True,
        "lane": offer["lane"],
        "sku_kind": offer["sku_kind"],
    }
)
cfg["offers"] = offers
cfg["reason"] = (
    "Resume hunt 13:00: conversion chase $19-$79; mid-gap $21/$62 added; "
    "no $170+ invent inflate; NEW ua-*=0. "
    + ("PayPal wired." if paypal_wired else "PayPal not wired — skipped.")
)
OFFERS_CFG.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")

sheet = offer_pay_sheet(oid)
assert sheet.get("ok"), sheet
blurb = (
    f"BUY NOW: Stripe card/Link {url} "
    f"OR {sheet['amount']} USDC on {', '.join(sheet.get('chains') or [])} "
    f"to {sheet['receive_address']}. Deliverable: {offer['name']}."
)
meta = {
    "offer_id": oid,
    "cycle": CYCLE,
    "settlement": "multi_rail_stripe_usdc",
    "rails": ["stripe_card", "stripe_link", "usdc"],
    "stripe_url": url,
    "plink_id": link.get("id"),
    "usdc": {
        "amount": sheet.get("amount"),
        "asset": sheet.get("asset"),
        "chains": sheet.get("chains"),
        "receive_address": sheet.get("receive_address"),
    },
    "human_share_required": False,
    "invent_inventory": False,
    "conversion_tier": True,
    "why_converts": offer["why"],
    "source": offer["source"],
    "sku_kind": offer["sku_kind"],
    "lane": offer["lane"],
    "blurb_extra": blurb,
}
share = publish_offer_channels(
    url=url,
    title=f"BankrollBuilder — {offer['name']} (Stripe+USDC)",
    amount_usd=amt,
    meta=meta,
    force_moltbook=True,
)
share2 = publish_offer_channels(
    url=url,
    title=f"BankrollBuilder — {offer['name']} USDC settle",
    amount_usd=amt,
    meta={**meta, "primary_rail": "usdc"},
    force_moltbook=False,
)
molt = next((c for c in (share.get("channels") or []) if c.get("channel") == "moltbook"), {})
print(
    "DIST",
    oid,
    "posted",
    sorted(set([*(share.get("posted") or []), *(share2.get("posted") or [])])),
    "molt",
    molt.get("via") or molt.get("reason"),
)

# Patch hunt artifact
hunt_path = DESK / "zerocap_hunt_20261127_13.json"
hunt = json.loads(hunt_path.read_text(encoding="utf-8"))
sku_row = {
    "ok": True,
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
    "turnaround": offer["turnaround"],
    "desc": offer["desc"],
}
hunt.setdefault("created", []).append(sku_row)
hunt.setdefault("distributed_new", []).append(
    {
        "offer_id": oid,
        "name": offer["name"],
        "amount_usd": amt,
        "url": url,
        "posted": sorted(set([*(share.get("posted") or []), *(share2.get("posted") or [])])),
        "moltbook": molt,
        "ok": True,
        "sku_kind": "conversion_service",
        "lane": "cash_push",
    }
)
hunt.setdefault("opp_light", {})["new_service_skus"] = [
    c["offer_id"] for c in hunt.get("created") or []
]
hunt["sku2_note"] = (
    f"Second mid-gap $62 added {now.isoformat()} after $29 blocked by invent hiring_spotlight_48h."
)
hunt_path.write_text(json.dumps(hunt, indent=2) + "\n", encoding="utf-8")
print("UPDATED", hunt_path)
print(f"SKU ${amt:.0f} {oid} {url}")
