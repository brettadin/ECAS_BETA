"""Verified, bounded cross-section form protocols; no network side effects."""
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from types import MappingProxyType
import math
import re
from urllib.parse import urlencode, urlsplit

from .exomol_cross_section import CrossSectionProvenance, LICENCE_URL, ReferenceImportError, parse_cross_section

ORIGIN = 'https://www.exomol.com'
SERVICE_PATH = '/xsec/12C-16O2/'
SERVICE_URL = ORIGIN+SERVICE_PATH
CITATIONS = ('Hill, Yurchenko & Tennyson (2013), Icarus 226, 1673–1677',
             'Yurchenko et al. (2020), MNRAS 496, 5282–5291, UCL-4000',
             'Tennyson & Yurchenko (2012), MNRAS 425, 21–33, ExoMol')


@dataclass(frozen=True)
class ProductService:
    formula: str
    isotopologue: str
    dataset: str
    maximum_wavenumber: int
    maximum_temperature: int
    dataset_phrase: str
    citations: tuple[str, ...]

    @property
    def url(self):
        return ORIGIN + '/xsec/' + self.isotopologue + '/'


SERVICES = MappingProxyType({
    '12C-16O2': ProductService('CO2','12C-16O2','UCL-4000',20000,4000,
        'generated from the line list UCL-4000',CITATIONS),
    '1H2-16O': ProductService('H2O','1H2-16O','POKAZATEL',41200,5000,
        'generated from the POKAZATEL line list',
        (CITATIONS[0],'Polyansky et al. (2018), MNRAS 480, 2597–2608, POKAZATEL',CITATIONS[2])),
    '12C-1H4': ProductService('CH4','12C-1H4','MM',12000,2000,
        'generated from the MM line list',
        (CITATIONS[0],'Yurchenko et al. (2024), MNRAS 528, 3719–3729, MM',CITATIONS[2])),
})


@dataclass(frozen=True)
class ProductRequest:
    minimum: int
    maximum: int
    temperature: int
    spacing: str
    isotopologue: str = '12C-16O2'  # Missing in original v1 cache records: CO2.

    def __post_init__(self):
        if not isinstance(self.isotopologue, str) or self.isotopologue not in SERVICES:
            raise ReferenceImportError('Unsupported reference service identity')
        service = self.service
        if any(type(v) is not int for v in (self.minimum, self.maximum, self.temperature)):
            raise ReferenceImportError('Initial service support requires whole-number limits and temperature')
        if not 0<=self.minimum<self.maximum<=service.maximum_wavenumber or not 100<=self.temperature<=service.maximum_temperature:
            raise ReferenceImportError(f'{service.formula}: require 0–{service.maximum_wavenumber} cm^-1 '
                                       f'and 100–{service.maximum_temperature} K')
        if not isinstance(self.spacing,str) or len(self.spacing)>32 or not re.fullmatch(r'[0-9]+(?:\.[0-9]{1,6})?',self.spacing):
            raise ReferenceImportError('Require a positive decimal spacing string with at most six decimals')
        try:
            step = Decimal(self.spacing)
            intervals = Decimal(self.maximum-self.minimum)/step
            if not step.is_finite() or step<Decimal('0.000001') or step!=step.quantize(Decimal('0.000001')):
                raise ValueError('step')
            if intervals!=intervals.to_integral_value() or not 1<=intervals<=9999:
                raise ValueError('grid')
        except (InvalidOperation, ValueError, TypeError, ZeroDivisionError):
            raise ReferenceImportError('Require an exact inclusive grid of 2–10000 points and positive spacing with at most six decimals') from None
        object.__setattr__(self,'spacing',format(step,'.6f'))

    @property
    def service(self):
        return SERVICES[self.isotopologue]

    @property
    def parameters(self):
        return dict(dnu=self.spacing, numin=str(self.minimum), numax=str(self.maximum),
                    T=str(self.temperature), spoon_feed='on')

    @property
    def product_path(self):
        return f'/results/{self.isotopologue}_{self.minimum}-{self.maximum}_{self.temperature}K_{Decimal(self.spacing):.6f}.sigma'

    @property
    def point_count(self):
        return int(Decimal(self.maximum-self.minimum)/Decimal(self.spacing))+1


@dataclass(frozen=True)
class AnonymousForm:
    token: str = field(repr=False)

    def body(self, request):
        return urlencode(dict(request.parameters, csrfmiddlewaretoken=self.token)).encode('ascii')


def supported_entry(entry):
    service = SERVICES.get(entry.isotopologue)
    return service is not None and (entry.formula, entry.dataset) == (service.formula, service.dataset)


def _html(raw):
    if not isinstance(raw, bytes) or not raw or len(raw)>262144:
        raise ReferenceImportError('Require a nonempty product page within 256 KiB')
    try: return raw.decode('utf-8')
    except UnicodeError as error: raise ReferenceImportError('Product page is not UTF-8') from error


def parse_form(raw, isotopologue='12C-16O2'):
    if not isinstance(isotopologue,str) or isotopologue not in SERVICES:
        raise ReferenceImportError('Unsupported reference service identity')
    service = SERVICES[isotopologue]
    class FormParser(HTMLParser):
        def __init__(self): super().__init__(); self.active=False; self.forms=[]; self.current=None; self.text=[]
        def handle_data(self, data): self.text.append(data)
        def handle_starttag(self, tag, attrs):
            attributes=dict(attrs)
            if tag=='form':
                self.active=attributes.get('method','').lower()=='post'
                if self.active:
                    self.current=(attributes.get('action'), [])
                    self.forms.append(self.current)
            if tag=='input' and self.active:
                self.current[1].append(attributes)
        def handle_endtag(self, tag):
            if tag=='form': self.active=False
    parser=FormParser(); parser.feed(_html(raw))
    description=' '.join(' '.join(parser.text).split())
    compact=re.sub(r'\s+','',description)
    if (service.dataset_phrase not in description or 'zero-pressure' not in description or
        'Doppler-broadened lines only' not in description or 'cm2/molec' not in compact or 'cm-1' not in compact):
        raise ReferenceImportError('Service dataset, units or broadening description changed')
    if (f'(0-{service.maximum_wavenumber}cm-1)' not in compact or
            f'(100-{service.maximum_temperature}K)' not in compact):
        raise ReferenceImportError('Service temperature or wavenumber limits changed')
    if len(parser.forms)!=1 or parser.forms[0][0]!='/xsec/'+service.isotopologue+'/':
        raise ReferenceImportError('Unsupported cross-section form action')
    fields=parser.forms[0][1]
    named=[item['name'] for item in fields if 'name' in item]
    expected={'csrfmiddlewaretoken','dnu','numin','numax','T','spoon_feed'}
    if set(named)!=expected or len(named)!=len(expected):
        raise ReferenceImportError('Cross-section form fields changed')
    token=next(item.get('value','') for item in fields if item.get('name')=='csrfmiddlewaretoken')
    if not re.fullmatch('[A-Za-z0-9]{32,128}', token):
        raise ReferenceImportError('Missing anonymous anti-forgery state')
    return AnonymousForm(token)


def product_url(raw, request):
    class LinkParser(HTMLParser):
        def __init__(self): super().__init__(); self.links=[]
        def handle_starttag(self, tag, attrs):
            if tag=='a':
                link=dict(attrs).get('href','')
                if '.sigma' in link: self.links.append(link)
    parser=LinkParser(); parser.feed(_html(raw))
    expected=ORIGIN+request.product_path
    resolved=set()
    for link in parser.links:
        absolute=ORIGIN+link if link.startswith('/') and not link.startswith('//') else link
        if absolute != expected:
            raise ReferenceImportError('Response product does not match requested origin, identity or settings')
        resolved.add(absolute)
    if resolved!={expected}:
        raise ReferenceImportError('No matching two-column cross-section product returned')
    return expected


def validate_product(raw, request):
    service=request.service
    provenance=CrossSectionProvenance(service.formula,service.isotopologue,service.dataset,float(request.temperature),
        0.,'doppler_only',ORIGIN+request.product_path,service.citations,LICENCE_URL)
    product=parse_cross_section(raw,provenance)
    if len(product.points)!=request.point_count:
        raise ReferenceImportError('Product sample count does not match requested grid')
    step=Decimal(request.spacing)
    for index,(coordinate, _) in enumerate(product.points):
        expected=float(Decimal(request.minimum)+index*step)
        if not math.isclose(coordinate,expected,rel_tol=0,abs_tol=5e-7):
            raise ReferenceImportError('Product coordinates do not match requested grid')
    return product
