# Molecular reference provider investigation — 2026-10-28

Status: initial bounded provider/representation decision, not end-to-end reference
retrieval or empirical validation. User confirmed independent review complete and
authorized progression from Chunk 5; no individual new findings report was supplied.
Real-data validation stays deferred. No credentials, dataset downloads or added
dependencies were used in this increment; public documentation/catalogue pages
were read through web tools. Access date for all linked sources: 2026-10-28.

## Provider comparison

| Source | Verified interface/product facts | Implication for initial ECAS scope |
| --- | --- | --- |
| ExoMol | [Public data index](https://www.exomol.com/data/) documents molecule/isotopologue navigation, master ExoMol.all and definition files. [Search](https://www.exomol.com/data/search/) offers formula/isotopologue and dataset-name fields. | Initial candidate for anonymous discovery. Common-name aliases and catalogue parsing still need verification; an empty unsubmitted form is not evidence of absent products. |
| NIST WebBook | [Name search](https://webbook.nist.gov/chemistry/name-ser/) supports names/patterns and IR filtering; [home page](https://webbook.nist.gov/chemistry/) also links formula, CAS and InChI search. [Coblentz guidance](https://webbook.nist.gov/chemistry/coblentz/) describes sample-state and resolution differences. | Useful laboratory reference candidate, not an interchangeable hot-gas opacity or transit-depth spectrum. Sample conditions must accompany products. |
| HITRAN/HAPI | [Current HAPI page](https://www.hitran.org/hapi/) says an API key is required for data downloading and HAPI use. [FAQ](https://www.hitran.org/faq/) defines vacuum-wavenumber coordinates and distinguishes parameter data from atmospheric modelling. | Do not implement credentialed retrieval under current no-real-credentials restriction. Free access does not remove authentication requirements. |

## Access/attribution evidence

[ExoMol's licence page](https://www.exomol.com/data/licence/) states CC BY-SA 4.0
with attribution, indication of changes, ShareAlike and dataset-paper citations.
Preserve raw originals, product identity, references and licence URL alongside any
processed representation. This is a record of published terms, not a blanket legal
assessment of all derived software or third-party products.

NIST explicitly marks the [WebBook](https://webbook.nist.gov/chemistry/) as covered
by copyright. Do not assume government hosting implies unrestricted redistribution.
HAPI's code licence is distinct from dataset attribution/access. No bulk download,
redistribution promise or private-account workflow is introduced here.

## Initial bounded choice

Use **ExoMol as the initial source to investigate/implement for anonymous molecular
reference discovery**, with a narrow **two-column zero-pressure .sigma cross-section
representation** as the first parser target. This is calculated reference data,
not a measured exoplanet spectrum or selected atmospheric forward model.

The [CO2 cross-section service](https://www.exomol.com/xsec/12C-16O2/) explicitly
documents zero pressure/Doppler-only broadening, a default single-column file and
an optional two-column file with bin-center wavenumber and cross section. Wavenumber
units are cm^-1; cross-section units are cm^2/molecule. The page identifies its
UCL-4000 parent line list and references. Its displayed parameter limits are specific
to that page, not universal limits for all ExoMol products. A service description
and reachable form do not prove successful generation or anonymous retrieval.

This excludes default single-column grids, line lists, k-tables, compressed files,
arbitrary pressure broadening and generic JCAMP-DX. [The IUPAC JCAMP-DX publication](https://iupac.org/wp-content/uploads/2021/08/JCAMP-DX_IR_1988.pdf)
was identified as a format reference; full encoding/record variants and NIST
product-download behavior were not established. Do not advertise JCAMP support.
No provider is assumed to cover the NASA example's full range at suitable conditions.

## Implemented parser, not network integration

`ecas/ingestion/exomol_cross_section.py` parses supplied UTF-8 bytes into an immutable
MolecularCrossSection. It retains numeric values/order, source hash/byte count,
explicit molecule/isotopologue/dataset, temperature, zero pressure, broadening,
source URL, references and licence. It performs no wavelength/observable conversion
and does not instantiate SpectrumData. Caller provenance is not authenticated.

Bounds: 1 MiB, 10,000 points, at least two increasing finite nonnegative wavenumbers
and nonnegative finite cross sections. Zero coordinate is preserved, never inverted.
Only two numerical columns are supported; comments/header encodings and inferred
one-column grids are rejected. Unknown conditions, mismatched representation metadata
and unsupported source origins fail explicitly. Positive temperature is required;
the parser cannot verify applicability or provider availability at that temperature.
Pressure and broadening are mandatory, not silently defaulted.

28 synthetic cases cover representation/provenance, malformed numerics/columns,
invalid conditions/origins, bounds and zero-coordinate preservation. No molecular
product was downloaded or scored. Full suite: 452 passed/one existing symlink-
privilege skip (8.02 s). Focused: 67 passed/one skipped (0.93 s).
Commands: `.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py reference-parser-focused`
and reference-parser-full; logs/command metadata in verification_20261028.

## Still required

1. Verify master catalogue schema and programmatic discovery with original metadata;
   preserve canonical formula, isotopologue, dataset and aliases as separate identities.
2. Verify actual service request fields/response/download mechanics without supplying
   an email or credentials; a linked page is not a tested download API.
3. Validate one small authorized product against the documented representation,
   retaining original bytes/parameters/licence/citations and capture provenance.
4. Add bounded retrieval/cancellation/cache integrity/offline reopening and catalogue
   states distinguishing failed search, no match, unsupported or unavailable products.
5. Connect in-app molecule/identifier search and selection, showing type, conditions,
   coverage, units and retrieval status. Common-name resolution must be evidenced.

No generated source data, parser or catalogue membership may imply molecular
presence. Cross sections stay ineligible for direct transit-depth comparison without
an explicit physical model. New parser/provider choice awaits independent review;
existing review confirmation does not cover code written afterward.

Tool limitations: NIST water CGI request was inaccessible and one H2O isotopologue
page timed out; neither proves absence of data. The CO2 catalogue/isotopologue/
cross-section landing pages were readable. No repeated bulk probing or bypass.
