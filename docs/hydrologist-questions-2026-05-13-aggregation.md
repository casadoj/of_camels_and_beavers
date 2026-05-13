# Hydrograph Aggregation — Statistics & Zoom-Tier Conventions

**Date:** 2026-05-13
**Author:** Davor (with Mary, Business Analyst Agent)
**Subject:** Choosing summary statistics, zoom-tier breakpoints, and on-the-fly index computation for the hydrograph chart and the period-statistics screen
**Related code:** `time_series_*_daily` / `time_series_*_monthly` continuous aggregates; `station.getTimeSeries` query; future on-the-fly index procedure

---

## Context

The hydrograph today loads the full daily record for a station regardless of the zoom level the user is viewing (for example, ~14 600 daily points across a 40-year span). The database is built on TimescaleDB and already contains four pre-computed summary tables (daily and monthly summaries for stations and reservoirs), but the application never queries them. Two surfaces depend on those summaries: the **hydrograph chart** (visual exploration) and the **period-statistics screen** (where the user picks a date range and we report CAMELS-style indices). Per your earlier guidance, station indices and the rest of the statistics will be **computed on-the-fly from the database** at request time — not loaded as pre-computed snapshots through the ingestion pipeline. That makes the choice of what to pre-aggregate doubly important: the pre-aggregated summary tables are the substrate that lets on-the-fly index computation stay fast even on multi-decade windows.

This matters because:

- The current summaries compute only the **arithmetic mean** for discharge, temperature and PET, and the **sum** for precipitation. Once we start serving these summaries directly to the chart and feeding them into the on-the-fly index endpoint, the visual shape of the hydrograph changes — and so does the information available to the period-statistics screen.
<br><font color='maroon'>**@casadoj**: The statistic in discharge is the sum. However, discharge time series are prone to gaps, and those gaps would disturb the accumulated value. For that reason, the annual values of discharge are computed as the mean ($mm/d$) multiplied by 365 days in a year.</font><br>
- The CAMELS family of datasets (CAMELS-FR, CAMELS-GB, CAMELS-INDIA, CAMELS-SPAT) consistently publishes a **suite** of statistics — mean, median, max, min, percentiles — precisely because no single statistic captures both typical conditions and extremes. We need your guidance on which of these we should compute and display.
<br><font color='maroon'>**@casadoj**: It's true that the CAMELS dataset includes more statistics. Those will be added to the dataset, but I don't think they are necessary in the website, as this is meant for users to classify stations. If we want to complicate things, the clymograph could show not only the monthly means but a meaure of the uncertainty (like whiskers with the 25 and 75 percentiles), but it might require a lot of work for something that is not that meaningful.</font><br>
- The choice has knock-on effects: the regime classifier (Natural / Semi-natural / Regulated / Unknown) sits downstream and may be sensitive to how we aggregate.

Each question is grouped by impact:

- **Group A** — Choice of summary statistic. Highest semantic value to clarify; affects what numbers both the chart and the period-statistics screen show.
- **Group B** — Zoom-tier breakpoints. When does the chart switch from raw daily to a coarser summary?
- **Group C** — Missing-data handling at the summary level.
- **Group D** — Hydrological-year convention and regime-specific concerns.
- **Group E** — On-the-fly statistics for the period-statistics screen — which indices, with what precision, under what coverage rules.
- **Group F** — Anything you'd like to flag that we did not ask.

For each question we propose a **default** based on common CAMELS practice. Confirming the defaults is a valid answer — they exist so you do not have to start from a blank page.

---

## Group A — Summary statistic for each variable (highest value to clarify)

### A1. Discharge — central tendency

Streamflow distributions are positively skewed and the arithmetic mean is biased by a small number of high-flow days. CAMELS-family datasets publish **both** the mean (for mass-balance and total volumes) **and** the median Q50 (as a more representative "typical day"). The current daily/monthly summaries compute only mean discharge.

**Proposed default:** Compute **mean and median** in both the daily and monthly summaries, and let the chart show the mean as the primary line with the median visible as an optional second line in the legend.

**Alternatives:**
1. Mean only (current behaviour — simplest, but masks skew).
2. Median only as the primary line (cleaner "typical-flow" reading, but loses the mass-balance interpretation).
3. Mean primary, median surfaced only in the statistics pill, not on the line.

> **Question:** Which of these should we adopt for the daily and monthly summaries, and which should be the "main" line drawn on the chart? If you prefer something other than the four options above, please describe.

<br><font color='maroon'>**@casadoj**: All the comments above being true, I think none of those statistics are necessary. The purpose of the website is to check how feasible are the discharge time series. For that purpose, I think the best comparison is the average annual accumulation, i.e., mean annual cumulative precipitation and mean annual cumulative discharge, all in $mm$. That's what it is shown in the [dummy version](https://casadoj.github.io/of_camels_and_beavers/). It could be interesting to show the mean annual maximums (precipitation and discharge, all in $mm$), as an indication of regulation.</font><br>

---

### A2. Discharge — preserving floods and droughts under summarisation

When a 40-year view is rendered from monthly means, individual flood peaks and individual drought days disappear into the bucket average. CAMELS practice is to **publish additional max / min / percentile statistics alongside the mean** so that downsampled views still carry the extreme signal. Concretely:

- **Daily max** preserved per monthly bucket → preserves flood peak signal.
- **Daily min** preserved per monthly bucket → preserves low-flow / drought signal.
- **Percentile band** (e.g. Q5–Q95 or Q10–Q90 computed inside each bucket) → preserves dispersion.

**Proposed default:** In every monthly summary, also compute **max discharge** and **min discharge** observed during that month. The chart draws the mean as the main line and renders **max as a faint envelope above** and **min as a faint envelope below**, so the user always sees the range of conditions inside that month.

**Alternatives:**
1. Mean only on the chart, max/min reachable only via a tooltip or detail panel.
2. Mean line plus daily-max-discharge envelope (no min envelope) — emphasises peak signal.
3. Mean line plus full Q5–Q95 percentile band (richer but visually busier; would require approximate percentiles from the TimescaleDB Toolkit).
4. No envelope, but show **annual maximum daily discharge** as a separate dotted line — the standard CAMELS "annual peak" signature.

> **Question:** Which combination of statistics do you want preserved when the chart is summarised? Specifically: must the **flood peak signal** be visually preserved even at the 40-year zoom, or is it sufficient to surface peaks through the statistics pill and the diagnostics panel without drawing them on the line?

<br><font color='maroon'>**@casadoj**: Only monthly mean values are enough. We are looking for general trends to understand the catchment behaviour. For instance, a catchment dominated by snow may have a lot of precipitation in winter that only shows up in the discharge during the spring melt. If we want to complicate things, we can add the 25-75 percentiles for each month. What it is vital is that the monthly climatology compares precipitation, discharge and potential evapotranspiration in the same units ($mm$).</font><br>

---

### A3. Precipitation — total over the bucket

Precipitation is currently summarised as **SUM** of daily precipitation per bucket. This is the conventional "monthly precipitation total" reading and matches CAMELS practice. We do not propose to change it.

**Proposed default:** Keep `SUM(precip_mm)` for daily and monthly summaries.

**Optional addition:** Also compute **max-1-day precipitation** per month (the wettest single day of the bucket). This is useful for distinguishing a month with one large storm from a month of evenly-distributed rain.

> **Question:** Confirm that SUM is correct, and tell us whether the "wettest day of the month" is worth carrying alongside the monthly total.

<br><font color='maroon'>**@casadoj**: We don't need the "wettest day of the month".</font><br>

---

### A4. Temperature — central tendency vs. envelope

Temperature is currently summarised as **AVG** per bucket. For a long-term hydrograph view, mean temperature is the standard reading, but climatic-extremes (cold snaps, heatwaves) are lost.

**Proposed default:** Keep `AVG(temp_degc)` as the main statistic. Also compute **daily min and max temperature** per bucket and surface them on demand (not drawn by default to keep the chart readable).

**Alternative:** Just `AVG`, no min/max.

> **Question:** Do you need monthly min/max temperature available for the chart or the statistics panel, or is monthly-mean temperature sufficient?

<br><font color='maroon'>**@casadoj**: Average temperature is enough, as we only want to see the seasonality.</font><br>

---

### A5. PET — mean daily rate or total demand?

Potential evapotranspiration (PET) is currently summarised as **AVG(pet_mm)** in the daily and monthly summaries. The unit "mm/day" makes AVG a mean *rate*, which is fine for comparing months side-by-side. However, water-balance bookkeeping conventionally uses the **total PET demand** over the bucket (i.e. SUM), so that PET, precipitation and discharge are all expressed in the same units (mm per bucket).

CAMELS-FR uses **SUM** for monthly PET totals. Today we are using AVG, which is inconsistent with that convention.

**Proposed default:** Switch monthly PET aggregation to **SUM(pet_mm)** so that PET, precipitation and discharge-mm are all "total mm in the bucket". Keep AVG only if you want a daily-rate reading.

> **Question:** Should monthly PET be a **total** (mm/month, our proposal) or a **mean daily rate** (mm/day, current)? Either is defensible — we just want the answer to match Spanish hydrology convention and SAIH/CEDEX outputs.

<br><font color='maroon'>**@casadoj**: My version of the website computes the accumulated potential evapotranspiration. The idea is that discharge, precipitation and evapotranspiration must be in the same units: all represent sums in $mm$.</font><br>

---

## Group B — Zoom-tier breakpoints and visual fidelity

### B1. When should the chart switch from raw daily to a monthly summary?

We propose the chart pick its data source based on the time range the user is looking at:

| Time range visible on screen | Data source the chart queries | Approximate points drawn |
|---|---|---|
| Up to 2 years | Raw daily record | 365 – 730 |
| 2 to 15 years | **Daily summary** (still day-resolution, but pre-computed) | 730 – 5 500 |
| Above 15 years | **Monthly summary** | 24 – 480 |

The daily summary tier exists for completeness (it gives us pre-computed mean/max/min per day rather than recomputing on the fly), but at intermediate zooms (~5–15 years) it would also let us draw a smoothed weekly version if you prefer. The monthly tier kicks in for the wide-zoom case (your "I'm looking at 40 years").

**Trade-off:** At the boundary (e.g. zooming from 14y to 16y), the curve's shape will change — daily peaks vanish, the line becomes smoother. We can either accept that visible "step" or add a transitional zone where both daily and monthly are blended.

> **Question:** Are these breakpoints reasonable? In particular: at what zoom does daily detail stop being useful for you and become visual noise? If you'd rather not have a switch at all (always show one consistent tier), say so.

<br><font color='maroon'>**@casadoj**: If I understood this correctly, you're proposing to switch from daily to monthly values depending on the length of the period defined by the user. That was not my idea. We don't show monthly time series ever. There is a plot that shows the raw daily time series, and there is a plot that shows the seasonality (or climatology), which are monthly means over the whole selected period (not a time series of monthly values). Both the daily time series and monthly climatology are complementary plots to understand the data, we don't switch from one to the other.</font><br>

---

### B2. Alternative — never switch tier, always show envelopes

An alternative to switching aggregation tier is to **always draw the same monthly-mean line** but **always also show the daily-max envelope**. This means:

- At a 1-year zoom, the user sees the monthly-mean line plus 12 envelope segments above/below covering each month's daily min and max — visually similar to a candlestick chart in finance.
- At a 40-year zoom, the same monthly-mean line spans 480 months with a tight envelope around it.

This is closer to how multi-decade discharge plots are presented in hydrology papers — one continuous line with shaded ranges showing variability.

**Trade-off:** No tier switch, simpler implementation. But at the 1-year zoom the user loses the day-by-day resolution that they currently see in the modal, which may matter for flood-event analysis.

> **Question:** Do you prefer the **tier-switching** approach (B1) or the **always-envelope-around-monthly-mean** approach (B2)? Or some mix — for example "always show monthly mean line, but allow user to toggle to raw daily for events"?

<br><font color='maroon'>**@casadoj**: See answer to comment B1.</font><br>

---

### B3. Visual budget

Roughly how many points on screen feels right to you for the hydrograph? Too few and the curve loses character; too many and individual marks become invisible. The current default is 10 000 (and the algorithm picks them by perceptual importance).

**Proposed default:** Around 1 000–2 000 points drawn on screen. Beyond that, the eye can no longer distinguish individual marks at the modal's width (~700 px).

> **Question:** Is 1 000–2 000 a reasonable upper bound, or do you prefer a different visual density?

<br><font color='maroon'>**@casadoj**: The whole daily time series should be presented,so the user has a first idea of how long the records are, and what they look like. The plot should allow to zoom in-out (ideally both in X and Y axis), so the user can go into detail.</font><br>

---

## Group C — Missing-data policy in summaries

### C1. Threshold for invalidating a monthly summary

CAMELS-FR convention: **a monthly summary is invalid if more than 3 days of data are missing in that month**. If any single month inside a hydrological year is invalid, **the whole year is treated as missing** for annual aggregation.

**Proposed default:** Adopt the CAMELS-FR rule — monthly summary invalid if > 3 days missing; annual mean invalid if any constituent month is invalid.

**Alternative thresholds:**
1. More permissive — e.g. invalid only if > 7 missing days (allows reporting a month with one missing week).
2. Stricter — invalid if any day is missing (rigorous, but probably gives many invalid months in Spanish historical records).
3. Different rule for stations vs reservoirs — reservoir records are often coarser.

> **Question:** Confirm the 3-day rule, propose an alternative threshold, or tell us if the rule should depend on the entity type (station vs reservoir).

<br><font color='maroon'>**@casadoj**: I have been way more relaxed. Since the **monthly** values are means over the whole period, I don't apply a threshold. Example, if I'm computing the average total precipitation in February, I compute the mean of all available days and multiply by 28 (as the most frequent number of days of the month); in this way, I don't mind if some days are missing. For the **annual** values, I adopted the rule of removing years missing 10% of the data. Again, I compute mean annual values and multiply by 365 to be more robust agains missing data. We can revise this 10% threshold.</font><br>

---

### C2. Visual display of invalid summaries

Once a monthly summary is marked invalid, how should the chart show it?

**Proposed default:** Render an explicit gap in the line (no segment connecting the two valid neighbours). The existing missing-data rug at the bottom already marks the underlying missing days.

**Alternatives:**
1. Gap in the line (default proposal).
2. Draw the line through the gap with a dotted style, signalling "interpolated".
3. Show a hollow dot at the bucket centre with no line — emphasises invalidity.

> **Question:** Pick a default style for invalid monthly summaries on the chart, or describe a convention you already use elsewhere.

<br><font color='maroon'>**@casadoj**: This would apply to the annual plot, not to the monthly plot. The time series of annual discharge is a line plot with gaps if the year is missing more than 10% of the days (see answer to comment C1).</font><br>

---

### C3. Effect on regime classification

The questionnaire-driven regime classifier sits downstream of these summaries. If a station has many invalid months (e.g. half of its 40-year record was excluded under the 3-day rule), the annual statistics fed to the classifier are biased toward whatever years did pass the rule. CAMELS literature flags this concern but does not give a closed-form recommendation.

**Proposed default:** Show the classifier the **count of valid months** alongside the statistics it consumes, and treat any station with **< 30 complete hydrological years** as **Unknown** by default unless an expert overrides.

> **Question:** Is 30 complete hydrological years the right minimum for offering a confident classification? If not, what minimum record length would you want to enforce?

<br><font color='maroon'>**@casadoj**: The amount of missing data is not a value that defines the hydrological regime. The question about the hydrological regime should allow four answeres: natural, semi-natural, regulated, other. "Other" is meant for cases such as stations missing a lot of data; if there's a lot of data missing, we don't mind what is the regime, that time series is not good enough.</font><br>

---

## Group D — Hydrological year and regime-specific concerns

### D1. Calendar year vs. hydrological year

Annual means today are computed using the **calendar year** (Jan – Dec). Spanish hydrology and CAMELS-FR both use a **hydrological year starting 1 October** (so the 2025 hydrological year runs Oct 2024 → Sep 2025).

**Proposed default:** Switch annual means and annual statistics to the **hydrological year starting 1 October**. Calendar year stays as the date axis on the chart itself — only the annual aggregation boundary changes.

**Question:** Confirm October-start for the hydrological year, or specify the convention you use (some Mediterranean studies use September-start).

<br><font color='maroon'>**@casadoj**: Yes, it's better if we calculate annual values considering the start of the year October 1st. The idea is that the water balance closes at that moment of the year; all the precipitation in winter and spring has drained out of the catchment by the beginning of October.</font><br>

---

### D2. Regulated rivers — preserving the dam-release signature

In regulated rivers, dam operators release water in sub-monthly pulses. A monthly mean smooths these pulses to invisibility, which is exactly the visual fingerprint that distinguishes a regulated regime from a natural one.

**Proposed default:** For regulated and semi-natural stations, when the user zooms in below 5 years, **force the daily-summary tier** (do not collapse to monthly) so the pulses remain visible. The user can still zoom further out for the long-term view.

**Alternative:** Always show the **daily flashiness index** (Richards–Baker) as a secondary metric in the statistics pill, regardless of zoom.

> **Question:** Should the chart treat regulated stations differently from natural ones at the same zoom, or do you prefer a uniform aggregation policy across regime types?

<br><font color='maroon'>**@casadoj**: We are not presenting monthly time series, so this comment doesn't apply.</font><br>

---

### D3. Intermittent and ephemeral streams — zero-flow visibility

In intermittent / ephemeral Mediterranean streams (likely common in southern and eastern Spain), the **count of zero-flow days per month** is a defining regime indicator. Under monthly-mean aggregation, a month with 25 zero-flow days and 5 days of moderate flow looks similar to a month with 30 days of low-but-non-zero flow.

**Proposed default:** Add a **zero-flow-days count** per monthly summary, and show it as a small mark on the chart (e.g. a tick at the bucket boundary whose height encodes "0–30 zero-flow days").

> **Question:** Is the zero-flow count useful at chart level, or is it sufficient to surface it only in the diagnostics panel?

<br><font color='maroon'>**@casadoj**: Zero flows are indeed a common feature in many Spanish rivers. That's why I added the square root and logarithmic transformations, because the stretch the low flows and zero flows are easily spotted. I'll note down the idea of counting days with zero flow as a new attribute in CAMELS-ES, but I wouldn't added to the website.</font><br>

---

## Group E — On-the-fly statistics for the period-statistics screen

The period-statistics screen lets the user pick a station, choose a time range, and see CAMELS-style indices for that station and period. Per your decision that station indices and other statistics are computed **on-the-fly from the database** (not loaded at ingest time), the pre-aggregated summary tables from Group A become the substrate for this screen: a 40-year custom window can be aggregated from ~480 monthly bucket rows instead of ~14 600 raw daily rows, which is what keeps the screen responsive. The questions below lock down **which indices** we compute, **with what precision**, and **under what coverage rules** before refusing or warning.

### E1. Which index catalog?

CAMELS-FR (and CAMELS-GB / Addor 2017) publish a fairly standard set of streamflow indices that we can reproduce one-for-one. A reasonable baseline set:

- **Magnitude:** mean discharge, median discharge (Q50), annual maximum 1-day flow, annual minimum monthly flow (QMNA).
- **Distribution:** Q5, Q10, Q90, Q95; FDC slope (33rd–66th percentile log-transformed).
- **Variability:** standard deviation, coefficient of variation (CV) of annual and monthly flows.
- **Timing:** half-flow date (HFD) — day of the hydrological year by which 50 % of cumulative flow has been reached.
- **High flows:** frequency and mean duration of days where flow > 9 × median daily flow.
- **Low flows:** frequency and mean duration of days where flow < 25th percentile.
- **Zero flow:** frequency of zero-flow days per year.
- **Regime indicators:** Baseflow Index (BFI — Ladson 2013 digital filter), Richards–Baker Flashiness Index.

**Proposed default:** Compute all of the above on the user-selected period. Each index is a small column on the screen with a tooltip explaining definition + units.

**Alternative — minimum viable set:** mean discharge, Q5 / Q50 / Q95, BFI, R-B flashiness, zero-flow frequency. Easier to explain to non-specialists, fewer numbers on the screen.

> **Question:** Which set should we ship? Specifically: any index in the baseline list above we should **drop** (because you never use it), and any we should **add** (because Spanish practice expects it but CAMELS does not cover it)?

<br><font color='maroon'>**@casadoj**: All these indices are very important to be included in the CAMELS-ES dataset, but I'm not sure we need to show them in the website, especially if the website computes indices on the fly.</font><br>

---

### E2. Period selectors on the screen

What time-window controls does the user need to pick the analysis period?

**Proposed default:** Three concurrent selectors, mutually exclusive:
1. **Hydrological year** drop-down (per D1, Oct–Sep).
2. **Custom date range** (free start/end picker).
3. **Presets**: "Last 5 years", "Last 10 years", "Full record".

The screen state lives in URL search params, so a hydrologist can paste a link and reach the same view.

**Alternative — simpler:** only hydrological year drop-down + "Full record". Less flexible but less to misuse.

> **Question:** Are these selectors right? Specifically: should the custom range also offer **calendar year** as an option (e.g. for climate-cycle alignment), or is hydrological year always the right boundary?

<br><font color='maroon'>**@casadoj**: Those three are fine. "Full record" as default, the custom date range and selecting a specific hydrological year. The last one could be skipped, if it complicates things.</font><br>

---

### E3. Exact vs. approximate percentiles

Percentile indices (Q5, Q10, Q50, Q90, Q95) on a multi-decade window require either a full sort of every daily value in the window (exact) or a single-pass approximate algorithm (T-Digest / `percentile_agg` from the TimescaleDB Toolkit). The trade-off:

| Approach | Compute cost on a 40-year window | Error | Reproducible across DB versions |
|---|---|---|---|
| Exact (full sort) | O(n log n) per request, ~50 ms for daily data | 0 % | Yes, bit-for-bit |
| Approximate (T-Digest) | O(n) and incrementally computable in continuous aggregates, ~5 ms | typically < 1 % relative | Yes, but with that 1 % tolerance |

**Proposed default:** Approximate for any window > 1 year (fast enough to feed live interaction); exact for windows ≤ 1 year (negligible cost difference).

**Alternative:** Always exact. The result is reproducible to the bit across versions, which matters if these numbers ever end up in a publication.

> **Question:** Is the < 1 % approximation acceptable for the screen, or do you need exact percentiles? If you need exact for publication-grade work, we can offer an "export exact" button that recomputes on demand while the screen itself stays approximate.

---

### E4. Validity rule for index computation

Should indices respect the monthly-validity rule from C1 (only days from valid months count), or use all non-NaN daily values in the selected period regardless of month-level invalidity?

**Trade-off:** Strict gives statistics that are comparable across stations because the same rule excludes the same kinds of gappy months. Lenient gives more data to work with on partially-gappy stations but mixes high-quality and low-quality months without distinction.

**Proposed default:** **Strict.** Indices are computed over days that belong to valid months (per C1's 3-day-per-month threshold). The screen displays a coverage badge — "X of Y days valid" — so the hydrologist sees what got excluded.

**Alternative:** Lenient — use all non-NaN daily values; surface a missingness percentage but do not exclude.

> **Question:** Strict or lenient — and is there a class of index where the rule should differ (e.g. zero-flow frequency, which is sensitive to which days were excluded)?

---

### E5. Coverage threshold for refusing to compute

What happens when the user picks a period that is mostly missing data?

**Proposed default:** Compute and display all indices regardless of coverage, but mark the screen with a prominent badge: "X % of days valid in this period". Refuse to compute (show empty-state with explanation) only when coverage falls below **10 %** of the selected period.

**Alternative thresholds:**
1. Refuse below 50 % — only show indices when the period is "mostly there".
2. Always compute, never refuse — let the badge speak for itself.
3. Always compute, but mark the screen "Indicative" in red when coverage < 50 %.

> **Question:** Where should the refusal threshold sit, and is the per-screen badge sufficient warning, or do you want a per-index flag (e.g. greying out low-flow indices specifically when the dry-season months are gappy)?

---

### E6. Spanish-specific indices and frameworks

CAMELS-FR and CAMELS-GB do not cover Iberian-specific frameworks. Notably:

- **IAHRIS** (Indicators of Hydrologic Alteration for Iberian Rivers) defines its own index family for natural-vs-altered regime comparison.
- **CEDEX environmental-flow indices** for regulatory compliance.
- **Sequía / drought indices** specific to Mediterranean hydroclimatology (e.g. SPI variants applied to streamflow).

**Proposed default:** Ship the CAMELS-FR set first (E1) and add any Spanish-specific indices in a follow-up once you flag the priority ones.

> **Question:** Are there any Spanish-specific indices that should be there from day one — i.e. that you would consider the screen incomplete without — versus follow-up additions? If yes, please name them so we can size the work.

---

## Group F — Anything we missed

> **Question:** Is there any aggregation, display, or statistics choice that you would normally see on a multi-decade hydrograph or a period-statistics report from CEDEX / SAIH / your own analyses that we have not asked about here? If yes, please describe — we would rather know now than discover it after wiring the summaries in.

---

## Summary of impact

| Group | Hydrologist input changes | Implementation cost on our side |
|---|---|---|
| A | Yes — which statistics get computed and shown on both surfaces | Small per statistic (one column per CAgg); larger if percentiles are required |
| B | Yes — defines the user-visible UX behaviour on the chart | Medium — server-side tier routing + client refetch on zoom |
| C | Yes — semantic decision on data validity | Small — predicate inside CAgg query and a display style |
| D | Yes — hydrological-year boundary, regime-specific treatment | Small for D1 (constant), medium for D2 (regime-aware routing) |
| E | Yes — defines the index catalog, precision policy, and coverage thresholds | Medium — on-the-fly tRPC procedure backed by CAggs + (optionally) TimescaleDB Toolkit |
| F | Open-ended | Unknown |

We will wait for your answers (or your "defaults look fine" sign-off) before locking the implementation. If anything in the proposed defaults already looks wrong, please flag it — every default in this document is a reasonable guess from CAMELS literature, not a settled choice.
