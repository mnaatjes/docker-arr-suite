#!/usr/bin/env python3
"""
manage_indexers.py - Deterministic Prowlarr Indexer Provisioner

Connects to the Prowlarr API, queries supported schemas, validates indexer
connectivity via /api/v1/indexer/test, and creates/enables declared indexers.

Usage:
    python3 manage_indexers.py [--host 192.168.1.52] [--port 9696] [--api-key KEY]
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_INDEXERS = [
    {
        "name": "The Pirate Bay",
        "baseUrl": "https://thepiratebay.org/",
        "enable": True,
    },
    {
        "name": "YTS",
        "baseUrl": "https://yts.mx/",
        "enable": True,
    },
    {
        "name": "Nyaa.si",
        "baseUrl": "https://nyaa.si/",
        "enable": True,
    },
]


def make_request(url, method="GET", data=None, api_key=None, timeout=20):
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


def get_existing_indexers(base_api, api_key):
    status, body = make_request(f"{base_api}/api/v1/indexer", api_key=api_key)
    if status != 200:
        raise RuntimeError(f"Failed to fetch existing indexers: {status} {body}")
    return {idx["name"].lower(): idx for idx in body}


def get_indexer_schemas(base_api, api_key):
    status, body = make_request(f"{base_api}/api/v1/indexer/schema", api_key=api_key)
    if status != 200:
        raise RuntimeError(f"Failed to fetch indexer schemas: {status} {body}")
    return {schema["name"].lower(): schema for schema in body}


def provision_indexer(base_api, api_key, definition, existing_map, schema_map):
    name = definition["name"]
    name_lower = name.lower()

    if name_lower in existing_map:
        print(f"[SKIP] Indexer '{name}' is already configured in Prowlarr (id={existing_map[name_lower]['id']}).")
        return True

    if name_lower not in schema_map:
        print(f"[ERROR] Indexer schema for '{name}' not found in Prowlarr supported catalog.")
        return False

    schema = schema_map[name_lower].copy()
    schema["enable"] = definition.get("enable", True)
    schema["appProfileId"] = 1

    if "baseUrl" in definition and definition["baseUrl"]:
        for field in schema.get("fields", []):
            if field.get("name") == "baseUrl":
                field["value"] = definition["baseUrl"]

    print(f"[TESTING] Validating indexer '{name}' via /api/v1/indexer/test...")
    test_status, test_body = make_request(
        f"{base_api}/api/v1/indexer/test",
        method="POST",
        data=schema,
        api_key=api_key,
        timeout=30,
    )

    if test_status != 200:
        print(f"[FAIL] Connectivity test failed for '{name}': {test_status} {test_body}")
        return False

    print(f"[SUCCESS] Connectivity test passed for '{name}'. Creating indexer...")
    create_status, create_body = make_request(
        f"{base_api}/api/v1/indexer",
        method="POST",
        data=schema,
        api_key=api_key,
        timeout=20,
    )

    if create_status in (200, 201):
        print(f"[CREATED] Indexer '{name}' successfully created and enabled (id={create_body.get('id')}).")
        return True
    else:
        print(f"[ERROR] Failed to create indexer '{name}': {create_status} {create_body}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Deterministic Prowlarr Indexer Provisioner")
    parser.add_argument("--host", default=os.getenv("PROWLARR_HOST", "192.168.1.52"), help="Prowlarr host IP or hostname")
    parser.add_argument("--port", default=os.getenv("PROWLARR_PORT", "9696"), help="Prowlarr port")
    parser.add_argument("--api-key", default=os.getenv("PROWLARR_API_KEY", ""), help="Prowlarr API Key")
    parser.add_argument("--config-file", default="", help="JSON file with list of indexers to provision")
    args = parser.parse_args()

    api_key = args.api_key.strip()
    if not api_key:
        print("Error: Prowlarr API key required. Pass --api-key or set PROWLARR_API_KEY environment variable.", file=sys.stderr)
        sys.exit(1)

    base_api = f"http://{args.host}:{args.port}"
    print(f"Connecting to Prowlarr API at {base_api}...")

    indexers_to_provision = DEFAULT_INDEXERS
    if args.config_file:
        with open(args.config_file, "r") as f:
            indexers_to_provision = json.load(f)

    existing_map = get_existing_indexers(base_api, api_key)
    schema_map = get_indexer_schemas(base_api, api_key)

    success_count = 0
    for idx_def in indexers_to_provision:
        if provision_indexer(base_api, api_key, idx_def, existing_map, schema_map):
            success_count += 1

    print(f"\nExecution complete: {success_count}/{len(indexers_to_provision)} indexers verified/provisioned.")


if __name__ == "__main__":
    main()
