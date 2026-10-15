---
title: "How-To: Manage Indexers and Synchronize Arr Applications"
tags: ["how-to", "prowlarr", "radarr", "sonarr", "lidarr", "readarr", "api", "automation"]
created_at: "2026-10-15"
last_updated_at: "2026-10-15"
---

# How-To: Manage Indexers and Synchronize Arr Applications

## 1. Context & Architecture

Prowlarr operates as the single control plane for torrent indexers and Usenet trackers in the Arr suite. Rather than configuring indexers manually across individual media apps (Radarr, Sonarr, Lidarr, Readarr):
1. **Indexers are added to Prowlarr** via the Prowlarr REST API (`scripts/manage_indexers.py`).
2. **Applications are linked to Prowlarr** with `fullSync` enabled via the Applications API (`scripts/sync_arr_applications.py`).
3. **Prowlarr deterministically syncs indexers** to all linked applications matching their appropriate media categories (e.g., Movies to Radarr, TV to Sonarr, Audio to Lidarr, Books to Readarr).

---

## 2. Prerequisites

* `python3` installed on the execution controller.
* Environment variables or command line arguments providing service API keys (retrieved from `homelab-ops` Ansible Vault under `vault_arr_api_keys`).
* Container network accessibility to Prowlarr at `http://<host>:9696`.

---

## 3. Provisioning Indexers via `manage_indexers.py`

The script [`scripts/manage_indexers.py`](file:///home/michael/src/github.com/mnaatjes/docker-arr-suite/scripts/manage_indexers.py) queries Prowlarr's Cardigann schema catalog, executes an end-to-end connectivity test (`/api/v1/indexer/test`), and creates/enables the indexers if valid.

### 3.1 Provisioning Default Curated Indexers

```bash
python3 scripts/manage_indexers.py \
  --host 192.168.1.52 \
  --port 9696 \
  --api-key "<PROWLARR_API_KEY>"
```

### 3.2 Provisioning Custom Indexers from JSON

To specify custom public or private indexers, create a JSON definition file:

```json
[
  {
    "name": "The Pirate Bay",
    "baseUrl": "https://thepiratebay.org/",
    "enable": true
  },
  {
    "name": "YTS",
    "baseUrl": "https://yts.mx/",
    "enable": true
  },
  {
    "name": "Nyaa.si",
    "baseUrl": "https://nyaa.si/",
    "enable": true
  }
]
```

Run with `--config-file`:

```bash
python3 scripts/manage_indexers.py --config-file indexers.json --api-key "<PROWLARR_API_KEY>"
```

---

## 4. Linking Applications & Triggering Sync via `sync_arr_applications.py`

The script [`scripts/sync_arr_applications.py`](file:///home/michael/src/github.com/mnaatjes/docker-arr-suite/scripts/sync_arr_applications.py) registers Radarr, Sonarr, Lidarr, and Readarr with Prowlarr using Docker bridge inter-container network routing:

```bash
python3 scripts/sync_arr_applications.py \
  --host 192.168.1.52 \
  --prowlarr-key "<PROWLARR_KEY>" \
  --radarr-key "<RADARR_KEY>" \
  --sonarr-key "<SONARR_KEY>" \
  --lidarr-key "<LIDARR_KEY>" \
  --readarr-key "<READARR_KEY>"
```

Once registered, Prowlarr immediately initiates category synchronization. Any new indexer subsequently added to Prowlarr is automatically pushed to all registered applications.

---

## 5. Unified Verification via `verify_indexers_sync.py`

The script [`scripts/verify_indexers_sync.py`](file:///home/michael/src/github.com/mnaatjes/docker-arr-suite/scripts/verify_indexers_sync.py) executes a single-pass health check across Prowlarr and all registered downstream applications, printing a complete status report:

```bash
python3 scripts/verify_indexers_sync.py \
  --host 192.168.1.52 \
  --prowlarr-key "<PROWLARR_KEY>" \
  --sonarr-key "<SONARR_KEY>" \
  --radarr-key "<RADARR_KEY>" \
  --lidarr-key "<LIDARR_KEY>" \
  --readarr-key "<READARR_KEY>"
```

The script asserts that each application is actively receiving indexers from Prowlarr and exits with code `0` on success.
