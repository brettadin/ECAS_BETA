"""Auditable catalog of scientific software, archives, molecular databases, and papers.

Every record distinguishes what ECAS directly implements from what serves as
external scientific inspiration, data provider, or benchmark publication.
Canonical URLs and DOIs are stored without tracking parameters, and molecular
presence in a reference database or model is never equated with an observational
detection.
"""
from dataclasses import dataclass
from urllib.parse import urlsplit

CATEGORY_FILTERS = (
    'All',
    'Software',
    'Data archive',
    'Molecular data',
    'Python library',
    'Publication',
)

EVIDENCE_STATUSES = (
    'reported_detection',
    'independent_confirmation',
    'tentative_or_disputed',
    'upper_limit_or_non_detection',
    'model_predicted_presence',
    'not_assessed',
)


@dataclass(frozen=True)
class ScientificResource:
    resource_id: str
    title: str
    category: str
    resource_type: str
    authors_or_organization: str
    description: str
    canonical_url: str
    doi: str | None
    version_or_release: str
    publication_date: str
    access_date: str
    license: str
    access_label: str
    contribution: str
    ecas_components: tuple[str, ...]
    citation: str
    verification_status: str
    notes_and_limitations: str

    @property
    def short_description(self) -> str:
        return self.description

    @property
    def authors_or_org(self) -> str:
        return self.authors_or_organization

    @property
    def version_or_scope(self) -> str:
        return self.version_or_release

    @property
    def license_spdx(self) -> str:
        return self.license

    @property
    def ecas_contribution(self) -> str:
        return self.contribution


@dataclass(frozen=True)
class MolecularDatabaseSpec:
    database_id: str
    name: str
    data_types: tuple[str, ...]
    typical_temperature_max_k: float
    primary_use: str
    canonical_url: str
    citation: str
    limitations: str

    @property
    def typical_temp_range_k(self) -> tuple[float, float]:
        low = 1000.0 if self.database_id == 'nist-asd' else (300.0 if self.database_id == 'hitemp' else 100.0)
        return (low, self.typical_temperature_max_k)


@dataclass(frozen=True)
class SpeciesEvidenceRecord:
    species: str
    status: str
    observing_mode: str
    instrument: str
    publication: str
    doi: str | None
    summary: str
    caveats: str

    def __post_init__(self):
        if self.status not in EVIDENCE_STATUSES:
            raise ValueError(f'Unsupported evidence status: {self.status!r}')
        if not self.species.strip() or not self.publication.strip() or not self.caveats.strip():
            raise ValueError('SpeciesEvidenceRecord requires non-empty species, publication, and caveats')


@dataclass(frozen=True)
class BenchmarkPlanetRecord:
    planet_name: str
    host_star: str
    primary_modes: tuple[str, ...]
    why_benchmark: str
    main_research_direction: str
    key_publications: tuple[str, ...]
    species_assessments: tuple[SpeciesEvidenceRecord, ...]


def _verify_clean_https_url(url: str) -> str:
    parts = urlsplit(url)
    if parts.scheme != 'https' or not parts.netloc or 'utm_source' in parts.query:
        raise ValueError(f'Resource URL must be clean canonical HTTPS without tracking params: {url!r}')
    return url


_CATALOG: tuple[ScientificResource, ...] = (
    ScientificResource(
        resource_id='petitradtrans',
        title='petitRADTRANS',
        category='Software',
        resource_type='software',
        authors_or_organization='Mollière et al. / MPIA',
        description='Atmospheric forward modeling and retrieval',
        canonical_url='https://petitradtrans.readthedocs.io/en/latest/',
        doi='10.1051/0004-6361/201935470',
        version_or_release='3.x documentation referenced',
        publication_date='2019-06',
        access_date='2026-10-28',
        license='MIT (v3+) / GPL-3.0 (earlier releases); verify specific release',
        access_label='Open source',
        contribution=(
            'Informed ECAS forward-model provenance requirements (T-P profile, gravity, '
            'reference pressure, radii, species mixing ratios, opacity sources, and '
            'instrument response) and external model export adapter design. Not bundled '
            'or reimplemented inside ECAS.'
        ),
        ecas_components=('ecas/comparison/forward_model.py', 'ecas/comparison/model_adapters.py'),
        citation='Mollière, P., Wardenier, J. P., van Boekel, R., et al. 2019, A&A, 627, A67. doi:10.1051/0004-6361/201935470',
        verification_status='verified_canonical_metadata',
        notes_and_limitations='Major versions (v2 vs v3 SpectralModel) change APIs and opacity file layouts.',
    ),
    ScientificResource(
        resource_id='poseidon',
        title='POSEIDON',
        category='Software',
        resource_type='software',
        authors_or_organization='MacDonald, R. J. & contributors',
        description='Multidimensional exoplanet atmospheric modeling and retrieval framework',
        canonical_url='https://poseidon-retrievals.readthedocs.io/',
        doi='10.21105/joss.04873',
        version_or_release='1.2+ documentation referenced',
        publication_date='2023-01',
        access_date='2026-10-28',
        license='BSD-3-Clause',
        access_label='Open source',
        contribution=(
            'Informed separation between atmospheric model construction, multi-mode '
            'observables (transmission, emission, reflection), and statistical parameter '
            'inference. Studied as reference architecture; not bundled.'
        ),
        ecas_components=('ecas/comparison/forward_model.py', 'docs/SCIENTIFIC_COMPARISON_AND_INTERPRETATION.md'),
        citation='MacDonald, R. J. 2023, JOSS, 8(81), 4873; MacDonald, R. J. & Madhusudhan, N. 2017, MNRAS, 469, 1979.',
        verification_status='verified_canonical_metadata',
        notes_and_limitations='Requires precomputed opacity grids not distributed with ECAS.',
    ),
    ScientificResource(
        resource_id='taurex3',
        title='TauREx 3',
        category='Software',
        resource_type='software',
        authors_or_organization='Al-Refaie, A. F., Changeat, Q., Waldmann, I. P., & Tinetti, G. (UCL)',
        description='Extensible Bayesian inverse-modeling and atmospheric retrieval framework',
        canonical_url='https://taurex3-public.readthedocs.io/en/latest/',
        doi='10.3847/1538-4357/ac0252',
        version_or_release='3.x documentation referenced',
        publication_date='2021-08',
        access_date='2026-10-28',
        license='BSD-3-Clause',
        access_label='Open source',
        contribution=(
            'Informed modular separation between forward-model configuration, chemistry '
            'assumptions, and external adapter contracts (`from_taurex_export`). Not bundled.'
        ),
        ecas_components=('ecas/comparison/forward_model.py', 'ecas/comparison/model_adapters.py'),
        citation='Al-Refaie, A. F., Changeat, Q., Waldmann, I. P., & Tinetti, G. 2021, ApJ, 917, 37. doi:10.3847/1538-4357/ac0252',
        verification_status='verified_canonical_metadata',
        notes_and_limitations='Bayesian evidence comparisons remain conditional on model family and prior volumes.',
    ),
    ScientificResource(
        resource_id='platon',
        title='PLATON',
        category='Software',
        resource_type='software',
        authors_or_organization='Zhang, M., Chachan, Y., Kempton, E. M.-R., Knutson, H. A., & Chang, W.',
        description='Fast exoplanet transit and eclipse forward modeling and retrieval',
        canonical_url='https://platon.readthedocs.io/en/latest/',
        doi='10.3847/1538-4357/ab9d1c',
        version_or_release='6.x documentation referenced',
        publication_date='2020-08',
        access_date='2026-10-28',
        license='GPL-3.0',
        access_label='Open source',
        contribution=(
            'Informed compact forward-model input specifications, bin-integrated '
            'instrument response handling, and external PLATON curve ingestion. '
            'No GPL source code is copied into ECAS.'
        ),
        ecas_components=('ecas/comparison/alignment.py', 'ecas/comparison/model_adapters.py'),
        citation='Zhang, M., Chachan, Y., Kempton, E. M.-R., Knutson, H. A., & Chang, W. 2020, ApJ, 899, 27. doi:10.3847/1538-4357/ab9d1c',
        verification_status='verified_canonical_metadata',
        notes_and_limitations='GPL-3.0 license requires keeping PLATON as an external process/file producer rather than copying code.',
    ),
    ScientificResource(
        resource_id='pyratbay',
        title='Pyrat Bay',
        category='Software',
        resource_type='software',
        authors_or_organization='Cubillos, P. E. & Blecic, J.',
        description='Python radiative-transfer, line sampling, and Bayesian retrieval toolkit',
        canonical_url='https://pyratbay.readthedocs.io/en/latest/',
        doi='10.1093/mnras/stab1405',
        version_or_release='2.x documentation referenced',
        publication_date='2021-05',
        access_date='2026-10-28',
        license='GPL-2.0',
        access_label='Open source',
        contribution=(
            'Informed line-list sampling vs cross-section distinctions and multi-stage '
            'radiative-transfer provenance tracking. Studied as reference only.'
        ),
        ecas_components=('docs/SCIENTIFIC_COMPARISON_AND_INTERPRETATION.md',),
        citation='Cubillos, P. E. & Blecic, J. 2021, MNRAS, 505, 2675. doi:10.1093/mnras/stab1405',
        verification_status='verified_canonical_metadata',
        notes_and_limitations='GPL-2.0 licensed; studied for methodology only, with zero code reuse.',
    ),
    ScientificResource(
        resource_id='nasa-exoplanet-archive',
        title='NASA Exoplanet Archive',
        category='Data archive',
        resource_type='archive',
        authors_or_organization='NASA Exoplanet Science Institute (NExScI) / Caltech-IPAC',
        description='Planet parameters and published atmospheric spectra',
        canonical_url='https://exoplanetarchive.ipac.caltech.edu/',
        doi='10.26133/NEA36',
        version_or_release='Atmospheric Spectroscopy Table & TAP service',
        publication_date='2023-01',
        access_date='2026-10-28',
        license='Public archive / NASA open data policy (attribution required)',
        access_label='Open source',
        contribution=(
            'Primary source for confirmed planet alias resolution, published transmission '
            'spectra discovery, and IPAC .tbl spectral ingestion in ECAS.'
        ),
        ecas_components=(
            'ecas/ingestion/nasa_discovery.py',
            'ecas/ingestion/nasa_aliases.py',
            'ecas/ingestion/nasa_archive.py',
            'ecas/ingestion/nasa_table.py',
            'ecas/ui/nasa_browser.py',
        ),
        citation='NASA Exoplanet Archive, Atmospheric Spectroscopy Table, Caltech/IPAC, doi:10.26133/NEA36; Akeson et al. 2013, PASP, 125, 989.',
        verification_status='verified_canonical_metadata',
        notes_and_limitations='Multiple reductions of the same observation exist; always cite both the archive DOI and the original measurement paper.',
    ),
    ScientificResource(
        resource_id='stsci-mast',
        title='Mikulski Archive for Space Telescopes (MAST)',
        category='Data archive',
        resource_type='archive',
        authors_or_organization='Space Telescope Science Institute (STScI)',
        description='Mission archive for JWST, HST, and TESS raw and calibrated data products',
        canonical_url='https://archive.stsci.edu/',
        doi=None,
        version_or_release='JWST / HST archive services',
        publication_date='2024-01',
        access_date='2026-10-28',
        license='Public mission archive (STScI / NASA data policy)',
        access_label='Open source',
        contribution=(
            'Informed FITS binary-table and ECSV spectral format requirements and the '
            'distinction between raw, calibrated, and extracted 1D science spectra.'
        ),
        ecas_components=('ecas/ingestion/tabular_formats.py',),
        citation='Space Telescope Science Institute (STScI), Mikulski Archive for Space Telescopes (MAST), https://archive.stsci.edu/',
        verification_status='verified_canonical_metadata',
        notes_and_limitations='MAST observations contain multiple calibration levels (Stage 1/2/3); do not treat unextracted exposures as 1D planetary spectra.',
    ),
    ScientificResource(
        resource_id='exoplanet-eu',
        title='Extrasolar Planets Encyclopaedia (Exoplanet.eu)',
        category='Data archive',
        resource_type='archive',
        authors_or_organization='Schneider, J. & Paris Observatory team',
        description='Independent catalog of exoplanet and host-star parameters with VO/TAP access',
        canonical_url='https://exoplanet.eu/',
        doi='10.1051/0004-6361/201116713',
        version_or_release='Dynamic VO/TAP catalog',
        publication_date='2011-08',
        access_date='2026-10-28',
        license='Open scientific catalog',
        access_label='Open source',
        contribution=(
            'Reference for independent catalog cross-checking and Virtual Observatory '
            'interoperability planning.'
        ),
        ecas_components=('docs/Chunk_7/RESEARCH_AND_MODELING_FOUNDATION.md',),
        citation='Schneider, J., Dedieu, C., Le Sidaner, P., Savalle, R., & Zolotukhin, I. 2011, A&A, 532, A79.',
        verification_status='verified_canonical_metadata',
        notes_and_limitations='Catalog inclusion criteria and parameter values can differ from NASA Exoplanet Archive.',
    ),
    ScientificResource(
        resource_id='cds-vizier',
        title='VizieR Catalogue Service',
        category='Data archive',
        resource_type='archive',
        authors_or_organization='Centre de Données astronomiques de Strasbourg (CDS)',
        description='Published astronomical data tables and paper-associated spectral catalogs',
        canonical_url='https://vizier.cds.unistra.fr/',
        doi='10.26093/cds/vizier',
        version_or_release='CDS VizieR service',
        publication_date='2000-04',
        access_date='2026-10-28',
        license='Open academic archive',
        access_label='Open source',
        contribution='Reference for published paper table formats (ASCII/TSV/VOTable/FITS) and provenance retention.',
        ecas_components=('ecas/ingestion/tabular_formats.py',),
        citation='Ochsenbein, F., Bauer, P., & Marcout, J. 2000, A&AS, 143, 23. doi:10.26093/cds/vizier',
        verification_status='verified_canonical_metadata',
        notes_and_limitations='Each VizieR catalog has paper-specific units and column definitions that must be inspected.',
    ),
    ScientificResource(
        resource_id='nasa-ads',
        title='NASA Astrophysics Data System (ADS)',
        category='Data archive',
        resource_type='archive',
        authors_or_organization='Smithsonian Astrophysical Observatory / NASA',
        description='Bibliographic archive for peer-reviewed astrophysics and characterization papers',
        canonical_url='https://ui.adsabs.harvard.edu/',
        doi=None,
        version_or_release='ADS modern interface',
        publication_date='2000-04',
        access_date='2026-10-28',
        license='Public bibliographic service',
        access_label='Open source',
        contribution=(
            'Used to resolve bibcode links in NASA transmission tables and trace '
            'published molecular evidence classifications to primary papers.'
        ),
        ecas_components=('ecas/ui/source_links.py', 'ecas/ui/project_labels.py'),
        citation='Kurtz, M. J., Eichhorn, G., Accomazzi, A., et al. 2000, A&AS, 143, 41.',
        verification_status='verified_canonical_metadata',
        notes_and_limitations='Bibliographic metadata must be checked against the full text of the primary paper.',
    ),
    ScientificResource(
        resource_id='exomol',
        title='ExoMol',
        category='Molecular data',
        resource_type='molecular_database',
        authors_or_organization='Tennyson, J., Yurchenko, S. N., & UCL ExoMol group',
        description='Molecular line lists for opacity calculations',
        canonical_url='https://www.exomol.com/',
        doi='10.1016/j.jms.2016.05.002',
        version_or_release='Master index + UCL-4000 (CO2), POKAZATEL (H2O), MM (CH4)',
        publication_date='2016-09',
        access_date='2026-10-28',
        license='Open scientific data (cite ExoMol release + line-list paper)',
        access_label='Open source',
        contribution=(
            'Provides the public master catalogue and bounded zero-pressure Doppler-broadened '
            'absorption cross sections (CO2, H2O, CH4) retrieved and cached in ECAS.'
        ),
        ecas_components=(
            'ecas/ingestion/exomol_catalogue.py',
            'ecas/ingestion/exomol_product.py',
            'ecas/ingestion/exomol_reference_cache.py',
            'ecas/ui/molecular_browser.py',
        ),
        citation=(
            'Tennyson, J., Yurchenko, S. N., Al-Refaie, A. F., et al. 2016, J. Mol. Spectrosc., 327, 73; '
            'Yurchenko et al. 2020 (UCL-4000); Polyansky et al. 2018 (POKAZATEL); Yurchenko et al. 2024 (MM).'
        ),
        verification_status='verified_canonical_metadata',
        notes_and_limitations=(
            'Retrieved .sigma products are zero-pressure Doppler-only cross sections in '
            'cm^2/molecule on wavenumber cm^-1, not planetary transit-depth spectra.'
        ),
    ),
    ScientificResource(
        resource_id='hitran',
        title='HITRAN & HAPI',
        category='Molecular data',
        resource_type='molecular_database',
        authors_or_organization='Gordon, I. E. et al. / Center for Astrophysics | Harvard & Smithsonian',
        description='High-resolution molecular spectroscopic transition parameters and cross sections',
        canonical_url='https://hitran.org/',
        doi='10.1016/j.jqsrt.2021.107949',
        version_or_release='HITRAN2020',
        publication_date='2022-01',
        access_date='2026-10-28',
        license='Open access with registration/citation terms',
        access_label='Open source',
        contribution=(
            'Reference for terrestrial/moderate-temperature molecular line parameters '
            'and temperature-applicability boundaries.'
        ),
        ecas_components=('ecas/resources/catalog.py',),
        citation='Gordon, I. E., Rothman, L. S., Hargreaves, R. J., et al. 2022, JQSRT, 277, 107949. doi:10.1016/j.jqsrt.2021.107949',
        verification_status='verified_canonical_metadata',
        notes_and_limitations='Standard HITRAN line lists are optimized near 296 K and can omit hot bands needed above ~500-700 K.',
    ),
    ScientificResource(
        resource_id='hitemp',
        title='HITEMP',
        category='Molecular data',
        resource_type='molecular_database',
        authors_or_organization='Rothman, L. S., Hargreaves, R. J., Gordon, I. E., et al. (CfA)',
        description='High-temperature molecular spectroscopic database for hot planetary atmospheres',
        canonical_url='https://hitran.org/hitemp/',
        doi='10.1016/j.jqsrt.2010.05.001',
        version_or_release='HITEMP2010 / 2020 updates',
        publication_date='2010-10',
        access_date='2026-10-28',
        license='Open scientific access (citation required)',
        access_label='Open source',
        contribution=(
            'Reference for high-temperature opacity completeness comparisons alongside '
            'ExoMol in hot-Jupiter forward modeling.'
        ),
        ecas_components=('ecas/resources/catalog.py',),
        citation='Rothman, L. S., Gordon, I. E., Barber, R. J., et al. 2010, JQSRT, 111, 2139. doi:10.1016/j.jqsrt.2010.05.001',
        verification_status='verified_canonical_metadata',
        notes_and_limitations='Covers a focused subset of molecules (H2O, CO2, CO, NO, OH, NO2, CH4, N2O) rather than all species.',
    ),
    ScientificResource(
        resource_id='nist-asd',
        title='NIST Atomic Spectra Database',
        category='Molecular data',
        resource_type='molecular_database',
        authors_or_organization='National Institute of Standards and Technology (NIST)',
        description='Reference atomic transition wavelengths, energy levels, and oscillator strengths',
        canonical_url='https://physics.nist.gov/asd',
        doi='10.18434/T4W30F',
        version_or_release='NIST ASD v5.11',
        publication_date='2023-12',
        access_date='2026-10-28',
        license='US Government public work (attribution requested)',
        access_label='Open source',
        contribution='Reference for atomic alkali/metal lines (e.g. Na I, K I) in optical transmission spectroscopy.',
        ecas_components=('ecas/resources/catalog.py',),
        citation='Kramida, A., Ralchenko, Yu., Reader, J., & NIST ASD Team, NIST Atomic Spectra Database, doi:10.18434/T4W30F.',
        verification_status='verified_canonical_metadata',
        notes_and_limitations='Provides atomic transition data, not pressure-broadened planetary opacity tables.',
    ),
    ScientificResource(
        resource_id='astropy',
        title='Astropy',
        category='Python library',
        resource_type='library',
        authors_or_organization='The Astropy Collaboration',
        description='Astronomy tables, units, and FITS handling',
        canonical_url='https://www.astropy.org/',
        doi='10.3847/1538-4357/ac7c74',
        version_or_release='ECSV v1.0 & FITS BINTABLE conventions',
        publication_date='2022-08',
        access_date='2026-10-28',
        license='BSD-3-Clause',
        access_label='Open source',
        contribution=(
            'Defines the ECSV v1.0 header specification and FITS binary-table conventions '
            'supported by ECAS tabular format ingestion.'
        ),
        ecas_components=('ecas/ingestion/tabular_formats.py',),
        citation='Astropy Collaboration, Price-Whelan, A. M., Lim, P. L., et al. 2022, ApJ, 935, 167. doi:10.3847/1538-4357/ac7c74',
        verification_status='verified_canonical_metadata',
        notes_and_limitations='ECAS implements a bounded, dependency-light ECSV and FITS BINTABLE reader without requiring full astropy runtime installation.',
    ),
    ScientificResource(
        resource_id='numpy',
        title='NumPy',
        category='Python library',
        resource_type='library',
        authors_or_organization='Harris, C. R. et al. / NumPy Developers',
        description='Numerical arrays, linear algebra, Cholesky factorization, and trapezoidal quadrature',
        canonical_url='https://numpy.org/doc/stable/',
        doi='10.1038/s41586-020-2649-2',
        version_or_release='2.5.4 (installed in ECAS environment)',
        publication_date='2020-09',
        access_date='2026-10-28',
        license='BSD-3-Clause',
        access_label='Open source',
        contribution=(
            'Powers residual vector arithmetic, Cholesky covariance whitening, and '
            'piecewise-linear top-hat bin integration in ECAS.'
        ),
        ecas_components=(
            'ecas/comparison/residuals.py',
            'ecas/comparison/alignment.py',
            'ecas/comparison/candidates.py',
        ),
        citation='Harris, C. R., Millman, K. J., van der Walt, S. J., et al. 2020, Nature, 585, 357. doi:10.1038/s41586-020-2649-2',
        verification_status='verified_canonical_metadata',
        notes_and_limitations='Recorded in comparison record software_environment provenance.',
    ),
    ScientificResource(
        resource_id='retrieval-challenges-2026',
        title='Computational challenges in exoplanet atmospheric retrieval',
        category='Publication',
        resource_type='publication',
        authors_or_organization='Springer Nature review (2026)',
        description='Retrieval methodology and computational limitations',
        canonical_url='https://doi.org/10.1007/s41115-026-00031-9',
        doi='10.1007/s41115-026-00031-9',
        version_or_release='2026 review article',
        publication_date='2026',
        access_date='2026-10-28',
        license='Open source',
        access_label='Open source',
        contribution=(
            'Informed ECAS conceptual distinction between forward modeling, likelihood '
            'evaluation, posterior degeneracies, and Bayesian model comparison.'
        ),
        ecas_components=('docs/SCIENTIFIC_COMPARISON_AND_INTERPRETATION.md', 'docs/Chunk_7/RESEARCH_AND_MODELING_FOUNDATION.md'),
        citation='Computational challenges in exoplanet atmospheric retrieval (2026), Living Reviews / Springer Nature, doi:10.1007/s41115-026-00031-9.',
        verification_status='verified_canonical_metadata',
        notes_and_limitations='Methodological review; ECAS does not claim to implement full posterior retrieval.',
    ),
    ScientificResource(
        resource_id='wasp39b-feinstein-2023',
        title='Early Release Science of the exoplanet WASP-39b with JWST NIRISS',
        category='Publication',
        resource_type='publication',
        authors_or_organization='Feinstein, A. D. et al. (JWST Transiting Exoplanet Community ERS Team)',
        description='JWST NIRISS/SOSS 0.6–2.8 um transmission spectrum of WASP-39 b',
        canonical_url='https://doi.org/10.1038/s41586-022-05674-1',
        doi='10.1038/s41586-022-05674-1',
        version_or_release='Nature 614, 670–675 (2023)',
        publication_date='2023-02',
        access_date='2026-10-28',
        license='Published scientific article & public NASA archive table',
        access_label='Open access',
        contribution=(
            'Primary real-data observational benchmark fixture (`data/NASA/2026-10-27/feinstein-2023.tbl`, '
            '331 points) used in ECAS ingestion, project storage, and comparison tests.'
        ),
        ecas_components=('data/NASA/2026-10-27/feinstein-2023.tbl', 'ecas/ingestion/nasa_table.py'),
        citation='Feinstein, A. D., Radica, M., Welbanks, L., et al. 2023, Nature, 614, 670. doi:10.1038/s41586-022-05674-1',
        verification_status='verified_canonical_metadata',
        notes_and_limitations='Contains signed asymmetric error columns (pl_trandeperr1/2) that ECAS preserves without symmetrizing.',
    ),
    ScientificResource(
        resource_id='wasp39b-carter-2024',
        title='A benchmark JWST near-infrared spectrum for the exoplanet WASP-39 b',
        category='Publication',
        resource_type='publication',
        authors_or_organization='Carter, A. L., May, E. M., et al. (JWST ERS Team)',
        description='Synthesized multi-instrument JWST near-infrared transmission benchmark for WASP-39 b',
        canonical_url='https://www.nature.com/articles/s41550-024-02292-x',
        doi='10.1038/s41550-024-02292-x',
        version_or_release='Nature Astronomy (2024)',
        publication_date='2024-07',
        access_date='2026-10-28',
        license='Published scientific article',
        access_label='Open access',
        contribution=(
            'Informed ECAS multi-instrument wavelength-coverage, instrument-offset, '
            'and reduction-consistency benchmark guidelines.'
        ),
        ecas_components=('docs/Chunk_7/RESEARCH_AND_MODELING_FOUNDATION.md',),
        citation='Carter, A. L., May, E. M., Espinoza, N., et al. 2024, Nature Astronomy, 8, 1008. doi:10.1038/s41550-024-02292-x',
        verification_status='verified_canonical_metadata',
        notes_and_limitations='Demonstrates that combining instruments or reductions requires accounting for systematic offsets and instrument responses.',
    ),
)

for _res in _CATALOG:
    _verify_clean_https_url(_res.canonical_url)
    if _res.category not in CATEGORY_FILTERS[1:]:
        raise ValueError(f'Unknown category {_res.category!r} on {_res.resource_id}')


_MOLECULAR_DATABASES: tuple[MolecularDatabaseSpec, ...] = (
    MolecularDatabaseSpec(
        database_id='exomol',
        name='ExoMol',
        data_types=('line_list', 'cross_section', 'partition_function', 'k_table'),
        typical_temperature_max_k=4000.0,
        primary_use='Hot exoplanet, brown-dwarf, and cool-star atmospheres (up to 2000–5000 K depending on line list).',
        canonical_url='https://www.exomol.com/',
        citation='Tennyson et al. (2016, 2020, 2024)',
        limitations='Public .sigma web service returns zero-pressure Doppler-broadened cross sections only.',
    ),
    MolecularDatabaseSpec(
        database_id='hitran',
        name='HITRAN',
        data_types=('line_list', 'experimental_cross_section', 'cia'),
        typical_temperature_max_k=500.0,
        primary_use='Terrestrial and temperate atmospheres near 296 K.',
        canonical_url='https://hitran.org/',
        citation='Gordon et al. (2022), JQSRT 277, 107949',
        limitations='Incomplete hot-band transitions at elevated temperatures (> 500–700 K); use HITEMP or ExoMol for hot Jupiters.',
    ),
    MolecularDatabaseSpec(
        database_id='hitemp',
        name='HITEMP',
        data_types=('line_list',),
        typical_temperature_max_k=3000.0,
        primary_use='High-temperature gas-giant and stellar atmospheres for covered molecules (H2O, CO2, CO, CH4, NO, OH, N2O, NO2).',
        canonical_url='https://hitran.org/hitemp/',
        citation='Rothman et al. (2010); Hargreaves et al. (2020)',
        limitations='Available for 8 molecules only; large line-list files require line-sampling or correlated-k precomputation.',
    ),
    MolecularDatabaseSpec(
        database_id='nist-asd',
        name='NIST Atomic Spectra Database',
        data_types=('atomic_line_list', 'energy_levels'),
        typical_temperature_max_k=10000.0,
        primary_use='Atomic transitions (e.g., Na I, K I, H, Fe) in optical/UV transmission and high-resolution spectroscopy.',
        canonical_url='https://physics.nist.gov/asd',
        citation='Kramida et al., NIST ASD',
        limitations='Does not provide molecular rovibrational bands or H2/He pressure-broadened wing profiles.',
    ),
    MolecularDatabaseSpec(
        database_id='geisa',
        name='GEISA',
        data_types=('line_list', 'cross_section'),
        typical_temperature_max_k=500.0,
        primary_use='Planetary and Earth atmospheric spectroscopy cross-comparison.',
        canonical_url='https://geisa.aeris-data.fr/',
        citation='Delahaye et al. (2021), J. Mol. Spectrosc. 380, 111510',
        limitations='Primarily curated for Earth and solar-system planetary temperatures unless paired with high-T extensions.',
    ),
)


_BENCHMARK_PLANETS: tuple[BenchmarkPlanetRecord, ...] = (
    BenchmarkPlanetRecord(
        planet_name='WASP-39 b',
        host_star='WASP-39',
        primary_modes=('transmission_spectroscopy',),
        why_benchmark='JWST Early Release Science benchmark with NIRISS/SOSS, NIRSpec PRISM/G395H, and NIRCam coverage (0.6–5.5 um).',
        main_research_direction='Molecular features (H2O, CO2, SO2, CO, Na), photochemistry, clouds, and cross-instrument retrieval consistency.',
        key_publications=(
            'Feinstein et al. 2023, Nature 614, 670 (NIRISS/SOSS)',
            'JWST Transiting Exoplanet Community ERS Team 2023, Nature 614, 649 (NIRSpec PRISM)',
            'Alderson et al. 2023, Nature 614, 664 (NIRSpec G395H)',
            'Rustamkulov et al. 2023, Nature 614, 659 (PRISM SO2)',
            'Carter, May et al. 2024, Nature Astronomy 8, 1008 (synthesized benchmark)',
        ),
        species_assessments=(
            SpeciesEvidenceRecord(
                species='CO2',
                status='independent_confirmation',
                observing_mode='transmission_spectroscopy',
                instrument='JWST NIRSpec PRISM & G395H',
                publication='JWST ERS Team 2023, Nature 614, 649; Alderson et al. 2023, Nature 614, 664',
                doi='10.1038/s41586-022-05269-w',
                summary='Prominent 4.3 um absorption feature independently detected across NIRSpec modes and pipelines.',
                caveats='Inferred metallicity and C/O ratio remain conditional on radiative-transfer, cloud, and chemical assumptions.',
            ),
            SpeciesEvidenceRecord(
                species='H2O',
                status='independent_confirmation',
                observing_mode='transmission_spectroscopy',
                instrument='JWST NIRISS/SOSS, NIRSpec, NIRCam & HST',
                publication='Feinstein et al. 2023, Nature 614, 670; Ahrer et al. 2023, Nature 614, 653',
                doi='10.1038/s41586-022-05674-1',
                summary='Multiple near-infrared water absorption bands resolved from 0.9 to 3.0 um.',
                caveats='Band amplitudes are degenerate with cloud-deck pressure, haze slope, and reference radius.',
            ),
            SpeciesEvidenceRecord(
                species='SO2',
                status='independent_confirmation',
                observing_mode='transmission_spectroscopy',
                instrument='JWST NIRSpec PRISM & G395H',
                publication='Rustamkulov et al. 2023, Nature 614, 659; Tsai et al. 2023, Nature 617, 483',
                doi='10.1038/s41586-022-05677-y',
                summary='4.05 um absorption feature attributed to photochemically produced SO2.',
                caveats='Not predicted by thermochemical equilibrium alone; requires disequilibrium photochemistry modeling.',
            ),
            SpeciesEvidenceRecord(
                species='CH4',
                status='upper_limit_or_non_detection',
                observing_mode='transmission_spectroscopy',
                instrument='JWST NIRSpec & NIRCam',
                publication='Ahrer et al. 2023, Nature 614, 653; Alderson et al. 2023, Nature 614, 664',
                doi='10.1038/s41586-022-05590-4',
                summary='No statistically significant 3.3 um CH4 absorption peak detected; upper limits reported.',
                caveats='Upper limits depend on assumed temperature structure, metallicity, and vertical mixing (K_zz).',
            ),
        ),
    ),
    BenchmarkPlanetRecord(
        planet_name='K2-18 b',
        host_star='K2-18',
        primary_modes=('transmission_spectroscopy',),
        why_benchmark='Temperate sub-Neptune illustrating strong model degeneracy and the distinction between tentative claims and confirmed detections.',
        main_research_direction='CH4/CO2 retrievals, internal atmospheric scenarios (mini-Neptune vs Hycean), and sensitivity to priors/systematics.',
        key_publications=(
            'Madhusudhan et al. 2023, ApJL 955, L19 (JWST NIRISS + NIRSpec)',
            'Wogan et al. 2024, ApJL 963, L7 (photochemical & interior modeling alternatives)',
        ),
        species_assessments=(
            SpeciesEvidenceRecord(
                species='CH4',
                status='reported_detection',
                observing_mode='transmission_spectroscopy',
                instrument='JWST NIRISS/SOSS & NIRSpec G395H',
                publication='Madhusudhan et al. 2023, ApJL 955, L19',
                doi='10.3847/2041-8213/acf577',
                summary='Reported absorption features attributed to CH4 in transmission spectra.',
                caveats='Abundance constraints and bulk atmospheric interpretation remain model-dependent.',
            ),
            SpeciesEvidenceRecord(
                species='DMS',
                status='tentative_or_disputed',
                observing_mode='transmission_spectroscopy',
                instrument='JWST NIRISS/SOSS & NIRSpec G395H',
                publication='Madhusudhan et al. 2023, ApJL 955, L19',
                doi='10.3847/2041-8213/acf577',
                summary='Marginal/tentative inference only; not a robust or independently confirmed detection.',
                caveats='Sensitive to instrumental offset treatment, noise realization, and alternative molecular/atmospheric models.',
            ),
        ),
    ),
)


def resource_catalog() -> tuple[ScientificResource, ...]:
    """Return the immutable tuple of verified scientific resources."""
    return _CATALOG


def get_resource(resource_id: str) -> ScientificResource:
    normalized = resource_id.strip().lower()
    if normalized.startswith('software-'):
        normalized = normalized[len('software-'):]
    for item in _CATALOG:
        if item.resource_id == resource_id or item.resource_id == normalized:
            return item
    raise KeyError(f'Unknown resource_id: {resource_id!r}')


def get_resource_by_id(resource_id: str) -> ScientificResource | None:
    try:
        return get_resource(resource_id)
    except KeyError:
        return None


def filter_resources(
    *,
    category: str = 'All',
    query: str = '',
    resources: tuple[ScientificResource, ...] = _CATALOG,
) -> tuple[ScientificResource, ...]:
    """Filter resources by category pill and case-insensitive substring query."""
    if category not in CATEGORY_FILTERS:
        raise ValueError(f'Unsupported category filter {category!r}; expected one of {CATEGORY_FILTERS}')
    needle = query.strip().lower()
    results: list[ScientificResource] = []
    for item in resources:
        if category != 'All' and item.category != category:
            continue
        if needle:
            haystack = ' '.join((
                item.resource_id,
                item.title,
                item.category,
                item.authors_or_organization,
                item.description,
                item.canonical_url,
                item.doi or '',
                item.contribution,
                ' '.join(item.ecas_components),
                item.citation,
            )).lower()
            if needle not in haystack:
                continue
        results.append(item)
    return tuple(results)


def molecular_databases() -> tuple[MolecularDatabaseSpec, ...]:
    return _MOLECULAR_DATABASES


def get_molecular_database_spec(database_name_or_id: str) -> MolecularDatabaseSpec | None:
    needle = database_name_or_id.strip().lower()
    for spec in _MOLECULAR_DATABASES:
        if spec.database_id == needle or spec.name.lower() == needle or needle in spec.name.lower():
            return spec
    return None


def validate_temperature_applicability(database_id: str, temperature_k: float) -> tuple[bool, str]:
    """Check whether a molecular database is suitable for a target atmospheric temperature."""
    if isinstance(temperature_k, bool) or not isinstance(temperature_k, (int, float)) or temperature_k <= 0:
        raise ValueError('temperature_k must be a positive number')
    spec = get_molecular_database_spec(database_id)
    if spec is None:
        raise KeyError(f'Unknown molecular database_id: {database_id!r}')
    if temperature_k <= spec.typical_temperature_max_k:
        return True, (
            f'{spec.name} is applicable at {temperature_k:g} K '
            f'(typical upper limit ~{spec.typical_temperature_max_k:g} K). {spec.limitations}'
        )
    return False, (
        f'Temperature {temperature_k:g} K exceeds {spec.name} typical upper applicability '
        f'(~{spec.typical_temperature_max_k:g} K): missing hot-band transitions may bias opacities. '
        f'{spec.limitations}'
    )


def benchmark_planets() -> tuple[BenchmarkPlanetRecord, ...]:
    return _BENCHMARK_PLANETS


def get_benchmark_planet(planet_name: str) -> BenchmarkPlanetRecord | None:
    needle = planet_name.strip().lower()
    for planet in _BENCHMARK_PLANETS:
        if planet.planet_name.lower() == needle:
            return planet
    return None


SCIENTIFIC_RESOURCES = _CATALOG
MOLECULAR_DATABASE_SPECS = _MOLECULAR_DATABASES
BENCHMARK_PLANETS = _BENCHMARK_PLANETS
