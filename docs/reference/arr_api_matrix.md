---
title: "Reference: Arr Suite Network and REST API Matrix"
tags: ["reference", "arr", "api", "networking", "ports", "docker"]
created_at: "2026-10-15"
last_updated_at: "2026-10-15"
---

# Reference: Arr Suite Network and REST API Matrix

## 1. Network Topology & Service Endpoints

The `docker-arr-suite` stack runs under Docker Compose attached to bridge network `docker-arr-suite_default`. Services communicate internally via container DNS and externally via exposed host port bindings on `192.168.1.52`.

| Service | Host Port | Internal Docker URL | Base REST API URL | Auth Header |
|---|---|---|---|---|
| **Prowlarr** | `9696` | `http://prowlarr:9696` | `/api/v1` | `X-Api-Key` |
| **Sonarr** | `8989` | `http://sonarr:8989` | `/api/v3` | `X-Api-Key` |
| **Radarr** | `7878` | `http://radarr:7878` | `/api/v3` | `X-Api-Key` |
| **Lidarr** | `8686` | `http://lidarr:8686` | `/api/v1` | `X-Api-Key` |
| **Readarr** | `8787` | `http://readarr:8787` | `/api/v1` | `X-Api-Key` |
| **Bazarr** | `6767` | `http://bazarr:6767` | `/api` | `X-Api-Key` |

---

## 2. Prowlarr Synchronized Category IDs

When Prowlarr links with downstream applications, it filters indexer feeds using standard Newznab/Torznab category codes:

* **Movies (`Radarr`):** `2000` (Movies), `2010` (Foreign), `2020` (Other), `2030` (SD), `2040` (HD), `2045` (UHD), `2050` (BluRay), `2060` (3D).
* **TV (`Sonarr`):** `5000` (TV), `5010` (WEB-DL), `5020` (Foreign), `5030` (SD), `5040` (HD), `5045` (UHD), `5070` (Anime), `5080` (Documentary).
* **Audio (`Lidarr`):** `3000` (Audio), `3010` (MP3), `3020` (Video), `3040` (Lossless).
* **Books (`Readarr`):** `7000` (Books), `7010` (Mags), `7020` (EBook), `7030` (Comics).

---

## 3. Configuration & State Persistence

| Service | Host Storage Path | Configuration File |
|---|---|---|
| **Prowlarr** | `/opt/homelab/prod/data/docker-arr-suite/prowlarr` | `config.xml` |
| **Sonarr** | `/opt/homelab/prod/data/docker-arr-suite/sonarr` | `config.xml` |
| **Radarr** | `/opt/homelab/prod/data/docker-arr-suite/radarr` | `config.xml` |
| **Lidarr** | `/opt/homelab/prod/data/docker-arr-suite/lidarr` | `config.xml` |
| **Readarr** | `/opt/homelab/prod/data/docker-arr-suite/readarr` | `config.xml` |
| **Bazarr** | `/opt/homelab/prod/data/docker-arr-suite/bazarr` | `config/config.yaml` |
