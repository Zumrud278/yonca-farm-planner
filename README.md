# Yonca AI Farm Planner — Technical Documentation

**Version:** 1.0.2 | **Status:** Prototype | **Base URL:** `https://api.yonca.az/v1`

---

## 1. Executive Summary

Yonca AI Farm Planner is a mobile-first agricultural advisory platform that delivers AI-driven agronomic recommendations to smallholder farmers across Azerbaijan. The prototype operates on a rule-based recommendation engine backed by a synthetic dataset of five representative farm profiles, enabling demonstration and validation without dependency on live sensor or market data. The backend is built on FastAPI (Python 3.11) with PostgreSQL and Redis, deployed as a single-host Docker stack for rapid iteration. A self-contained SDK module integrates Yonca into existing mobile host applications via a minimal four-method public API, with full offline support through ONNX Runtime Mobile and a local SQLite cache. The architecture is explicitly designed so synthetic data components can be replaced with real data pipelines with no changes to the API contract or client SDK.

---

## 2. System Architecture

### 2.1 Component Overview

The system is organised into four layers: the Mobile Plugin (client-side SDK), the API Gateway, the Core Services tier, and the Data Layer.

```
┌─────────────────────────────────────────────────────────────────┐
│  MOBILE APP (Host)                                              │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Yonca Plugin Module (SDK)                             │    │
│  │  ┌───────────────┐  ┌──────────────┐  ┌────────────┐  │    │
│  │  │ Offline       │  │ Sync Queue   │  │ Local DB   │  │    │
│  │  │ Recommender   │  │ (outbox)     │  │ (SQLite)   │  │    │
│  │  └───────┬───────┘  └──────┬───────┘  └─────┬──────┘  │    │
│  └──────────┼─────────────────┼────────────────┼──────────┘    │
└─────────────┼─────────────────┼────────────────┼───────────────┘
              │  REST (online)  │                │
              ▼                 ▼                │
┌─────────────────────────────────────────────┐ │
│  API Gateway (FastAPI)                      │ │
│  ┌─────────────┐  ┌──────────────────────┐  │ │
│  │  Auth / JWT │  │  Rate Limiter        │  │ │
│  └──────┬──────┘  └──────────────────────┘  │ │
│         │                                   │ │
│  ┌──────▼────────────────────────────────┐  │ │
│  │  Route Handlers                       │  │ │
│  │  /farms  /recommend  /sync  /ref      │  │ │
│  └──────┬────────────────────────────────┘  │ │
└─────────┼───────────────────────────────────┘ │
          │                                     │
┌─────────▼───────────────────────────────────┐ │
│  Core Services                              │ │
│  ┌──────────────┐  ┌──────────────────────┐ │ │
│  │  Recommend   │  │  Farm Profile Svc    │ │ │
│  │  Engine      │  └──────────────────────┘ │ │
│  └──────────────┘  ┌──────────────────────┐ │ │
│  ┌──────────────┐  │  Reference Data Svc  │ │ │
│  │  Sync Svc    │  └──────────────────────┘ │ │
│  └──────────────┘                           │ │
└────────┬────────────────────────────────────┘ │
         │                                      │
┌────────▼──────────────────────────────────────┘
│  Data Layer
│  ┌────────────┐  ┌─────────────────┐
│  │ PostgreSQL │  │  Redis (cache)  │
│  └────────────┘  └─────────────────┘
│  ┌──────────────────────────────────┐
│  │  Synthetic Dataset (5 farms)     │
│  └──────────────────────────────────┘
└─────────────────────────────────────
```

### 2.2 Technology Stack

| Layer | Technology | Rationale |
|---|---|---|
| API Framework | FastAPI (Python 3.11) | Async, automatic OpenAPI docs, lightweight |
| Recommendation Engine | Rule-based + scikit-learn | No GPU required; model exportable to ONNX |
| Mobile Inference | ONNX Runtime Mobile | Offline inference on device |
| Mobile Local DB | SQLite via Room (Android) / GRDB (iOS) | Zero-config offline storage |
| Server Database | PostgreSQL 15 | Relational with JSONB for flexible profile metadata |
| Cache | Redis 7 | Recommendation TTL cache (6-hour default) |
| Authentication | JWT (RS256) | Stateless; supports offline token validation |
| Sync Protocol | Outbox pattern + idempotent POST | Handles partial connectivity gracefully |
| Packaging | Docker + docker-compose | Single-host deployable for prototype phase |
| CI/CD | GitHub Actions | Lint, test, build pipeline |

### 2.3 Data Flow

**Online path:**

1. The mobile app calls `POST /recommend` with `farm_id` and current conditions (soil moisture, season, weather flag).
2. The API Gateway validates the JWT, routes to the Recommendation Engine.
3. The Engine queries the farm profile and evaluates the rule-set/model, scoring candidate actions and returning a ranked list.
4. The response is cached in Redis with a 6-hour TTL and written to the device's SQLite store via the SDK.

**Offline path:**

1. The SDK detects no connectivity and serves the last cached recommendation from SQLite.
2. Any farm updates or feedback events are written to the outbox table in SQLite.
3. On reconnect, the SDK automatically POSTs queued events to `POST /sync/push` and retrieves server-side changes via `GET /sync/pull`.

**Reference data flow:**

Crop calendars, pest alerts, and pricing data are bundled as versioned static JSON blobs. The app downloads these on first run and whenever a version mismatch is detected via `GET /ref/version`.

---

## 3. Farm Profiles & Synthetic Data Schema

### 3.1 Prototype Farm Profiles

The prototype dataset contains five synthetic farm profiles representing the primary agricultural archetypes present in Azerbaijan:

| Farm ID | Type | Region | Area (ha) | Soil Type | Primary Use Case |
|---|---|---|---|---|---|
| `farm-001` | wheat | Ganja-Gazakh | 12.4 | loam | Dryland cereal, irrigation scheduling |
| `farm-002` | livestock | Karabakh | 85.0 | clay | Grazing rotation, feed planning |
| `farm-003` | orchard | Absheron | 3.2 | sandy-loam | Fruit tree pest & irrigation |
| `farm-004` | vegetable | Shirvan | 1.8 | silt | High-frequency advisory, greenhouse |
| `farm-005` | mixed | Lankaran | 22.0 | clay-loam | Multi-crop rotation planning |

### 3.2 Farm Profile Database Schema

```sql
CREATE TABLE farms (
    farm_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id      UUID NOT NULL REFERENCES users(user_id),
    type          VARCHAR(20) NOT NULL
                    CHECK (type IN ('wheat','livestock','orchard','mixed','vegetable')),
    area_ha       NUMERIC(8,2) NOT NULL,
    region        VARCHAR(100) NOT NULL,
    soil_type     VARCHAR(50) NOT NULL,
    metadata      JSONB DEFAULT '{}',
    created_at    TIMESTAMPTZ DEFAULT now(),
    last_updated  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_farms_owner ON farms(owner_id);
CREATE INDEX idx_farms_type ON farms(type);
CREATE INDEX idx_farms_metadata ON farms USING GIN(metadata);
```

The `metadata` JSONB column stores farm-specific extended attributes such as irrigation source, crop varieties, certifications, and sensor identifiers. It is intentionally schema-free to accommodate diverse farm types without requiring migrations during the prototype phase.

### 3.3 Recommendation Storage Schema

```sql
CREATE TABLE recommendations (
    recommendation_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id            UUID NOT NULL REFERENCES farms(farm_id),
    season             VARCHAR(10) NOT NULL,
    weather_flag       VARCHAR(20) NOT NULL,
    soil_moisture      SMALLINT,
    actions            JSONB NOT NULL,
    model_version      VARCHAR(20) NOT NULL,
    generated_at       TIMESTAMPTZ DEFAULT now()
);
```

---

## 4. Recommendation Engine Logic

### 4.1 Architecture

The Recommendation Engine is a hybrid system combining a deterministic rule layer with a lightweight scikit-learn scoring model. This approach ensures interpretable, auditable outputs suitable for agronomist review, while providing a path to data-driven personalisation as real farm data accumulates.

### 4.2 Input Features

The engine accepts the following feature vector per request:

| Feature | Type | Values |
|---|---|---|
| `farm_type` | categorical | wheat, livestock, orchard, mixed, vegetable |
| `soil_type` | categorical | loam, clay, sandy-loam, silt, clay-loam |
| `season` | categorical | spring, summer, autumn, winter |
| `weather_flag` | categorical | normal, drought, frost, excess_rain |
| `soil_moisture` | integer | 0–100 (percentage) |

### 4.3 Rule Layer

The rule layer maps (farm_type × season × weather_flag) tuples to a candidate action set. Each rule is stored as a JSON record with preconditions and a base-score weight. Rules are evaluated deterministically and act as hard constraints — for example, irrigation actions are suppressed when `weather_flag = excess_rain`.

**Example rule record:**

```json
{
  "rule_id": "R-042",
  "preconditions": {
    "farm_type": ["wheat"],
    "season": ["spring"],
    "weather_flag": ["drought"],
    "soil_moisture_max": 30
  },
  "action": {
    "category": "irrigation",
    "title": "Urgent Irrigation Required",
    "description": "Soil moisture critically low during spring wheat growth stage. Apply 35–40mm via furrow or drip.",
    "due_in_days": 2,
    "base_confidence": 0.92
  }
}
```

### 4.4 Scoring Model

After rule-based filtering, the scikit-learn model (a gradient-boosted classifier trained on synthetic labelled outcomes) re-ranks the candidate action list. The model outputs a confidence score (0.0–1.0) per action. Actions are sorted by confidence × priority weight and the top five are returned.

The model is exported to ONNX format for deployment both server-side (via `onnxruntime`) and on-device (via ONNX Runtime Mobile). Both execution environments use the identical model artifact, ensuring consistent outputs regardless of connectivity state.

### 4.5 Output Ranking

```
final_score = confidence × priority_weight × recency_discount
```

Where `recency_discount` penalises actions identical to those delivered in the prior 48 hours (sourced from the local SQLite cache), reducing recommendation fatigue.

---

## 5. API Reference

**Base URL:** `https://api.yonca.az/v1`

**Authentication:** All endpoints except `/health` and `/auth/token` require a Bearer JWT in the `Authorization` header.

**Error format:**

```json
{
  "error": "string",
  "detail": "string",
  "request_id": "uuid"
}
```

---

### 5.1 Authentication

#### `POST /auth/token`

Issues a short-lived access token for a registered device.

**Request body:**

```json
{
  "device_id": "string",
  "secret": "string"
}
```

**Response `200 OK`:**

```json
{
  "access_token": "string (JWT)",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

**Error codes:** `401` — Invalid credentials. `429` — Rate limit exceeded (5 requests/minute per device).

---

### 5.2 Farm Profiles

#### `GET /farms`

Returns all farms visible to the authenticated user.

**Response `200 OK`:**

```json
[
  {
    "farm_id": "uuid",
    "type": "wheat|livestock|orchard|mixed|vegetable",
    "area_ha": 12.4,
    "region": "string",
    "soil_type": "string",
    "last_updated": "ISO8601"
  }
]
```

---

#### `GET /farms/{farm_id}`

Returns the full profile for a single farm, including the `metadata` JSONB object.

**Path parameter:** `farm_id` — UUID.

**Response `200 OK`:**

```json
{
  "farm_id": "uuid",
  "owner_id": "uuid",
  "type": "string",
  "area_ha": 12.4,
  "region": "string",
  "soil_type": "string",
  "metadata": {},
  "created_at": "ISO8601",
  "last_updated": "ISO8601"
}
```

**Error codes:** `404` — Farm not found or not owned by requesting user.

---

#### `POST /farms`

Creates a new farm profile.

**Request body:**

```json
{
  "type": "wheat|livestock|orchard|mixed|vegetable",
  "area_ha": 12.4,
  "region": "string",
  "soil_type": "string",
  "owner_id": "uuid",
  "metadata": {}
}
```

**Response `201 Created`:**

```json
{
  "farm_id": "uuid",
  "created_at": "ISO8601"
}
```

---

#### `PATCH /farms/{farm_id}`

Partially updates a farm profile. Only supplied fields are modified.

**Request body:** Any subset of `{ type, area_ha, region, soil_type, metadata }`.

**Response `200 OK`:**

```json
{
  "farm_id": "uuid",
  "updated_at": "ISO8601"
}
```

---

### 5.3 Recommendations

#### `POST /recommend`

Generates a ranked action list for a given farm and current conditions.

**Request body:**

```json
{
  "farm_id": "uuid",
  "season": "spring|summer|autumn|winter",
  "weather_flag": "normal|drought|frost|excess_rain",
  "soil_moisture": 0,
  "requested_at": "ISO8601"
}
```

**Response `200 OK`:**

```json
{
  "recommendation_id": "uuid",
  "farm_id": "uuid",
  "actions": [
    {
      "priority": 1,
      "category": "irrigation|fertilization|pest_control|harvest|grazing",
      "title": "string",
      "description": "string",
      "due_in_days": 3,
      "confidence": 0.87
    }
  ],
  "generated_at": "ISO8601",
  "model_version": "1.0.2"
}
```

The response is simultaneously written to Redis (TTL 6h) and returned to the SDK for local SQLite persistence.

---

#### `GET /recommend/{recommendation_id}`

Retrieves a previously generated recommendation by ID.

**Response `200 OK`:** Same schema as `POST /recommend` response. Served from Redis cache if available; falls back to PostgreSQL.

---

### 5.4 Sync

#### `POST /sync/push`

Accepts a batch of device-side events from the SDK outbox queue. All events are processed idempotently; duplicate `event_id` values are silently acknowledged.

**Request body:**

```json
{
  "device_id": "string",
  "events": [
    {
      "event_id": "uuid",
      "type": "farm_update|action_feedback",
      "payload": {},
      "occurred_at": "ISO8601"
    }
  ]
}
```

**Response `200 OK`:**

```json
{
  "accepted": ["uuid"],
  "rejected": [
    { "event_id": "uuid", "reason": "string" }
  ]
}
```

---

#### `GET /sync/pull`

Returns all server-side changes since a given timestamp for the specified device.

**Query parameters:** `device_id` (string, required), `since` (ISO8601 timestamp, required).

**Response `200 OK`:**

```json
{
  "delta": [
    {
      "entity": "farm|recommendation",
      "op": "upsert|delete",
      "data": {}
    }
  ],
  "server_time": "ISO8601"
}
```

---

### 5.5 Reference Data

#### `GET /ref/version`

Returns the current version identifiers for all reference datasets. The SDK calls this endpoint on startup to detect stale local copies.

**Response `200 OK`:**

```json
{
  "crop_calendar": "2.1",
  "pest_index": "1.4",
  "pricing": "3.0"
}
```

---

#### `GET /ref/{dataset}`

Downloads a versioned reference dataset. Supported values for `{dataset}`: `crop_calendar`, `pest_index`, `pricing`.

**Query parameters:** `version` (string, optional — defaults to latest).

**Response `200 OK`:**

```json
{
  "version": "string",
  "locale": "az",
  "data": [ ]
}
```

**Response headers:** `ETag`, `Cache-Control: max-age=86400`.

---

### 5.6 Health

#### `GET /health`

Returns the operational status of the API and its dependencies. No authentication required.

**Response `200 OK`:**

```json
{
  "status": "ok",
  "db": "ok",
  "cache": "ok",
  "version": "1.0.2"
}
```

---

## 6. Chatbot Design

### 6.1 Purpose & Scope

The Yonca in-app chatbot provides a natural-language interface over the recommendation and reference data APIs. It is designed for low-literacy and low-bandwidth users and therefore favours short, actionable responses in Azerbaijani and Russian, with English as a fallback.

### 6.2 Supported Intents

| Intent ID | Trigger Phrases (az) | Backend Action | Response Type |
|---|---|---|---|
| `get_recommendation` | "nə etməliyəm", "tövsiyə ver" | `POST /recommend` | Ranked action card |
| `explain_action` | "niyə", "bu nədir" | Local rule lookup | Text explanation |
| `farm_status` | "fermam haqqında", "sahəm" | `GET /farms/{id}` | Profile summary card |
| `weather_alert` | "yağış", "quraqlıq", "dolu" | `POST /recommend` (weather_flag override) | Updated recommendation |
| `pest_query` | "zərərverici", "xəstəlik", "böcək" | `GET /ref/pest_index` | Pest detail card |
| `pricing_query` | "qiymət", "bazar" | `GET /ref/pricing` | Price table |
| `help` | "kömək", "nə edə bilər" | Static | Capability list |
| `fallback` | (unrecognised) | — | Clarification prompt |

### 6.3 Language & Tone Guidelines

The chatbot must communicate with the following principles:

**Brevity:** Responses must not exceed three sentences. Complex information is surfaced as tappable cards rather than inline text.

**Actionability:** Every non-fallback response ends with a concrete next step or a confirmation prompt.

**Uncertainty transparency:** Confidence scores below 0.70 trigger a qualifier such as "Bu tövsiyə təxminidir — aqronomunuzla məsləhətləşin" ("This recommendation is approximate — consult your agronomist").

**Avoidance of technical language:** Terms such as "soil moisture percentage" are rendered as simple analogies in the local language ("torpaq quru görünür" — "the soil looks dry").

### 6.4 Sample Dialogue

```
User: Buğdaya nə vaxt su verim?
Bot:  Torpağınızın nəmliyi aşağıdır. Bu həftə suvarmağı tövsiyə edirik —
      ən geci 3 gün ərzində. [Ətraflı bax →]

User: Niyə?
Bot:  Baharda torpaq nəmliyi 30%-dən aşağı düşdükdə buğdanın böyüməsi
      ləngidir. Suvarmaq məhsuldarlığı qoruyacaq.
```

---

## 7. Data Safety Principles

### 7.1 Prototype Data Policy

The prototype operates exclusively on synthetic data. No real farmer identifiers, GPS coordinates, or financial information are stored or transmitted. All `farm_id`, `owner_id`, and `device_id` values in the prototype environment are randomly generated UUIDs with no mapping to real individuals.

### 7.2 Authentication & Authorisation

All API traffic is served over TLS 1.3. JWTs are signed with RS256 (asymmetric keys); the public key is distributed to SDKs at build time for offline validation. Tokens expire after 3600 seconds. Device secrets are stored as bcrypt hashes (cost factor 12) in PostgreSQL. Row-level security policies in PostgreSQL ensure that each authenticated user can only access records with a matching `owner_id`.

### 7.3 Data Minimisation

The API collects only the agronomic inputs required to generate a recommendation: farm type, soil type, region, season, weather flag, and soil moisture. No location tracking beyond region-level is performed. The `metadata` JSONB column is explicitly excluded from analytics queries and log output.

### 7.4 On-Device Data

Data stored in the device SQLite database is encrypted at rest via the host OS keystore (Android Keystore / iOS Data Protection class `NSFileProtectionComplete`). The SDK does not write any data outside its designated application sandbox.

### 7.5 Audit Logging

All write operations (farm creation, recommendation generation, sync events) are appended to an append-only audit log in PostgreSQL. Log records include timestamp, `device_id`, endpoint, and a hash of the request body. Audit logs are retained for 90 days in the prototype environment.

---

## 8. Yonca Plugin Integration Guide

### 8.1 SDK Architecture

Yonca is distributed as a self-contained SDK module. The host application is not required to implement any backend logic, authentication flow, or sync mechanism. The public API surface is intentionally minimal.

```
Host App
└── YoncaSDK (AAR / XCFramework)
    ├── YoncaClient        ← single entry point
    ├── OfflineEngine      ← ONNX model + SQLite
    ├── SyncManager        ← background sync (WorkManager / BGTask)
    └── YoncaUI (optional) ← composable fragments / SwiftUI views
```

### 8.2 Android Integration

**Step 1 — Add dependency:**

```groovy
// build.gradle (app)
dependencies {
    implementation "az.yonca:sdk:1.0.2"
}
```

**Step 2 — Initialise in `Application.onCreate()`:**

```kotlin
YoncaSDK.init(
    context = this,
    config = YoncaConfig(
        apiBase = "https://api.yonca.az/v1",
        deviceSecret = BuildConfig.YONCA_SECRET,
        syncIntervalMin = 30
    )
)
```

**Step 3 — Request a recommendation:**

```kotlin
YoncaSDK.getRecommendation(
    farmId = "uuid",
    conditions = FarmConditions(
        season = Season.SPRING,
        weatherFlag = WeatherFlag.NORMAL,
        soilMoisture = 45
    )
) { result ->
    when (result) {
        is Success -> renderActions(result.actions)
        is Offline -> renderCachedActions(result.actions)
        is Error   -> showError(result.message)
    }
}
```

### 8.3 iOS Integration

**Step 1 — Add Swift Package:**

```swift
// Package.swift or Xcode SPM panel
.package(url: "https://github.com/yonca-az/sdk-ios", from: "1.0.2")
```

**Step 2 — Initialise in `AppDelegate` or `@main` struct:**

```swift
YoncaSDK.initialise(
    config: YoncaConfig(
        apiBase: "https://api.yonca.az/v1",
        deviceSecret: Secrets.yoncaDeviceSecret,
        syncIntervalMinutes: 30
    )
)
```

**Step 3 — Request recommendation:**

```swift
YoncaSDK.shared.getRecommendation(
    farmId: "uuid",
    conditions: FarmConditions(season: .spring, weatherFlag: .normal, soilMoisture: 45)
) { result in
    switch result {
    case .success(let rec): renderActions(rec.actions)
    case .offline(let rec): renderCachedActions(rec.actions)
    case .failure(let err): showError(err)
    }
}
```

### 8.4 Public API Contract

The SDK exposes exactly four public methods. Everything else — authentication, caching, background sync, retry logic — is internal.

| Method | Description |
|---|---|
| `init` / `initialise` | Configure the SDK once at app startup |
| `getRecommendation(farmId:conditions:)` | Fetch or serve cached recommendations |
| `getFarmProfile(farmId:)` | Retrieve farm profile data |
| `submitFeedback(recommendationId:outcome:)` | Record agronomic outcome for model improvement |

The host application owns navigation and UI presentation. Yonca owns data, inference, and sync. The optional `YoncaUI` component provides pre-built composable fragments and SwiftUI views to accelerate integration but is not required.

### 8.5 ProGuard / R8 Rules (Android)

```
-keep class az.yonca.sdk.** { *; }
-keep interface az.yonca.sdk.** { *; }
-dontwarn ai.onnxruntime.**
```

---

## 9. Future Roadmap — Replacing Synthetic Data with Real Data

The prototype architecture is intentionally designed so that the synthetic data layer can be swapped for live data pipelines without any changes to the API contract, mobile SDK, or client applications. The following sequence describes the recommended migration path.

### 9.1 Phase 1 — Real Farm Onboarding (0–3 months)

The five hardcoded synthetic farm profiles in the `Synthetic Dataset` store are replaced by the standard `POST /farms` onboarding flow. Each farm is registered with a real `owner_id` obtained through SMS-based user authentication. The `metadata` JSONB column is extended to capture GPS boundary polygons and irrigation source identifiers. No changes are required to the Recommendation Engine or SDK at this phase.

### 9.2 Phase 2 — Live Weather Integration (1–4 months)

The `weather_flag` input field currently requires manual selection by the farmer or agronomist. In Phase 2, this is replaced by an automated lookup against a weather API (e.g., Open-Meteo or a national meteorological feed) keyed on the farm's region. The Farm Profile Service is extended to resolve `region` to a coordinate bounding box, and a scheduled job updates a `weather_cache` table every 3 hours. The `/recommend` endpoint reads from `weather_cache` if no `weather_flag` is supplied in the request body. The API contract remains backward-compatible.

### 9.3 Phase 3 — Soil Sensor Integration (3–9 months)

When IoT soil sensors are deployed, their readings replace the manual `soil_moisture` field. Sensors publish to an MQTT broker; a lightweight ingest service writes time-series readings to a `sensor_readings` table in PostgreSQL (or TimescaleDB for scale). The Recommendation Engine is updated to query the latest reading for the farm's registered sensor ID from `metadata.sensor_id`. Farms without sensors continue to accept manual input.

### 9.4 Phase 4 — Model Retraining on Real Outcomes (6–18 months)

The `submitFeedback` SDK method begins accumulating real agronomic outcomes (action taken, crop yield delta, problem resolved). Once a minimum of 500 labelled outcomes per farm type are collected, the scikit-learn model is retrained on this corpus using a monthly GitHub Actions pipeline. The new model artifact is versioned, tested for accuracy regression, exported to ONNX, and deployed to the API server and distributed to SDK clients via the existing reference data versioning mechanism (`/ref/version`). The synthetic training data is retired at this milestone.

### 9.5 Phase 5 — Personalisation & Regional Expansion (12–24 months)

With sufficient per-farm data, the rule layer is progressively replaced by farm-specific learned models. The system is extended to support additional crops and regions beyond Azerbaijan. Multi-language support is formalised with a translation management integration. The single-host Docker deployment is migrated to a managed Kubernetes cluster to support concurrent regional instances.

### 9.6 Migration Checklist

| Milestone | Synthetic Component Retired | Replacement |
|---|---|---|
| Real onboarding live | Hardcoded 5-farm dataset | PostgreSQL `farms` table with real users |
| Weather API integrated | Manual `weather_flag` | Automated weather cache lookup |
| Sensors deployed | Manual `soil_moisture` | IoT sensor time-series feed |
| 500+ feedback samples | Synthetic training labels | Real agronomic outcome labels |
| Model retrained | Synthetic scikit-learn model | Outcome-trained ONNX model |
