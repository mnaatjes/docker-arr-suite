#!/usr/bin/env python3
"""
verify_indexers_sync.py - Unified Indexer Synchronization Verification Tool

Queries Prowlarr and all registered downstream Arr applications (Sonarr, Radarr,
Lidarr, Readarr) via REST API to verify and report active indexer synchronization.

Usage:
    python3 verify_indexers_sync.py \
        [--host 192.168.1.52] \
        --prowlarr-key KEY \
        [--radarr-key KEY] \
        [--sonarr-key KEY] \
        [--lidarr-key KEY] \
        [--readarr-key KEY]
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def query_indexers(url, api_key, timeout=10):
    headers = {
        "Accept": "application/json",
        "X-Api-Key": api_key,
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
            return True, [idx["name"] for idx in data]
    except Exception as e:
        return False, str(e)


def main():
    parser = argparse.ArgumentParser(description="Verify indexer sync across all Arr suite services")
    parser.add_argument("--host", default=os.getenv("ARR_HOST", "192.168.1.52"), help="Arr suite host IP")
    parser.add_argument("--prowlarr-port", default="9696", help="Prowlarr port")
    parser.add_argument("--prowlarr-key", default=os.getenv("PROWLARR_API_KEY", ""), help="Prowlarr API key")
    parser.add_argument("--radarr-port", default="7878", help="Radarr port")
    parser.add_argument("--radarr-key", default=os.getenv("RADARR_API_KEY", ""), help="Radarr API key")
    parser.add_argument("--sonarr-port", default="8989", help="Sonarr port")
    parser.add_argument("--sonarr-key", default=os.getenv("SONARR_API_KEY", ""), help="Sonarr API key")
    parser.add_argument("--lidarr-port", default="8686", help="Lidarr port")
    parser.add_argument("--lidarr-key", default=os.getenv("LIDARR_API_KEY", ""), help="Lidarr API key")
    parser.add_argument("--readarr-port", default="8787", help="Readarr port")
    parser.add_argument("--readarr-key", default=os.getenv("READARR_API_KEY", ""), help="Readarr API key")
    args = parser.parse_args()

    services = [
        {"name": "Prowlarr (Master)", "url": f"http://{args.host}:{args.prowlarr_port}/api/v1/indexer", "key": args.prowlarr_key},
        {"name": "Sonarr (TV)", "url": f"http://{args.host}:{args.sonarr_port}/api/v3/indexer", "key": args.sonarr_key},
        {"name": "Radarr (Movies)", "url": f"http://{args.host}:{args.radarr_port}/api/v3/indexer", "key": args.radarr_key},
        {"name": "Lidarr (Audio)", "url": f"http://{args.host}:{args.lidarr_port}/api/v1/indexer", "key": args.lidarr_key},
        {"name": "Readarr (Books)", "url": f"http://{args.host}:{args.readarr_port}/api/v1/indexer", "key": args.readarr_key},
    ]

    print(f"=== Arr Suite Indexer Synchronization Report [{args.host}] ===\n")
    all_ok = True

    for svc in services:
        name = svc["name"]
        key = svc["key"].strip()
        if not key:
            print(f"[-] {name:18} : [SKIPPED - No API key provided]")
            continue

        ok, result = query_indexers(svc["url"], key)
        if not ok:
            print(f"[x] {name:18} : FAILED ({result})")
            all_ok = False
        else:
            print(f"[+] {name:18} : {len(result)} indexers active")
            for idx in sorted(result):
                print(f"      - {idx}")
        print()

    if all_ok:
        print("All configured services reachable and verified.")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
