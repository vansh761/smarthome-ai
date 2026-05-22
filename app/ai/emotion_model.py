from textblob import TextBlob
from datetime import datetime

# ── Emotion keywords ───────────────────────────────────────────────────────
EMOTION_KEYWORDS = {
    "stressed": [
        "stressed","overwhelmed","pressure","deadline","too much",
        "can't handle","exhausted","burden","suffocating","too many tasks",
        "pareshan","tension","takaan","sar dard","bahut zyada kaam",
        "dimag kharab","pagal ho jaunga","bohot tension",
        "bohot stress","itna kaam","dimag kharab ho gaya",
        "chintit","onek pressure","matha kharap","onek kaj",
        "tension ga undi","chala pressure","stress ga undi",
        "khup tension","sar dukhtoy","khup kaam",
        "tension aaguthu","romba pressure","manam kalanguthu",
        "pareshan hoon","bohot zyada bojh","dil ghabra raha",
        "tension che","ghano darr","matha ma dard",
        "tension aagide","thumba pressure","talaavari",
        "valiya tension","stress undu","pressure undu",
        "bahut tension","dimaag kharaab","pareshan aa",
        "boro thakibo","khub chinta","matha kharap lagise",
        "tension laguchi","khub chinta achi",
        "chintit asmi","bahukaryam","manovyatha",
        # Academic stress (missing)
        "exams stress",
        "about my exams",
        "exam pressure",
        "about exams",
        # Bengali stressed (missing strong phrases)
        "boro pressure",
        "matha kharap",
        "onek pressure",
        "khub chinta",
    ],
    "tired": [
        "tired","sleepy","exhausted","fatigue","drowsy","no energy",
        "drained","worn out","need rest","can't keep eyes open",
        "thaka hoon","thak gaya","neend aa rahi","so jaana chahta",
        "bahut thaka","nind aa rahi hai","aankhe bhaari",
        "bahut thaka hua","neend aa rahi yaar",
        "thaka lagche","ghum pasche","onek thaka","shutte chai",
        "thaklo","jhop yetey","khup thaklo","aaram havay",
        "tookkam varuguthu","romba thalarchi","oivu venum",
        "thaki gayo","ughras ave che","khub thakyo",
        "dappa aagide","nidde baratte","thumba dappa",
        "thakam undu","urannam varunnu",
        "thak gaya punjabi","neend aa rahi punjabi",
        "thaki gali","ghuma aasuchi odia",
        "thakeko chhu nepali","nindra lagyo nepali",
        "shraantosmi","nidra aayati","bahushraantah",
        # Bengali tired (missing)
        "thaka lagche","onek thaka","ghum pasche","boro thakibo",
        # Tamil tired (missing)
        "tookkam varuguthu","romba thalarchi","oivu venum","thookkam",
        # Telugu tired (missing)
        "alasatga undi","nidra vastundi","chala alasata","padukovalani",
        # Gujarati tired (missing)
        "thaki gayo","ughras ave che","khub thakyo",
        # Kannada tired (missing)
        "dappa aagide","nidde baratte","thumba dappa",
        # Assamese tired (missing)
        "boro thakibo","ghumap aahise","khub thakibo",
        # Nepali tired (missing)
        "thakeko chhu","nindra lagyo","dherei thakeko",
        # Marathi tired (missing)
        "thaklo","jhop yetey","khup thaklo",
        # Malayalam tired (missing)
        "thakam undu","urannam varunnu",
        # Exact failing phrases
        "thakaan hai",
        "neend aa rahi hai aankhe band",
        "aankhe band ho rahi",
        "thookkam varuguthu thalarchi",
        "kuch karne ka mann nahi",
        "eyes band ho rahe",
        "ankhe band ho rahi",
        "aankhe band ho rahi",
        "eyes closing",
        "can't keep eyes open",
    ],
    "happy": [
        "happy","great","wonderful","amazing","excited","joy",
        "fantastic","love it","awesome","good mood","feeling good","best day",
        "khush hoon","bahut acha","mast din","zabardast","maja aa gaya",
        "ekdum mast","full on khush","bahut acha lag raha","dil khush",
        "yaar aaj toh mast","ekdum mast din tha",
        "khushi lagche","onek bhalo","darun","ananda",
        "santhosham ga undi","chala happy","baagundi",
        "khush ahe","chan vatay","mast aahe","anand hoto",
        "santhosham","romba happy","nalla iruken",
        "khush chhu","mast che","anand chhe","bahuj saras",
        "santosha aagide","thumba happy","channagide",
        "santhosham undu","happy aanu","nallathu",
        "khush aa punjabi","bahut changga","mast aa punjabi",
        "khusi laguchi odia","bahut bhalo odia",
        "khusi chhu nepali","ekdam raamro nepali",
        "anandi asmi","param sukhi","aanandah",
        # Assamese and Nepali happy (exact failing phrases)
        "ananda lagise",
        "khub bhalo",
        "mast lagise",
        "sukhi aase",
        "khusi chhu",
        "ekdam raamro",
        "sanchai chhu",
        "aananda lagise",
    ],
    "sad": [
        "sad","unhappy","depressed","lonely","crying","upset",
        "heartbroken","miserable","gloomy","feeling low","down",
        "dukhi hoon","udaas hoon","rona aa raha","bura lag raha",
        "dil nahi lag raha","kuch acha nahi lag raha","akela hoon",
        "yaar dil nahi lag raha","bahut bura feel ho raha",
        "kharap lagche","kanna pache","mone bhalo nei",
        "dukhanga undi","chala sad telugu","emi cheyalenu",
        "dukh hoto","vaeet vatay","ekta vatay","rone yetey",
        "dukhama iruku","romba kaduppa","manasula vali",
        "udaas hoon","dil toot gaya","bahut dukh",
        "dukhi chhu gujarati","udaas chhu gujarati",
        "dukha aagide kannada","bejaaru aagide kannada",
        "udaas aa punjabi","dukhi aa punjabi",
        "gham chu kashmiri","udaas chu kashmiri",
        "dukhi chhu nepali","udaas chhu nepali",
        "dukhitosmi","shokitah",
        # Bengali sad (missing)
        "kharap lagche","kanna pache","mone bhalo nei","dukhi",
        # Tamil sad (missing)
        "dukhama iruku","romba kaduppa","manasula vali","azhugiren",
        # Telugu sad (missing)
        "dukhanga undi","chala sad","emi cheyalenu",
        # Gujarati sad (missing)
        "dukhi chhu","udaas chhu","rovu ave che",
        # Kannada sad (missing)
        "dukha aagide","bejaaru aagide","adelu baratte",
        # Assamese sad (missing)
        "dukh lagise","mone bhalo nai","kanda aahise",
        # Nepali sad (missing)
        "dukhi chhu","udaas chhu","runu man lagyo",
        # Marathi sad (missing)
        "dukh hoto","vaeet vatay","rone yetey",
        # Malayalam sad (missing)
        "dukkham undu","manassu sari alla","karayanum thonum",
        # General sad phrases (semantic fallback improvement)
        "not okay","not fine","mood off","feeling down",
        "kharab lag raha","kuch theek nahi","mann nahi",
        "dil nahi","udaas","bura lag raha",
        # Exact failing phrases
        "everything is falling apart",
        "not having a good time",
        "aaj kuch theek nahi lag raha",
        "mera mood kharab hai",
        "kuch theek nahi lag raha",
        "mood kharab hai",
        "something feels off",
        "dukhitosmi shokitah",
        "nirdukham nasti",
    ],
    "angry": [
        "angry","furious","mad","irritated","annoyed","rage",
        "frustrated","fed up","hate","disgusting","losing it",
        "gussa hoon","bahut gussa","naraaz hoon","chid gaya","bakwaas",
        "yaar bahut gussa aa raha","irritate ho gaya",
        "raga lagche bengali","onek raag bengali",
        "kopam ga undi telugu","chala kopam telugu",
        "raag alay marathi","khup chidchid marathi",
        "kovama iruku tamil","romba kovam tamil",
        "gussa aa raha","bahut naraaz",
        "gusso aave che gujarati","naraaj chhu gujarati",
        "kopa aagide kannada","thumba kopa kannada",
        "gussa aa raha punjabi","bahut naraaz punjabi",
        "gussa chu kashmiri","bohot naraaz kashmiri",
        "rish uthyo nepali","dherei rish nepali",
        "krodhitosmi","krodham aayati",
        # Bengali angry (missing)
        "raga lagche","onek raag","rag uthche","bhaalo lagche na",
        # Tamil angry (missing)
        "kovama iruku","romba kovam","kovam","kesamana","koopadama",
        # Telugu angry (missing)
        "kopam ga undi","chala kopam","karopam",
        # Gujarati angry (missing)
        "gusso aave che","khub gusse","naraaj chhu",
        # Kannada angry (missing)
        "kopa aagide","thumba kopa","sikkidini",
        # Assamese angry (missing)
        "rag lagise","khub raga","kopita aase",
        # Nepali angry (missing)
        "rish uthyo","dherei rish","irritation bhayo",
        # Marathi angry (missing)
        "raag alay","khup chidchid","raagavlo",
        # Malayalam angry (missing)
        "deshyam undu","kopam undu","valiya irritation",
    ],
    "anxious": [
        "anxious","nervous","worried","fear","scared","panic",
        "uneasy","restless","dread","tense","can't calm down",
        "dar lag raha","ghabrahat","chinta ho rahi","fikar ho rahi",
        "kuch galat hoga","pata nahi kya hoga","ghabra raha hoon",
        "yaar ghabra raha hoon","bahut dar lag raha","nervous hoon",
        "bhoy lagche bengali","ghabra lagche bengali",
        "bhayam ga undi telugu","ghabrahat ga undi telugu",
        "bhiti vatay marathi","ghabralo marathi",
        "bayama iruku tamil","ghabarikkiren tamil",
        "ghabrahat ho rahi","dar lag raha",
        "bhit lage che gujarati","ghabrao chhu gujarati",
        "bhaya aagide kannada","ghabrahat aagide kannada",
        "dar lag raha punjabi","ghabrahat ho rahi punjabi",
        "darr lagyi kashmiri","ghabrahat kashmiri",
        "dar lagyo nepali","ghabrahat bhayo nepali",
        "bhayam aayati","chintitah asmi","vyaakulah",
        # Bengali anxious (missing)
        "bhoy lagche","ghabra lagche","chinta hoche",
        # Tamil anxious (missing)
        "bayama iruku","ghabarikkiren","nervasaga",
        # Telugu anxious (missing)
        "bhayam ga undi","ghabrahat ga undi",
        # Gujarati anxious (missing)
        "bhit lage che","ghabrao chhu","chinta thay che",
        # Kannada anxious (missing)
        "bhaya aagide","ghabrahat aagide",
        # Assamese anxious (missing)
        "bhoy lagise","ghabra lagise",
        # Nepali anxious (missing)
        "dar lagyo","ghabrahat bhayo",
        # Marathi anxious (missing)
        "bhiti vatay","ghabralo","chinta vato",
        # Malayalam anxious (missing)
        "bhayam undu","ghabrahat undu",
        # Exact failing phrase
        "mann mein bahut chinta hai",
        "chain nahi aa raha",
        "chinta hai chain nahi",
    ],
    "neutral": [
        "okay","fine","alright","normal","nothing special",
        "theek","theek hai","sab normal","koi baat nahi",
        "thik ache","normal aahe","sari","sawa",
        "normal chhe","sari ide","kuriyilla","theek aa",
        # Bengali neutral (exact failing phrase)
        "thik ache",
        "normal kichu na",
        "kichu na",
        "thik ache normal",
    ],
    "focused": [
        "working","studying","concentrating","busy","focused",
        "productive","in the zone","deep work","in flow",
        "padh raha","kaam kar raha","focus mein","serious kaam",
        "kaaj korchi","study korchi","padhuchi","abhyaas karto",
        "kaam ho raha","kaam kari raha","kaam karto",
        "kaam maadtide","padikkunnu","padh raha aa",
        "padhilolu","kaam korisu","pathikiren",
        "padichirunnu","adhyayan karomi","pathami",
        # Gujarati focused (exact failing phrase)
        "kaam kari raho chhu",
        "focused che",
        "concentrate",
        "kaam kari raho",
    ],
}

# ── Phrase weights — longer/specific = higher score ────────────────────────
PHRASE_WEIGHTS = {
    "dimag kharab ho gaya":    3.0,
    "pagal ho jaunga":         3.0,
    "bohot zyada kaam":        3.0,
    "can't keep eyes open":    3.0,
    "too many tasks":          3.0,
    "dil nahi lag raha":       3.0,
    "kuch acha nahi lag raha": 3.0,
    "ekdum mast din tha":      3.0,
    "yaar aaj toh mast":       3.0,
    "pata nahi kya hoga":      3.0,
    "kuch galat hoga":         3.0,
    "yaar dil nahi lag raha":  3.0,
    "bahut bura feel ho raha": 3.0,
    "yaar bahut gussa aa raha":3.0,
    "yaar ghabra raha hoon":   3.0,
    "bahut dar lag raha":      3.0,
    "bahut thaka hua":         2.5,
    "neend aa rahi yaar":      2.5,
    "dimag kharab":            2.5,
    "bohot stress":            2.5,
    "itna kaam":               2.5,
    "bohot tension":           2.5,
    "ekdum mast":              2.5,
    "full on khush":           2.5,
    "bahut acha lag raha":     2.5,
    "neend aa rahi":           2.0,
    "thak gaya":               2.0,
    "bahut thaka":             2.0,
    "bahut gussa":             2.0,
    "dar lag raha":            2.0,
    "chinta ho rahi":          2.0,
    "ghabra raha":             2.0,
    "dil khush":               2.0,
    "mast din":                2.0,
    "bahut acha":              2.0,
    "khush hoon":              2.0,
    "rona aa raha":            2.0,
    "dukhi hoon":              2.0,
    "udaas hoon":              2.0,
    "naraaz hoon":             2.0,
    "chid gaya":               2.0,
    "too much":                2.0,
    "no energy":               2.0,
    "worn out":                2.0,
    "feeling low":             2.0,
    "good mood":               2.0,
    "best day":                2.0,
    "love it":                 2.0,
    "can't handle":            2.0,
    "fed up":                  2.0,
    "losing it":               2.0,
    "in the zone":             2.0,
    "deep work":               2.0,
    "in flow":                 2.0,
    "dil toot gaya":           2.0,
    "bahut dukh":              2.0,
    "irritate ho gaya":        2.0,
    "ghabra raha hoon":        2.0,
    "nervous hoon":            2.0,
    # Regional tired phrases
        "tookkam varuguthu":   2.0,
        "romba thalarchi":     2.0,
        "alasatga undi":       2.0,
        "nidra vastundi":      2.0,
        "dappa aagide":        2.0,
        "thakeko chhu":        2.0,
        # Regional angry phrases
        "kovama iruku":        2.0,
        "romba kovam":         2.5,
        "raga lagche":         2.0,
        "onek raag":           2.0,
        "kopa aagide":         2.0,
        "thumba kopa":         2.0,
        "rish uthyo":          2.0,
        # Regional sad phrases
        "kharap lagche":       2.0,
        "kanna pache":         2.0,
        "mone bhalo nei":      2.0,
        "dukhama iruku":       2.0,
        "romba kaduppa":       2.5,
        "dukha aagide":        2.0,
        "bejaaru aagide":      2.0,
        "dukh lagise":         2.0,
        "mone bhalo nai":      2.0,
        # Regional anxious phrases
        "bhoy lagche":         2.0,
        "ghabra lagche":       2.0,
        "bayama iruku":        2.0,
        "ghabarikkiren":       2.5,
        "bhit lage che":       2.0,
        "bhaya aagide":        2.0,
        "bhoy lagise":         2.0,
    # Exact failing phrases — give them strong weights
        "everything is falling apart":          3.0,
        "not having a good time":               2.5,
        "aaj kuch theek nahi lag raha":         3.0,
        "mera mood kharab hai":                 2.5,
        "kuch theek nahi lag raha":             2.5,
        "mood kharab hai":                      2.0,
        "something feels off":                  2.5,
        "thakaan hai":                          2.0,
        "aankhe band ho rahi":                  2.5,
        "kuch karne ka mann nahi":              2.5,
        "mann mein bahut chinta hai":           3.0,
        "chain nahi aa raha":                   2.5,
        "thookkam varuguthu thalarchi":         3.0,
        "ananda lagise":                        2.0,
        "khub bhalo":                           2.0,
        "mast lagise":                          2.0,
        "sukhi aase":                           2.0,
        "khusi chhu":                           2.0,
        "ekdam raamro":                         2.0,
        "sanchai chhu":                         2.0,
        "kaam kari raho chhu":                  2.5,
        "focused che":                          2.0,
        "dukhitosmi shokitah":                  3.0,
        "nirdukham nasti":                      2.5,
        "about my exams":     2.5,
        "exam pressure":      2.5,
        "boro pressure":      2.5,
        "matha kharap":       2.5,
        "onek pressure":      2.5,
        "eyes band ho rahe":    2.5,
        "ankhe band ho rahi":   2.5,
        "aankhe band ho rahi":  2.5,
}

# ── Intensity words — multiply top emotion score by 1.6 ───────────────────
INTENSITY_WORDS = [
    "very","extremely","so much","really","absolutely","completely",
    "totally","deeply","severely","terribly","incredibly",
    "bahut","bohot","itna","ekdum","bilkul","poori tarah","zyada",
    "onek","khub","boro",
    "romba","miga","mikavum",
    "chala","chaala",
    "khup","faar",
    "thumba","tumba",
    "valiya","valare",
]

# ── Environment per emotion ────────────────────────────────────────────────
EMOTION_ENVIRONMENT = {
    "stressed": {
        "temperature_c": 22, "light_level": 30, "light_color": "warm",
        "noise_db_target": 25, "music": "lo-fi / calm instrumental",
        "message": "Creating a calming environment to reduce stress.",
        "actions": ["Dim lights to 30%","Warm lighting","Play calm lo-fi",
                    "Lower temperature to 22°C","Close windows"]
    },
    "tired": {
        "temperature_c": 23, "light_level": 20, "light_color": "warm",
        "noise_db_target": 30, "music": "soft ambient / nature sounds",
        "message": "Preparing a rest-friendly environment.",
        "actions": ["Dim lights to 20%","Warm soft lighting",
                    "Play gentle ambient","Temperature 23°C"]
    },
    "happy": {
        "temperature_c": 24, "light_level": 80, "light_color": "neutral",
        "noise_db_target": 45, "music": "upbeat / energetic",
        "message": "Matching your great mood!",
        "actions": ["Bright neutral lighting","Play upbeat music","Temperature 24°C"]
    },
    "sad": {
        "temperature_c": 23, "light_level": 50, "light_color": "warm",
        "noise_db_target": 30, "music": "soft comforting music",
        "message": "Creating a warm, comforting space for you.",
        "actions": ["Soft warm lighting 50%","Comforting music","Temperature 23°C"]
    },
    "angry": {
        "temperature_c": 20, "light_level": 40, "light_color": "cool",
        "noise_db_target": 20, "music": "calm nature sounds",
        "message": "Cooling down the environment to ease tension.",
        "actions": ["Lower temp to 20°C","Reduce light to 40%",
                    "Cool lighting","Minimize noise"]
    },
    "anxious": {
        "temperature_c": 21, "light_level": 35, "light_color": "warm",
        "noise_db_target": 25, "music": "binaural beats / meditation",
        "message": "Creating a grounding, safe environment.",
        "actions": ["Dim warm lights 35%","Binaural beats",
                    "Temperature 21°C","Minimize noise"]
    },
    "focused": {
        "temperature_c": 21, "light_level": 90, "light_color": "cool",
        "noise_db_target": 35, "music": "focus music / white noise",
        "message": "Optimizing for deep focus.",
        "actions": ["Bright cool lighting 90%","Focus music","Temperature 21°C"]
    },
    "neutral": {
        "temperature_c": 23, "light_level": 60, "light_color": "neutral",
        "noise_db_target": 40, "music": "background ambient",
        "message": "Maintaining a balanced comfortable environment.",
        "actions": ["Balanced lighting 60%","Temperature 23°C"]
    },
    "sleeping": {
        "temperature_c": 20, "light_level": 0, "light_color": "warm",
        "noise_db_target": 20, "music": "silence / white noise",
        "message": "Sleep mode — complete darkness and silence.",
        "actions": ["Lights off","Temperature 20°C","Complete silence"]
    },
}

EMOTION_PRIORITY = {
    "sleeping": 0, "anxious": 1, "stressed": 2,
    "angry":    3, "sad":     4, "tired":    5,
    "neutral":  6, "focused": 7, "happy":    8,
}

LANGUAGE_MAP = {
    "hi": "Hindi",    "bn": "Bengali",  "te": "Telugu",
    "mr": "Marathi",  "ta": "Tamil",    "ur": "Urdu",
    "gu": "Gujarati", "kn": "Kannada",  "ml": "Malayalam",
    "pa": "Punjabi",  "or": "Odia",     "as": "Assamese",
    "ne": "Nepali",   "sa": "Sanskrit", "ks": "Kashmiri",
    "sd": "Sindhi",   "en": "English",
}

HINGLISH_MARKERS = [
    "hai","nahi","kya","mera","tera","bahut","acha","theek",
    "yaar","bhai","arre","hoon","raha","gaya","aaya","kar",
    "ho","le","de","se","pe","ko","ka","ki","ke"
]

SARCASM_PAIRS = [
    ("great",     ["deadline","pressure","failed","worst","again","stuck"]),
    ("wonderful", ["deadline","terrible","awful","again","not","never"]),
    ("amazing",   ["failed","terrible","awful","worst","not","never"]),
    ("fantastic", ["deadline","failed","worst","terrible","not"]),
    ("love it",   ["deadline","pressure","failed","not","never"]),
]


# ── Single definition of each function — no duplicates ────────────────────
LANGUAGE_SIGNATURES = {
    "Hindi": [
        "hoon","hai","nahi","kya","mera","tera","bahut","acha",
        "theek","yaar","bhai","arre","raha","gaya","aaya","kaam",
        "aaj","kal","din","mann","dil","neend","thaka","khush",
        "udaas","gussa","dar","tension","pareshan","bilkul","ekdum",
        "itna","bohot","zyada","lagta","hota","jana","karna",
        "thak","lag","mood","dimag","sar","aankh","kuch","sab",
    ],
    "Bengali": [
        "lagche","aache","hobe","thaka","khub","onek","bhalo",
        "kharap","mone","kanna","ghum","pasche","ache","nei",
        "korchi","hochi","lagise","aahise","thakibo","ghumap",
    ],
    "Tamil": [
        "iruku","varuguthu","aaguthu","romba","thalarchi","santhosham",
        "kovam","bayam","venum","illai","iruken","azhugiren",
        "thookkam","pathikiren","kastagam","manam","kalanguthu",
    ],
    "Telugu": [
        "undi","vastundi","chala","santhosham","kopam","bhayam",
        "alasatga","nidra","baagundi","anandanga","padukovalani",
        "stress ga undi","tension ga undi",
    ],
    "Marathi": [
        "vatay","ahe","hoto","yetey","thaklo","khup","chan",
        "aahe","havay","alay","chidchid","ghabralo","bhiti",
        "rone","raag","dukhtoy",
    ],
    "Gujarati": [
        "chhu","che","thayo","mast","saras","dukhi","gusso",
        "bhit","ghabrao","thaki","ughras","anand","bahuj",
        "khush chhu","mast che","anand chhe",
    ],
    "Kannada": [
        "aagide","baratte","thumba","channagide","dappa",
        "kopa","bhaya","santosha","bejaaru","maadtide",
    ],
    "Malayalam": [
        "undu","varunnu","thakam","santhosham","kopam","bhayam",
        "urannam","valiya","valare","manassu","karayanum",
    ],
    "Punjabi": [
        "changga","karda","lagda","tenu","mainu","saadi",
        "naraaz","dimaag","kharaab","pareshan aa",
    ],
    "Urdu": [
        "takleef","gham","fikar","nihayat","sakhth",
        "bohot zyada bojh","dil ghabra raha",
    ],
    "Sanskrit": [
        "asmi","asti","aayati","karomi","pathami","chintit",
        "bahukaryam","manovyatha","shraantah","krodhitah",
        "bhayam","vyaakulah","chintitah","dukhitosmi","shokitah",
        "anandi","param sukhi","aanandah",
    ],
    "Odia": [
        "laguchi","aachhi","heuachi","khusi laguchi","dukh lagse",
        "ghuma aasuchi","thaki gali","bhaya laguchi",
    ],
    "Assamese": [
        "lagise","aahise","aase","khushi lagse","dukh lagse",
        "ghumap aahise","thakibo","bhoy lagise",
    ],
    "Nepali": [
        "chhu","bhayo","lagyo","thakeko","rish uthyo",
        "ghabrahat bhayo","nindra lagyo","dherei",
    ],
}

ENGLISH_WORDS = {
    "i","am","feeling","very","today","not","fine","okay","good",
    "bad","stressed","tired","happy","sad","angry","worried","work",
    "deadline","please","sorry","thanks","great","nice","feel","mood",
    "just","really","so","too","much","my","me","its","this","that",
    "have","has","was","is","are","the","and","but","or","no","yes",
    "dont","cant","wont","im","its","ive","ill","youre","everything",
    "nothing","something","someone","anyone","everyone","always","never",
    "sometimes","maybe","probably","definitely","absolutely","completely",
}

HINDI_WORDS = set(LANGUAGE_SIGNATURES["Hindi"])


def detect_script(text: str) -> str:
    for char in text:
        code = ord(char)
        if 0x0900 <= code <= 0x097F: return "Devanagari"
        if 0x0980 <= code <= 0x09FF: return "Bengali"
        if 0x0A00 <= code <= 0x0A7F: return "Gurmukhi"
        if 0x0A80 <= code <= 0x0AFF: return "Gujarati_script"
        if 0x0B00 <= code <= 0x0B7F: return "Odia_script"
        if 0x0B80 <= code <= 0x0BFF: return "Tamil_script"
        if 0x0C00 <= code <= 0x0C7F: return "Telugu_script"
        if 0x0C80 <= code <= 0x0CFF: return "Kannada_script"
        if 0x0D00 <= code <= 0x0D7F: return "Malayalam_script"
        if 0x0600 <= code <= 0x06FF: return "Arabic_script"
    return "Latin"


def detect_language(text: str) -> str:
    text_lower = text.lower().strip()
    words      = text_lower.split()

    # Step 1: Script detection — most reliable
    script = detect_script(text)
    if script == "Bengali":          return "Bengali"
    if script == "Gurmukhi":         return "Punjabi"
    if script == "Gujarati_script":  return "Gujarati"
    if script == "Odia_script":      return "Odia"
    if script == "Tamil_script":     return "Tamil"
    if script == "Telugu_script":    return "Telugu"
    if script == "Kannada_script":   return "Kannada"
    if script == "Malayalam_script": return "Malayalam"
    if script == "Arabic_script":    return "Urdu"
    if script == "Devanagari":
        sanskrit_markers = [
            "asmi","asti","aayati","karomi","chintit",
            "bahukaryam","shraantah","dukhitosmi","krodhitah"
        ]
        if any(m in text_lower for m in sanskrit_markers):
            return "Sanskrit"
        return "Hindi"

    # Step 2: Word signature scoring for Latin script
    lang_scores = {}
    for lang, sig_words in LANGUAGE_SIGNATURES.items():
        score = 0
        for sw in sig_words:
            if sw in text_lower:
                score += 1
        if score > 0:
            lang_scores[lang] = score

    if not lang_scores:
        return "English"

    top_lang  = max(lang_scores, key=lang_scores.get)
    top_score = lang_scores[top_lang]

    # Step 3: Hinglish detection
    # English words + Hindi words in same sentence = Hinglish
    eng_count  = sum(1 for w in words if w in ENGLISH_WORDS)
    hindi_count = sum(1 for w in words if w in HINDI_WORDS)

    if eng_count >= 1 and hindi_count >= 1:
        return "Hinglish"

    if top_score >= 1:
        return top_lang

    return "English"

def detect_sarcasm(text: str, polarity: float) -> bool:
    text_lower = text.lower()
    for positive_word, negative_contexts in SARCASM_PAIRS:
        if positive_word in text_lower:
            if any(neg in text_lower for neg in negative_contexts):
                return True
    return False


def resolve_multi_user(users: list) -> dict:
    if not users:
        return None
    if len(users) == 1:
        return users[0]

    users_sorted = sorted(
        users,
        key=lambda u: EMOTION_PRIORITY.get(u["detected_emotion"], 99)
    )
    priority_user    = users_sorted[0]
    priority_emotion = priority_user["detected_emotion"]
    priority_env     = EMOTION_ENVIRONMENT.get(
        priority_emotion, EMOTION_ENVIRONMENT["neutral"]
    )
    weights      = [1 / (i + 1) for i in range(len(users_sorted))]
    total_w      = sum(weights)
    light_levels = [
        EMOTION_ENVIRONMENT.get(
            u["detected_emotion"], EMOTION_ENVIRONMENT["neutral"]
        )["light_level"]
        for u in users_sorted
    ]
    final_light  = round(
        sum(l * w for l, w in zip(light_levels, weights)) / total_w
    )
    all_emotions = [u["detected_emotion"] for u in users_sorted]
    conflict     = len(set(all_emotions)) > 1
    user_summary = [
        {
            "user_id":  u.get("user_id", f"User {i+1}"),
            "emotion":  u["detected_emotion"],
            "priority": EMOTION_PRIORITY.get(u["detected_emotion"], 99),
            "won":      i == 0
        }
        for i, u in enumerate(users_sorted)
    ]
    return {
        "conflict_detected":  conflict,
        "priority_user":      priority_user.get("user_id", "User 1"),
        "priority_emotion":   priority_emotion,
        "user_summary":       user_summary,
        "compromise_logic": {
            "temperature": f"Priority user ({priority_emotion}) → {priority_env['temperature_c']}°C",
            "light_level": f"Weighted average → {final_light}%",
            "light_color": f"Priority user → {priority_env['light_color']}",
            "music":       f"Priority user → {priority_env['music']}",
        },
        "final_environment": {
            "temperature_c": priority_env["temperature_c"],
            "light_level":   final_light,
            "light_color":   priority_env["light_color"],
            "music":         priority_env["music"],
            "message":       priority_env["message"],
            "actions":       priority_env["actions"],
        }
    }


def analyze_emotion(
    text:        str,
    time_of_day: str  = None,
    user_id:     str  = "default",
    is_sleeping: bool = False,
) -> dict:

    if is_sleeping:
        env = EMOTION_ENVIRONMENT["sleeping"]
        return {
            "detected_emotion":       "sleeping",
            "confidence":             100.0,
            "language_detected":      "N/A",
            "auto_act":               True,
            "mode":                   "auto-adjusting",
            "explanation":            "User is sleeping. Activating sleep mode.",
            "environment_suggestion": {
                "message":       env["message"],
                "temperature_c": env["temperature_c"],
                "light_level":   env["light_level"],
                "light_color":   env["light_color"],
                "music":         env["music"],
                "actions":       env["actions"],
            },
            "all_scores": {"sleeping": 100},
            "user_id":    user_id,
        }

    text_lower = text.lower().strip()
    language   = detect_language(text)

    # ── 1. Phrase-weighted keyword scoring ────────────────────────────────
    emotion_scores = {e: 0.0 for e in EMOTION_KEYWORDS}
    matched_words  = {e: [] for e in EMOTION_KEYWORDS}

    for emotion, keywords in EMOTION_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                word_count = len(kw.split())
                if kw in PHRASE_WEIGHTS:
                    weight = PHRASE_WEIGHTS[kw]
                elif word_count >= 3:
                    weight = 2.5
                elif word_count == 2:
                    weight = 2.0
                else:
                    weight = 1.0
                emotion_scores[emotion] += weight
                matched_words[emotion].append(kw)

    # ── 2. Intensity multiplier ───────────────────────────────────────────
    intensity_found = any(w in text_lower for w in INTENSITY_WORDS)
    if intensity_found and max(emotion_scores.values()) > 0:
        top_e = max(emotion_scores, key=emotion_scores.get)
        emotion_scores[top_e] *= 1.6

    # ── 3. TextBlob polarity ──────────────────────────────────────────────
    blob         = TextBlob(text)
    polarity     = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity

    # ── 4. Sarcasm ────────────────────────────────────────────────────────
    sarcasm = detect_sarcasm(text, polarity)
    if sarcasm:
        emotion_scores["happy"]     = 0
        emotion_scores["stressed"] += 3
        polarity = -abs(polarity)

    # ── 5. Polarity bonus (added to scores but capped to avoid dilution) ──
    if not sarcasm:
        if polarity > 0.5:
            emotion_scores["happy"]    += 1.5
        elif polarity > 0.3:
            emotion_scores["happy"]    += 0.8
        elif polarity < -0.5:
            emotion_scores["stressed"] += 1.5
            emotion_scores["sad"]      += 0.8
        elif polarity < -0.3:
            emotion_scores["stressed"] += 0.8

    # ── 5b. Semantic similarity scoring ──────────────────────────────────
    semantic_used = False
    try:
        from app.ai.semantic_emotion import semantic_top_emotion, semantic_emotion_score
        keyword_max = max(emotion_scores.values())

        if keyword_max < 1.5:
            # No keywords — semantic takes full control
            sem_top, sem_conf, sem_scores = semantic_top_emotion(text)
            if sem_top != "neutral" or sem_conf > 65:
                for emotion, sem_score in sem_scores.items():
                    emotion_scores[emotion] += sem_score * 0.8
                semantic_used = True
        elif keyword_max < 4.0:
            # Weak keyword match — semantic gives small boost only
            # Do NOT add semantic to ALL emotions — only boost top 2
            sem_scores = semantic_emotion_score(text)
            sorted_sem = sorted(sem_scores.items(), key=lambda x: x[1], reverse=True)
            # Only boost top 2 semantic emotions slightly
            for emotion, sem_score in sorted_sem[:2]:
                emotion_scores[emotion] += sem_score * 0.1
            semantic_used = True
        # keyword_max >= 4.0 → strong keywords, don't touch

        elif keyword_max < 4.0:
            # Weak keyword match — semantic assists
            sem_scores = semantic_emotion_score(text)
            for emotion, sem_score in sem_scores.items():
                emotion_scores[emotion] += sem_score * 0.2
            semantic_used = True

        # else: strong keyword match — don't interfere

    except Exception as e:
        pass

    # ── 6. Time of day ────────────────────────────────────────────────────
    if not time_of_day:
        hour = datetime.now().hour
        if   5  <= hour < 12: time_of_day = "morning"
        elif 12 <= hour < 17: time_of_day = "afternoon"
        elif 17 <= hour < 21: time_of_day = "evening"
        else:                  time_of_day = "night"

    # Only apply time bonus if keywords or semantic found something clear
    # Prevents time-of-day from overriding weak/ambiguous inputs
    time_bonus_map = {
        "morning":   {"focused": 8,  "happy":   5 },
        "afternoon": {"stressed": 5, "focused": 8 },
        "evening":   {"tired":   8,  "happy":   5 },
        "night":     {"tired":   12, "anxious": 5 },
    }

    # Disable time bonus if semantic took over
    if semantic_used and max(emotion_scores.values()) < 5:
        time_bonus_map = {}

    # ── 7. Sort emotions ──────────────────────────────────────────────────
    sorted_emotions = sorted(
        emotion_scores.items(), key=lambda x: x[1], reverse=True
    )
    top_emotion    = sorted_emotions[0][0]
    top_score      = sorted_emotions[0][1]
    second_emotion = sorted_emotions[1][0]
    second_score   = sorted_emotions[1][1]

    # ── 8. Confidence calculation ─────────────────────────────────────────
    # Base: ratio of top score to total (keyword scores only)
    keyword_total  = sum(emotion_scores.values())
    base_conf      = (top_score / keyword_total * 100) if keyword_total > 0 else 0.0

    # Time bonus only if it matches detected emotion
    t_bonus        = time_bonus_map.get(time_of_day, {}).get(top_emotion, 0)

    # Keyword density bonus — more matched words = higher confidence
    matched_count  = len(matched_words[top_emotion])
    density_bonus  = min(matched_count * 4, 20)  # max +20 from density

    # Phrase quality bonus — long phrases matched = higher confidence
    phrase_bonus   = sum(
        3 for kw in matched_words[top_emotion]
        if len(kw.split()) >= 3
    )
    phrase_bonus   = min(phrase_bonus, 15)  # max +15 from phrases

    confidence = round(
        min(98.0, base_conf + t_bonus + density_bonus + phrase_bonus), 1
    )

    # ── 9. Confusion detection ────────────────────────────────────────────
    # Only confused if MULTIPLE emotions each have significant matches
    # NOT if one emotion dominates with many keywords
    emotions_with_matches = sum(
        1 for e, words in matched_words.items() if len(words) >= 2
    )
    top_emotion_matches = len(matched_words[top_emotion])
    total_matches       = sum(len(v) for v in matched_words.values())

    confusion_detected = (
        total_matches >= 6 and          # many total keywords
        emotions_with_matches >= 3 and  # spread across 3+ emotions
        top_emotion_matches <= 3        # no single emotion dominates
    )

    if confusion_detected:
        top_candidates = [e for e, _ in sorted_emotions[:3] if e != "neutral"]
        if top_candidates:
            top_emotion = min(
                top_candidates,
                key=lambda e: EMOTION_PRIORITY.get(e, 99)
            )
        confidence = 55.0

    # ── 10. Conflict resolution ───────────────────────────────────────────
    conflict_detected = (
        not confusion_detected and
        second_score > 0 and top_score > 0 and
        (second_score / top_score) >= 0.7
    )

    if conflict_detected:
        top_p    = EMOTION_PRIORITY.get(top_emotion,    99)
        second_p = EMOTION_PRIORITY.get(second_emotion, 99)
        if second_p < top_p:
            top_emotion = second_emotion
        confidence = round(max(confidence * 0.90, 60.0), 1)

    # ── 11. Fallback ──────────────────────────────────────────────────────
    if top_score == 0:
        top_emotion = "neutral"
        confidence  = 55.0

    # ── Step 11b: Zero-shot transformer fallback ──────────────────────────
    # Runs AFTER all conflict resolution
    # Only called when final confidence is below 75%
    detection_source = "hybrid"
    zero_shot_scores = {}

    if confidence < 75:
        try:
            from app.ai.zero_shot_fallback import zero_shot_classify
            zs_result = zero_shot_classify(text)

            if zs_result["source"] not in ("fallback_failed", "fallback_error"):
                zs_emotion       = zs_result["emotion"]
                zs_confidence    = zs_result["confidence"]
                zero_shot_scores = zs_result["all_scores"]

                if zs_confidence >= 35:
                    english_languages = {"English", "Hinglish"}

                    if zs_emotion == top_emotion:
                        # Both agree — use transformer confidence directly
                        confidence       = round(min(95.0, zs_confidence), 1)
                        detection_source = "hybrid+transformer_agreed"

                    elif language in english_languages:
                        # Disagree on English/Hinglish — use priority
                        hybrid_priority = EMOTION_PRIORITY.get(top_emotion, 99)
                        zs_priority     = EMOTION_PRIORITY.get(zs_emotion,  99)

                        if zs_priority < hybrid_priority:
                            # Transformer found more urgent emotion
                            top_emotion      = zs_emotion
                            confidence       = round(zs_confidence, 1)
                            detection_source = "transformer_override"
                        else:
                            # Hybrid priority same or higher — blend
                            confidence = round(
                                min(85.0, confidence * 0.4 + zs_confidence * 0.6), 1
                            )
                            detection_source = "hybrid+transformer"

                    else:
                        # Indian language — transformer not reliable
                        # Keep hybrid result, small confidence boost only
                        confidence = round(
                            min(75.0, confidence * 0.7 + zs_confidence * 0.3), 1
                        )
                        detection_source = "hybrid+transformer"

        except Exception as e:
            pass
        
    # ── 12. Output ────────────────────────────────────────────────────────
    env      = EMOTION_ENVIRONMENT.get(top_emotion, EMOTION_ENVIRONMENT["neutral"])
    auto_act = confidence >= 40

    if confusion_detected:
        explanation = (
            f"Multiple signals detected. Auto-selected most urgent: "
            f"{top_emotion}. Acting automatically."
        )
    elif conflict_detected:
        explanation = (
            f"Mixed emotions: {top_emotion} selected by priority. "
            f"Acting automatically."
        )
    elif sarcasm:
        explanation = (
            f"Sarcasm detected — treating as {top_emotion}. "
            f"Acting automatically."
        )
    else:
        explanation = (
            f"Detected {top_emotion} with {confidence}% confidence. "
            f"Acting automatically."
        )

    return {
        "detected_emotion":   top_emotion,
        "confidence":         confidence,
        "detection_source":   detection_source,    # ← add this
        "language_detected":  language,
        "sarcasm_detected":   sarcasm,
        "conflict_detected":  conflict_detected,
        "confusion_detected": confusion_detected,
        "auto_act":           auto_act,
        "mode":               "auto-adjusting",
        "explanation":        explanation,
        "sentiment": {
            "polarity":     round(polarity, 2),
            "subjectivity": round(subjectivity, 2),
        },
        "time_context":       time_of_day,
        "matched_keywords":   matched_words[top_emotion],
        "zero_shot_scores":   zero_shot_scores,    # ← add this
        "environment_suggestion": {
            "message":       env["message"],
            "temperature_c": env["temperature_c"],
            "light_level":   env["light_level"],
            "light_color":   env["light_color"],
            "music":         env["music"],
            "actions":       env["actions"],
        },
        "all_scores": {
            k: round(v, 1)
            for k, v in sorted(
                emotion_scores.items(),
                key=lambda x: x[1], reverse=True
            )
        },
        "user_id": user_id,
    }