"""
Builder for d/acc Fellowship Tally forms.

Generates Tally block JSON (schema mirrored from existing CISAI form zx2pPq)
and POSTs to https://api.tally.so/forms. Run with TALLY_API set.

  python3 build_tally_forms.py funders      # create one form
  python3 build_tally_forms.py all          # create all four
  python3 build_tally_forms.py --dry all    # print JSON only
"""
import json, os, sys, uuid, urllib.request

API = "https://api.tally.so/forms"
KEY = os.environ.get("TALLY_API")

# --------------------------------------------------------------------------
# Block primitives
# --------------------------------------------------------------------------

def _u(): return str(uuid.uuid4())

def _schema(text, bold=False):
    """Minimal safeHTMLSchema for plain text."""
    if bold:
        return [[text, [["tag", "span"], ["font-weight", "700"]]]]
    return [[text]]

def form_title(text):
    return {"type": "FORM_TITLE", "groupType": "TEXT", "uuid": _u(), "groupUuid": _u(),
            "payload": {"title": text, "safeHTMLSchema": _schema(text)}}

def text(s):
    return {"type": "TEXT", "groupType": "TEXT", "uuid": _u(), "groupUuid": _u(),
            "payload": {"safeHTMLSchema": _schema(s)}}

def h2(s):
    return {"type": "HEADING_2", "groupType": "HEADING_2", "uuid": _u(), "groupUuid": _u(),
            "payload": {"safeHTMLSchema": _schema(s)}}

def h3(s):
    return {"type": "HEADING_3", "groupType": "HEADING_3", "uuid": _u(), "groupUuid": _u(),
            "payload": {"safeHTMLSchema": _schema(s)}}

def divider():
    return {"type": "DIVIDER", "groupType": "DIVIDER", "uuid": _u(), "groupUuid": _u(), "payload": {}}

_page_idx = [0]
def page_break(first=False, last=False, thank_you=False):
    i = _page_idx[0]; _page_idx[0] += 1
    return {"type": "PAGE_BREAK", "groupType": "PAGE_BREAK", "uuid": _u(), "groupUuid": _u(),
            "payload": {"index": i, "isFirst": first, "isLast": last,
                        "isThankYouPage": thank_you, "isQualifiedForThankYouPage": thank_you}}

def _title(q):
    # The create API requires TITLE blocks to have their own groupUuid,
    # distinct from the input block that follows.
    return {"type": "TITLE", "groupType": "QUESTION", "uuid": _u(), "groupUuid": _u(),
            "payload": {"safeHTMLSchema": _schema(q, bold=True)}}

def _simple_input(kind, q, required=True, placeholder="", help_=None):
    g = _u()
    blocks = [_title(q)]
    if help_: blocks.append(text(help_))
    blocks.append({"type": kind, "groupType": kind, "uuid": _u(), "groupUuid": g,
                   "payload": {"isRequired": required, "placeholder": placeholder}})
    return blocks

def short(q, **kw):    return _simple_input("INPUT_TEXT", q, **kw)
def email(q, **kw):    return _simple_input("INPUT_EMAIL", q, **kw)
def link(q, **kw):     return _simple_input("INPUT_LINK", q, **kw)
def long(q, **kw):     return _simple_input("TEXTAREA", q, **kw)

def _options(kind, group_type, q, options, required=True, multiple=False, other=False, help_=None):
    g = _u()
    blocks = [_title(q)]
    if help_: blocks.append(text(help_))
    n = len(options)
    for i, opt in enumerate(options):
        p = {"isRequired": required, "index": i, "isFirst": i == 0, "isLast": i == n - 1, "text": opt}
        if kind == "DROPDOWN_OPTION": p["allowMultiple"] = multiple
        if kind == "CHECKBOX": p["hasOtherOption"] = other
        blocks.append({"type": kind, "groupType": group_type, "uuid": _u(), "groupUuid": g, "payload": p})
    return blocks

def dropdown(q, options, **kw):   return _options("DROPDOWN_OPTION", "DROPDOWN", q, options, **kw)
def choice(q, options, **kw):     return _options("MULTIPLE_CHOICE_OPTION", "MULTIPLE_CHOICE", q, options, **kw)
def checkboxes(q, options, **kw): return _options("CHECKBOX", "CHECKBOXES", q, options, **kw)

def flat(*groups):
    out = []
    for g in groups:
        out.extend(g if isinstance(g, list) else [g])
    return out

# --------------------------------------------------------------------------
# Shared content
# --------------------------------------------------------------------------

TRACKS = ["Resilience", "Sensemaking", "Cooperation", "Empowerment", "Hope"]
TRACK_HELP = ("Resilience — cyber, bio, climate, and cognitive security. "
              "Sensemaking — bridging systems, provenance, forecasting, agency-preserving AI. "
              "Cooperation — agent protocols, middle-power governance, preference aggregation, cooperative AI. "
              "Empowerment — privacy-preserving compute, zero-knowledge auth, decentralised energy, public goods. "
              "Hope — design sketches for a better world.")
PATHS = ["Policy interventions", "Technical research", "Founding & fieldbuilding"]
CONTACT = "dacc@cisai.co"

def thank_you(program_line):
    return flat(
        page_break(thank_you=True, last=True),
        h2("Thank you"),
        text(program_line),
        text(f"Cape Institute for Safe AI · {CONTACT}"),
    )

def settings(closed_title, closed_desc):
    return {
        "language": "en",
        "isClosed": False,
        "closeMessageTitle": closed_title,
        "closeMessageDescription": closed_desc,
        "hasSelfEmailNotifications": True,
        "hasProgressBar": True,
        "hasPartialSubmissions": True,
        "pageAutoJump": False,
        "saveForLater": True,
        "styles": {"theme": "LIGHT"},
    }

# --------------------------------------------------------------------------
# Forms
# --------------------------------------------------------------------------

def form_funders():
    _page_idx[0] = 0
    blocks = flat(
        form_title("d/acc Fellowship — Funders"),
        text("Thank you for your interest in supporting the d/acc Fellowship. "
             "The fellowship hosts fellows in Cape Town from March to June, with a $3,500 monthly stipend, "
             "working across resilience, sensemaking, cooperation, empowerment, and hope. "
             "Leave your details and we will be in touch."),
        page_break(first=True),
        short("Your name"),
        email("Your email address"),
        short("Organisation or fund", required=False),
        long("How would you like to support the fellowship?",
             help_="Stipends, residencies, track sponsorship, open-source outputs, or something else. A sentence or two is enough."),
        long("Anything else?", required=False),
        thank_you("We have received your message and will reply shortly."),
    )
    return {"status": "PUBLISHED", "name": "d/acc Fellowship — Funders", "blocks": blocks,
            "settings": settings("This form is closed.", f"Please contact {CONTACT}.")}


def form_mentors():
    _page_idx[0] = 0
    blocks = flat(
        form_title("d/acc Fellowship — Mentors"),
        text("The d/acc Fellowship hosts fellows in Cape Town from March to June. Mentors guide a fellow's work "
             "across one of five tracks — remotely or in person. This form takes about five minutes."),
        page_break(first=True),
        short("Your name"),
        email("Your email address"),
        short("Organisation and role"),
        link("Profile URL (website, LinkedIn, or Scholar)", required=False),
        checkboxes("Which tracks could you mentor?", TRACKS, other=True, help_=TRACK_HELP),
        checkboxes("How would you like to be involved?",
                   ["Mentor a fellow through the program", "Give a talk or workshop",
                    "Advise on a specific project", "Review applications", "Host a fellow at my organisation"],
                   other=True),
        dropdown("Roughly how much time could you offer per month?",
                 ["1–2 hours", "3–5 hours", "6–10 hours", "More than 10 hours"]),
        long("Briefly, what would you bring to a fellow?", required=False,
             help_="Areas of expertise, networks, or the kind of work you would most like to see happen."),
        long("Anything else?", required=False),
        thank_you("Thank you for offering to mentor. We will be in touch as the cohort forms."),
    )
    return {"status": "PUBLISHED", "name": "d/acc Fellowship — Mentors", "blocks": blocks,
            "settings": settings("Mentor sign-up is closed.", f"Please contact {CONTACT}.")}


def form_partners():
    _page_idx[0] = 0
    blocks = flat(
        form_title("d/acc Fellowship — Partners & Collaborators"),
        text("Organisations working on resilience, sensemaking, cooperation, or empowerment who want to host, "
             "co-run, or collaborate with the d/acc Fellowship. This form takes about five minutes."),
        page_break(first=True),
        short("Your name"),
        email("Your email address"),
        short("Organisation"),
        link("Website", required=False),
        checkboxes("What kind of partnership are you interested in?",
                   ["Host a fellow or project", "Co-run an event or workshop", "Research collaboration",
                    "Provide infrastructure, data, or compute", "Policy working group",
                    "Field-building or community"], other=True),
        checkboxes("Which tracks are most relevant to you?", TRACKS, other=True, help_=TRACK_HELP),
        long("Describe the collaboration you have in mind.",
             help_="A paragraph is plenty. What would success look like for you?"),
        long("Anything else?", required=False),
        thank_you("Thank you. We will be in touch to discuss next steps."),
    )
    return {"status": "PUBLISHED", "name": "d/acc Fellowship — Partners & Collaborators", "blocks": blocks,
            "settings": settings("Partner sign-up is closed.", f"Please contact {CONTACT}.")}


def form_fellows():
    _page_idx[0] = 0
    blocks = flat(
        form_title("d/acc Fellowship — Application"),
        text("Thank you for your interest in the d/acc Fellowship."),
        text("The fellowship runs from March to June in Cape Town, South Africa, hosted at the Cape Institute for Safe AI, "
             "with a $3,500 monthly stipend. Fellows follow one of three paths — policy interventions, technical research, "
             "or founding and fieldbuilding — across five tracks: resilience, sensemaking, cooperation, empowerment, and hope."),
        text("This application takes roughly 1–2 hours. You can save and return to it. "
             f"Questions: {CONTACT}"),

        page_break(first=True),
        h2("Basic information"),
        short("Your first name"),
        short("Your last name"),
        email("Your email address"),
        short("Country of residence"),
        dropdown("What stage of your career are you in? (select as many as apply)",
                 ["Employed, full-time", "Employed, part-time", "Self-employed",
                  "Working (0–5 years)", "Working (6–15 years)", "Working (15+ years)",
                  "Not employed, but looking", "Not employed, and not looking", "Retired",
                  "Pursuing a doctoral degree (e.g. PhD)", "Pursuing a graduate degree (e.g. Masters)",
                  "Pursuing an undergraduate degree", "Pursuing a professional degree",
                  "Pursuing other degree/diploma", "Student (high school)"], multiple=True),
        dropdown("What is your highest level of education?",
                 ["PhD (complete)", "PhD (in progress)", "Masters (complete)", "Masters (in progress)",
                  "Postgraduate Honours/Diploma (complete)", "Postgraduate Honours/Diploma (in progress)",
                  "Bachelors (complete)", "Bachelors (in progress)",
                  "Higher certificate/Associate degree (complete)", "Higher certificate/Associate degree (in progress)",
                  "High school", "Other"]),
        short("University, institution, or company", required=False, help_="e.g. University of Cape Town, or Amazon"),
        short("Position", required=False, help_="e.g. Postgraduate student, or Senior software engineer"),
        short("If you are a student, what program are you enrolled in?", required=False, help_="e.g. MSc in Computer Science"),
        short("Where do you have the right to work?", help_="This helps us understand visa requirements for Cape Town."),
        link("Profile URL (CV or LinkedIn)",
             help_="If linking a CV on Google Drive, please make sure anyone with the link can view it."),
        long("Are there any previous projects or experiences you'd like to highlight as especially relevant?", required=False,
             help_="e.g. previous fellowships (MATS, PIBBSS, ERA, Pivotal, Talos, CAIRF), founded projects, policy work, or open-source contributions, with dates."),

        page_break(),
        h2("About you"),
        long("What are your career aspirations? (100–250 words)",
             help_="Outline 2–3 potential paths you are considering and how this fellowship fits your trajectory."),
        long("Why do you want to be part of the d/acc Fellowship? (150–300 words)",
             help_="You might mention your motivation for working on civilisational resilience, what d/acc means to you, "
                   "and how the Cape Town setting or the CISAI community matters to your plans — none of these are required."),
        long("What have been your preferred sources for learning about AI safety, d/acc, or civilisational resilience?",
             help_="Please be specific — researchers, papers, podcasts, courses, books — rather than general categories."),
        long("Describe a time when you demonstrated high agency. (100–200 words)",
             help_="A time you took initiative to solve a problem, build something new, or drive a project forward despite "
                   "obstacles or uncertainty. This could be in research, work, community, or personal life. "
                   "See neelnanda.io/blog/44-agency for what we mean."),
        long("Please link 1–2 writing samples, code repositories, products, or similar that illustrate skills relevant to the fellowship, and give brief context.",
             help_="Note whether others helped produce the work. If you don't have a relevant sample, briefly explain why — "
                   "there are many valid reasons. For writing, choose something whose first pages show your skills even if we don't read further."),

        page_break(),
        h2("Path and tracks"),
        choice("Which path best describes the work you want to do during the fellowship?", PATHS,
               help_="Fellows are expected to follow one path, though work often blends them."),
        checkboxes("Which tracks are you most interested in? (select all that apply)",
                   TRACKS + ["Wildcard (please specify below)"], other=False, help_=TRACK_HELP),
        long("For your selected track(s), describe the work you would like to undertake during the fellowship and why it matters.",
             help_="No strict word count; about a paragraph per track is appropriate. If you selected Wildcard, name the topic domain here. "
                   "We understand this will evolve."),
        long("Optional — South African local impact", required=False,
             help_="We give extra weight to solutions rooted in local context that strengthen infrastructure, education, cultural resilience, "
                   "or economic empowerment while serving as models that can scale. If your proposed work has this dimension, describe it."),

        page_break(),
        h2("Logistics"),
        choice("The fellowship is designed for full-time, in-person participation in Cape Town from March to June. "
               "Part-time participation is possible but voids eligibility for the stipend. In what capacity would you like to be considered?",
               ["Full-time, in person (eligible for stipend)", "Part-time, in person (no stipend)", "Remote (no stipend)"],
               help_="Participants who can attend the full duration in person will be prioritised."),
        long("Please confirm your availability from March to June and note any constraints.",
             help_="e.g. dates you would need to be away, visa considerations, or existing commitments."),
        long("How did you hear about this opportunity?",
             help_="List all that apply — e.g. LinkedIn, X, the AI Safety South Africa Slack, a referral."),
        choice("Do you have a disability?", ["Yes", "No", "Prefer not to say"]),
        long("If yes, please describe any accommodations you may need to participate.", required=False),
        choice("Would you like us to share your profile with other AI safety and d/acc organisations for relevant opportunities?",
               ["Yes please", "No, thank you"]),
        long("Anything else?", required=False,
             help_="Additional context, experiences, or circumstances that help us understand your application. Feedback on the process is also welcome."),

        divider(),
        h3("Diversity & inclusion"),
        text("This information helps us build a diverse and inclusive cohort. All questions in this section are optional."),
        dropdown("Gender", ["Woman", "Man", "Non-binary", "Prefer not to say", "Prefer to self-describe"], required=False),
        dropdown("Ethnicity / race",
                 ["African/Black African", "Coloured", "Indian/South Asian", "East Asian", "Southeast Asian",
                  "Middle Eastern/North African", "White/European", "Hispanic/Latino",
                  "Native American/Indigenous American", "Pacific Islander", "Mixed/Multiracial", "Other"], required=False),
        text("By submitting this application you consent to the collection, use, and storage of your information by the "
             "Cape Institute for Safe AI for program administration and communication about this opportunity."),

        thank_you("We have received your application and will be in touch with next steps. "
                  "Thank you for wanting to build a more resilient world."),
    )
    return {"status": "PUBLISHED", "name": "d/acc Fellowship — Application", "blocks": blocks,
            "settings": settings("Applications for the d/acc Fellowship are now closed.",
                                 "Thank you for your interest. Stay connected with the Cape Institute for Safe AI for future cohorts.")}


FORMS = {"funders": form_funders, "mentors": form_mentors, "partners": form_partners, "fellows": form_fellows}

# --------------------------------------------------------------------------

def create(payload):
    req = urllib.request.Request(API, data=json.dumps(payload).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json",
                                          "Accept": "application/json",
                                          "User-Agent": "dacc-fellowship-forms/1.0 (+curl)"})
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "body": e.read().decode()}

if __name__ == "__main__":
    args = sys.argv[1:]
    dry = "--dry" in args
    args = [a for a in args if a != "--dry"]
    names = list(FORMS) if (not args or args[0] == "all") else args
    results = {}
    for n in names:
        payload = FORMS[n]()
        if dry:
            print(json.dumps(payload, indent=1)[:3000]); continue
        if not KEY: sys.exit("TALLY_API not set")
        r = create(payload)
        results[n] = r
        print(n, "→", r.get("id") or r)
    if results:
        json.dump(results, open("/tmp/opencode/tally_results.json", "w"), indent=1)
