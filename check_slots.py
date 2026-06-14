import os
import sys
import requests

# ── Config ────────────────────────────────────────────────────────────────────

CAMPAIGN_ID = "4737220"
TARGET_TIER = "SKYHIGHHONEY"
SIGNUP_URL = "https://www.patreon.com/join/mattnathanson"

ACCESS_TOKEN = os.environ.get("PATREON_ACCESS_TOKEN")

API_URL = (
    f"https://www.patreon.com/api/oauth2/v2/campaigns/{CAMPAIGN_ID}"
    f"?include=tiers&fields[tier]=title,remaining,published,patron_count"
)

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "User-Agent": "SlotWatcher/1.0",
}

# ── Fetch ─────────────────────────────────────────────────────────────────────

def fetch_tiers():
    resp = requests.get(API_URL, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    tiers = []
    for item in data.get("included", []):
        if item.get("type") != "tier":
            continue
        attrs = item.get("attributes", {})
        title = attrs.get("title", "")
        remaining = attrs.get("remaining")
        published = attrs.get("published", True)
        if published and title == TARGET_TIER:
            tiers.append({"title": title, "remaining": remaining})
    return tiers

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not ACCESS_TOKEN:
        print("ERROR: PATREON_ACCESS_TOKEN secret is not set.", file=sys.stderr)
        sys.exit(0)

    print(f"Checking Patreon campaign {CAMPAIGN_ID}...")

    tiers = fetch_tiers()

    if not tiers:
        print(f"WARNING: Tier '{TARGET_TIER}' not found — name may have changed.")
        sys.exit(0)

    tier = tiers[0]
    remaining = tier["remaining"]
    print(f"  {tier['title']}: {remaining if remaining is not None else 'unlimited'} remaining")

    if remaining is not None and remaining > 0:
        slot_word = "slot" if remaining == 1 else "slots"
        print(f"SLOT OPEN: {tier['title']} has {remaining} {slot_word} available!")
        print(f"Sign up here: {SIGNUP_URL}")
        sys.exit(1)  # Intentional failure — triggers GitHub email notification
    else:
        print("No open slots. Nothing to do.")
        sys.exit(0)

if __name__ == "__main__":
    main()
