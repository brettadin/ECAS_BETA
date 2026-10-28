# Additional ExoMol products — 2026-10-28

Two small calculated reference cross sections, not observations or validated
atmosphere models. Each .sigma file preserves original provider bytes: 308 bytes,
11 inclusive points at 4000–4010 cm^-1, spacing 1 cm^-1, 500 K. Conditions stated
by the provider: zero pressure, Doppler-only broadening; units cm^2/molecule.

| Formula / dataset | Service | Product SHA-256 |
| --- | --- | --- |
| H2O / POKAZATEL | https://www.exomol.com/xsec/1H2-16O/ | `695a0560817ca90d7eb4e09f5e3479daa53ec551a23acba530e3ad42955b25f3` |
| CH4 / MM | https://www.exomol.com/xsec/12C-1H4/ | `cc47d79cf6ba4bb286982f4ffbd74b4af11db32fbc2ee1960209a8e991b77151` |

`*-product-provenance.json` records exact UTC times, GET/POST/GET URLs, response
status/hashes, public parameters and conditions. `*-product-links.html` retains
unchanged result-page bytes, checked not to contain the transient form/cookie state.
`*-form-sanitized.html` is explicitly transformed: its anti-forgery token is replaced
with 64 synthetic S characters. `*-form-provenance.json` distinguishes original
and transformed hashes and omits token values. No email/account credentials were
supplied; fresh anonymous CSRF state was used only for the same-form POST and was
not sent to the product GET. No redirect or automatic retry was used.

ExoMol provider terms: https://www.exomol.com/data/licence/ ; CC BY-SA 4.0:
https://creativecommons.org/licenses/by-sa/4.0/ . Numerical product values are
unchanged; the form transformation is declared. Required attribution retained:

- Hill, Yurchenko & Tennyson (2013), Icarus 226, 1673–1677, cross-section method.
- Polyansky et al. (2018), MNRAS 480, 2597–2608, POKAZATEL water line list.
- Yurchenko et al. (2024), MNRAS 528, 3719–3729, MM methane line list. The methane
  page's inline citation says 2023; its full bibliography gives 2024. Source text
  is preserved rather than corrected.
- Tennyson & Yurchenko (2012), MNRAS 425, 21–33, ExoMol.

The dated master catalogue links these exact isotopes to their datasets. This does
not establish current inventory completeness, other isotope availability or
comparability with transit-depth data. See the Chunk 5.1 user-feedback workflow
for implementation, acceptance boundaries and executed tests.
