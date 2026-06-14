import sys
import requests

# ── Config ────────────────────────────────────────────────────────────────────

CAMPAIGN_ID = "4737220"
PATREON_URL = f"https://www.patreon.com/api/campaigns/{CAMPAIGN_ID}?include=tiers&fields[reward]=title,remaining,patron_count,published"

TARGET_TIER = "SKYHIGHHONEY"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.patreon.com/",
}

SIGNUP_URL = f"https://www.patreon.com/join/mattnathanson"

# ── Fetch ─────────────────────────────────────────────────────────────────────

def fetch_tiers():
    resp = requests.get(PATREON_URL, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    tiers = []
    for item in data.get("included", []):
        if item.get("type") != "reward":
            continue
        attrs = item.get("attributes", {})
        title = attrs.get("title", "")
        remaining = attrs.get("remaining")       # None = unlimited, int = capped
        published = attrs.get("published", False)
        if published and title == TARGET_TIER:
            tiers.append({
                "title": title,
                "remaining": remaining,
            })
    return tiers

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"Checking Patreon campaign {CAMPAIGN_ID}...")

    tiers = fetch_tiers()

    if not tiers:
        print(
            "WARNING: No matching tiers found in API response. "
            "The tier names or campaign structure may have changed."
        )
        sys.exit(0)

    open_tiers = [t for t in tiers if t["remaining"] is not None and t["remaining"] > 0]

    for t in tiers:
        status = t["remaining"] if t["remaining"] is not None else "unlimited"
        print(f"  {t['title']}: {status} remaining")

    if open_tiers:
        remaining = open_tiers[0]["remaining"]
        slot_word = "slot" if remaining == 1 else "slots"
        print(f"SLOT OPEN: {open_tiers[0]['title']} has {remaining} {slot_word} available!")
        print(f"Sign up here: {SIGNUP_URL}")
        sys.exit(1)  # Intentional failure — triggers GitHub email notification
    else:
        print("No open slots. Nothing to do.")
        sys.exit(0)

if __name__ == "__main__":
    main()
