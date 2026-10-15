#!/usr/bin/env python3
"""
sync_arr_applications.py - Deterministic Prowlarr Application Sync Tool

Registers downstream Arr applications (Radarr, Sonarr, Lidarr, Readarr)
into Prowlarr with 'fullSync' enabled. Once registered, Prowlarr automatically
and deterministically synchronizes all configured indexers directly to each app.

Usage:
    python3 sync_arr_applications.py \
        --prowlarr-key KEY \
        --radarr-key KEY \
        --sonarr-key KEY \
        --lidarr-key KEY \
        --readarr-key KEY
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def make_request(url, method="GET", data=None, api_key=None, timeout=25):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
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


def get_existing_apps(prowlarr_url, prowlarr_key):
    status, body = make_request(f"{prowlarr_url}/api/v1/applications", api_key=prowlarr_key)
    if status != 200:
        raise RuntimeError(f"Failed to fetch existing applications: {status} {body}")
    return {app["name"].lower(): app for app in body}


def get_app_schemas(prowlarr_url, prowlarr_key):
    status, body = make_request(f"{prowlarr_url}/api/v1/applications/schema", api_key=prowlarr_key)
    if status != 200:
        raise RuntimeError(f"Failed to fetch application schemas: {status} {body}")
    return {schema["implementationName"].lower(): schema for schema in body}


def register_application(prowlarr_url, prowlarr_key, app_name, app_server_url, app_api_key, prowlarr_server_url, schema_map, existing_map):
    name_lower = app_name.lower()
    if name_lower in existing_map:
        print(f"[SKIP] Application '{app_name}' already registered in Prowlarr (id={existing_map[name_lower]['id']}).")
        return True

    if name_lower not in schema_map:
        print(f"[ERROR] Schema for application implementation '{app_name}' not found.")
        return False

    app_spec = schema_map[name_lower].copy()
    app_spec["name"] = app_name
    app_spec["syncLevel"] = "fullSync"

    for field in app_spec.get("fields", []):
        if field.get("name") == "prowlarrUrl":
            field["value"] = prowlarr_server_url
        elif field.get("name") == "baseUrl":
            field["value"] = app_server_url
        elif field.get("name") == "apiKey":
            field["value"] = app_api_key

    print(f"[TESTING] Testing Prowlarr connection to '{app_name}' at {app_server_url}...")
    test_status, test_body = make_request(
        f"{prowlarr_url}/api/v1/applications/test",
        method="POST",
        data=app_spec,
        api_key=prowlarr_key,
    )

    if test_status != 200:
        print(f"[FAIL] Test connection failed for '{app_name}': {test_status} {test_body}")
        return False

    print(f"[SUCCESS] Test passed for '{app_name}'. Registering application...")
    create_status, create_body = make_request(
        f"{prowlarr_url}/api/v1/applications",
        method="POST",
        data=app_spec,
        api_key=prowlarr_key,
    )

    if create_status in (200, 201):
        print(f"[REGISTERED] Application '{app_name}' registered successfully (id={create_body.get('id')}). Prowlarr is now syncing indexers.")
        return True
    else:
        print(f"[ERROR] Failed to register '{app_name}': {create_status} {create_body}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Deterministic Prowlarr Application Sync Tool")
    parser.add_argument("--host", default=os.getenv("PROWLARR_HOST", "192.168.1.52"), help="Prowlarr host")
    parser.add_argument("--port", default=os.getenv("PROWLARR_PORT", "9696"), help="Prowlarr port")
    parser.add_argument("--prowlarr-key", default=os.getenv("PROWLARR_API_KEY", ""), help="Prowlarr API key")
    parser.add_argument("--radarr-key", default=os.getenv("RADARR_API_KEY", ""), help="Radarr API key")
    parser.add_argument("--sonarr-key", default=os.getenv("SONARR_API_KEY", ""), help="Sonarr API key")
    parser.add_argument("--lidarr-key", default=os.getenv("LIDARR_API_KEY", ""), help="Lidarr API key")
    parser.add_argument("--readarr-key", default=os.getenv("READARR_API_KEY", ""), help="Readarr API key")
    args = parser.parse_args()

    prowlarr_key = args.prowlarr_key.strip()
    if not prowlarr_key:
        print("Error: --prowlarr-key or PROWLARR_API_KEY required.", file=sys.stderr)
        sys.exit(1)

    prowlarr_url = f"http://{args.host}:{args.port}"
    # Internal Docker bridge network URLs used for inter-container communication
    prowlarr_internal = "http://prowlarr:9696"

    apps_to_sync = [
        {"name": "Radarr", "server_url": "http://radarr:7878", "api_key": args.radarr_key.strip()},
        {"name": "Sonarr", "server_url": "http://sonarr:8989", "api_key": args.sonarr_key.strip()},
        {"name": "Lidarr", "server_url": "http://lidarr:8686", "api_key": args.lidarr_key.strip()},
        {"name": "Readarr", "server_url": "http://readarr:8787", "api_key": args.readarr_key.strip()},
    ]

    existing_map = get_existing_apps(prowlarr_url, prowlarr_key)
    schema_map = get_app_schemas(prowlarr_url, prowlarr_key)

    success_count = 0
    total_candidates = 0
    for target in apps_to_sync:
        if not target["api_key"]:
            print(f"[SKIP] API key not provided for {target['name']}.")
            continue
        total_candidates += 1
        if register_application(prowlarr_url, prowlarr_key, target["name"], target["server_url"], target["api_key"], prowlarr_internal, schema_map, existing_map):
            success_count += 1

    print(f"\nApplication sync configuration complete: {success_count}/{total_candidates} applications registered/synced.")


if __name__ == "__main__":
    main()
