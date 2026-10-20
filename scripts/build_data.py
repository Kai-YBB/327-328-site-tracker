"""Build data/sites.json for the Carpentry Site Tracker from live open data.

Run from anywhere:  python3 scripts/build_data.py
Testing offline:    python3 scripts/build_data.py --cache <folder with saved raw responses>

Hand-entered records (Boston Employment Commission findings, City projects,
contractor union records, union local contacts) live in this file under the
sections marked MANUAL RECORDS. Edit those by hand when new BEC minutes or
agendas come out. See MAINTENANCE.md.

The script never overwrites data/sites.json with a result that looks broken:
if a source fails or returns far fewer sites than expected, it stops with an
error and the published page keeps the last good data.
"""
import json, math, os, re, sys, time, datetime, collections
import urllib.request, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "sites.json")
MAP_FILE = os.path.join(ROOT, "data", "map.json")
ARGS = sys.argv[1:]
CACHE = ARGS[ARGS.index("--cache") + 1] if "--cache" in ARGS else None
TODAY = datetime.date.today().isoformat()
UA = {"User-Agent": "carpentry-site-tracker/1.0 (weekly open data refresh)"}


def get_json(url, cache_name):
    """Fetch JSON from a public API, with retries. In --cache mode, read a saved file instead."""
    if CACHE:
        d = json.load(open(os.path.join(CACHE, cache_name)))
        return json.loads(d["rawHtml"]) if isinstance(d, dict) and "rawHtml" in d else d
    last = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # network hiccup or bad response; retry
            last = e
            time.sleep(10 * (attempt + 1))
    sys.exit(f"FETCH FAILED: {url}\n  {last}")


A80_URL = "https://gis.bostonplans.org/hosting/rest/services/Hosted/A80_project_points_all/FeatureServer/0/query"
A80_FIELDS = ("project_id,project__project_name,project_street_number,project_street_name,project_street_suffix,"
              "neighborhood,project_zip_code,project_status,project__record_type,last_filed_date,"
              "last_board_approved_date,coo_permit_date,total_residential_units,gross_square_footage,"
              "description,website_url,longitude,latitude,total_development_cost,display_on_web")


def a80(where, cache_name):
    q = urllib.parse.urlencode({"where": where, "outFields": A80_FIELDS, "returnGeometry": "false", "f": "json"})
    r = get_json(A80_URL + "?" + q, cache_name)
    if "error" in r:
        sys.exit(f"Boston Planning query error: {r['error']}")
    if r.get("exceededTransferLimit"):
        sys.exit("Boston Planning query returned too many records; add paging.")
    return r["features"]


# ---------------------------------------------------------------- sources
SRC = {
    "a80": {"label": "Boston Planning Department, Article 80 development projects (status: Permitted / Under Construction)",
            "url": "https://www.bostonplans.org/projects/development-projects", "date": TODAY},
    "bosHousing": {"label": "City of Boston, housing projects in construction (boston.gov)",
                   "url": "https://www.boston.gov/project-stage-bh/construction", "date": TODAY},
    "pfd": {"label": "City of Boston Public Facilities Department, projects in construction",
            "url": "https://www.boston.gov/departments/public-facilities/project-search", "date": TODAY},
    "camDevLog": {"label": "Cambridge Community Development Dept., Development Log 2026 Q2 (Building Permit Granted)",
                  "url": "https://www.cambridgema.gov/-/media/Files/CDD/FactsandMaps/DevelopmentLogs/developmentlog2026q2.pdf", "date": "2026-06-30"},
    "somPermits": {"label": "Somerville Inspectional Services, building permit applications (active permits, $2M and up)",
                   "url": "https://data.somervillema.gov/d/nneb-s3f7", "date": TODAY},
    "neuMaf": {"label": "Northeastern University, Multipurpose Athletics Facility construction page",
               "url": "https://pref.northeastern.edu/maf-construction", "date": TODAY},
}

BEC = {
    "m2024-07": ("BEC hearing minutes, July 17, 2024", "https://www.boston.gov/sites/default/files/file/2024/10/July%2017%5ELJ%202024_BEC%20Hearing%20Minutes_0.pdf", "2024-07-17"),
    "m2024-08": ("BEC hearing minutes, Aug 21, 2024", "https://www.boston.gov/sites/default/files/file/2024/10/August%2021%5ELJ%202024_BEC%20Hearing%20Minutes.pdf", "2024-08-21"),
    "m2024-09": ("BEC hearing minutes, Sept 18, 2024", "https://www.boston.gov/sites/default/files/file/2024/10/September%2018%2C%202024%5ELJ%202024_BEC%20Hearing%20Minutes.pdf", "2024-09-18"),
    "m2024-10": ("BEC hearing minutes, Oct 16, 2024", "https://www.boston.gov/sites/default/files/file/2024/12/October%2016%2C%202024%5ELJ%202024_BEC%20Hearing%20Minutes.pdf", "2024-10-16"),
    "m2024-11": ("BEC hearing minutes, Nov 20, 2024", "https://www.boston.gov/sites/default/files/file/2024/12/Nov20%2C%202024%5ELJ%202024_BEC%20Hearing%20Minutes.pdf", "2024-11-20"),
    "m2024-12": ("BEC hearing minutes, Dec 18, 2024", "https://www.boston.gov/sites/default/files/file/2025/07/December%2018%2C%202024%5ELJ%202024_BEC%20Hearing%20Minutes.pdf", "2024-12-18"),
    "m2025-01": ("BEC hearing minutes, Jan 15, 2025", "https://www.boston.gov/sites/default/files/file/2025/07/January%2015%2C%202025%5ELJ_BEC%20Hearing%20Minutes%20%283%29.pdf", "2025-01-15"),
    "m2025-02": ("BEC hearing minutes, Feb 19, 2025", "https://www.boston.gov/sites/default/files/file/2025/07/February%2019%2C%202025%5ELJ_BEC%20Hearing%20Minutes.docx.pdf", "2025-02-19"),
    "m2025-03": ("BEC hearing minutes, March 19, 2025", "https://www.boston.gov/sites/default/files/file/2025/07/March%2019%2C%202025%5ELJ_BEC%20Hearing%20Minutes.docx%20%281%29.pdf", "2025-03-19"),
    "m2025-04": ("BEC hearing minutes, April 16, 2025", "https://www.boston.gov/sites/default/files/file/2025/07/April%2016%2C%202025%5ELJ_BEC%20Hearing%20Minutes.docx%20%281%29.pdf", "2025-04-16"),
    "m2025-05": ("BEC hearing minutes, May 21, 2025", "https://www.boston.gov/sites/default/files/file/2025/07/May%2021%2C%202025_BEC%20Hearing%20Minutes.docx%20%281%29.pdf", "2025-05-21"),
    "m2025-06": ("BEC hearing minutes, June 18, 2025", "https://www.boston.gov/sites/default/files/file/2025/07/June%2018%2C%202025_BEC%20Hearing%20Minutes.docx%20%281%29.pdf", "2025-06-18"),
    "a2026-01": ("BEC agenda, Jan 21, 2026", "https://www.boston.gov/sites/default/files/file/2026/01/January%2021%2C%202026%5ELJ_BEC%20Agenda_Public%20Notice.docx.pdf", "2026-01-21"),
    "a2026-02": ("BEC agenda, Feb 18, 2026", "https://www.boston.gov/sites/default/files/file/2026/02/February%2018%2C%202026%5ELJ_BEC%20Agenda_Public%20Notice.docx%20%281%29.pdf", "2026-02-18"),
    "a2026-03": ("BEC agenda, March 18, 2026", "https://content.boston.gov/sites/default/files/file/2026/03/March%2018%2C%202026%5ELJ_BEC%20Agenda_Public%20Notice.docx.pdf", "2026-03-18"),
    "a2026-04": ("BEC agenda, April 15, 2026", "https://search.boston.gov/sites/default/files/file/2026/04/April%2015%2C%202026%5ELJ_BEC%20Agenda_Public%20Notice.docx%20%281%29.pdf", "2026-04-15"),
    "a2026-05": ("BEC agenda, May 20, 2026", "https://content.boston.gov/sites/default/files/file/2026/05/May%2020%2C%202026%5ELJ_BEC%20Agenda%20-%20Public%20Notice.docx%20%281%29.pdf", "2026-05-20"),
    "a2026-06": ("BEC agenda, June 17, 2026", "https://www.boston.gov/sites/default/files/file/2026/06/Employment.6.10.2026.pdf", "2026-06-17"),
    "a2026-07": ("BEC agenda, July 15, 2026", "https://www.boston.gov/sites/default/files/file/2026/07/BECH.7.13.2026.pdf", "2026-07-15"),
    "a2026-08": ("BEC agenda, Aug 19, 2026", "https://www.boston.gov/sites/default/files/file/2026/08/Employment.8.3.2026.pdf", "2026-08-19"),
    "a2026-09": ("BEC agenda, Sept 16, 2026", "https://search.boston.gov/sites/default/files/file/2026/09/September%2016%2C%202026%5ELJ_BEC%20Agenda_Public%20Notice.docx.pdf", "2026-09-16"),
}

def ev(ref, text):
    lab, url, date = BEC[ref]
    return {"src": lab, "url": url, "date": date, "text": text}

LOCAL_328_BOSTON = {"Allston", "Brighton", "Charlestown", "East Boston"}

def boston_local(nbhd):
    return "328" if nbhd in LOCAL_328_BOSTON else "327"

def clean(s):
    if not s:
        return ""
    s = s.replace("\r", " ").replace("\n", " ")
    s = s.replace("\u2014", ", ").replace("\u2013", "-")  # source text: swap em and en dashes
    s = re.sub(r"\s+", " ", s).strip()
    return s

def short(s, n=520):
    s = clean(s)
    if len(s) <= n:
        return s
    cut = s[:n].rsplit(" ", 1)[0]
    return cut.rstrip(",;:") + "..."

def money(v):
    if not v:
        return None
    return int(v)

# ------------------------------------------------------ Boston Article 80
# MANUAL RECORDS: Article 80 projects that BEC agendas show as active but the
# Planning Department list does not yet mark "Permitted / Under Construction".
EXTRA_A80_IDS = [3912, 4499, 4710]
pts = a80("project_status = 'Permitted / Under Construction'", "a80_points_raw.json")
other = a80("project_id IN (%s)" % ",".join(map(str, EXTRA_A80_IDS)), "a80_other_raw.json")
A = {f["attributes"]["project_id"]: f["attributes"] for f in pts + other}

def a80_site(pid, **over):
    a = A[pid]
    addr = " ".join(x for x in [a.get("project_street_number"), a.get("project_street_name"), a.get("project_street_suffix")] if x)
    nb = a["neighborhood"]
    if nb == "Boston":
        nb = "Downtown"
    s = {
        "id": f"bos-{pid}",
        "name": clean(a["project__project_name"]),
        "address": f"{clean(addr)}, Boston, MA {a.get('project_zip_code') or ''}".strip(),
        "city": "Boston",
        "area": nb,
        "local": boston_local(nb),
        "lat": round(a["latitude"], 6) if a.get("latitude") else None,
        "lng": round(a["longitude"], 6) if a.get("longitude") else None,
        "stage": "Under construction",
        "units": a.get("total_residential_units") or None,
        "sqft": a.get("gross_square_footage") or None,
        "cost": money(a.get("total_development_cost")),
        "approved": a.get("last_board_approved_date"),
        "coo": a.get("coo_permit_date"),
        "desc": short(a.get("description")),
        "size": "Large" if a.get("project__record_type") == "Large Project" else "Small",
        "link": a.get("website_url") or SRC["a80"]["url"],
        "linkLabel": "Planning Dept. project page",
        "source": "a80",
        "developer": None, "gc": None, "contractors": [], "labor": None, "laborNote": None,
        "laborRef": None, "bec": [], "notes": [], "permit": None,
    }
    if s["link"].startswith("http://"):
        s["link"] = "https://" + s["link"][7:]
    s.update(over)
    return s

sites = []
uc = [f["attributes"] for f in pts if f["attributes"]["project_status"] == "Permitted / Under Construction"]
for a in uc:
    if a.get("display_on_web") == 0:
        continue
    sites.append(a80_site(a["project_id"]))
by_id = {s["id"]: s for s in sites}

def attach(pid, gc=None, contractors=None, labor=None, laborNote=None, laborRef=None, bec=None, notes=None, developer=None):
    s = by_id.get(f"bos-{pid}")
    if s is None:  # project left the under-construction list (likely finished); its BEC notes are no longer shown
        print(f"note: project {pid} is no longer listed as under construction; skipped its manual record")
        return
    if gc: s["gc"] = gc
    if contractors: s["contractors"] += contractors
    if labor: s["labor"] = labor; s["laborNote"] = laborNote; s["laborRef"] = laborRef
    if bec: s["bec"] += bec
    if notes: s["notes"] += notes
    if developer: s["developer"] = developer

def C(name, role):
    return {"name": name, "role": role}

# BEC details matched to Article 80 projects
attach(3260, gc="Walsh Brothers",
       contractors=[C("Turner Construction", "Major subcontractor"), C("T.J. McCartney", "Carpentry"), C("Sullivan & McLaughlin", "Electrical")],
       labor="union", laborNote="Listed as Union (project name: MGH Cambridge Street).", laborRef="a2026-05",
       bec=[ev("a2026-05", "Project review, listed as Union."), ev("m2024-09", "15% complete; eight-year project. Walsh Brothers GC, Turner a major subcontractor, T.J. McCartney doing carpentry.")])
attach(4757, gc="Shawmut Design and Construction",
       bec=[ev("a2026-08", "Project review (listed as Boston University Towers)."), ev("m2024-12", "Phased 44-month renovation of an occupied building. Shawmut is GC.")])
attach(3303, gc="Skanska",
       labor="union", laborNote="Described as a union project.", laborRef="m2025-01",
       bec=[ev("a2026-01", "Project review."), ev("m2025-01", "Skanska presented; three-year project, 25% complete, about 20 contractors.")])
attach(4724, contractors=[C("Bond Building Construction", "Presented to the BEC")],
       bec=[ev("a2026-09", "Project review (7278 White Stadium Renovation Project)."), ev("m2024-09", "Special presentation. East grandstand expected to finish at the end of 2026.")])
attach(3600, gc="RISE Construction Management",
       contractors=[C("Scorpions Contracting", "Drywall, rough framing, tape and paint, MEP"), C("G&C Concrete", "Concrete"), C("Sunrise Erectors", "Facade and glazing"), C("J. Derenzo Company", "Sitework")],
       bec=[ev("a2026-07", "Project review."), ev("m2025-01", "Construction scheduled Nov 2024 to Aug 25, 2026, with interiors through July 2026.")],
       developer="Boston Residential Group")
attach(1488, gc="Wadleigh & Associates", contractors=[C("NEBS", "Framing and windows")],
       bec=[ev("m2025-01", "Estimated completion March 2026.")], developer="H Street Associates, LLC")
attach(3729, contractors=[C("NEI Contracting", "Presented to the BEC")],
       bec=[ev("m2024-10", "About 20 months of construction. Jamaica Plain NDC presented.")])
attach(4573, gc="Erise Builders", contractors=[C("Nicoya Construction", "Construction manager")],
       labor="open", laborNote="Listed as Non-Union (project name: Harvard Standish).", laborRef="m2025-03",
       bec=[ev("a2026-04", "Project review (Harvard Standish)."), ev("m2025-03", "Listed as Non-Union. Construction began late March 2025.")])
attach(3946, gc="Dellbrook JKS", developer="Viet-AID",
       bec=[ev("m2025-05", "Hamilton at Mt. Everett. Notice to proceed May 12, 2025.")],
       notes=["City housing list: Hamilton at Mt. Everett, 33 Hamilton Street."])
attach(4276, gc="John Moriarty & Associates",
       contractors=[C("G&C Concrete", "Concrete"), C("Island Exterior Fabricators", "Curtain wall"), C("The Welch Corp.", "Sitework"), C("American Plumbing", "Plumbing"), C("Otis Elevator", "Elevator")],
       bec=[ev("m2025-02", "Strider Hotel at Boston Landing. Certificate of occupancy planned for March 2027.")],
       developer="New Balance Development")
attach(4038, labor="open", laborNote="Listed as Open Shop.", laborRef="a2026-05",
       bec=[ev("a2026-05", "Special presentation, listed as Open Shop.")],
       notes=["City housing list: 775 Huntington Ave rental and ownership, Roxbury Tenants of Harvard Association."])
attach(3699, labor="open", laborNote="Listed as Open Shop.", laborRef="a2026-03",
       bec=[ev("a2026-03", "Special presentation and project review, listed as Open Shop.")])
attach(4296, bec=[ev("a2026-01", "Special presentation.")], developer="Lincoln Avenue Capital",
       notes=["City housing list: Residences at 1471 Blue Hill Ave."])
attach(4016, bec=[ev("a2026-02", "Project review (Boys & Girls Club Dorchester Field House).")])
attach(4186, bec=[ev("a2026-06", "Special presentation.")])
attach(4631, bec=[ev("a2026-08", "Special presentation.")])
attach(4298, bec=[ev("a2026-08", "Project review (Allston Post, 25-39 Harvard Ave.).")])
attach(3333, bec=[ev("a2026-09", "Special presentation (14 Ellington St. and 8 Old Rd).")],
       developer="Harvard Street Neighborhood Health Center", notes=["City housing list: 14 Ellington / 8 Old Rd."])
attach(4748, bec=[ev("a2026-09", "Special presentation (Mission Hill Pathway).")], developer="ODJ Dev LLC",
       notes=["City housing list: Mission Hill Pathway, 77 Terrace Street and 778-796 Parker Street."])
attach(2594, notes=["City housing list also shows 127 Amory Street (The Community Builders) and Amory Greene (Urban Edge) in construction on Amory Street."])
attach(4025, notes=["City housing list also shows NUBA Homes (Urbanica) in construction."], developer="Urbanica")
attach(4301, notes=["City housing list: Brooke House at Olmsted Village (2Life Communities)."])
attach(3500, notes=["City housing list: Plan Nubian, 75-81 Dudley (Madison Park Development Corporation)."], developer="Madison Park Development Corporation")
attach(4305, notes=["City housing list: 361 Centre Street, Blessed Sacrament (Pennrose)."], developer="Pennrose")
attach(4339, notes=["City housing list: McDevitt Senior Homes, 207-209 E St (South Boston NDC)."], developer="South Boston Neighborhood Development Corporation")
attach(4304, notes=["City housing list: 55 Hudson Street, Parcel R-1 (Asian Community Development Corporation)."], developer="Asian Community Development Corporation")
attach(4031, notes=["City housing list: Columbia Crossing (POAH)."], developer="Preservation of Affordable Housing (POAH)")
attach(3763, notes=["City housing list: 4200 Washington Street (Boston Communities, LLC)."])
attach(4510, notes=["City housing list: 247 Hancock Street (Arx Urban)."], developer="Arx Urban")

# Boston projects not in the Article 80 under-construction list
extra = []
extra.append(a80_site(3912, stage="Under construction",
    gc="Lee Kennedy Co. and HJ Russell (joint venture)", developer="WinnDevelopment (presented)",
    labor="open", laborNote="Listed as Open Shop on the March 2026 agenda. The April 2025 minutes list it under Non-Union, though the presenter called it a union project.", laborRef="a2026-03",
    bec=[ev("a2026-03", "Project review, listed as Open Shop."), ev("m2025-04", "Lee Kennedy and HJ Russell JV. Current phase due October 2026.")],
    notes=["The Planning Department list still shows this project as Under Review."]))
extra.append(a80_site(4499, stage="Starting now",
    labor="union", laborNote="Listed as Union (Mildred Hailey 2).", laborRef="a2026-03",
    bec=[ev("a2026-03", "Special presentation and project review (Mildred Hailey 2), listed as Union.")],
    notes=["The Planning Department list shows this project as Board Approved."]))
extra.append(a80_site(4710, stage="Starting now",
    bec=[ev("a2026-08", "Special presentation (Joslin Place, Dana-Farber hospital).")],
    notes=["The Planning Department list shows this project as Board Approved (June 2025)."]))

def manual(id_, name, address, area, local, lat, lng, stage, source, link, linkLabel, **kw):
    s = {"id": id_, "name": name, "address": address, "city": kw.pop("city", "Boston"), "area": area, "local": local,
         "lat": lat, "lng": lng, "stage": stage, "units": None, "sqft": None, "cost": None, "approved": None, "coo": None,
         "desc": "", "size": kw.pop("size", "Small"), "link": link, "linkLabel": linkLabel, "source": source,
         "developer": None, "gc": None, "contractors": [], "labor": None, "laborNote": None, "laborRef": None,
         "bec": [], "notes": [], "permit": None}
    s.update(kw)
    return s

extra.append(manual("bos-neu-maf", "Northeastern University Multipurpose Athletics Facility",
    "St. Botolph Street (former Matthews Arena site), Boston, MA 02115", "Fenway", "327", None, None,
    "Under construction", "neuMaf", SRC["neuMaf"]["url"], "Northeastern construction page", size="Large",
    gc="Suffolk Construction", desc="New athletics facility on the Matthews Arena site. Geothermal wells drilled first, then the building goes on top.",
    bec=[ev("a2026-04", "Special presentation (Northeastern University MAF).")],
    notes=["Exact street number not published on the construction page."]))
extra.append(manual("bos-pfd-necc", "BCYF North End Community Center", "471 Commercial Street, Boston, MA 02109", "North End", "327",
    42.367522, -71.053199, "Under construction", "pfd", "https://www.boston.gov/departments/public-facilities/project/north-end-community-center",
    "City project page", size="Large", desc="New community center next to Mirabella Pool, replacing the Nazzaro Community Center. Completion expected summer 2028.",
    developer="City of Boston", bec=[ev("a2026-07", "Special presentation.")]))
extra.append(manual("bos-pfd-grovehall", "BCYF Grove Hall Community Center", "40 Geneva Avenue, Boston, MA 02121", "Dorchester", "327",
    42.307793, -71.080556, "Under construction", "pfd", "https://www.boston.gov/departments/public-facilities/project/bcyf-grove-hall-community-center",
    "City project page", size="Small", sqft=41866, desc="41,866 sq ft community center with a pool and gym. Completion expected spring 2028.", developer="City of Boston"))
extra.append(manual("bos-pfd-ems", "EMS Seaport Station", "34 Drydock Avenue, Boston, MA 02210", "South Boston Waterfront", "327",
    42.344769, -71.031415, "Under construction", "pfd", "https://www.boston.gov/departments/public-facilities/project/emergency-medical-services-seaport-station",
    "City project page", cost=13000000, desc="New Emergency Medical Services station, $13 million budget. Completion expected winter 2026.", developer="City of Boston"))
extra.append(manual("bos-pfd-fclib", "Fields Corner Library", "1520 Dorchester Avenue, Boston, MA 02122", "Dorchester", "327",
    42.298689, -71.060559, "Under construction", "pfd", "https://www.boston.gov/departments/public-facilities/project/fields-corner-library",
    "City project page", sqft=14790, cost=30900000, gc="J&J Contractors", developer="City of Boston",
    desc="New two-story library, about 14,790 sq ft, replacing the 1960s building. City lists completion in 2026.",
    bec=[ev("a2026-04", "Project review (Fields Corner Library, 7246)."), ev("m2025-06", "J&J Contractors GC. Substantial completion May 2026, final completion July 2026.")]))
extra.append(manual("bos-pfd-26court", "26 Court Street full renovation", "26 Court Street, Boston, MA 02108", "Downtown", "327",
    42.359132, -71.059171, "Under construction", "pfd", "https://www.boston.gov/departments/public-facilities/project/26-court-street-full-renovation",
    "City project page", size="Large", gc="Shawmut Design and Construction", developer="City of Boston",
    laborNote="Described as both union and non-union, filed sub-bid job.", laborRef="m2024-12",
    bec=[ev("m2024-12", "Shawmut GC. Described as both union and non-union (file sub-bid). About 35% of work hours remained.")]))
extra.append(manual("bos-pfd-clougherty", "Clougherty Pool and bathhouse", "345 Bunker Hill Street, Boston, MA 02129", "Charlestown", "328",
    42.381649, -71.067936, "Under construction", "pfd", "https://www.boston.gov/departments/public-facilities/project/clougherty-pool-replacement-and-bathhouse-renovation",
    "City project page", gc="J&J Contractors", developer="City of Boston",
    labor="open", laborNote="Confirmed Open Shop by the BRJP construction monitor.", laborRef="m2024-08",
    bec=[ev("m2024-08", "Open Shop. J&J self-performs. Bathhouse phase was due June 2025; the city still lists it in construction.")]))
extra.append(manual("bos-mildred-ave", "30-32 Mildred Avenue", "30-32 Mildred Avenue, Boston, MA 02126", "Mattapan", "327",
    42.276214, -71.091692, "Starting now", "bosHousing", SRC["bosHousing"]["url"], "City housing list",
    developer="Norfolk Design & Construction LLC", bec=[ev("a2026-07", "Special presentation.")]))
extra.append(manual("bos-127-amory", "127 Amory Street", "127 Amory Street, Boston, MA 02119", "Roxbury", "327",
    42.319063, -71.100832, "Starting now", "bosHousing", SRC["bosHousing"]["url"], "City housing list",
    developer="The Community Builders", labor="open", laborNote="Listed as Open Shop.", laborRef="a2026-05",
    bec=[ev("a2026-05", "Special presentation and project review, listed as Open Shop.")],
    notes=["Same block as the 125 Amory Street Development."]))
extra.append(manual("bos-whb-capen", "Welcome Home Boston Phase II: Capen / Norfolk", "Capen Street and Norfolk Street, Mattapan, Boston, MA", "Mattapan", "327",
    None, None, "Starting now", "bosHousing", SRC["bosHousing"]["url"], "City housing list",
    developer="Codman Square Neighborhood Development Corporation", desc="City-supported homeownership on city-owned lots.",
    bec=[ev("a2026-02", "Special presentation.")], notes=["Lot numbers not published. Look for the job sign on these streets."]))
extra.append(manual("bos-whb-ballou", "Welcome Home Boston Phase II: Ballou / Selden", "Ballou Avenue and Selden Street, Boston, MA 02124", "Mattapan", "327",
    None, None, "Under construction", "bosHousing", SRC["bosHousing"]["url"], "City housing list",
    developer="Visionary Investors Building Equity, LLC", desc="City-supported homeownership on city-owned lots.",
    bec=[ev("a2026-06", "Project review (Ballou/Selden Street).")], notes=["Lot numbers not published. Look for the job sign on these streets."]))
extra.append(manual("bos-whb-erie", "Welcome Home Boston Phase I: Erie / Glenway", "Erie Street and Glenway Street, Boston, MA 02121", "Roxbury", "327",
    None, None, "Under construction", "bosHousing", SRC["bosHousing"]["url"], "City housing list",
    developer="African Community Economic Development of New England (ACEDONE)", desc="City-supported homeownership on city-owned lots.",
    bec=[ev("a2026-09", "Project review (Erie Glenway Street).")], notes=["Lot numbers not published. Look for the job sign on these streets."]))
for e in extra:
    if e["id"] in by_id:  # the Planning Dept. list caught up; merge the manual record into the live one
        live = by_id[e["id"]]
        for k in ("gc", "developer", "labor", "laborNote", "laborRef"):
            if e.get(k):
                live[k] = e[k]
        live["bec"] += e["bec"]
        continue
    sites.append(e)

# --------------------------------------------------------------- Cambridge
def cambridge():
    """The Development Log 'Current Edition' dataset gets a new id each quarter, so look it up by name."""
    ds_id, ds_name = "wjwg-93qh", "Development Log Current Edition 2026 Q2"
    if not CACHE:
        cat = get_json("https://api.us.socrata.com/api/catalog/v1?domains=data.cambridgema.gov&limit=50&q="
                       + urllib.parse.quote("Development Log Current Edition"), "cam_catalog.json")
        best = None
        for res in cat.get("results", []):
            nm = res["resource"]["name"]
            m = re.match(r"^Development Log Current Edition (\d{4}) Q(\d)$", nm.strip())
            if m and (best is None or (int(m[1]), int(m[2])) > best[0]):
                best = ((int(m[1]), int(m[2])), res["resource"]["id"], nm)
        if best:
            ds_id, ds_name = best[1], best[2]
    q = urllib.parse.urlencode({"$limit": 1000, "$select": "project_id,project_name,address,status,developer,neighborhood,project_type,permit_type,project_description,total_gfa,residential_units,building_permit,primary_use,latitude,longitude,note"})
    rows = get_json(f"https://data.cambridgema.gov/resource/{ds_id}.json?{q}", "cam_socrata_raw.json")
    SRC["camDevLog"] = {"label": f"Cambridge Community Development Dept., {ds_name} (Building Permit Granted)",
                        "url": f"https://data.cambridgema.gov/d/{ds_id}", "date": TODAY}
    return rows


cam = cambridge()
for r in cam:
    if r.get("status") != "Building Permit Granted":
        continue
    nb = re.sub(r"^\d+\s*-\s*", "", r.get("neighborhood") or "").strip()
    gfa = int(float(r.get("total_gfa") or 0)) or None
    units = int(float(r.get("residential_units") or 0)) or None
    s = manual(f"cam-{r['project_id']}", clean(r["project_name"]), f"{clean(r['address'])}, Cambridge, MA", "Cambridge", "328",
               float(r["latitude"]) if r.get("latitude") else None, float(r["longitude"]) if r.get("longitude") else None,
               "Building permit granted", "camDevLog", "https://www.cambridgema.gov/CDD/factsandmaps/developmentlog", "Cambridge Development Log",
               city="Cambridge", size="Large" if (gfa or 0) >= 50000 else "Small",
               sqft=gfa, units=units, developer=clean(r.get("developer")) or None,
               desc=short(r.get("project_description")), permit=("BP " + r["building_permit"]) if r.get("building_permit") else None)
    s["subarea"] = nb
    s["kind"] = clean(r.get("primary_use"))
    note = clean(r.get("note"))
    if note:
        s["notes"].append(short(note, 300))
    sites.append(s)

# --------------------------------------------------------------- Somerville
SOM_WHERE = ("application_type='Building Permit' AND status='Issued' AND estimated_construction_cost >= 2000000 "
             "AND issue_date >= '%sT00:00:00'" % (datetime.date.today() - datetime.timedelta(days=4 * 365)).isoformat())
som = get_json("https://data.somervillema.gov/resource/nneb-s3f7.json?" + urllib.parse.urlencode({
    "$limit": 5000, "$where": SOM_WHERE,
    "$select": "application_number,application_type,application_subtype,department,status,currently_active,application_address,"
               "application_latitude,application_longitude,application_neighborhood,issue_date,expiration_date,close_date,"
               "estimated_construction_cost,contractor_company,contractor_name,applicant_company_name,project_description_or_business_name"}),
    "som_raw.json")
groups = {}
for r in som:
    if r.get("application_type") != "Building Permit" or r.get("status") != "Issued":
        continue
    if str(r.get("currently_active")) not in ("1", "True", "true"):
        continue
    if "Repair" in (r.get("application_subtype") or ""):
        continue
    key = re.sub(r",\s*SOMERVILLE.*$", "", (r.get("application_address") or "").upper()).strip()
    groups.setdefault(key, []).append(r)
for key, rs in groups.items():
    top = max(rs, key=lambda x: float(x.get("estimated_construction_cost") or 0))
    total = max(float(x.get("estimated_construction_cost") or 0) for x in rs)
    if total < 2_000_000:
        continue
    addr = key.title().replace(" St", " St").replace(" Ave", " Ave")
    names = []
    for x in rs:
        for f, role in (("contractor_company", "Contractor on permit"), ("applicant_company_name", "Permit applicant")):
            v = clean(x.get(f))
            if v and v.lower() not in [n["name"].lower() for n in names]:
                names.append(C(v, role))
    desc = clean(top.get("project_description_or_business_name"))
    desc = re.sub(r"(?i)^(approved fee waiver attached[^A-Z]*|p&z [^:]*:\s*)", "", desc).strip()
    s = manual(f"som-{top['application_number']}", addr, f"{addr}, Somerville, MA", "Somerville", "328",
               float(top["application_latitude"]), float(top["application_longitude"]),
               "Building permit issued", "somPermits", "https://data.somervillema.gov/d/nneb-s3f7", "Somerville permit data",
               city="Somerville", size="Large" if total >= 10_000_000 else "Small", cost=int(total),
               contractors=names, desc=short(desc, 320),
               permit=", ".join(sorted(x["application_number"] for x in rs)))
    s["subarea"] = top.get("application_neighborhood") or ""
    s["kind"] = top.get("application_subtype")
    s["permitIssued"] = (top.get("issue_date") or "")[:10]
    s["permitExpires"] = (top.get("expiration_date") or "")[:10]
    sites.append(s)

# ------------------------------------------------------------ contractors
def K(key, name, aliases, evidence):
    return {"key": key, "name": name, "aliases": aliases, "evidence": evidence}

def E(label, ref, text):
    d = ev(ref, text) if ref in BEC else {"src": SRC[ref]["label"], "url": SRC[ref]["url"], "date": SRC[ref]["date"], "text": text}
    d["label"] = label
    return d

contractors = [
    K("shawmut", "Shawmut Design and Construction", ["shawmut"], [
        E("union", "m2024-12", "Described as signatory to the Laborers and Carpenters (26 Court Street review)."),
        E("union", "m2024-11", "GC on 100 South Campus Drive, described as a 100% union project."),
        E("info", "m2025-05", "GC on 175 North Harvard Street (mass timber).")]),
    K("gvw", "GVW Inc.", ["gvw"], [
        E("union", "m2025-04", "Listed as signatory with Carpenters Local 328, Laborers Local 22 and Masons Local 3 (PJ Kennedy School).")]),
    K("suffolk", "Suffolk Construction", ["suffolk construction"], [
        E("union", "m2024-11", "Called its 109 Brookline Ave job a union project."),
        E("union", "m2025-03", "GC on Landmark Phase III (421 Park Drive), listed as Union."),
        E("info", "neuMaf", "Listed as contractor for the Northeastern Multipurpose Athletics Facility.")]),
    K("dimeo", "Dimeo Construction", ["dimeo"], [
        E("union", "m2025-03", "Construction manager on 41 LaGrange Street, described as 100% union."),
        E("union", "m2024-10", "Old Colony Phase 6, described as 100% union."),
        E("union", "m2024-07", "Whittier Place Phase 3, described as a union project.")]),
    K("commodore", "Commodore Builders", ["commodore builders", "commodore"], [
        E("union", "m2024-11", "900 Morrissey Boulevard, described as a 100% union project.")]),
    K("turner", "Turner Construction", ["turner construction"], [
        E("union", "m2024-10", "Did carpentry and labor work on the Enterprise Research Center lab project, described as 100% union."),
        E("info", "m2025-06", "GC on Fan Pier Parcel H. A subcontractor there requested a Local 327 carpenter."),
        E("info", "m2024-09", "Major subcontractor on MGH Cambridge Street.")]),
    K("walsh", "Walsh Brothers", ["walsh brothers"], [
        E("union", "a2026-05", "GC on MGH Cambridge Street, listed as Union."),
        E("info", "m2024-09", "Named as GC on MGH Cambridge Street.")]),
    K("tjmccartney", "T.J. McCartney", ["mccartney"], [
        E("union", "a2026-05", "Carpentry contractor on MGH Cambridge Street, which is listed as Union."),
        E("info", "m2024-09", "Carpentry was the 4th largest trade on MGH Cambridge Street.")]),
    K("consigli", "Consigli Construction", ["consigli"], [
        E("info", "m2025-02", "GC on Enterprise Research Center projects in Allston, where Local 328 was referenced."),
        E("info", "m2025-06", "GC on Suffolk University, 101 Tremont Street.")]),
    K("riggs", "Riggs Contracting", ["riggs"], [
        E("info", "m2025-02", "Concrete and mass timber at the Enterprise Research Center; hires carpenter apprentices.")]),
    K("jma", "John Moriarty & Associates", ["moriarty"], [
        E("info", "m2025-02", "Construction manager on the Strider Hotel at Boston Landing.")]),
    K("leekennedy", "Lee Kennedy Co.", ["lee kennedy"], [
        E("open", "a2026-03", "Joint venture GC (with HJ Russell) on Mary Ellen McCormack, listed as Open Shop."),
        E("info", "m2025-04", "Same project listed under Non-Union in April 2025, though the presenter called it a union project.")]),
    K("hjrussell", "HJ Russell & Company", ["hj russell", "h.j. russell", "h j russell"], [
        E("open", "a2026-03", "Joint venture GC (with Lee Kennedy) on Mary Ellen McCormack, listed as Open Shop."),
        E("info", "m2025-04", "Carpentry described as HJ Russell's specialty on that project.")]),
    K("skanska", "Skanska", ["skanska"], [
        E("union", "m2025-01", "Simmons University project, described as a union project.")]),
    K("dellbrook", "Dellbrook JKS", ["dellbrook"], [
        E("info", "m2025-05", "GC on Hamilton at Mt. Everett, Dorchester.")]),
    K("rise", "RISE Construction Management", ["rise construction"], [
        E("info", "m2025-01", "GC on 55 India Street.")]),
    K("wadleigh", "Wadleigh & Associates", ["wadleigh"], [
        E("info", "m2025-01", "GC on 2 H Street.")]),
    K("nei", "NEI Contracting", ["nei contracting", "nei general contracting"], [
        E("open", "m2024-10", "Columbia West Preservation, described as open shop."),
        E("info", "m2024-10", "Presented on Cheney Street Apartments.")]),
    K("baldhill", "Bald Hill Builders", ["bald hill"], [
        E("open", "m2024-08", "Bartlett Station, described as Open Shop / Section 3.")]),
    K("jj", "J&J Contractors", ["j&j contractors", "j & j contractors", "j&j contractor", "j & j contractor"], [
        E("open", "m2024-08", "Clougherty Pool confirmed Open Shop; J&J self-performs."),
        E("info", "m2025-06", "GC on Fields Corner Library.")]),
    K("reycon", "ReyCon Construction", ["reycon"], [
        E("open", "m2024-09", "44-46 Soldiers Field Place, described as open shop.")]),
    K("erise", "Erise Builders", ["erise"], [
        E("open", "m2025-03", "Harvard Standish, listed as Non-Union.")]),
    K("nicoya", "Nicoya Construction", ["nicoya", "necoya"], [
        E("open", "m2025-03", "Construction manager on Harvard Standish, listed as Non-Union.")]),
    K("stronghand", "Strong Hand General Construction", ["strong hand"], [
        E("open", "m2025-02", "Carpentry on 405 Washington Street, described as an open shop job.")]),
    K("bond", "Bond Building Construction", ["bond building"], [
        E("info", "m2024-09", "Presented the White Stadium renovation.")]),
    K("haycon", "Haycon", ["haycon"], [
        E("info", "m2025-05", "GC on 273 Highland Street."),
        E("info", "m2024-07", "GC on Stonley Brookley, with J&R Carpentry doing carpentry.")]),
    K("metric", "Metric Construction", ["metric construction"], [
        E("info", "m2024-09", "GC on 36-40 Sprague Street.")]),
    K("eci", "East Coast Interiors / Millwork One", ["east coast interiors", "millwork one", "eci"], [
        E("union", "m2025-03", "Interior finish carpentry on 41 LaGrange Street, described as 100% union."),
        E("union", "m2024-10", "Finish carpentry (ECI) on Old Colony Phase 6, described as 100% union.")]),
    K("century", "Century Drywall", ["century drywall"], [
        E("union", "m2025-03", "Drywall and acoustical ceilings on 41 LaGrange Street, described as 100% union.")]),
    K("hcarr", "H. Carr & Sons", ["h. carr", "h carr", "hcarr"], [
        E("union", "m2024-10", "Metal studs, drywall and fireproofing on Old Colony Phase 6, described as 100% union."),
        E("union", "m2025-04", "Acoustical ceilings on the PJ Kennedy School, where the GC (GVW) is signatory with Carpenters Local 328.")]),
    K("tara", "Tara (rough carpentry)", ["tara"], [
        E("union", "m2024-10", "Rough carpentry and framing on Old Colony Phase 6, described as 100% union.")]),
    K("gcconcrete", "G&C Concrete", ["g&c concrete", "g & c concrete", "gc concrete"], [
        E("union", "m2025-03", "Concrete on 41 LaGrange Street, described as 100% union."),
        E("info", "m2025-06", "Requested a Local 327 carpenter on Fan Pier Parcel H.")]),
    K("sfconcrete", "S&F Concrete", ["s&f concrete", "s & f concrete"], [
        E("union", "m2024-10", "On the Enterprise Research Center lab project, described as 100% union."),
        E("union", "m2024-11", "On 109 Brookline Ave, described as a union project.")]),
    K("wlfrench", "W.L. French", ["w.l. french", "wl french", "w l french"], [
        E("union", "m2024-10", "On the Enterprise Research Center lab project, described as 100% union."),
        E("info", "m2025-05", "Mass timber work on 175 North Harvard Street.")]),
    K("scorpions", "Scorpions Contracting", ["scorpions"], [
        E("info", "m2025-01", "Drywall, rough framing, tape and paint on 55 India Street.")]),
    K("nebs", "NEBS", ["nebs"], [
        E("info", "m2025-01", "Framing and windows on 2 H Street.")]),
    K("frg", "FRG Contractor Corp.", ["frg contractor"], [
        E("open", "m2024-10", "Rough carpentry on Columbia West Preservation, described as open shop.")]),
    K("eagleprime", "Eagle Prime Corp.", ["eagle prime"], [
        E("open", "m2024-10", "Finish carpentry on Columbia West Preservation, described as open shop.")]),
    K("jrcarpentry", "J&R Carpentry", ["j&r carpentry", "j & r carpentry"], [
        E("info", "m2024-07", "Carpentry on Stonley Brookley (Haycon).")]),
    K("liberty", "Liberty Construction", ["liberty construction"], [
        E("union", "m2024-11", "Suffolk's self-performing arm on 109 Brookline Ave, described as a union project.")]),
    K("starlite", "Starlite Building Services", ["starlite", "starlight"], [
        E("union", "m2024-11", "Shawmut's self-perform superstructure crew on 100 South Campus Drive, described as 100% union.")]),
]

# --------------------------------------------------------------- map
# Town and neighborhood outlines are fixed; they were built once from US Census
# and Boston Planning Department boundaries and saved in data/map.json.
MAP = json.load(open(MAP_FILE))

# MANUAL RECORDS: start points for distance sorting
points = {
    "l327": {"name": "Local 327 hall", "address": "1252 Massachusetts Ave, Dorchester", "lat": 42.3218093, "lng": -71.0619873},
    "l328": {"name": "Local 328 hall", "address": "10 Holworthy Street, Cambridge", "lat": 42.3750625, "lng": -71.1502614},
}

locals_info = [
    {"local": "327", "name": "Carpenters Local 327", "address": "1252 Massachusetts Avenue, Dorchester, MA 02125",
     "phone": "617-379-5600", "email": "cbrady@nasrcc.org", "page": "https://www.nasrcc.org/local/local-327/",
     "people": [["District Manager", "Joe Walsh"], ["Organizing Manager", "John O'Connor"],
                ["Business Representatives", "Mark Dellascio, Grady Eason"],
                ["Organizers", "Frank Baxter, Ernie Belo, John Burrows, Cesar Rijo, Michelle Wright"],
                ["CREW Leaders", "Chris McDermott, Keisha Cambell"]],
     "covers": "Boston (except Allston, Brighton, Charlestown and East Boston), the Boston Harbor Islands, Dedham and Milton.",
     "meets": "Last Wednesday of the month, 5 PM, Florian Hall, 55 Hallet Street, Dorchester.", "asOf": "2026-10-16"},
    {"local": "328", "name": "Carpenters Local 328", "address": "10 Holworthy Street, Cambridge, MA 02138",
     "phone": "617-391-9545", "email": "ptimmins@nasrcc.org", "page": "https://www.nasrcc.org/local/local-328/",
     "people": [["Regional Manager", "Raheem Shepard"], ["Business Manager", "Greg Poole"],
                ["Business Representatives", "Jim Burrows, John Cusack"],
                ["CREW Leaders", "Jeff Jameson, Loni Jean Rodrigo"]],
     "covers": "Allston, Belmont, Brighton, Brookline, Cambridge, Charlestown, Chelsea, East Boston, Everett, Malden, Medford, Revere, Somerville, Waverley and Winthrop.",
     "meets": "Every third Thursday, 5 PM, Anthony's of Malden, 105 Canal Street, Malden.", "asOf": "2026-05-28"},
]

names_only = [
    {"name": "Brian J. Honan Apartments deep energy retrofit", "area": "Allston / Brighton", "local": "328", "who": "Allston Brighton CDC", "ref": "a2026-01", "what": "Special presentation"},
    {"name": "Dorchester Community Center (city project 7291)", "area": "Dorchester", "local": "327", "who": "City of Boston", "ref": "a2026-04", "what": "Special presentation"},
    {"name": "Talbot Commons Phase Two (two sites in South Dorchester)", "area": "Dorchester", "local": "327", "who": "Codman Square NDC", "ref": "a2026-06", "what": "Project review"},
    {"name": "Engine 17 Phase II (city project 7309)", "area": "Dorchester", "local": "327", "who": "City of Boston", "ref": "a2026-07", "what": "Project review"},
]
for n in names_only:
    lab, url, date = BEC[n["ref"]]
    n.update({"src": lab, "url": url})

other_tools = [
    {"name": "Boston Residents Jobs Policy dashboard", "url": "https://app.powerbigov.us/view?r=eyJrIjoiZDI3ZThmNTgtMDIwMS00NWFiLTg4N2EtZTM5YjljMThmNmNkIiwidCI6Ijg1NTI4ODdjLWNiYzMtNGVlNS05ZmQzLWVhMjE3ZTMwMjZmYyJ9",
     "what": "Work hours by project, contractor and trade for Boston jobs covered by the policy. Filter the trade to Carpenter to see which subcontractors are logging carpenter hours on a project."},
    {"name": "Citywide Project Tracker", "url": "https://www.boston.gov/project-tracker",
     "what": "City-led projects only (schools, libraries, parks, community centers, streets). No contractor or union information."},
    {"name": "Planning Department development projects", "url": "https://www.bostonplans.org/projects/development-projects",
     "what": "Every Article 80 project in Boston with status, documents and contacts."},
    {"name": "NASRCC Find a Local", "url": "https://www.nasrcc.org/find-a-local/",
     "what": "Office, phone and staff for every carpenters local in the North Atlantic States Regional Council."},
]

uncovered = {"327": ["Dedham", "Milton"], "328": ["Belmont", "Brookline", "Chelsea", "Everett", "Malden", "Medford", "Revere", "Winthrop"]}

out = {
    "generated": TODAY,
    "sites": sites,
    "contractors": contractors,
    "sources": SRC,
    "bec": {k: {"label": v[0], "url": v[1], "date": v[2]} for k, v in BEC.items()},
    "map": MAP,
    "points": points,
    "locals": locals_info,
    "namesOnly": names_only,
    "otherTools": other_tools,
    "uncovered": uncovered,
    "cba": {"label": "Boston, Eastern MA, Northern New England Carpenters CBA, Sept 1, 2023 to Aug 31, 2027 (covers Locals 327 and 328)",
            "url": "https://www.mass.gov/doc/carpenters-ne-reg-council-boston-eastern-08-31-2027/download"},
}
counts = collections.Counter(x["city"] for x in sites)
problems = []
if counts["Boston"] < 40: problems.append(f"only {counts['Boston']} Boston sites (expected 60+)")
if counts["Cambridge"] < 5: problems.append(f"only {counts['Cambridge']} Cambridge sites")
if counts["Somerville"] < 3: problems.append(f"only {counts['Somerville']} Somerville sites")
if problems:
    sys.exit("NOT WRITTEN, data looks broken: " + "; ".join(problems))
json.dump(out, open(OUT, "w"), separators=(",", ":"), ensure_ascii=False)
print("wrote", OUT)
print("sites", len(sites), dict(counts), collections.Counter(x["local"] for x in sites))
print("labor", collections.Counter(x["labor"] for x in sites))
