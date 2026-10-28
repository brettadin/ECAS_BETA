# ExoMol public catalogue and calculated reference captures — 2026-10-28

The master catalogue is original provider metadata. The separately described
.sigma sample below is a calculated cross section, not a measured planetary spectrum.

- Provider: ExoMol, https://www.exomol.com/data/
- Source: https://www.exomol.com/db/exomol.all
- Original bytes: exomol.all, 189391 bytes, SHA-256
  `3bc26ed45c5483839ee7a17ce4b135bdd5b2230147b6c261e07102884ffe646c`.
- Capture details: exomol.all.provenance.json records exact UTC start/end, HTTP
  status, content type, byte count, hash and anonymous retrieval. One bounded HTTPS
  GET; no cookies, authentication, proxy environment, redirects or product requests.
- Attribution: ExoMol database, Tennyson et al., *The ExoMol database: Molecular
  line lists for exoplanet and other hot atmospheres* (2016),
  https://arxiv.org/abs/1603.05890, and the individual dataset papers when products
  are used. This catalogue does not replace their attribution requirements.
- Provider terms: https://www.exomol.com/data/licence/ states CC BY-SA 4.0:
  https://creativecommons.org/licenses/by-sa/4.0/ . Source bytes are unchanged.

Capture is a dated snapshot, not a promise of current provider completeness or
accuracy. Index version 20260605; 102 molecules, 242 distinct isotopologues and
250 dataset records. Names, formulae, isotopologues, InChI keys, dataset identifiers
and version labels remain separate. Non-calendar labels and ambiguous aliases are
retained; the parser warns rather than fixing provider facts. Dataset membership
does not establish downloadable cross sections, temperature, pressure, units,
coverage or direct compatibility with transmission spectra.

The initial master-link URL redirects; retrieval used the documented final HTTPS
origin directly. The local request first failed DNS under restricted networking;
an approved network retry succeeded. No retry loop or credentialed access used.

Parser/search audit: docs/Chunk_5_1/verification_catalogue_20261028/catalogue-audit.json.
Raw .all byte preservation is configured in .gitattributes. Future captures should
use new dated files instead of overwriting this provenance-bound source.

## Small calculated reference sample

`CO2-12C-16O2-500K-4000-4010-dnu1.sigma` contains unchanged provider bytes from
https://www.exomol.com/results/12C-16O2_4000-4010_500K_1.000000.sigma : 308 bytes,
11 inclusive points, SHA-256
`d323b5dd2f11c87a3cd6c0dc041fd625f00d56ec05cc2f2f2fb756cb01ea9fab`.
Requested through https://www.exomol.com/xsec/12C-16O2/ with T=500 K,
numin=4000 cm^-1, numax=4010 cm^-1, dnu=1 cm^-1, spoon_feed=on (two columns).
Provider description: UCL-4000 line list, zero pressure, Doppler-only broadening;
coordinates cm^-1 and cross sections cm^2/molecule. This is a small protocol fixture,
not an empirically validated atmosphere or observation-matching reference.

The sibling `.sigma.provenance.json` records anonymous form submission and product
retrieval timing, settings, hashes and HTTP status. `CO2-sample-product-links.html`
preserves the unchanged result-page bytes. `CO2-product-form-sanitized.html` is a
transformed form capture: its transient anti-forgery token was replaced with 64
synthetic S characters. The sibling provenance distinguishes its original and
stored hashes. No reusable cookie/token, email or account credential is included.
Restricted-network DNS failures preceded explicitly approved successful requests.

Attribution for this sample: Hill, Yurchenko & Tennyson (2013), *Icarus* 226,
1673–1677; Yurchenko et al. (2020), *MNRAS* 496, 5282–5291 (UCL-4000);
Tennyson & Yurchenko (2012), *MNRAS* 425, 21–33 (ExoMol). Provider licence:
CC BY-SA 4.0 at the URLs above. Scientific values and product bytes are unchanged;
the form transformation is explicitly identified. See
`docs/Chunk_5_1/PRODUCT_RETRIEVAL_IMPLEMENTATION.md` for application/test status.
