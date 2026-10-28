# ECAS review checkpoint — 2026-10-28

## Resume and review here

Workspace: `C:/AI-Projects/Bwett AI Project UwU/ECAS_BETA`.
Review branch: `codex/roadmap-reconciliation-20261028`.
Baseline: `2de79c7e025b492c900cc34a067e2875b744d8ab` (merged PR #1).
The user authorized this checkpoint and publication for review. The resulting
commit on this branch contains the changes below; this checkpoint does not
authorize merging into master. Preserve unrelated parent/coordinator work.

Local recovery bundle: `.checkpoints/review-ready-20261028.zip` and sibling
`review-ready-20261028-manifest.json`. The manifest records per-file SHA-256,
archive SHA-256, baseline and branch. The bundle covers Git-listed source, tests,
documentation and supplied public fixtures. It excludes Git metadata, dependencies,
private projects, runtime caches and credentials. It is a working-file snapshot;
Git may normalize text line endings in the publication. The archive is ignored
and stays local. The earlier reviewed-20261028 bundle remains unchanged.

To recover, verify the archive hash and each extracted file against the manifest,
extract into a separate folder, compare with the current project and restore only
needed files deliberately. Do not automatically overwrite the working tree or
reset Git. A clean checkout of the published branch is the portable review copy.

## Included changes

- Chunk 4: repaired CSV dispatch; NASA planet-alias resolution and clearer empty/
  unsupported results; functional project create/select/attach/reopen/copy with
  source bytes/provenance and integrity checks; snapshot-consistent SQLite reads,
  selective indexed loading and portable legacy hashes; presentation-only NASA
  links, compact controls and clear import/project errors.
- Chunk 5: offline comparison-readiness investigation, response/binning/uncertainty
  and fitted-template experiments, robustness/null calibration, limited initial
  method decision, eligibility contract and import adapter. These are research
  prototypes under docs, not an application comparison/scoring workflow.
- Chunk 5.1: ExoMol provider investigation, narrow calculated-cross-section parser,
  searchable public catalogue, bounded explicit refresh/cancel, validated caches,
  and Comparisons reference browser. Initial product retrieval supports only
  CO2 / 12C-16O2 / UCL-4000 with explicit temperature/range/spacing. Downloaded
  references display separately and reopen offline with original bytes/provenance.
- Dated public NASA/ExoMol fixtures and verification/review records. The form
  fixture has an explicitly synthetic anti-forgery token; no reusable account
  state is included. Runtime caches and private project databases are ignored.

## Verification and review status

Latest focused tests: **172 passed, 1 skipped**, 2.80 s, exit 0.
Latest full tests: **538 passed, 1 skipped**, 7.20 s, exit 0.
Commands/logs/runtime metadata:
`docs/Chunk_5_1/verification_product_20261028/reference-product-{focused,full}*`.
The skip concerns Windows directory-symlink privileges. Tests use recorded public
fixtures and fakes, without live network access. The ignored local sanitized
driver's exact pytest invocations are retained in the run JSON files.

Approved live actual-window/Qt verification downloaded and reopened an 11-point
CO2 cross section: 500 K, 4000–4010 cm^-1, spacing 1 cm^-1, zero pressure,
Doppler-only. The reopened values matched and no ExoMol client was constructed
offline. Source SHA-256:
`d323b5dd2f11c87a3cd6c0dc041fd625f00d56ec05cc2f2f2fb756cb01ea9fab`.
Initial failed checks remain in the evidence; they are not counted as passed.

Prior Chunk 4 Argon correction reviews returned no findings and the user confirmed
earlier manual acceptance. The user also confirmed independent review of the
earlier Chunk 5 foundation. **New Chunk 5.1 code has not received independent
review or fresh human desktop acceptance.** Earlier acceptance does not cover it.
Offscreen rendering lacked normal font glyphs, so it establishes geometry only.
Real-data scientific validation is explicitly deferred.

## Morning review

Use the existing project environment or install the declared requirements into a
fresh environment, then launch `python main.py` from the repository. Automated
checks can run with `python -m pytest -q -o pythonpath=.` in a clean environment.
No extra paid review service or agent is required.

1. In Comparisons search Water/H2O and inspect distinct isotope/dataset records.
   Confirm unsupported retrieval is explained rather than offered for every hit.
2. Search CO2 and select 12C-16O2 / UCL-4000. With explicit approval for public
   network use, download the small default reference. Check settings, displayed
   units/conditions, readable normal-font layout, progress and cancel/error states.
3. Close and reopen ECAS, then open the saved reference offline. Confirm the
   reference is independent of the currently loaded observational spectrum.
4. Review the new source/tests in Chunk 5.1, particularly callback reentrancy,
   cancellation/shutdown, fixed-origin form protocol, provenance and cache handling.
   Detailed feature/evidence map: `docs/Chunk_5_1/PRODUCT_RETRIEVAL_IMPLEMENTATION.md`.

## Remaining work and constraints

Chunk 5.1 is incomplete: broader verified product mappings and explicit independent
observation/reference pairing through the eligibility rules remain. Production
comparison/atmospheric modelling is not implemented. Cross sections are not transit
depth and successful download/overlap does not establish molecular presence.

Use `docs/ECAS_development_plan.md` and `docs/brains/PROJECT_STATE.md` for current
direction; older chunk notes preserve their own historical status. Do not run the
superseded coordinator probe. No additional paid agents/model services, real
application credentials or unrelated file access. No force-push, history rewrite,
merge or deployment is authorized by this review-publication request.
