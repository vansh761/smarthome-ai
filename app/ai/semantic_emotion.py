from sentence_transformers import SentenceTransformer, util
import torch

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
_model = None
_reference_embeddings = None

EMOTION_REFERENCES = {
    "stressed": [
        "I am feeling very stressed and overwhelmed",
        "there is too much pressure and work",
        "I cannot handle all these deadlines",
        "my mind is exhausted from too much work",
        "I am burning out from all the responsibilities",
        "today my mood is not fine because of work",
        "things are not going well and I feel burdened",
        "I am not okay there is too much going on",
        "my head is spinning from all the pressure",
        "everything is going wrong I feel stressed",
        "I feel like I am losing control of things",
        "too much on my plate right now",
        # Hindi
        "bahut zyada tension hai aur kaam khatam nahi ho raha",
        "dimag bilkul kharab ho gaya hai pressure se",
        "itna kaam hai ki sambhal nahi pa raha",
        "aaj bahut pareshan hoon sab kuch galat ho raha",
        # Hinglish
        "yaar bohot stressed hoon kuch samajh nahi aa raha",
        "mujhe na bohot tension ho rahi hai aaj kal",
        "dimag ka bharta ban gaya hai itni tension se",
        "sir dard ho raha hai pressure ke wajah se",
    ],
    "tired": [
        "I am feeling very tired and sleepy",
        "I have no energy left at all",
        "I just want to sleep and rest",
        "my body is exhausted and drained",
        "I cannot keep my eyes open",
        "feeling completely worn out today",
        "I need rest I am so fatigued",
        "too tired to do anything right now",
        "my body feels heavy and slow",
        "I am running on empty today",
         # Hindi
        "bahut thaka hua hoon aaj kuch karne ka mann nahi",
        "neend aa rahi hai aankhe band ho rahi hain",
        "itna thaka hoon ki uth bhi nahi sakta",
        # Hinglish
        "yaar ekdum thak gaya hoon no energy left",
    ],
    "happy": [
        "I am feeling very happy and joyful",
        "today is a wonderful and amazing day",
        "I am excited and in a great mood",
        "feeling fantastic everything is going well",
        "I love today it is so good",
        "my mood is excellent I feel great",
        "feeling on top of the world right now",
        "everything is going perfectly today",
        "I feel light and cheerful today",
        "life feels good and positive right now",
        # Hindi
        "aaj bahut khushi ho rahi hai sab kuch acha lag raha",
        "dil bahut khush hai aaj ka din mast raha",
        "ekdum acha feel ho raha hai bahut mast mood hai",
        # Hinglish
        "yaar aaj toh bahut mast din tha feeling amazing",

    ],
    "sad": [
        "I am feeling very sad and lonely",
        "I feel depressed and low today",
        "feeling heartbroken and miserable",
        "I want to cry everything feels gloomy",
        "my mood is down and I feel unhappy",
        "nothing feels right I am feeling low",
        "feeling blue and disconnected today",
        "today my mood is not fine I feel sad",
        "I do not feel good emotionally",
        "I am not feeling okay today",
        "something feels off I do not know why",
        "just not myself today",
        "today my mood is not fine",
        "I am not doing well today",
        "not having a good time right now",
        "I feel like everything is falling apart",
        "my mood is off today",
        "not feeling great today",
        "feeling a bit off today",
        "I feel empty inside",
        "things do not feel right today",
        "I feel disconnected from everything",
         # Hindi
        "aaj kuch theek nahi lag raha dil udaas hai",
        "mera mood kharab hai kuch acha nahi lag raha",
        "bahut bura lag raha hai aaj kuch sahi nahi",
        "dil nahi lag raha kisi kaam mein aaj",
        "aaj bahut akela feel ho raha hoon",
        # Hinglish
        "yaar mood bilkul kharab hai kuch theek nahi",
        "not feeling okay aaj kuch off lag raha hai",
        "I feel blah and unmotivated today",
    ],
    "angry": [
        "I am feeling very angry and furious",
        "I am so irritated and frustrated",
        "I feel rage and annoyance right now",
        "everything is making me mad today",
        "I am fed up and losing patience",
        "feeling disgusted and deeply annoyed",
        "I want to scream I am so angry",
        "nothing is working and I am furious",
        # Hindi
        "mujhe bahut gussa aa raha hai aaj",
        "bahut irritate ho raha hoon kisi wajah se",
        "aaj mood bilkul off hai bahut gussa aa raha",
        "har choti baat pe gussa aa raha hai yaar",
        # Hinglish
        "yaar aaj bohot gusse mein hoon bas matt poocho",
        "irritated ho raha hoon aaj kal sab cheezon se",
    ],
    "anxious": [
        "I am feeling very anxious and nervous",
        "I am worried and scared about what will happen",
        "feeling panicked and uneasy right now",
        "I cannot calm down I am so restless",
        "dread and fear are overwhelming me",
        "my heart is racing from anxiety",
        "feeling tense and on edge today",
        "I keep worrying about what might go wrong",
        "I have a bad feeling about things",
        # Hindi
        "mujhe bahut tension ho rahi hai aaj kal",
        "mujhe kal se dar lag raha hai kuch galat hoga",
        "ghabrahat ho rahi hai kuch theek nahi lag raha",
        "mind mein same tension chal rahi hai",
        # Hinglish
        "yaar bohot nervous feel kar raha hoon aaj",
        "anxious feel ho raha hai na jaane kyu",
    ],
    "focused": [
        "I am working and fully concentrated",
        "I am studying and being very productive",
        "I am in deep focus mode right now",
        "feeling productive and in the zone",
        "concentrating hard on my work today",
        "I am deeply engaged in what I am doing",
    ],
    "neutral": [
        "I am feeling okay nothing special",
        "everything is normal and fine today",
        "my mood is average nothing particular",
        "I feel alright just going about my day",
        "nothing notable happening today",
        "just a regular average day for me",
        "I just feel blah today",
        "feeling blah nothing in particular",
        "meh kind of day nothing special",
        "just blah today",
    ],
}


def get_model():
    global _model
    if _model is None:
        print("Loading semantic model...")
        _model = SentenceTransformer(MODEL_NAME)
        print("Semantic model loaded")
    return _model


def get_reference_embeddings():
    global _reference_embeddings
    if _reference_embeddings is None:
        model = get_model()
        _reference_embeddings = {}
        for emotion, sentences in EMOTION_REFERENCES.items():
            embs = model.encode(sentences, convert_to_tensor=True)
            _reference_embeddings[emotion] = torch.mean(embs, dim=0)
    return _reference_embeddings


def semantic_emotion_score(text: str) -> dict:
    """
    Returns emotion scores 0-100 based on semantic similarity.
    Higher = more similar to that emotion.
    """
    model     = get_model()
    ref_embs  = get_reference_embeddings()
    input_emb = model.encode(text, convert_to_tensor=True)

    scores = {}
    for emotion, ref_emb in ref_embs.items():
        similarity        = util.cos_sim(input_emb, ref_emb).item()
        scores[emotion]   = round(max(0, similarity * 100), 2)

    return scores


def semantic_top_emotion(text: str) -> tuple:
    """
    Returns (top_emotion, confidence, all_scores).
    Used when keyword system finds nothing.
    """
    scores     = semantic_emotion_score(text)
    sorted_s   = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top        = sorted_s[0][0]
    top_score  = sorted_s[0][1]
    second     = sorted_s[1][1]

    # Confidence: how much does top beat second place
    gap        = top_score - second
    confidence = round(min(85.0, 50.0 + gap * 2), 1)

    return top, confidence, scores