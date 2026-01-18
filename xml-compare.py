import urllib.parse
import xml.etree.ElementTree as ET
from urllib.request import Request, urlopen
from typing import Dict, Any, List, Tuple
import random

LIVE_URL = "URL1"
SRV_URL  = "URL2"

IGNORE_TAGS = {"color", "season", "description", "variations"}  # ignore these fields/subtrees entirely
URL_TAGS = {"link", "image", "additional_imageurl"}            # compare URLs ignoring domain


def fetch_xml(url: str) -> str:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=120) as resp:
        return resp.read().decode("utf-8", errors="replace")


def norm_text(s: str) -> str:
    return (s or "").strip()


def norm_url(s: str) -> str:
    s = norm_text(s)
    if not s:
        return ""
    u = urllib.parse.urlparse(s)
    path = u.path or ""
    query = ("?" + u.query) if u.query else ""
    return path + query  # ignore scheme + host


def get_text(el: ET.Element) -> str:
    return norm_text(el.text or "")


def element_to_flat_dict(product_el: ET.Element) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for child in list(product_el):
        tag = child.tag.strip()

        if tag in IGNORE_TAGS:
            continue

        # ignore variations subtree completely
        if tag == "variations":
            continue

        if list(child):
            # nested (rare besides variations). Keep XML string to detect diffs if needed.
            out[tag] = norm_text(ET.tostring(child, encoding="unicode"))
        else:
            val = get_text(child)
            if tag in URL_TAGS:
                val = norm_url(val)
            out[tag] = val

    return out


def index_products(xml_text: str) -> Dict[str, Dict[str, Any]]:
    root = ET.fromstring(xml_text)
    products = root.findall(".//product")

    idx: Dict[str, Dict[str, Any]] = {}
    for p in products:
        d = element_to_flat_dict(p)

        pid = norm_text(d.get("id", ""))
        mpn = norm_text(d.get("mpn", ""))

        # prefer id; fallback to mpn
        key = f"id:{pid}" if pid else (f"mpn:{mpn}" if mpn else None)
        if not key:
            continue

        idx[key] = d

    return idx


def sample_keys(keys: List[str], take_per_section: int = 5) -> List[str]:
    n = len(keys)
    if n == 0:
        return []

    # define ranges (percentages)
    start_range  = (0, int(n * 0.2))           # first ~20%
    middle_range = (int(n * 0.4), int(n * 0.6))# middle ~20%
    end_range    = (int(n * 0.8), n)           # last ~20%

    def pick_from_range(r):
        lo, hi = r
        pool = keys[lo:hi]
        if not pool:
            return []
        return random.sample(pool, min(take_per_section, len(pool)))

    sample = []
    sample += pick_from_range(start_range)
    sample += pick_from_range(middle_range)
    sample += pick_from_range(end_range)

    # unique (just in case)
    seen = set()
    final = []
    for k in sample:
        if k not in seen:
            final.append(k)
            seen.add(k)

    return final


def diff_dict(a: Dict[str, Any], b: Dict[str, Any]) -> List[Tuple[str, str, str]]:
    diffs = []
    keys = sorted(set(a.keys()) | set(b.keys()))
    for k in keys:
        va = a.get(k, "")
        vb = b.get(k, "")
        if str(va) != str(vb):
            diffs.append((k, str(va), str(vb)))
    return diffs


def main():
    print("Fetching feeds...")
    live_xml = fetch_xml(LIVE_URL)
    srv_xml  = fetch_xml(SRV_URL)

    live = index_products(live_xml)
    srv  = index_products(srv_xml)

    print(f"Counts: live={len(live)} srv={len(srv)}")

    common = sorted(set(live.keys()) & set(srv.keys()))
    only_live = sorted(set(live.keys()) - set(srv.keys()))
    only_srv  = sorted(set(srv.keys()) - set(live.keys()))

    print(f"Common keys: {len(common)}")
    print(f"Only in live: {len(only_live)}")
    print(f"Only in srv : {len(only_srv)}")

    picked = sample_keys(common)
    print("\nSample keys:")
    for k in picked:
        print(f"- {k}")

    for k in picked:
        a = live[k]
        b = srv[k]
        diffs = diff_dict(a, b)

        print("\n" + "=" * 90)
        print(f"{k}  |  live_id={a.get('id','')}  srv_id={b.get('id','')}")
        if not diffs:
            print(" MATCH (ignoring color/season/description/variations + ignoring domain in URLs)")
        else:
            print(f" DIFFS ({len(diffs)} fields):")
            for field, va, vb in diffs:
                print(f"- {field}\n  live  : {va}\n  server: {vb}")


if __name__ == "__main__":
    main()
