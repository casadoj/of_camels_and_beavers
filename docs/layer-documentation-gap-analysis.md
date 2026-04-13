# Layer & Documentation Gap Analysis Report — KAJO-CAMELS

**Date:** 2026-04-05
**Author:** Mary (Business Analyst Agent)
**Sources:** GIS layers (4 GeoJSON files), PRD v1.0, Architecture v1.0, NotebookLM CAMELS Notebook (54 sources), CAMELS-ES Zenodo dataset documentation

---

## 1. Executive Summary

This report is a **bidirectional** cross-reference between the four GIS layers delivered by the hydrologist and the documented requirements in the PRD, architecture document, and the CAMELS-ES scientific standard. Neither source is treated as final authority — both are inputs to establish a corrected, unified truth.

The analysis reveals:
- **3 critical gaps** — missing layers that block MVP features
- **5 significant discrepancies** — conflicts between delivered data and documented expectations
- **13 surplus attributes** in layers not mapped to any documented requirement (potential new features or droppable fields)
- **8 documented requirements** with no data source in the delivered layers
- **19 specific questions** that need to be resolved with the hydrologist to establish the new authoritative state

**Key finding:** The delivered layers represent the *pre-selection pool* (835 stations from the Anuario de Aforos), not the final CAMELS-ES dataset (269 near-natural catchments). This is by design — the whole purpose of KAJO-CAMELS is to enable expert classification of this larger pool. However, this means the `regime` field in the delivered data represents the researcher's *preliminary* solo classification (v1), which the platform will replace with multi-expert consensus.

**Methodology note:** Each discrepancy is tagged with the recommended correction direction: **[FIX-DOCS]** (documentation should be updated to match reality), **[FIX-DATA]** (hydrologist should correct the data), or **[ASK]** (needs clarification before either can be corrected).

---

## 2. Layer Inventory & Analysis

### 2.1 stations.geojson — Gauging Stations

| Property | Value |
|----------|-------|
| **Features** | 835 point features |
| **CRS** | CRS84 (WGS84 geographic) |
| **Attributes** | 26 fields |
| **Geometry** | Point |

**Attribute Summary:**

| Attribute | Type | Unique | Nulls | Notes |
|-----------|------|--------|-------|-------|
| `id_roea` | int | 835 | 0 | Primary key — ROEA station identifier |
| `location` | str | 806 | 0 | Station location name |
| `comment` | str | 30 | 719 (86%) | Researcher notes — mostly empty |
| `active` | int | 2 | 0 | 752 active, 83 inactive |
| `catch_skm_station` | int | 635 | 0 | Catchment area at station (km2) |
| `catch_skm_river` | int | 371 | 0 | Catchment area of river |
| `id_sheet` | int | 461 | 0 | Map sheet reference |
| `elevation_m` | float | 526 | 1 | Station elevation |
| `elevation_max_m` | float | 251 | 362 (43%) | Max basin elevation — high null rate |
| `years_daily` | int | 27 | 0 | Years of daily data available |
| `years_monthly` | int | 105 | 0 | Years of monthly data available |
| `years_instant` | int | 63 | 0 | Years of instantaneous data |
| `id_basin` | int | 697 | 0 | Basin identifier |
| `id_municipality` | int | 699 | 0 | Municipality code |
| `x_etrs89` | int | 834 | 0 | Easting in ETRS89 (UTM zone 30?) |
| `y_etrs89` | int | 834 | 0 | Northing in ETRS89 |
| `lon_wgs84` | float | 823 | 0 | Longitude WGS84 |
| `lat_wgs84` | float | 818 | 0 | Latitude WGS84 |
| `id_saih` | str | 399 | 405 (48%) | SAIH real-time network ID |
| `basin` | str | 10 | 0 | Basin authority name |
| `river` | str | 451 | 0 | River name |
| `regime` | str | 4 | 0 | Preliminary regime classification |
| `system` | str | 124 | 0 | Hydrological system |
| `discharge` | int | 1 | 0 | Boolean field that defines stations with discharge time series. All are 1 because stations without time series were filtered |
| `start` | float | 27 | 0 | Study period start year |
| `end` | float | 27 | 0 | Study period end year |

**Regime Distribution:**

| Value | Count | % |
|-------|-------|---|
| `natural` | 296 | 35.4% |
| `unkown` | 272 | 32.6% |
| `altered` | 261 | 31.3% |
| `regulated` | 6 | 0.7% |

**Basin Distribution:**

| Basin | Stations |
|-------|----------|
| EBRO | 218 |
| DUERO | 180 |
| TAJO | 124 |
| MIÑO-SIL | 55 |
| GUADALQUIVIR | 55 |
| JUCAR | 50 |
| GALICIA COSTA | 41 |
| CANTABRICO | 40 |
| GUADIANA | 39 |
| SEGURA | 33 |

### 2.2 reservoirs.geojson — Reservoir Polygons

| Property | Value |
|----------|-------|
| **Features** | 393 polygon features |
| **CRS** | **EPSG:25830** (ETRS89 / UTM zone 30N) — **DIFFERENT from other layers!** |
| **Attributes** | 18 fields |
| **Geometry** | Polygon + MultiPolygon |

**Key Attributes:**

| Attribute | Type | Unique | Nulls | Notes |
|-----------|------|--------|-------|-------|
| `SNCZI` | int | 393 | 0 | National Dam Safety ID |
| `ID_EMBALSE` | float | 393 | 0 | Reservoir identifier |
| `NOMBRE` | str | 393 | 0 | Reservoir name |
| `NMN_SUP` | float | 360 | 8 | Normal maximum level surface (m2) |
| `NMN_CAPAC` | float | 362 | 2 | Normal maximum level capacity (hm3) |
| `NMN_COTA` | float | 198 | 170 (43%) | Normal maximum level elevation |
| `NAE_COTA` | float | 7 | 386 (98%) | Emergency level elevation — nearly all null |
| `DEMARC` | str | 11 | 0 | Basin authority name |
| `PROVINCIA` | str | 74 | 0 | Province |
| `SUP_CUENCA` | float | 210 | 173 (44%) | Upstream catchment area |
| `AP_M_ANUAL` | float | 169 | 184 (47%) | Mean annual inflow |
| `USO` | str | 16 | 5 | Multi-value use types (water supply, hydroelectric, flood defence, etc.) |

### 2.3 basin_authorities.geojson — Administrative Boundaries

| Property | Value |
|----------|-------|
| **Features** | 11 MultiPolygon features |
| **CRS** | CRS84 (WGS84) |
| **Attributes** | 6 fields — clean, no nulls |

Represents the 11 *demarcaciones hidrográficas* (basin authority administrative regions). Maps to the `basin` field in stations and `DEMARC` in reservoirs.

### 2.4 stations_basins_3sec.geojson — Delineated Catchment Basins

| Property | Value |
|----------|-------|
| **Features** | 835 polygon features |
| **CRS** | CRS84 (WGS84) |
| **Attributes** | 7 fields |
| **File size** | 67 MB (largest layer) |

**Attributes:**

| Attribute | Type | Notes |
|-----------|------|-------|
| `ID` | int | Matches `id_roea` from stations — **1:1 linkage confirmed (835/835)** |
| `area` | **str** | Catchment area — **stored as string, should be numeric!** |
| `lat` | **str** | Centroid latitude — **stored as string!** |
| `lon` | **str** | Centroid longitude — **stored as string!** |
| `area_3sec` | float | Area from 3-arcsecond DEM delineation |
| `lat_3sec` | float | DEM-derived centroid latitude |
| `lon_3sec` | float | DEM-derived centroid longitude |

---

## 3. Critical Gaps — Missing Layers

These are layers required by the PRD and architecture that are **not present** in the delivered data.

### GAP-1: River Polylines (FR5, Architecture: `rivers` table) — CRITICAL

**Requirement:** FR5 states "Any user can view river polylines on the map." Architecture defines `rivers` table with GIST spatial index and upstream/downstream navigation relies on `river_id` + `river_measure` in stations table.

**Status:** No river polyline layer delivered. This blocks:
- FR5 (river display on map)
- FR12 (upstream/downstream navigation — requires `ST_LineLocatePoint` on river geometries)
- River-network-based exploration (core UX paradigm)

**Impact:** HIGH — The entire upstream/downstream navigation paradigm depends on river geometry. Without this, `river_id`, `river_measure`, `next_upstream_station_id`, and `next_downstream_station_id` cannot be computed.

**Source suggestion:** HydroRIVERS dataset (free, global, from HydroSHEDS) or the Spanish national river network from IGN/MITECO.

### GAP-2: Sub-Basin Polygons (FR4, Architecture: `sub_basins` table) — MEDIUM

**Requirement:** FR4 states "Any user can view sub-basin polygons on the map when zoomed in (~1000+ polygons, pre-delineated from DEM)."

**Status:** `stations_basins_3sec.geojson` provides per-station catchments (835 polygons) delineated from MERIT DEM. This is close but semantically different — these are station drainage basins, not sub-basins in the sense of subdivided larger catchments.

**Clarification needed:** Are the 835 station basins intended to serve as the "sub-basins" layer for FR4? If so, this gap is resolved. If FR4 envisions a separate sub-basin delineation (e.g., HydroBASINS level 8-12), this layer is still missing.

### GAP-3: Time Series Data — NOT IN SCOPE (but worth noting)

**Note:** No time series data (Parquet files) is included in the delivered layers. The PRD and architecture describe per-station Parquet files (`camelses_{id}.csv` in CAMELS-ES standard) with discharge, precipitation, temperature, PET, etc.

**This is expected** — layers and time series are separate deliverables. But confirming: when will the Parquet files be delivered? The ingestion pipeline design depends on their schema.

---

## 4. Significant Discrepancies

### DISC-1: CRS Mismatch — Reservoirs vs. Everything Else

| Layer | CRS |
|-------|-----|
| stations.geojson | CRS84 (WGS84 geographic) |
| stations_basins_3sec.geojson | CRS84 |
| basin_authorities.geojson | CRS84 |
| **reservoirs.geojson** | **EPSG:25830 (ETRS89 / UTM zone 30N)** |

**Impact:** PostGIS and Martin require consistent CRS (SRID 4326 for web mapping). The reservoirs layer must be reprojected to WGS84 before ingestion. This is straightforward (`ST_Transform` or `ogr2ogr`) but must be handled in the ingestion pipeline.

**Question for hydrologist:** Was the EPSG:25830 CRS intentional (native format from SNCZI), or should the researcher provide a reprojected version?

### DISC-2: Regime Values Don't Match Architecture Enum

**Layer values:** `natural`, `unkown` (typo!), `altered`, `regulated`
**Architecture enum:** `NATURAL`, `SEMI_NATURAL`, `REGULATED`, `UNKNOWN`

| Layer Value | Architecture Enum | Issue |
|-------------|-------------------|-------|
| `natural` | `NATURAL` | OK (case mapping) |
| `unkown` | `UNKNOWN` | **Typo in layer** (`unkown` → `unknown`) |
| `altered` | — | **No equivalent!** Architecture has no `ALTERED` type |
| `regulated` | `REGULATED` | OK (case mapping) |
| — | `SEMI_NATURAL` | **Missing in layer!** |

**Critical question:** The architecture defines `SEMI_NATURAL` as a classification option (amber color), but the delivered data has `altered` instead. Are these the same concept? The PRD questionnaire (FR25a) asks contributors to classify as "natural/semi-natural/regulated" — but the delivered data has "natural/altered/regulated/unknown." 

This discrepancy may be intentional: the researcher's v1 classification used different categories than the v2 questionnaire will offer. But it needs explicit confirmation.

### DISC-3: 835 Stations vs. 269 CAMELS-ES Catchments

**Delivered:** 835 stations from the Anuario de Aforos
**CAMELS-ES published dataset:** 269 near-natural catchments
**BULL database:** 484 basins (149 unaltered + 335 altered)

The delivered data includes all 835 stations from the broader pre-selection pool, including:
- 296 classified as "natural"
- 272 classified as "unknown" 
- 261 classified as "altered"
- 6 classified as "regulated"

**This is likely correct** — the platform's purpose is to enable re-classification of the full pool. But confirm: should the ingestion include all 835 stations, or only a subset?

### DISC-4: Data Type Issues in stations_basins_3sec.geojson

The `area`, `lat`, and `lon` fields are stored as **strings** instead of numbers. Sample: `area="765"`, `lat="43.228338"`. These must be cast to numeric during ingestion. This is a minor data quality issue but could cause silent bugs if not handled.

### DISC-5: Attribute Name Typo — `evelation_m`

The stations layer has `evelation_m` (missing first 'l') instead of `elevation_m`. The ingestion pipeline must rename this field.

---

## 5. Data Quality Observations

### 5.1 High Null Rates

| Layer | Attribute | Null % | Impact |
|-------|-----------|--------|--------|
| stations | `elevation_max_m` | 43% | Display gap in station metadata (FR20) |
| stations | `id_saih` | 48% | Cannot link to real-time SAIH network for half the stations |
| stations | `comment` | 86% | Expected — researcher notes only exist for exceptional cases |
| reservoirs | `NAE_COTA` | 98% | Emergency level effectively unavailable |
| reservoirs | `NMN_COTA` | 43% | Normal max level elevation missing for many |
| reservoirs | `SUP_CUENCA` | 44% | Upstream catchment area unknown for half |
| reservoirs | `AP_M_ANUAL` | 47% | Mean annual inflow unknown for half |

### 5.2 Regime Typo: `unkown` vs `unknown`

272 stations (32.6%) have regime value `unkown` — a misspelling. Must be corrected to `unknown` during ingestion.

### 5.3 `discharge` Field — All Values = 1

Every station has `discharge = 1`. This appears to be a boolean flag (has discharge data = yes) rather than a meaningful variable. Confirm with hydrologist whether this field serves any purpose in the platform.

### 5.4 Basin Naming Inconsistency

The `basin` field in stations uses different names than `DEMARC` in reservoirs for the same basin authority:

| Stations `basin` | Reservoirs `DEMARC` | Same? |
|-------------------|---------------------|-------|
| CANTABRICO | CANTABRICO OCCIDENTAL + CANTABRICO ORIENTAL | Split in reservoirs! |
| GALICIA COSTA | GALICIA-COSTA | Hyphen difference |

This will cause issues when joining stations to reservoirs by basin authority. The ingestion pipeline needs a mapping table.

### 5.5 Reservoir `USO` Field — Multi-Value

The `USO` (use) field contains multi-value entries separated by newlines: `"Abastecimiento\nDefensa frente avenidas"`. This needs to be parsed into an array or normalized during ingestion for filtering (FR9).

---

## 6. Complete Attribute Comparison Tables

These tables show **every attribute** — from GeoJSON layers AND from PRD/Architecture documentation — side by side with sample data. This is the foundation for defining the final data model. Each row is tagged:

- **MATCH** — attribute exists in both data and docs
- **DATA-ONLY** — attribute exists in layer but NOT in any documented requirement
- **DOCS-ONLY** — attribute is required by PRD/Architecture but NOT present in delivered data
- **MISMATCH** — attribute exists in both but values/semantics don't align

### 6.1 Stations — Complete Attribute Map

| # | GeoJSON Attribute | Sample Value | PRD/Arch Requirement | Status | Notes |
|---|-------------------|-------------|---------------------|--------|-------|
| 1 | `id_roea` | `1080` | stations PK, FR43 | **MATCH** | Primary identifier. Maps to `id` in DB schema |
| 2 | `location` | `ANDOAIN` | FR20: station name/location | **MATCH** | |
| 3 | `comment` | `INT 2003` (86% null) | FR20: "observation notes" | **MATCH** | Sparse but expected |
| 4 | `active` | `1` (752 active, 83 inactive) | — | **DATA-ONLY** | Active/inactive status. Not in FR20. Relevant for Q4 (station scope) |
| 5 | `catch_skm_station` | `765` | FR20: "drainage area" | **MATCH** | Catchment area at station pour point (km2) |
| 6 | `catch_skm_river` | `861` | — | **DATA-ONLY** | Catchment area of the river. Different from station area. Could inform river-level context |
| 7 | `sheet_id` | `64` | — | **DATA-ONLY** | IGN topographic sheet number |
| 8 | `evelation_m` | `38.0` | FR20: "elevation" | **MISMATCH** | Typo in field name: `evelation_m` → should be `elevation_m` |
| 9 | `elevation_max_m` | `1544.0` (43% null) | CAMELS-ES: `ele_mt_smx` | **DATA-ONLY** | Max catchment elevation. In CAMELS standard but not in FR20 |
| 10 | `years_daily` | `19` | — | **DATA-ONLY** | Years of daily data. Richer than start/end for data availability assessment |
| 11 | `years_monthly` | `66` | — | **DATA-ONLY** | Years of monthly data |
| 12 | `years_instant` | `29` | — | **DATA-ONLY** | Years of instantaneous data |
| 13 | `id_basin` | `1028` | — | **DATA-ONLY** | Numeric basin identifier (ROEA internal) |
| 14 | `id_municipality` | `20009` | — | **DATA-ONLY** | INE municipality code |
| 15 | `x_etrs89` | `579070` | — | **DATA-ONLY** | Easting ETRS89 UTM. Redundant with lon/lat + geometry |
| 16 | `y_etrs89` | `4786632` | — | **DATA-ONLY** | Northing ETRS89 UTM. Redundant with lon/lat + geometry |
| 17 | `lon_wgs84` | `-2.0135` | FR20: "coordinates" | **MATCH** | Longitude |
| 18 | `lat_wgs84` | `43.1342` | FR20: "coordinates" | **MATCH** | Latitude |
| 19 | `id_saih` | `A149` (49% null) | FR20: "SAIH code" | **MATCH** | Real-time network ID. Half of stations have no SAIH link |
| 20 | `basin` | `CANTABRICO` | FR20: "basin", FR9: filter | **MATCH** | Text field — should become FK to `basin_authorities` |
| 21 | `river` | `oria` | FR20: "river" | **MATCH** | Text field — should become FK to `rivers` table (pending GAP-1) |
| 22 | `regime` | `altered` | FR1: regime symbology, Arch: `regime_type` enum | **MISMATCH** | Values don't match enum. `altered` vs `SEMI_NATURAL`, typo `unkown`. See Q1 |
| 23 | `system` | `oria` (124 unique) | — | **DATA-ONLY** | Hydrological system — grouping between basin and river. Potentially significant |
| 24 | `discharge` | `1` (always 1) | — | **DATA-ONLY** | Boolean flag? Purpose unclear |
| 25 | `start` | `1991.0` | FR20: "pre-selected study period start/end"? | **MATCH?** | Ambiguous — record range or best-quality period? See Q12 |
| 26 | `end` | `2010.0` | FR20: "pre-selected study period start/end"? | **MATCH?** | Same ambiguity as `start` |
| — | `[geometry]` | `Point` CRS84 | Arch: `geom Point 4326` | **MATCH** | |
| — | — | — | FR20: "record period" | **MATCH?** | Could be `start`/`end` or derived from time series |
| — | — | — | FR19: Baseflow Index, Flashiness, CV, etc. | **DOCS-ONLY** | Pre-computed indices — separate delivery (`station_indices` table) |
| — | — | — | FR19a-h: All diagnostic metrics | **DOCS-ONLY** | Same — derived from time series |
| — | — | — | FR19d: Change point detection | **DOCS-ONLY** | Same |
| — | — | — | FR19e: Suggested regulation status | **DOCS-ONLY** | Same |
| — | — | — | Arch: `river_id` FK | **DOCS-ONLY** | Requires river polyline layer (GAP-1) |
| — | — | — | Arch: `river_measure` | **DOCS-ONLY** | Computed from river geometry (GAP-1) |
| — | — | — | Arch: `next_upstream_station_id` FK | **DOCS-ONLY** | Computed from river topology (GAP-1) |
| — | — | — | Arch: `next_downstream_station_id` FK | **DOCS-ONLY** | Computed from river topology (GAP-1) |

**Station attribute totals:** 26 in GeoJSON, ~34 referenced in docs (FR43). Delta = 8 indices + 4 river topology fields delivered separately.

### 6.2 Reservoirs — Complete Attribute Map

| # | GeoJSON Attribute | Sample Value | PRD/Arch Requirement | Status | Notes |
|---|-------------------|-------------|---------------------|--------|-------|
| 1 | `SNCZI` | `317` | Arch: reservoir PK candidate | **MATCH** | National dam safety ID. Integer. Used in INFORME URL |
| 2 | `INFORME` | `https://sig.mapama.gob.es/...` | — | **DATA-ONLY** | Link to official SNCZI dam report. Very useful for detail view |
| 3 | `ID_EMBALSE` | `317.0` | Arch: reservoir PK candidate | **MATCH** | Same values as SNCZI but stored as float. Redundant? |
| 4 | `NOMBRE` | `BEMBEZAR (AZUD DERIVACION)` | FR23: "name" | **MATCH** | |
| 5 | `NMN_SUP` | `1140000.0` (2% null) | — | **DATA-ONLY** | Surface area at normal max level (m2) |
| 6 | `NMN_CAPAC` | `12.01` (1% null) | FR23: "storage" | **MATCH** | Capacity at normal max level (hm3) |
| 7 | `NMN_COTA` | `96.8` (43% null) | FR23: "elevation"? | **MATCH?** | Normal max level elevation. Loose mapping to FR23 "elevation" |
| 8 | `NAE_COTA` | `1290.0` (**98% null**) | — | **DATA-ONLY** | Emergency level elevation. Effectively useless — drop candidate |
| 9 | `TITULAR` | `ESTADO\nCONF. HIDRO. GUADALQUIVIR` | FR23: "owner" | **MATCH** | Multi-line value. Needs parsing |
| 10 | `ADMON_COMP` | `Estado` (2 values) | — | **DATA-ONLY** | Administration type. Derivable from TITULAR |
| 11 | `DEMARC` | `GUADALQUIVIR` | Arch: basin FK | **MATCH** | Basin authority. Naming differs from stations! Should become FK |
| 12 | `PROVINCIA` | `Córdoba` | — | **DATA-ONLY** | Province. Not in FR23 but geographic context |
| 13 | `SUP_CUENCA` | `110.0` (44% null) | FR23: "catchment area" | **MATCH** | Upstream catchment area (km2) |
| 14 | `AP_M_ANUAL` | `13.0` (47% null) | FR23: "annual inflow" | **MATCH** | Mean annual inflow (hm3) |
| 15 | `TIPO_EMBAL` | `Embalse de presa` (2 values, 1% null) | FR23: "category"? | **MATCH?** | Reservoir type. Loose mapping to FR23 "category" |
| 16 | `DTOR_EXPLO` | `JUAN CHASTANG MARIN` (13% null) | — | **DATA-ONLY / GDPR** | Personal name — exploitation director. GDPR concern |
| 17 | `TIPO_TITUL` | `Estado\nEstado` (12 values) | — | **DATA-ONLY** | Ownership type. Overlaps with TITULAR |
| 18 | `USO` | `Abastecimiento\nDefensa frente avenidas` | FR23: "use" | **MATCH** | Multi-value, newline-separated. Needs parsing to array |
| — | `[geometry]` | `Polygon / MultiPolygon` **EPSG:25830** | Arch: `geom Polygon 4326` | **MISMATCH** | CRS mismatch — must reproject to 4326 |
| — | — | — | FR23: "river" | **DOCS-ONLY** | No river name in reservoir data. Needs spatial join or hydrologist input |
| — | — | — | FR22/FR43: "inflow-outflow bias" | **DOCS-ONLY** | Pre-computed metric. PRD says delivered as attribute — NOT present |
| — | — | — | Arch: `basin_id` FK | **DOCS-ONLY** | `DEMARC` is text — should become FK to `basin_authorities` |
| — | — | — | Arch: `river_id` FK | **DOCS-ONLY** | No river association. Needs spatial join (pending GAP-1) |

### 6.3 Basin Authorities — Complete Attribute Map

| # | GeoJSON Attribute | Sample Value | PRD/Arch Requirement | Status | Notes |
|---|-------------------|-------------|---------------------|--------|-------|
| 1 | `OBJECTID` | `31` | — | **DATA-ONLY** | Internal GIS object ID. Not useful as PK |
| 2 | `COD_DEMAR` | `11` | Arch: basin code | **MATCH** | Demarcation code. Could serve as natural key |
| 3 | `NOM_DEMAR` | `MIÑO-SIL` | FR3: basin names, FR9: filter | **MATCH** | Official basin name (uppercase) |
| 4 | `NOM_DEMARL` | `MIÑO-SIL` | — | **DATA-ONLY** | Same as NOM_DEMAR in this dataset. Long name variant? |
| 5 | `N_DEM_ING` | `MINHO` | — | **DATA-ONLY** | English name. Useful for i18n or English UI |
| 6 | `CUENCA_ID` | `1.0` (8 unique / 11 features) | — | **DATA-ONLY** | Basin group ID. Not unique — some basins share a group? |
| — | `[geometry]` | `MultiPolygon` CRS84 | Arch: `geom MultiPolygon 4326` | **MATCH** | |

**Note:** 11 features but `CUENCA_ID` has only 8 unique values — meaning some demarcaciones share a cuenca_id. This is the administrative vs. hydrological boundary distinction.

### 6.4 Station Basins (Catchments) — Complete Attribute Map

| # | GeoJSON Attribute | Sample Value | PRD/Arch Requirement | Status | Notes |
|---|-------------------|-------------|---------------------|--------|-------|
| 1 | `ID` | `1080` | Arch: FK to stations | **MATCH** | 1:1 with station `id_roea`. All 835 match |
| 2 | `area` | `765` **(string!)** | — | **DATA-ONLY** | Reported catchment area. Same as `catch_skm_station` in stations. **Wrong type** |
| 3 | `lat` | `43.228338` **(string!)** | — | **DATA-ONLY** | Reported centroid latitude. **Wrong type** |
| 4 | `lon` | `-2.026305` **(string!)** | — | **DATA-ONLY** | Reported centroid longitude. **Wrong type** |
| 5 | `area_3sec` | `781.7` | Arch: catchment area from DEM | **MATCH** | DEM-derived area. Compare with reported `area` for QA |
| 6 | `lat_3sec` | `43.2275` | — | **DATA-ONLY** | DEM-derived centroid lat |
| 7 | `lon_3sec` | `-2.026667` | — | **DATA-ONLY** | DEM-derived centroid lon |
| — | `[geometry]` | `Polygon` CRS84 (67MB!) | Arch: `geom Polygon 4326`, FR4? | **MATCH** | Very large file. May serve as FR4 sub-basins |

**Dual-value pattern:** Reported (`area`/`lat`/`lon`) vs DEM-derived (`area_3sec`/`lat_3sec`/`lon_3sec`) for the same physical quantities. Discrepancy = data quality indicator.

### 6.5 Missing Layers — Required by Docs, Not Delivered

| Layer | PRD Requirement | Architecture Table | Status | Impact |
|-------|----------------|-------------------|--------|--------|
| **River polylines** | FR5: river display, FR12: upstream/downstream | `rivers` (id, name, geom, basin_id) | **NOT DELIVERED** | CRITICAL — blocks navigation paradigm |
| **Sub-basins** | FR4: sub-basin polygons (~1000+) | `sub_basins` (geom) | **UNCLEAR** | Station basins (835) may serve this role |
| **Time series** | FR13-FR18: hydrographs, precipitation | `time_series` hypertable | **SEPARATE DELIVERY** | Expected as per-station Parquet files |
| **Station indices** | FR19-FR19h: all diagnostic metrics | `station_indices` table | **SEPARATE DELIVERY** | Computed from time series |
| **Reservoir time series** | FR21: storage, outflow, evaporation, inflow | `time_series` hypertable | **SEPARATE DELIVERY** | Expected as per-reservoir Parquet files |

---

## 7. Surplus Attributes — Detail Analysis

These attributes exist in the delivered GeoJSON but are **not referenced** in any PRD functional requirement or architecture schema. They may represent features the hydrologist expects to be visible, or they may be droppable. Each needs a decision.

### 6.1 stations.geojson — 10 Surplus Attributes

| Attribute | Values | Analysis | Recommended Action |
|-----------|--------|----------|-------------------|
| `catch_skm_river` | 371 unique, int | Catchment area of the **river** (not station). Different from `catch_skm_station`. FR20 only mentions "drainage area" (singular). This is a river-level aggregate that could help hydrologists understand relative station position. | **[ASK Q13]** Display in metadata? Or drop? |
| `sheet_id` | 461 unique, int | IGN topographic sheet number. Cross-references paper maps. Not in any FR. | **[ASK Q14]** Useful for hydrologists? Or legacy field? |
| `elevation_max_m` | 251 unique, 43% null | Maximum elevation in the catchment basin. **IS in CAMELS-ES standard** (`ele_mt_smx`). Not in FR20 but scientifically relevant for elevation range. | **[FIX-DOCS]** Likely should be added to FR20. Confirm with hydrologist. |
| `years_daily` / `years_monthly` / `years_instant` | Various | Record length broken down by temporal resolution. FR20 only says "record period" (start/end). These give richer availability information — e.g., a station could have 66 years monthly but only 19 years daily. | **[ASK Q15]** Display all three, or just start/end? Very relevant for data quality assessment. |
| `id_basin` | 697 unique, int | Numeric basin identifier (ROEA internal). Docs reference basin by name only. | **[ASK Q16]** Needed for any cross-referencing? Or derivable from `basin` name? |
| `id_municipality` | 699 unique, int | INE municipality code. Not in any documented requirement. Geographic context field. | **[ASK Q14]** Display? Or drop? |
| `x_etrs89` / `y_etrs89` | ~834 unique, int | Station coordinates in ETRS89 projected CRS. Redundant with `lon_wgs84`/`lat_wgs84` and GeoJSON geometry. | **Likely droppable** — but confirm if hydrologist uses ETRS89 for cross-referencing with national datasets. |
| `system` | 124 unique, str | **Hydrological system** — a grouping level BETWEEN basin and river (e.g., "oria", "nervion"). 124 systems across 10 basins. This is NOT mentioned anywhere in the PRD/architecture. Could be important for navigation/filtering. | **[ASK Q17]** This looks like a significant organizational concept. Should it be a filter option (FR9)? A display field? A grouping level in the sidebar? |
| `discharge` | Always 1 | Boolean flag — every station has discharge=1. Purpose unclear. Possibly indicates "has discharge data" vs. stations that only have level data. | **[ASK Q7]** Confirm purpose. Likely droppable. |

### 6.2 reservoirs.geojson — 7 Surplus Attributes

| Attribute | Values | Analysis | Recommended Action |
|-----------|--------|----------|-------------------|
| `INFORME` | 393 unique URLs | Link to official SNCZI dam safety report on the Ministry website. **Not in FR23 or docs.** Very useful — could provide a "View official report" link in the reservoir detail view. | **[FIX-DOCS]** Strong candidate for FR23 addition. Confirm with hydrologist. |
| `NMN_SUP` | 360 unique, 2% null | Surface area at normal maximum level (m2). Physical dimension of reservoir. Not in FR23. | **[ASK Q18]** Display in reservoir metadata? |
| `NMN_COTA` | 198 unique, 43% null | Elevation at normal maximum level. FR23 mentions "elevation" — this might be what was intended. | **[ASK]** Is this the "elevation" referenced in FR23? |
| `NAE_COTA` | 7 unique, **98% null** | Emergency level elevation. Nearly all null — effectively useless. | **Drop** — insufficient data coverage. |
| `TITULAR` | 59 unique, <1% null | Dam owner/entity. FR23 mentions "owner" — **this IS the data source for it**. But it's currently listed as surplus because the architecture doesn't map it. | **[FIX-DOCS]** Already required by FR23 "owner". Architecture needs explicit column mapping. |
| `ADMON_COMP` | 2 unique ("Estado" / other) | Administration competency — whether state-controlled. | **Likely droppable** — derivable from TITULAR. |
| `DTOR_EXPLO` | 112 unique, 13% null | Name of the exploitation director (person). **GDPR concern** — this is personal data. Should NOT be ingested without consent check. | **[FIX-DATA / GDPR]** Either remove from ingestion or confirm the data is public record. |
| `TIPO_TITUL` | 12 unique, <1% null | Ownership type classification. Overlaps with TITULAR/ADMON_COMP. | **[ASK Q18]** Useful? Or redundant? |

### 6.3 stations_basins_3sec.geojson — Dual-Value Pattern

| Attribute | Type | Notes |
|-----------|------|-------|
| `area` (string) | Reported area | From ministry/ROEA records |
| `area_3sec` (float) | DEM-derived area | Computed from MERIT 3-arcsecond DEM delineation |
| `lat`/`lon` (string) | Reported coordinates | Station coordinates from ministry |
| `lat_3sec`/`lon_3sec` (float) | DEM-derived coordinates | Basin centroid from DEM delineation |

**Analysis:** This layer has a **dual-value pattern** — reported values vs. DEM-derived values for the same physical quantities. The discrepancy between reported and DEM-derived areas is scientifically important (it indicates how well the DEM delineation matches the official catchment boundary). This is not documented anywhere in the PRD/architecture.

**[ASK Q19]** Should both values be stored and displayed? The area discrepancy could be shown as a data quality indicator.

---

## 8. Docs-Only Requirements — Detail Analysis

These are attributes or features explicitly required by the PRD/Architecture that have **no corresponding field** in the delivered layers. Either the data will come from a different delivery (time series, indices), or the documentation made assumptions that need correction.

### 8.1 Station Requirements Without Data

| PRD Requirement | Expected Source | Status | Action |
|----------------|----------------|--------|--------|
| FR20: "pre-selected study period start/end" | `start`/`end` fields? | **Ambiguous** — the layer has `start`/`end` as float years. Are these the algorithmically-selected best-quality periods (FR25b), or just the record availability range? | **[ASK Q12]** |
| FR19: Baseflow Index, Flashiness, etc. | `station_indices` table | **Expected separately** — these are pre-computed from time series, not GIS metadata. | Confirm delivery timeline |
| FR19d: Change point detection | `station_indices` table | Same as above | Confirm delivery timeline |
| FR19e: Suggested regulation status | `station_indices` table | Same as above | Confirm delivery timeline |
| FR12: `river_id`, `river_measure`, upstream/downstream FKs | **River polylines** (GAP-1) | **MISSING** — requires river geometry to compute | **Critical — GAP-1** |
| FR43: "34 attributes" for stations | Currently 26 in layer | **Discrepancy** — FR43 says 34 attributes, layer has 26. The missing 8 may be the pre-computed indices. Or FR43 count may be wrong. | **[FIX-DOCS]** Update FR43 to match actual attribute count, distinguishing GeoJSON metadata (26) from computed indices (separate delivery) |
| FR43: "pre-computed inflow-outflow bias" for reservoirs | Not in reservoir layer | **MISSING** — FR43 and FR22 explicitly require this as a reservoir GeoJSON attribute. Not present in delivered data. | **[ASK]** Will this be added to the reservoir GeoJSON? Or computed during ingestion? |

### 8.2 Reservoir Requirements Without Data

| PRD Requirement | Layer Attribute | Status | Action |
|----------------|----------------|--------|--------|
| FR23: "river" | **NOT IN LAYER** | No river name attribute in reservoirs. Cannot display "river" in metadata. | **[ASK]** Can hydrologist add a `river` field? Or derive from spatial join with stations? |
| FR23: "category" | `TIPO_EMBAL` (loose) | Has "Embalse de presa" and one other value. Loose mapping to "category". | **[ASK]** Is TIPO_EMBAL the intended "category"? |
| FR22: "inflow-outflow bias" | **NOT IN LAYER** | PRD explicitly marks this as "pre-computed by researcher". Not present. | **[FIX-DATA]** Hydrologist needs to add this field. |

### 8.3 Architecture Enum vs. Layer Reality

| Architecture Definition | Layer Reality | Correction Direction |
|------------------------|---------------|---------------------|
| `regime_type`: `NATURAL`, `SEMI_NATURAL`, `REGULATED`, `UNKNOWN` | `natural`, `unkown`, `altered`, `regulated` | **[ASK Q1]** — Is `altered` = `SEMI_NATURAL`? If yes, **[FIX-DOCS]** to note the v1→v2 taxonomy mapping. If no, **[FIX-DOCS]** to add `ALTERED` as 5th enum value + assign a color. |
| Classification colors: green/amber/red/**purple**/gray | 4 regime values map to green/amber(?)/red/gray | **[ASK]** What does **purple** represent? It's mentioned 3 times in the architecture but never defined. Possibly `altered` if it's a separate category from `semi-natural`? |
| Basin naming in architecture | `CANTABRICO` (stations) vs `CANTABRICO OCCIDENTAL`+`CANTABRICO ORIENTAL` (reservoirs) | **[FIX-DATA or FIX-DOCS]** — Need a canonical basin name list. The 11 *demarcaciones* from basin_authorities should be the authority. |

---

## 9. Mapping: Delivered Attributes → Architecture DB Schema

### 6.1 stations table

| Architecture Column | Source Attribute | Transform | Status |
|---------------------|-----------------|-----------|--------|
| `id` (PK) | `id_roea` | Direct | OK |
| `name` / `location` | `location` | Direct | OK |
| `geom` (Point, 4326) | GeoJSON geometry | Direct | OK |
| `drainage_area` | `catch_skm_station` | Direct | OK |
| `elevation` | `evelation_m` | **Rename** from typo | Fix needed |
| `basin_id` (FK) | `basin` + `id_basin` | Lookup/FK | Mapping needed |
| `river` | `river` | Direct | OK |
| `saih_code` | `id_saih` | Direct (nullable) | OK |
| `record_start` | `start` | Float → Date | Transform needed |
| `record_end` | `end` | Float → Date | Transform needed |
| `active` | `active` | Int → Boolean | Transform needed |
| `river_id` (FK) | — | **MISSING** — requires river polylines | GAP-1 |
| `river_measure` | — | **MISSING** — computed from river geometry | GAP-1 |
| `next_upstream_station_id` | — | **MISSING** — computed from river topology | GAP-1 |
| `next_downstream_station_id` | — | **MISSING** — computed from river topology | GAP-1 |
| `preliminary_regime` | `regime` | Map + fix typo | Transform needed |

### 6.2 reservoirs table

| Architecture Column | Source Attribute | Transform | Status |
|---------------------|-----------------|-----------|--------|
| `id` (PK) | `SNCZI` or `ID_EMBALSE` | Direct | Clarify which is PK |
| `name` | `NOMBRE` | Direct | OK |
| `geom` (Polygon, 4326) | GeoJSON geometry | **Reproject from 25830** | Fix needed |
| `capacity_hm3` | `NMN_CAPAC` | Direct | OK |
| `catchment_area` | `SUP_CUENCA` | Direct (44% null) | OK |
| `annual_inflow` | `AP_M_ANUAL` | Direct (47% null) | OK |
| `basin_authority` | `DEMARC` | FK mapping | Mapping needed |
| `use_types` | `USO` | **Parse multi-value** | Transform needed |
| `province` | `PROVINCIA` | Direct | OK |

### 6.3 Missing from Architecture

The following architecture-defined tables have no delivered data source:

| Table | Status | Needed By |
|-------|--------|-----------|
| `rivers` | **No data** | FR5, FR12 |
| `sub_basins` | **Unclear** — station basins may serve | FR4 |
| `time_series` (hypertable) | **Separate delivery** | FR13-FR19 |
| `station_indices` | **Separate delivery** — computed from time series | FR19-FR19h |

---

## 10. Questions for the Hydrologist

### Critical — Blocking ingestion pipeline and schema design

**Q1. Regime taxonomy mismatch** — The layer has `altered` but the platform's classification enum uses `SEMI_NATURAL`. Are these the same concept? Or does the v2 questionnaire intentionally change the taxonomy from v1? If different: should we have 5 categories (natural/semi-natural/altered/regulated/unknown) and what color maps to each?

**Q2. River polylines** — Needed for upstream/downstream navigation (FR12) and river display (FR5). Can you provide a river network layer? Options:
- (a) HydroRIVERS subset for Spain (free, from HydroSHEDS)
- (b) Spanish national river network from IGN/MITECO
- (c) Researcher-generated river geometry from the DEM delineation workflow

**Q3. Spatial FK relations (rivers AND basins)** — Currently, river and basin associations are text strings, not spatial relations. We propose converting to FK-based relations (see Section 11, Relational Design Opportunities). This affects multiple entities:
- **Rivers:** `river` text field in stations (451 values) → `river_id` FK to `rivers` table. Reservoirs currently have NO river field at all — spatial join could assign one.
- **Basins:** `basin` text field in stations and `DEMARC` text in reservoirs → `basin_id` FK to `basin_authorities` table. The `basin_authorities.geojson` layer (11 regions) is already delivered and could serve as the canonical basin reference.
- **`system` field** (124 values) — is this also an entity that needs its own table and FK?
- Do you agree with this relational approach? Can you validate station-to-river and reservoir-to-river assignments if we compute them spatially?

**Q4. Station scope** — Should all 835 stations be ingested, or only a subset (e.g., only `active=1` = 752 stations, or only specific basins)?

**Q5. Reservoir primary key** — Which identifier should be PK — `SNCZI` (dam safety ID, integer) or `ID_EMBALSE` (stored as float, same values)? The `INFORME` URL uses SNCZI.

**Q6. Inflow-outflow bias missing** — FR22 and FR43 say this is "pre-computed by researcher and delivered as reservoir GeoJSON attribute." It is NOT in the delivered reservoirs layer. Will it be added?

### Important — Affects data quality, display, and DB schema

**Q7. `discharge` field** — Always 1 for all 835 stations. What does this represent? Can it be dropped?

**Q8. `system` field (124 unique values)** — This appears to be a grouping level between basin and river (e.g., "oria" system contains multiple stations on the Oria river and tributaries). It is NOT mentioned anywhere in the PRD/architecture. Should it be:
- (a) A filter option alongside basin and regime (FR9)?
- (b) A display-only metadata field?
- (c) A potential FK relation (like rivers)?
- (d) Dropped?

**Q9. Sub-basin layer** — `stations_basins_3sec.geojson` has 835 basins matching 1:1 with stations. Is this the intended "sub-basin" layer for FR4, or is a separate sub-basin delineation (e.g., HydroBASINS) expected?

**Q10. Basin naming** — Differs between stations (`CANTABRICO`) and reservoirs (`CANTABRICO OCCIDENTAL` / `CANTABRICO ORIENTAL`). The `basin_authorities.geojson` has 11 regions. Which naming should be canonical? Should the two Cantabrian authorities be merged or kept separate?

**Q11. Reservoir CRS** — Reservoirs are in EPSG:25830, everything else in CRS84. We'll reproject during ingestion — just confirming this is the native SNCZI format, not an error.

**Q12. `start`/`end` fields** — Are these the researcher's algorithmically-selected "best quality" periods (as described in FR25b), or the full record availability range? FR25b says the study period is pre-computed as "longest period with ≥4 years and ≥90% annual availability."

### Surplus attributes — Keep, display, or drop?

**Q13. `catch_skm_river`** — Catchment area of the river (not station). Display alongside `catch_skm_station` in metadata? Or is it derivable/redundant?

**Q14. `sheet_id`, `id_municipality`, `x_etrs89`/`y_etrs89`** — IGN sheet number, municipality code, ETRS89 coordinates. Are any of these useful for hydrologists in the platform? Or legacy fields to drop?

**Q15. `years_daily`/`years_monthly`/`years_instant`** — Record length by temporal resolution. Very relevant for data quality assessment. Should all three be displayed (richer than just start/end)? Should they influence which stations are flagged for short records?

**Q16. `elevation_max_m`** — Max catchment elevation (matches CAMELS-ES `ele_mt_smx`). Should this be displayed in station metadata alongside station elevation? 43% null — acceptable?

**Q17. Reservoir `INFORME` URLs** — Links to official SNCZI dam safety reports. Add a "View official report" button in reservoir detail? Very useful contextual information.

**Q18. Reservoir `NMN_SUP`, `NMN_COTA`, `TIPO_TITUL`** — Surface area at normal max level, elevation at normal max level, ownership type. Display any of these? Or drop?

### Data delivery timeline

**Q19. Time series Parquet files** — When will per-station Parquet files be delivered? Schema design depends on file format.

**Q20. Static catchment attributes** — Will HydroATLAS/EFAS attributes be provided as separate CSV/Parquet? The 7 attributes in `stations_basins_3sec.geojson` are very sparse compared to the CAMELS-ES standard (~60 attributes).

**Q21. Dual area/coordinate values** — The basins layer has reported values (`area`, `lat`, `lon` as strings) AND DEM-derived values (`area_3sec`, `lat_3sec`, `lon_3sec` as floats). Should both be stored? The discrepancy between reported and DEM-derived areas is scientifically informative — display as a data quality indicator?

---

## 11. Recommendations & Relational Design

### Immediate Actions (resolve with hydrologist before ingestion pipeline):

1. **Resolve Q1 (regime taxonomy)** — This determines the enum definition, color mapping, and whether the architecture needs a 5th category. Cascade effect on design system, map symbology, questionnaire UI.

2. **Obtain river polylines (Q2) + decide on river FK design (Q3)** — This is the single most impactful gap. Without rivers, the core "follow the river" UX paradigm is broken. HydroRIVERS is the fastest path — it's freely available and already segmented with unique river IDs. The FK design decision (Q3) determines whether `river` stays as a text field or becomes a proper relational join to a `rivers` table — which in turn affects stations AND reservoirs.

3. **Confirm station scope (Q4)** — All 835 vs subset determines database sizing and ingestion logic.

4. **Get inflow-outflow bias (Q6)** — PRD explicitly says this is pre-computed. It's not in the data.

5. **Decide on surplus attributes (Q13-Q18)** — Before schema design, we need to know which of the 13+ surplus attributes to ingest vs. drop. This directly affects table column count and display requirements.

### Ingestion Pipeline Requirements (derived from analysis):

1. **Rename** `evelation_m` → `elevation_m`
2. **Fix typo** `unkown` → `unknown` in regime values
3. **Cast** `area`, `lat`, `lon` from string to numeric in basins layer
4. **Reproject** reservoir geometries from EPSG:25830 to SRID 4326
5. **Map** regime values: `natural` → `NATURAL`, `unknown` → `UNKNOWN`, `altered` → TBD, `regulated` → `REGULATED`
6. **Parse** reservoir `USO` field from newline-separated string to array
7. **Build** basin name mapping table for station-reservoir cross-referencing
8. **Generate** `river_id`, `river_measure`, upstream/downstream FKs from river polylines (once provided)
9. **Drop** `NAE_COTA` (98% null) and `DTOR_EXPLO` (personal data / GDPR)
10. **Strip** `INFORME` URLs or validate they are public — decide with hydrologist

### Documentation Updates Needed (after hydrologist resolves questions):

| Document | Section | Update |
|----------|---------|--------|
| **PRD** | FR20 | Add `elevation_max_m`, `years_daily/monthly/instant`, `system` (if kept), `catch_skm_river` (if kept) |
| **PRD** | FR23 | Add `INFORME` URL (if kept), clarify `TIPO_EMBAL` = "category", confirm `TITULAR` = "owner" |
| **PRD** | FR43 | Update "34 attributes" count to match actual (26 GeoJSON + N indices). Distinguish between GeoJSON static metadata and computed indices. |
| **PRD** | FR4 | Clarify whether station basins = sub-basins, or separate layer needed |
| **PRD** | FR9 | Consider adding `system` as filter option alongside basin and regime |
| **Architecture** | DB Schema | Add `river_id` FK design (pending river layer). Add reservoir CRS reprojection note. Add basin name normalization mapping. |
| **Architecture** | Enums | Update `regime_type` enum to match resolved taxonomy (4 or 5 values) |
| **Architecture** | Colors | Define what purple represents (currently undefined) |
| **Architecture** | Ingestion | Document all transforms: rename, cast, reproject, parse multi-value, basin name mapping |

### Relational Design Opportunities — Text Fields → FK Relations

The delivered layers currently use **text strings** for spatial relationships (basin name, river name). If we receive proper geometry layers (rivers, basins), these should become FK-based relations. This is a fundamental schema design decision that affects all three entity types.

#### Current state (text-based, fragile):

```
stations.basin   = "CANTABRICO"    (text, 10 values)
stations.river   = "oria"          (text, 451 values)
stations.system  = "oria"          (text, 124 values)
reservoirs.DEMARC = "CANTABRICO ORIENTAL"  (text, 11 values — DIFFERENT naming than stations!)
reservoirs — no river field at all
```

**Problems with text-based approach:**
- Basin naming inconsistency (stations: `CANTABRICO` vs reservoirs: `CANTABRICO OCCIDENTAL`/`CANTABRICO ORIENTAL`)
- No spatial validation — a station could claim to be in basin X but geometrically sit in basin Y
- No cross-entity queries (e.g., "all reservoirs in the same basin as station 1080")
- River names are lowercase, uncontrolled text — spelling variants likely

#### Proposed state (relation-based):

```
basin_authorities (id PK, name, code, name_en, geom MultiPolygon 4326)
  ↑
  ├── stations.basin_id FK → basin_authorities.id
  ├── reservoirs.basin_id FK → basin_authorities.id
  └── rivers.basin_id FK → basin_authorities.id (if rivers span one basin)

rivers (id PK, name, geom LineString/MultiLineString 4326, basin_id FK)
  ↑
  ├── stations.river_id FK → rivers.id
  │     + stations.river_measure FLOAT (0.0=source, 1.0=mouth)
  │     + stations.next_upstream_station_id FK → stations.id
  │     + stations.next_downstream_station_id FK → stations.id
  └── reservoirs.river_id FK → rivers.id (derived via spatial join)

stations_basins (id PK = station_id, geom Polygon 4326, area_reported, area_dem, ...)
  ↑
  └── stations.id = stations_basins.id (1:1)
```

**Benefits:**
- **Single source of truth** for basin names — `basin_authorities` table is canonical, no text matching
- **Consistent cross-entity queries** — stations and reservoirs in the same basin use the same FK
- **Spatial validation** — `ST_Contains(basin.geom, station.geom)` verifies assignment
- **River topology** — upstream/downstream navigation via `river_measure` on the same `river_id`
- **Reservoir-river association** — `ST_DWithin(reservoir.geom, river.geom, threshold)` assigns rivers to reservoirs
- **Filter consistency** — FR9 basin/regime filter works identically for stations and reservoirs

**What the hydrologist needs to provide or validate:**
1. **River polylines** with unique IDs and names (GAP-1)
2. **Station-to-river assignments** — can be computed via `ST_NearestPoint` but need validation
3. **Reservoir-to-river assignments** — can be derived spatially but need validation
4. **Basin naming** — confirm basin_authorities (11 regions) as canonical naming authority
5. **`system` field** (Q8) — is this a separate entity (exploitable system) that needs its own table, or just a grouping label?

**Trade-offs:**
- More complex ingestion pipeline (spatial joins, FK assignment, validation)
- Requires river polyline layer (GAP-1) before full relational model can be built
- Hydrologist must validate computed assignments (especially reservoir-to-river)
- Could build incrementally: start with basin FK (data available), add river FK later (pending river layer)

---

## 12. Summary Matrix

| Layer | Delivered | Quality | Gaps |
|-------|-----------|---------|------|
| **Stations** (835 pts) | Yes | Good — typo in field name, typo in regime value, regime taxonomy mismatch | River topology fields missing (depends on GAP-1) |
| **Reservoirs** (393 polys) | Yes | Moderate — CRS mismatch, high nulls in key fields, multi-value USO | CRS reprojection needed |
| **Basin Authorities** (11 polys) | Yes | Excellent — clean data | None |
| **Station Basins** (835 polys) | Yes | Good — string type issues | May or may not satisfy FR4 |
| **Rivers** (polylines) | **No** | N/A | **CRITICAL — blocks FR5, FR12** |
| **Sub-Basins** | **Unclear** | N/A | Depends on Q5 resolution |
| **Time Series** (Parquet) | **Not yet** | N/A | Expected as separate delivery |
| **Station Indices** | **Not yet** | N/A | Derived from time series |

---

---

## Appendix A: GDPR Note — `DTOR_EXPLO` Field

The reservoirs layer contains `DTOR_EXPLO` (exploitation director name) — personal data for 341 of 393 reservoirs. This is likely public record from SNCZI, but ingesting personal names into the platform creates GDPR obligations. **Recommendation:** Do not ingest this field unless explicitly needed. If needed, confirm the data is already public and document the lawful basis.

---

*Report generated by Mary (Strategic Business Analyst) using OSGeo4W Python for layer analysis, NotebookLM CAMELS Notebook for scientific context, and clear-thought decision framework for gap identification.*
