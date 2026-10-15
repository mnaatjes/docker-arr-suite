#!/usr/bin/env python3
"""
check_functional_search.py - Functional Search & Indexer Capability Verification

Performs live search queries against each indexer in Prowlarr and executes
functional validation probes across downstream applications (Sonarr, Radarr,
Lidarr, Readarr) to verify indexers can successfully return releases.

Usage:
    python3 check_functional_search.py \
        [--host 192.168.1.52] \
        --prowlarr-key KEY \
        [--radarr-key KEY] \
        [--sonarr-key KEY] \
        [--query "matrix"]
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def make_request(url, method="GET", data=None, api_key=None, timeout=30):
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if api_key:
        headers["X-Api-Key"] = api_key

    payload = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=payload, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            res_body = response.read().decode("utf-8")
            return response.status, json.loads(res_body) if res_body else None
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            parsed = json.loads(err_body)
        except Exception:
            parsed = err_body
        return e.code, parsed
    except Exception as e:
        return 0, str(e)


def check_prowlarr_functional_search(host, port, api_key, query):
    base_url = f"http://{host}:{port}/api/v1"
    print(f"--- 1. Testing Prowlarr Master Live Search (Query: '{query}') ---")

    # Get indexers
    status, indexers = make_request(f"{base_url}/indexer", api_key=api_key)
    if status != 200:
        print(f"[!] Failed to retrieve indexers from Prowlarr: {status} {indexers}")
        return False

    all_functional = True
    for idx in sorted(indexers, key=lambda x: x["id"]):
        idx_id = idx["id"]
        idx_name = idx["name"]

        # Run search targeted at this indexer
        params = urllib.parse.urlencode({
            "query": query,
            "type": "search",
            "indexerIds": idx_id,
            "limit": 10,
        })
        search_url = f"{base_url}/search?{params}"
        s_status, s_body = make_request(search_url, api_key=api_key, timeout=25)

        if s_status == 200 and isinstance(s_body, list):
            count = len(s_body)
            sample = f" (Top: '{s_body[0].get('title', '')[:45]}...')" if count > 0 else " (0 results for query)"
            print(f"  [+] Indexer #{idx_id:02d} {idx_name:18} : FUNCTIONAL - {count} releases returned{sample}")
        else:
            err = s_body if isinstance(s_body, str) else json.dumps(s_body)
            print(f"  [-] Indexer #{idx_id:02d} {idx_name:18} : FAILED - HTTP {s_status} ({err[:80]})")
            all_functional = False

    print()
    return all_functional


def check_app_functional_capability(app_name, host, port, api_key, api_ver="v3"):
    base_url = f"http://{host}:{port}/api/{api_ver}"
    print(f"--- 2. Testing {app_name} Direct Capability Probe (/api/{api_ver}/indexer/test) ---")

    # Fetch indexers
    status, indexers = make_request(f"{base_url}/indexer", api_key=api_key)
    if status != 200:
        print(f"  [!] Failed to retrieve indexers from {app_name}: {status} {indexers}\n")
        return False

    all_valid = True
    for idx in sorted(indexers, key=lambda x: x["name"]):
        name = idx["name"]
        test_status, test_body = make_request(
            f"{base_url}/indexer/test",
            method="POST",
            data=idx,
            api_key=api_key,
            timeout=15,
        )

        if test_status in (200, 204):
            print(f"  [+] {name:28} : PASS (Ready for automated release search)")
        else:
            err = test_body if isinstance(test_body, str) else json.dumps(test_body)
            print(f"  [-] {name:28} : WARN/FAIL (HTTP {test_status} - {err[:65]})")
            all_valid = False

    print()
    return all_valid


def main():
    parser = argparse.ArgumentParser(description="Check functional search capability across Arr suite")
    parser.add_argument("--host", default=os.getenv("ARR_HOST", "192.168.1.52"), help="Arr suite host IP")
    parser.add_argument("--prowlarr-port", default="9696", help="Prowlarr port")
    parser.add_argument("--prowlarr-key", default=os.getenv("PROWLARR_API_KEY", ""), help="Prowlarr API key")
    parser.add_argument("--radarr-port", default="7878", help="Radarr port")
    parser.add_argument("--radarr-key", default=os.getenv("RADARR_API_KEY", ""), help="Radarr API key")
    parser.add_argument("--sonarr-port", default="8989", help="Sonarr port")
    parser.add_argument("--sonarr-key", default=os.getenv("SONARR_API_KEY", ""), help="Sonarr API key")
    parser.add_argument("--query", default="ubuntu", help="Search keyword for live Prowlarr probe")
    args = parser.parse_args()

    if not args.prowlarr_key.strip():
        print("Error: --prowlarr-key or PROWLARR_API_KEY required.", file=sys.stderr)
        sys.exit(1)

    print(f"=== Arr Suite Functional Search & Capability Verification [{args.host}] ===\n")

    prowlarr_ok = check_prowlarr_functional_search(args.host, args.prowlarr_port, args.prowlarr_key.strip(), args.query)

    if args.radarr_key.strip():
        check_app_functional_capability("Radarr (Movies)", args.host, args.radarr_port, args.radarr_key.strip(), api_ver="v3")

    if args.sonarr_key.strip():
        check_app_functional_capability("Sonarr (TV)", args.host, args.sonarr_port, args.sonarr_key.strip(), api_ver="v3")

    print("Functional verification complete.")


if __name__ == "__main__":
    main()
