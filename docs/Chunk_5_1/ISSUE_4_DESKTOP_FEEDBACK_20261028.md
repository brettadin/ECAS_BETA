# Desktop feedback disposition — GitHub issue #4

Source: https://github.com/brettadin/ECAS_BETA/issues/4
Title: Desktop Acceptance review for 10/28/2026.
Issue updated: 2026-10-28T20:05:29Z; zero comments when read via the public API.
Reviewed build explicitly identified by the user: `49e3b96` on
`codex/roadmap-reconciliation-20261028`. The attached composite screenshot is
supporting visual context; the issue body supplies the detailed observations.

## Human review received

The user confirms readable UI/tooltips, working Overview shortcuts/storage paths,
observation loading/reopening with plots/tables, molecular download/cache reopening,
and preserved independent comparison inputs across navigation and new imports.
Their conclusion authorizes further development with the follow-ups below.
Record human desktop review as received/accepted for continued development with
known issues, not as flawless acceptance or scientific validation. The response to
checklist item 5 confirms path visibility; it does not explicitly verify CSV-selector
synchronization or restart reset. Do not invent those human checklist outcomes.
Prior automated/agent checks for those behaviors remain distinct evidence.

## Follow-ups checked against current code

| Item | Evidence and classification | Next action |
| --- | --- | --- |
| Repeated identical downloads create duplicate cache choices | Confirmed mechanism: store_reference uses a new UUID filename on every write; choices enumerate every valid record. Identical-looking choices are a usability defect. Distinct raw bytes, catalogue provenance or conditions must not be merged as though identical. | Define identity-aware reuse/deduplication without deleting existing captures or overwriting differing provenance; test repeated identical and differing records. |
| Successful download reportedly needs manual cached reopening to update the display | User-reported defect, not yet reproduced. The current received callback already stores, reloads choices, calls _show_reference(result), then announces success. A second manual open is not the intended success path. | Reproduce the actual request/completion/UI sequence and capture status, selected request and displayed identity. Do not assume which stage failed or dismiss the report because code calls _show_reference. |
| Comparisons observations named source.tbl | Confirmed presentation limitation: session choice uses only source_file.name, row count and session number. Saved project labels already use richer provenance, which Comparisons does not receive in its current getter. | Preserve and use available planet/publication/instrument metadata in session labels/tooltips, with explicit filename fallback and no invented identity. |
| Other H2O/CO2 catalogue entries cannot be downloaded | Known supported-scope limitation: only exact CO2/UCL-4000, H2O/POKAZATEL and CH4/MM main-isotopologue mappings have verified protocols. Catalogue presence does not prove a supported downloadable cross section. | Improve explanation/discoverability of supported records; investigate each additional service/representation before adding support. Never construct arbitrary download URLs from catalogue identifiers. |
| Same directories shown for generic and archive CSV choices | Expected: the schema choice controls CSV interpretation, not project/cache locations. Shared roots contain project-specific data; selecting a CSV schema does not select a storage directory. | Clarify wording if useful; no directory migration or per-schema folders are warranted by this report. |
| Molecular and comparison graphics, with appropriate layout | Explicit future requirement. Molecular reference plotting can show native wavenumber/cross-section units. An observational transit-depth spectrum and raw absorption cross section cannot share a meaningful comparison ordinate without a physical model. | Plan readable native-unit reference plots and separate/aligned inspection panels first. A scientifically valid shared-axis overlay remains subject to observable/unit/model/response requirements; do not label independent curves as a quantitative match or detection. |

The reported 400–4010 cm^-1 range describes that user's selected request, not the
provider's full supported coverage or the earlier 4000–4010 sample. Do not silently
substitute those ranges or infer planetary conditions from 500 K reference settings.

## Bounded continuation order

1. Reproduce/diagnose the display-update report; address duplicate cache choices
   and ambiguous observation labels with focused regression checks.
2. Clarify supported versus unavailable catalogue retrieval and settings semantics.
3. Design/add native-unit graphical inspection with usable sizing. Preserve the
   existing physical-model comparison block while building visual inspection.
4. Independent review and targeted desktop confirmation of new changes.

No implementation fix, fresh test run, live provider request, issue comment,
commit or push was performed for this triage-only increment. Issue #4 remains
open. Scientific validation stays deferred; earlier eight zero-findings reviews
do not override new user feedback or cover future fixes.
