import sys
import re
import json
import requests

# ── Config ────────────────────────────────────────────────────────────────────

PAGE_URL = "https://www.patreon.com/mattnathanson"
TARGET_TIER = "SKYHIGHHONEY"
SIGNUP_URL = "https://www.patreon.com/join/mattnathanson"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# ── Fetch & Parse ─────────────────────────────────────────────────────────────

def fetch_page():
    resp = requests.get(PAGE_URL, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.text

def extract_tiers(html):
    # Patreon embeds all page data as a JSON blob in a <script> tag
    match = re.search(r'window\.patreon\.bootstrap\s*=\s*({.*?});\s*</script>', html, re.DOTALL)
    if not match:
        # Try alternate embed format used in newer page versions
        match = re.search(r'"rewards"\s*:\s*(\[.*?\])', html, re.DOTALL)
        if not match:
            return None, "Could not find Patreon data blob in page HTML — structure may have changed."

        rewards_raw = match.group(1)
        try:
            rewards = json.loads(rewards_raw)
        except json.JSONDecodeError:
            return None, "Found rewards blob but failed to parse JSON."

        tiers = []
        for r in rewards:
            attrs = r.get("attributes", r)  # handle both wrapped and flat formats
            title = attrs.get("title", "")
            remaining = attrs.get("remaining")
            published = attrs.get("published", True)
            if published and title == TARGET_TIER:
                tiers.append({"title": title, "remaining": remaining})
        return tiers, None

    try:
        bootstrap = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None, "Found bootstrap blob but failed to parse JSON."

    # Dig through the bootstrap structure for reward/tier data
    tiers = []
    campaign = bootstrap.get("campaign", {})
    included = campaign.get("included", [])
    for item in included:
        if item.get("type") not in ("reward", "tier"):
            continue
        attrs = item.get("attributes", {})
        title = attrs.get("title", "")
        remaining = attrs.get("remaining")
        published = attrs.get("published", True)
        if published and title == TARGET_TIER:
            tiers.append({"title": title, "remaining": remaining})

    return tiers, None

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"Fetching {PAGE_URL}...")

    html = fetch_page()
    tiers, error = extract_tiers(html)

    if error:
        print(f"WARNING: {error}")
        sys.exit(0)

    if not tiers:
        print(f"WARNING: Tier '{TARGET_TIER}' not found in page data — name may have changed.")
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
