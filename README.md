# Met Office Warnings

[![Validate](https://github.com/Proffalken/ha-metoffice-weather-warnings/actions/workflows/validate.yml/badge.svg)](https://github.com/Proffalken/ha-metoffice-weather-warnings/actions/workflows/validate.yml)
[![Test](https://github.com/Proffalken/ha-metoffice-weather-warnings/actions/workflows/test.yml/badge.svg)](https://github.com/Proffalken/ha-metoffice-weather-warnings/actions/workflows/test.yml)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A Home Assistant custom integration that surfaces **UK Met Office severe weather
warnings** via the [National Severe Weather Warning Service (NSWWS) Public
API](https://metoffice.github.io/nswws-public-api/). Home Assistant's built-in
[`metoffice`](https://www.home-assistant.io/integrations/metoffice/) integration only
covers forecasts — this fills the warnings gap.

## Status

Validated against a live NSWWS API key and real warning data (August 2026). Along the
way, several things turned out to differ from the published docs at
[metoffice.github.io/nswws-public-api](https://metoffice.github.io/nswws-public-api/),
which appear stale:

- The API version is **v1.1**, not v1.0.
- The auth header is **`apikey`**, not `x-api-key`.
- There is **no fixed "issued" path**. `/objects/feed` returns an Atom feed whose
  `rel="related"` link ("Latest version of all issued warnings") points at the actual
  GeoJSON snapshot, under a URL containing the feed's own UUID — this integration
  discovers it on every poll rather than assuming a stable path.
- The base URL (`https://data.hub.api.metoffice.gov.uk/nswws/v1.1`) is a **fixed
  public host shared by every subscriber**, not a personal URL issued alongside the
  key as the docs implied — DataHub-style. It's pre-filled in the config flow.
- The GeoJSON warning properties include a `whatShouldIDo` field not mentioned in the
  docs, and `warningVersion` is a string (e.g. `"1.0"`), not a number.

If something still doesn't parse as expected, please
[open an issue](https://github.com/Proffalken/ha-metoffice-weather-warnings/issues) with a
redacted sample response.

**Known gap:** HACS's brand-assets check currently fails because this integration hasn't
been submitted to [home-assistant/brands](https://github.com/home-assistant/brands) yet
(needs an icon/logo). That's expected for a new integration and doesn't block installing
it as a HACS custom repository — only default-store listing.

## What you get

Each config entry (one NSWWS API key/area filter) creates one device with six
entities:

- `sensor.<name>_warning_level` — the highest-severity active warning matching your
  selected area or Home location: `none` / `yellow` / `amber` / `red`. Attributes include the full list
  of active warnings (headline, weather type, what to expect, what to do, valid
  from/to, likelihood, impact, affected areas) — use this one for templating.
- `binary_sensor.<name>_warning_active` — on when any warning matches your filter, for
  simple automation triggers. Attributes summarise the most severe active warning.
- `sensor.<name>_warning_headline` / `_warning_areas` / `_warning_valid_from` /
  `_warning_valid_to` — the single most severe active warning's headline, affected
  areas, and start/end time, each as its own plain entity. These exist so you can drop
  the details straight onto a dashboard with an ordinary entity card, without writing
  a template against `warning_level`'s attributes. They go to `unknown` when nothing's
  active. The headline sensor also carries what-to-expect/what-to-do/further-details
  as attributes, for the same "click through for more" experience as a weather app.

## Requirements

You need your own NSWWS Public API access — this is a *different* product from the
Met Office DataHub weather-forecast API and requires a separate signup:

1. Fill in the request form linked from the
   [NSWWS Public API docs](https://metoffice.github.io/nswws-public-api/).
2. Once approved, you'll receive an API key (the base URL is the same fixed public
   host for everyone — see the Status section above).

## Installation

### Via HACS (custom repository)

1. HACS → the ⋮ menu → **Custom repositories**.
2. Add `https://github.com/Proffalken/ha-metoffice-weather-warnings`, category **Integration**.
3. Install **Met Office Warnings**, then restart Home Assistant.

### Manual

Copy `custom_components/metoffice_warnings` into your Home Assistant `config/custom_components/` directory and restart.

## Configuration

Settings → Devices & Services → Add Integration → **Met Office Warnings**.

1. Enter your NSWWS API key (the base URL is pre-filled — only change it if Met
   Office tells you to).
2. If any warnings are currently active anywhere in the UK, you'll be offered a list
   of regions to filter to — leave **Monitor all UK regions** checked to track
   everything nationwide, or pick specific regions. If nothing is active right now,
   setup completes immediately monitoring the whole UK; refine the area filter later
   from the integration's **Configure** options.

Poll interval (default 10 minutes, minimum 5), region selection, and **Use Home\nlocation** can be changed afterwards via the integration's **Configure** options.\n\n### Optional Home location filtering\n\nEnable **Use Home location** to select warnings whose published GeoJSON polygons\ncover the latitude and longitude configured in Home Assistant (Settings → System →\nGeneral). This option is **off by default**, preserving the existing region-based\nbehaviour. It is useful near regional or warning boundaries, where selecting a broad\nregion may include warnings that do not actually cover your home.\n\n- With the option **off**, warnings match the selected regions as before.\n- With it **on**, warnings with usable Polygon or MultiPolygon geometry are\n  included only when the Home location is inside or on the warning boundary.\n  Polygon holes are respected.\n- If an individual warning has missing or unusable geometry, that warning falls\n  back to the selected region filter rather than disappearing silently.\n- If Home Assistant's Home coordinates are invalid or unavailable, filtering\n  falls back to the selected regions for all warnings.\n\nThe warning-level sensor exposes a `filter_method` attribute: `region`,\n`polygon`, `polygon_with_region_fallback`, or `region_fallback`. The existing\n`warnings` attribute contains only matched warnings; full polygon coordinates\nare deliberately **not** published as entity attributes.\n\n### Downloading diagnostics\n\nFor troubleshooting, open **Settings → Devices & Services → Met Office Warnings**,\nthen the integration's three-dot menu → **Download diagnostics**. The downloaded\nJSON includes the latest fetched warning polygons, **including excluded warnings**,\nand the `included`, `region_match`, and `polygon_match` decisions for each. This\nallows boundary issues to be investigated without adding large geometries to\nHome Assistant's recorder.\n\nThe API key is redacted and exact Home coordinates are not included. The\nexport can still contain detailed weather-warning geometry and configuration\ninformation, so review it before sharing publicly.

## How it works

Each poll fetches the NSWWS `/objects/feed` Atom feed, follows its `rel="related"`
link to discover the current warnings snapshot URL, then fetches that GeoJSON
`FeatureCollection` — which already excludes expired/cancelled warnings.\nLocation filtering is applied to that snapshot locally; it does not require\nan additional Met Office API request. It does
**not** yet consume the feed's individual `<entry>` change events (issued/updated/
cancelled) for faster, event-driven updates — that would mean tracking a feed cursor
across restarts, which is a reasonable follow-up now that the snapshot-polling
approach is validated against live data.

## Development

```console
uv sync --dev
uv run pytest -v
uv run ruff check .
```

### Releasing

Bump `version` in `custom_components/metoffice_warnings/manifest.json` (keep
`pyproject.toml`'s version in sync) and push to `main`. The `Release` workflow tags and
publishes a matching GitHub Release automatically — that's what HACS shows as the
installable version, so a version without a release just shows up as a commit hash.

Tests run against fixtures modeled on real captured NSWWS responses
(`tests/fixtures/`) — see the status note above for how they were validated.

## License

MIT — see [LICENSE](LICENSE).
