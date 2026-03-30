"""
synonym_normalizer.py
---------------------
Synonym-aware keyword similarity — the primary semantic layer when SBERT
is not available.

WHAT IT SOLVES:
  Without a transformer model, pure synonym swapping is invisible to every
  other signal (Winnowing, TF-IDF, keyword Jaccard all see zero overlap).
  This module maps words to canonical forms using a curated synonym dictionary,
  then computes two complementary scores:

  1. SYNONYM JACCARD
     Jaccard similarity on the canonicalized content-word sets.
     Catches synonym-for-synonym rewrites ("quick" → "fast", "jumps" → "leaps").

  2. SYNONYM CONTAINMENT
     What fraction of the SHORTER document's canonical words appear in the
     LONGER document's canonical word set?
     Catches "expansion plagiarism" — where someone takes "Climate change is
     a global threat" and pads it into a longer sentence. All original keywords
     are still present; the Jaccard is diluted by the extras, but containment
     is near 1.0.

  COMBINED RULE:
     If containment ≥ CONTAINMENT_THRESHOLD → use containment (expansion case)
     Otherwise → use Jaccard (balanced comparison)

SYNONYM DICTIONARY:
  Groups are plain Python sets. The canonical form is min(group) — i.e. the
  alphabetically first member. This is deterministic and needs no special config.
  All inflected forms (plurals, -ing, -ed, -s) are included explicitly so no
  stemmer is required.
"""

from Phase1_Text.preprocess.preprocessor import STOP_WORDS

# ── Synonym Groups ─────────────────────────────────────────────────────────────
# Each set is one equivalence class. All members map to min(set) as canonical.
SYNONYM_GROUPS = [

    # ── Eat / Consume / Ingest ────────────────────────────────────────────────
    {"eat", "eats", "ate", "eaten", "eating",
     "consume", "consumes", "consumed", "consuming",
     "ingest", "ingests", "ingested", "ingesting",
     "devour", "devours", "devoured", "devouring",
     "feed", "feeds", "fed", "feeding"},

    # ── Drink ─────────────────────────────────────────────────────────────────
    {"drink", "drinks", "drank", "drunk", "drinking",
     "sip", "sips", "sipped", "sipping",
     "gulp", "gulps", "gulped", "gulping"},

    # ── See / Observe ─────────────────────────────────────────────────────────
    {"see", "sees", "saw", "seen", "seeing",
     "observe", "observes", "observed", "observing",
     "view", "views", "viewed", "viewing",
     "watch", "watches", "watched", "watching",
     "witness", "witnesses", "witnessed", "witnessing",
     "notice", "notices", "noticed", "noticing",
     "perceive", "perceives", "perceived", "perceiving"},

    # ── Speak / Talk ──────────────────────────────────────────────────────────
    {"speak", "speaks", "spoke", "spoken", "speaking",
     "talk", "talks", "talked", "talking",
     "tell", "tells", "told", "telling",
     "communicate", "communicates", "communicated", "communicating"},

    # ── Write ─────────────────────────────────────────────────────────────────
    {"write", "writes", "wrote", "written", "writing",
     "compose", "composes", "composed", "composing",
     "author", "authors", "authored", "authoring",
     "draft", "drafts", "drafted", "drafting"},

    # ── Read ──────────────────────────────────────────────────────────────────
    {"read", "reads", "reading"},

    # ── Go / Travel ───────────────────────────────────────────────────────────
    {"go", "goes", "went", "gone", "going",
     "travel", "travels", "traveled", "travelling", "travelling",
     "move", "moves", "moved", "moving",
     "proceed", "proceeds", "proceeded", "proceeding"},

    # ── Come / Arrive ─────────────────────────────────────────────────────────
    {"come", "comes", "came", "coming",
     "arrive", "arrives", "arrived", "arriving",
     "reach", "reaches", "reached", "reaching",
     "appear", "appears", "appeared", "appearing"},

    # ── Take / Obtain ─────────────────────────────────────────────────────────
    {"take", "takes", "took", "taken", "taking",
     "obtain", "obtains", "obtained", "obtaining",
     "acquire", "acquires", "acquired", "acquiring",
     "grab", "grabs", "grabbed", "grabbing",
     "seize", "seizes", "seized", "seizing",
     "capture", "captures", "captured", "capturing",
     "gather", "gathers", "gathered", "gathering"},

    # ── Give / Provide ────────────────────────────────────────────────────────
    {"give", "gives", "gave", "given", "giving",
     "provide", "provides", "provided", "providing",
     "offer", "offers", "offered", "offering",
     "grant", "grants", "granted", "granting",
     "supply", "supplies", "supplied", "supplying",
     "deliver", "delivers", "delivered", "delivering"},

    # ── Get / Receive ─────────────────────────────────────────────────────────
    {"get", "gets", "got", "gotten", "getting",
     "receive", "receives", "received", "receiving",
     "obtain", "obtains", "obtained", "obtaining",
     "acquire", "acquires", "acquired", "acquiring"},

    # ── Know / Understand ─────────────────────────────────────────────────────
    {"know", "knows", "knew", "known", "knowing",
     "understand", "understands", "understood", "understanding",
     "comprehend", "comprehends", "comprehended", "comprehending",
     "realize", "realizes", "realized", "realizing",
     "grasp", "grasps", "grasped", "grasping"},

    # ── Begin / Start ─────────────────────────────────────────────────────────
    {"begin", "begins", "began", "begun", "beginning",
     "start", "starts", "started", "starting",
     "initiate", "initiates", "initiated", "initiating",
     "commence", "commences", "commenced", "commencing",
     "launch", "launches", "launched", "launching"},

    # ── End / Finish ──────────────────────────────────────────────────────────
    {"end", "ends", "ended", "ending",
     "finish", "finishes", "finished", "finishing",
     "complete", "completes", "completed", "completing",
     "conclude", "concludes", "concluded", "concluding",
     "terminate", "terminates", "terminated", "terminating",
     "stop", "stops", "stopped", "stopping",
     "cease", "ceases", "ceased", "ceasing"},

    # ── Keep / Maintain ───────────────────────────────────────────────────────
    {"keep", "keeps", "kept", "keeping",
     "maintain", "maintains", "maintained", "maintaining",
     "retain", "retains", "retained", "retaining",
     "preserve", "preserves", "preserved", "preserving",
     "sustain", "sustains", "sustained", "sustaining"},

    # ── Break / Destroy ───────────────────────────────────────────────────────
    {"break", "breaks", "broke", "broken", "breaking",
     "destroy", "destroys", "destroyed", "destroying",
     "damage", "damages", "damaged", "damaging",
     "ruin", "ruins", "ruined", "ruining",
     "shatter", "shatters", "shattered", "shattering"},

    # ── Buy / Purchase ────────────────────────────────────────────────────────
    {"buy", "buys", "bought", "buying",
     "purchase", "purchases", "purchased", "purchasing",
     "acquire", "acquires", "acquired", "acquiring",
     "obtain", "obtains", "obtained", "obtaining"},

    # ── Sell ──────────────────────────────────────────────────────────────────
    {"sell", "sells", "sold", "selling",
     "trade", "trades", "traded", "trading",
     "market", "markets", "marketed", "marketing"},

    # ── Bring / Carry ─────────────────────────────────────────────────────────
    {"bring", "brings", "brought", "bringing",
     "carry", "carries", "carried", "carrying",
     "transport", "transports", "transported", "transporting",
     "convey", "conveys", "conveyed", "conveying"},

    # ── Send / Transmit ───────────────────────────────────────────────────────
    {"send", "sends", "sent", "sending",
     "transmit", "transmits", "transmitted", "transmitting",
     "dispatch", "dispatches", "dispatched", "dispatching",
     "submit", "submits", "submitted", "submitting"},

    # ── Meet / Encounter ─────────────────────────────────────────────────────
    {"meet", "meets", "met", "meeting",
     "encounter", "encounters", "encountered", "encountering",
     "face", "faces", "faced", "facing"},

    # ── Sit / Rest ────────────────────────────────────────────────────────────
    {"sit", "sits", "sat", "sitting",
     "rest", "rests", "rested", "resting",
     "settle", "settles", "settled", "settling"},

    # ── Stand ─────────────────────────────────────────────────────────────────
    {"stand", "stands", "stood", "standing",
     "rise", "rises", "rose", "risen", "rising"},

    # ── Sleep ─────────────────────────────────────────────────────────────────
    {"sleep", "sleeps", "slept", "sleeping",
     "rest", "rests", "rested", "resting"},

    # ── Put / Place ───────────────────────────────────────────────────────────
    {"put", "puts", "putting",
     "place", "places", "placed", "placing",
     "position", "positions", "positioned", "positioning",
     "set", "sets", "setting",
     "lay", "lays", "laid", "laying"},

    # ── Hold ──────────────────────────────────────────────────────────────────
    {"hold", "holds", "held", "holding",
     "grip", "grips", "gripped", "gripping",
     "grasp", "grasps", "grasped", "grasping"},

    # ── Hear / Listen ─────────────────────────────────────────────────────────
    {"hear", "hears", "heard", "hearing",
     "listen", "listens", "listened", "listening"},

    # ── Feel / Touch ──────────────────────────────────────────────────────────
    {"feel", "feels", "felt", "feeling",
     "touch", "touches", "touched", "touching",
     "sense", "senses", "sensed", "sensing"},

    # ── Pay ───────────────────────────────────────────────────────────────────
    {"pay", "pays", "paid", "paying",
     "compensate", "compensates", "compensated", "compensating",
     "reimburse", "reimburses", "reimbursed", "reimbursing"},

    # ── Lose ──────────────────────────────────────────────────────────────────
    {"lose", "loses", "lost", "losing",
     "misplace", "misplaces", "misplaced", "misplacing",
     "forfeit", "forfeits", "forfeited", "forfeiting"},

    # ── Win ───────────────────────────────────────────────────────────────────
    {"win", "wins", "won", "winning",
     "triumph", "triumphs", "triumphed", "triumphing",
     "succeed", "succeeds", "succeeded", "succeeding",
     "prevail", "prevails", "prevailed", "prevailing"},

    # ── Choose / Select ───────────────────────────────────────────────────────
    {"choose", "chooses", "chose", "chosen", "choosing",
     "select", "selects", "selected", "selecting",
     "pick", "picks", "picked", "picking",
     "opt", "opts", "opted", "opting",
     "decide", "decides", "decided", "deciding"},

    # ── Leave / Depart ───────────────────────────────────────────────────────
    {"leave", "leaves", "left", "leaving",
     "depart", "departs", "departed", "departing",
     "exit", "exits", "exited", "exiting",
     "abandon", "abandons", "abandoned", "abandoning",
     "quit", "quits", "quitting"},

    # ── Open / Close ──────────────────────────────────────────────────────────
    {"open", "opens", "opened", "opening"},
    {"close", "closes", "closed", "closing",
     "shut", "shuts", "shutting"},

    # ── Grow / Develop (biology / general) ───────────────────────────────────
    {"grow", "grows", "grew", "grown", "growing",
     "develop", "develops", "developed", "developing",
     "evolve", "evolves", "evolved", "evolving",
     "mature", "matures", "matured", "maturing",
     "expand", "expands", "expanded", "expanding"},

    # ── Fall / Drop ───────────────────────────────────────────────────────────
    {"fall", "falls", "fell", "fallen", "falling",
     "drop", "drops", "dropped", "dropping",
     "descend", "descends", "descended", "descending",
     "plummet", "plummets", "plummeted", "plummeting",
     "decline", "declines", "declined", "declining"},

    # ── Throw / Toss ──────────────────────────────────────────────────────────
    {"throw", "throws", "threw", "thrown", "throwing",
     "toss", "tosses", "tossed", "tossing",
     "hurl", "hurls", "hurled", "hurling",
     "fling", "flings", "flung", "flinging"},

    # ── Cut ───────────────────────────────────────────────────────────────────
    {"cut", "cuts", "cutting",
     "slice", "slices", "sliced", "slicing",
     "trim", "trims", "trimmed", "trimming",
     "sever", "severs", "severed", "severing"},

    # ── Meet / Join ───────────────────────────────────────────────────────────
    {"join", "joins", "joined", "joining",
     "connect", "connects", "connected", "connecting",
     "unite", "unites", "united", "uniting",
     "combine", "combines", "combined", "combining",
     "merge", "merges", "merged", "merging"},

    # ── Teach ─────────────────────────────────────────────────────────────────
    {"teach", "teaches", "taught", "teaching",
     "instruct", "instructs", "instructed", "instructing",
     "train", "trains", "trained", "training",
     "educate", "educates", "educated", "educating"},

    # ── Learn ─────────────────────────────────────────────────────────────────
    {"learn", "learns", "learned", "learning",
     "study", "studies", "studied", "studying",
     "acquire", "acquires", "acquired", "acquiring"},

    # ── Fight / Struggle ──────────────────────────────────────────────────────
    {"fight", "fights", "fought", "fighting",
     "battle", "battles", "battled", "battling",
     "struggle", "struggles", "struggled", "struggling",
     "combat", "combats", "combated", "combating",
     "oppose", "opposes", "opposed", "opposing"},

    # ── Fruit / Produce nouns ─────────────────────────────────────────────────
    {"mango", "mangos", "mangoes"},
    {"apple", "apples"},
    {"banana", "bananas"},
    {"fruit", "fruits", "produce"},


    {"jump", "jumps", "jumped", "jumping",
     "leap", "leaps", "leaped", "leaping",
     "bound", "bounds", "bounded", "bounding",
     "spring", "springs", "sprang", "sprung",
     "hop", "hops", "hopped", "hopping",
     "vault", "vaults", "vaulted", "vaulting"},

    {"run", "runs", "ran", "running",
     "sprint", "sprints", "sprinted", "sprinting",
     "dash", "dashes", "dashed", "dashing",
     "race", "races", "raced", "racing",
     "jog", "jogs", "jogged", "jogging"},

    {"walk", "walks", "walked", "walking",
     "stroll", "strolls", "strolled", "strolling",
     "march", "marches", "marched", "marching",
     "stride", "strides", "strode", "striding"},

    {"fly", "flies", "flew", "flown", "flying",
     "soar", "soars", "soared", "soaring",
     "glide", "glides", "glided", "gliding"},

    # ── Speed / quickness ─────────────────────────────────────────────────────
    {"quick", "fast", "swift", "rapid", "speedy",
     "brisk", "hasty", "fleet", "nimble"},

    # ── Slowness / laziness ───────────────────────────────────────────────────
    {"slow", "sluggish", "lethargic", "torpid", "leisurely"},
    {"lazy", "idle", "indolent", "slothful", "inactive", "inert"},

    # ── Animals ───────────────────────────────────────────────────────────────
    {"dog", "dogs", "canine", "canines",
     "hound", "hounds", "pooch", "pooches",
     "mutt", "mutts", "cur", "curs"},

    {"cat", "cats", "feline", "felines", "kitty", "kitten", "kittens"},
    {"fox", "foxes", "vixen", "vixens"},

    {"horse", "horses", "steed", "steeds", "mare", "mares",
     "stallion", "stallions", "equine", "equines", "colt", "filly"},

    {"pig", "pigs", "swine", "hog", "hogs", "boar", "sow"},

    {"bird", "birds", "avian", "fowl"},

    # ── Colors / earth tones ──────────────────────────────────────────────────
    {"brown", "tan", "tawny", "beige", "chestnut", "mahogany", "brunette"},
    {"red", "crimson", "scarlet", "ruby", "vermillion"},
    {"blue", "azure", "cobalt", "indigo", "navy", "cerulean"},
    {"green", "emerald", "jade", "olive"},
    {"black", "ebony", "obsidian", "onyx"},
    {"white", "ivory", "cream", "pearl"},
    {"yellow", "golden", "amber", "blonde", "blond"},

    # ── Size ──────────────────────────────────────────────────────────────────
    {"big", "large", "huge", "enormous", "massive", "giant", "vast",
     "colossal", "immense", "tremendous", "great", "substantial"},

    {"small", "tiny", "little", "miniature", "minute",
     "petite", "slight", "minuscule"},

    {"tall", "high", "lofty", "elevated", "towering"},
    {"short", "low", "brief", "squat", "stubby"},

    # ── Positive qualities ────────────────────────────────────────────────────
    {"good", "great", "excellent", "fine", "superb",
     "outstanding", "wonderful", "terrific", "fantastic", "splendid"},

    {"important", "significant", "crucial", "vital", "essential",
     "critical", "key", "fundamental", "pivotal", "central"},

    {"interesting", "fascinating", "intriguing", "captivating",
     "compelling", "engaging", "riveting"},

    {"difficult", "hard", "challenging", "tough", "arduous",
     "demanding", "strenuous"},

    {"easy", "simple", "straightforward", "effortless",
     "uncomplicated", "manageable"},

    # ── Negative qualities ────────────────────────────────────────────────────
    {"bad", "poor", "terrible", "awful", "dreadful",
     "horrible", "appalling", "dreadful"},

    {"scary", "frightening", "terrifying", "terrified", "fearful",
     "dreadful", "alarming", "horrifying", "horrified"},

    # ── Emotional states ──────────────────────────────────────────────────────
    {"happy", "joyful", "cheerful", "glad", "content",
     "pleased", "delighted", "elated"},

    {"sad", "unhappy", "sorrowful", "melancholy",
     "depressed", "miserable", "gloomy"},

    {"afraid", "scared", "fearful", "terrified", "frightened",
     "anxious", "worried"},

    {"angry", "furious", "enraged", "irate", "livid", "outraged"},

    # ── Intelligence / ability ────────────────────────────────────────────────
    {"smart", "intelligent", "clever", "bright", "brilliant",
     "sharp", "astute", "shrewd"},

    {"strong", "powerful", "robust", "sturdy", "vigorous",
     "potent", "mighty", "forceful"},

    {"weak", "frail", "feeble", "fragile", "delicate"},

    # ── Academic / research verbs ─────────────────────────────────────────────
    {"analyze", "analyzes", "analyzed", "analyzing",
     "analysis", "analytical",
     "examine", "examines", "examined", "examining",
     "investigate", "investigates", "investigated", "investigating",
     "study", "studies", "studied", "studying",
     "assess", "assesses", "assessed", "assessing",
     "evaluate", "evaluates", "evaluated", "evaluating",
     "review", "reviews", "reviewed", "reviewing",
     "inspect", "inspects", "inspected", "inspecting"},

    {"show", "shows", "showed", "showing", "shown",
     "demonstrate", "demonstrates", "demonstrated", "demonstrating",
     "reveal", "reveals", "revealed", "revealing",
     "indicate", "indicates", "indicated", "indicating",
     "display", "displays", "displayed", "displaying",
     "exhibit", "exhibits", "exhibited", "exhibiting",
     "illustrate", "illustrates", "illustrated", "illustrating"},

    {"find", "finds", "found", "finding",
     "discover", "discovers", "discovered", "discovering",
     "uncover", "uncovers", "uncovered", "uncovering",
     "detect", "detects", "detected", "detecting",
     "identify", "identifies", "identified", "identifying",
     "determine", "determines", "determined", "determining"},

    {"use", "uses", "used", "using",
     "utilize", "utilizes", "utilized", "utilizing",
     "employ", "employs", "employed", "employing",
     "apply", "applies", "applied", "applying",
     "implement", "implements", "implemented", "implementing"},

    {"create", "creates", "created", "creating",
     "make", "makes", "made", "making",
     "produce", "produces", "produced", "producing",
     "generate", "generates", "generated", "generating",
     "develop", "develops", "developed", "developing",
     "build", "builds", "built", "building",
     "construct", "constructs", "constructed", "constructing",
     "form", "forms", "formed", "forming"},

    {"increase", "increases", "increased", "increasing",
     "rise", "rises", "rose", "risen", "rising",
     "grow", "grows", "grew", "grown", "growing",
     "expand", "expands", "expanded", "expanding",
     "surge", "surges", "surged", "surging",
     "climb", "climbs", "climbed", "climbing",
     "escalate", "escalates", "escalated", "escalating",
     "augment", "augments", "augmented", "augmenting"},

    {"decrease", "decreases", "decreased", "decreasing",
     "fall", "falls", "fell", "fallen", "falling",
     "drop", "drops", "dropped", "dropping",
     "decline", "declines", "declined", "declining",
     "reduce", "reduces", "reduced", "reducing",
     "shrink", "shrinks", "shrank", "shrunk", "shrinking",
     "diminish", "diminishes", "diminished", "diminishing",
     "dwindle", "dwindles", "dwindled", "dwindling"},

    {"cause", "causes", "caused", "causing",
     "lead", "leads", "led", "leading",
     "trigger", "triggers", "triggered", "triggering",
     "result", "results", "resulted", "resulting",
     "produce", "produces", "produced", "producing"},

    {"help", "helps", "helped", "helping",
     "assist", "assists", "assisted", "assisting",
     "support", "supports", "supported", "supporting",
     "aid", "aids", "aided", "aiding",
     "facilitate", "facilitates", "facilitated", "facilitating"},

    {"say", "says", "said", "saying",
     "state", "states", "stated", "stating",
     "claim", "claims", "claimed", "claiming",
     "assert", "asserts", "asserted", "asserting",
     "argue", "argues", "argued", "arguing",
     "contend", "contends", "contended", "contending",
     "maintain", "maintains", "maintained", "maintaining"},

    {"think", "thinks", "thought", "thinking",
     "believe", "believes", "believed", "believing",
     "consider", "considers", "considered", "considering",
     "feel", "feels", "felt", "feeling",
     "suppose", "supposes", "supposed", "supposing",
     "assume", "assumes", "assumed", "assuming"},

    {"need", "needs", "needed", "needing",
     "require", "requires", "required", "requiring",
     "demand", "demands", "demanded", "demanding",
     "necessitate", "necessitates", "necessitated"},

    # ── People / researchers ──────────────────────────────────────────────────
    {"scientist", "scientists",
     "researcher", "researchers",
     "investigator", "investigators",
     "scholar", "scholars",
     "expert", "experts",
     "analyst", "analysts"},

    {"student", "students", "pupil", "pupils", "learner", "learners"},
    {"teacher", "teachers", "instructor", "instructors",
     "professor", "professors", "educator", "educators"},

    {"doctor", "doctors", "physician", "physicians", "medic", "medics"},
    {"worker", "workers", "employee", "employees", "staff", "laborer"},

    # ── Data / information ────────────────────────────────────────────────────
    {"data", "datum", "dataset", "datasets"},
    {"information", "info", "knowledge", "intelligence"},
    {"result", "results", "outcome", "outcomes",
     "consequence", "consequences", "effect", "effects", "impact", "impacts"},

    # ── Common abstract nouns ─────────────────────────────────────────────────
    {"problem", "problems", "issue", "issues",
     "challenge", "challenges", "difficulty", "difficulties",
     "obstacle", "obstacles", "hurdle", "hurdles"},

    {"solution", "solutions", "answer", "answers",
     "resolution", "resolutions", "remedy", "remedies", "fix", "fixes"},

    {"method", "methods", "approach", "approaches",
     "technique", "techniques", "strategy", "strategies",
     "procedure", "procedures", "process", "processes"},

    {"idea", "ideas", "concept", "concepts", "notion", "notions",
     "theory", "theories"},

    {"goal", "goals", "aim", "aims", "objective", "objectives",
     "purpose", "purposes", "target", "targets"},

    # ── Climate / environment ─────────────────────────────────────────────────
    {"global", "worldwide", "international", "universal"},

    {"climate", "atmospheric", "environmental"},

    {"threat", "threats", "danger", "dangers",
     "menace", "menaces", "hazard", "hazards",
     "risk", "risks", "peril", "perils"},

    {"crisis", "crises", "emergency", "emergencies",
     "catastrophe", "catastrophes", "disaster", "disasters",
     "calamity", "calamities"},

    {"temperature", "temperatures", "heat", "warmth",
     "thermal", "warming"},

    {"emission", "emissions", "discharge", "discharges",
     "release", "releases", "output"},

    {"burn", "burns", "burned", "burning", "burnt",
     "combust", "combustion", "incinerate", "incineration"},

    {"fossil", "fossils", "petroleum", "coal", "hydrocarbon"},

    {"sea", "seas", "ocean", "oceans", "marine", "aquatic"},

    {"community", "communities",
     "population", "populations",
     "society", "societies",
     "settlement", "settlements"},

    {"level", "levels", "rate", "rates", "measure", "measurement"},

    {"effect", "effects", "impact", "impacts",
     "consequence", "consequences", "outcome", "outcomes",
     "result", "results", "ramification", "ramifications"},

    {"reduce", "reduces", "reduced", "reducing",
     "limit", "limits", "limited", "limiting",
     "cut", "cuts", "cutting",
     "lower", "lowers", "lowered", "lowering",
     "curb", "curbs", "curbed", "curbing",
     "mitigate", "mitigates", "mitigated", "mitigating"},

    # ── Health / medical ──────────────────────────────────────────────────────
    {"disease", "diseases", "illness", "illnesses",
     "condition", "conditions", "disorder", "disorders",
     "ailment", "ailments", "sickness"},

    {"treatment", "treatments", "therapy", "therapies",
     "cure", "cures", "remedy", "remedies"},

    {"patient", "patients", "subject", "subjects",
     "participant", "participants"},

    # ── Economy / society ─────────────────────────────────────────────────────
    {"money", "cash", "currency", "funds", "capital", "wealth"},

    {"company", "companies", "firm", "firms",
     "corporation", "corporations", "enterprise", "enterprises",
     "business", "businesses", "organization", "organizations"},

    {"country", "countries", "nation", "nations",
     "state", "states", "land", "lands"},

    {"city", "cities", "town", "towns",
     "urban", "municipality", "metropolis"},

    # ── Spatial / directional ─────────────────────────────────────────────────
    {"near", "close", "nearby", "adjacent", "neighboring"},
    {"far", "distant", "remote", "faraway"},
    {"above", "over", "atop", "overhead"},
    {"below", "under", "beneath", "underneath"},

    # ── Time ──────────────────────────────────────────────────────────────────
    {"old", "aged", "ancient", "elderly", "veteran", "antique"},
    {"new", "novel", "recent", "modern", "contemporary", "current", "fresh"},
    {"fast", "quick", "swift", "rapid", "speedy",
     "brisk", "hasty", "fleet"},  # duplicates fast/quick group — handled by set dedup

]

# ── Build lookup table ────────────────────────────────────────────────────────
# Maps every word (lowercased) → canonical form (alphabetically first in group).
# Built once at import time.

_WORD_TO_CANONICAL: dict[str, str] = {}

def _build_lookup() -> None:
    # FIX: Added collision detection. Words appearing in multiple synonym groups
    # are silently dropped after the first group (first-group-wins). This is
    # intentional but was undocumented. Log collisions so maintainers can
    # clean up the SYNONYM_GROUPS list rather than having silent data loss.
    collisions: dict[str, str] = {}  # word → first canonical it was assigned to
    for group in SYNONYM_GROUPS:
        clean_group = frozenset(group)
        canonical = min(clean_group)
        for word in clean_group:
            w = word.lower()
            if w in _WORD_TO_CANONICAL:
                # Already assigned — record collision but don't overwrite
                collisions[w] = _WORD_TO_CANONICAL[w]
            else:
                _WORD_TO_CANONICAL[w] = canonical
    # Uncomment the line below during development to surface duplicate entries:
    # if collisions: print(f"[synonym_normalizer] {len(collisions)} word collisions across groups: {list(collisions.keys())[:10]}")

_build_lookup()


def get_canonical(word: str) -> str:
    """
    Return the canonical form of a word, or the word itself if it has no
    synonym group in the dictionary.
    """
    return _WORD_TO_CANONICAL.get(word.lower(), word.lower())


# ── Scoring functions ─────────────────────────────────────────────────────────

CONTAINMENT_THRESHOLD = 0.80   # trigger containment mode above this level


def _content_canonical_set(tokens: list[str]) -> set[str]:
    """
    Extract unique content words from a token list and canonicalize them.
    Filters stop words and tokens shorter than 3 characters.
    """
    return {
        get_canonical(t)
        for t in tokens
        if t not in STOP_WORDS and len(t) >= 3
    }


def synonym_keyword_jaccard(tokens_a: list[str],
                             tokens_b: list[str]) -> float:
    """
    Jaccard similarity on synonym-canonicalized content-word sets.

    Returns float in [0.0, 1.0].
    """
    ca = _content_canonical_set(tokens_a)
    cb = _content_canonical_set(tokens_b)
    if not ca or not cb:
        return 0.0
    intersection = len(ca & cb)
    union = len(ca | cb)
    return intersection / union if union > 0 else 0.0


def synonym_containment(tokens_a: list[str],
                         tokens_b: list[str]) -> float:
    """
    Containment score: what fraction of the SHORTER document's canonical
    content words appear in the LONGER document?

    This is the key signal for "expansion plagiarism" where a short sentence
    is padded with filler — all original keywords are still present, but
    Jaccard is diluted by the extras.

    Returns float in [0.0, 1.0].
    """
    ca = _content_canonical_set(tokens_a)
    cb = _content_canonical_set(tokens_b)
    if not ca or not cb:
        return 0.0
    shorter, longer = (ca, cb) if len(ca) <= len(cb) else (cb, ca)
    overlap = len(shorter & longer)
    return overlap / len(shorter) if shorter else 0.0


def synonym_combined_score(tokens_a: list[str],
                            tokens_b: list[str]) -> float:
    """
    Combined synonym-aware semantic score.

    Strategy:
      - Compute synonym Jaccard (good for balanced rewrites)
      - Compute synonym containment (good for expansion plagiarism)
      - If containment >= CONTAINMENT_THRESHOLD (0.80):
            use containment — this is an expansion case, Jaccard would
            unfairly penalize the extra words added around the original.
      - Otherwise:
            use Jaccard — this is a balanced comparison, and we should
            not give extra credit just because one doc happens to cover
            a subset of the other doc's vocabulary.

    Returns float in [0.0, 1.0].
    """
    jac = synonym_keyword_jaccard(tokens_a, tokens_b)
    cont = synonym_containment(tokens_a, tokens_b)

    if cont >= CONTAINMENT_THRESHOLD:
        return cont
    return jac
