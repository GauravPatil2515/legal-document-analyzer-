from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import httpx, os, re, pathlib

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class Req(BaseModel):
    data: str = ""

TERMS = {
    "indemnify and hold harmless": "protect and not blame",
    "null and void": "completely invalid",
    "terms and conditions": "rules you must follow",
    "cease and desist": "stop immediately",
    "due diligence": "careful investigation",
    "force majeure": "unforeseeable extraordinary events",
    "caveat emptor": "buyer beware",
    "quid pro quo": "something given in exchange",
    "habeas corpus": "produce the person in court",
    "amicus curiae": "friend of the court",
    "bona fide": "genuine / in good faith",
    "de facto": "in practice",
    "ipso facto": "by that very fact",
    "mutatis mutandis": "with necessary changes made",
    "prima facie": "at first sight / on the face of it",
    "pro rata": "proportionally",
    "inter alia": "among other things",
    "in lieu of": "instead of",
    "pro bono": "done for free",
    "pursuant to": "according to / following",
    "notwithstanding": "despite / regardless of",
    "hereinafter": "referred to from now on as",
    "aforementioned": "previously mentioned",
    "indemnify": "compensate for loss or damage",
    "indemnification": "compensation for loss",
    "herein": "in this document",
    "hereby": "by means of this document",
    "thereof": "of that thing",
    "therein": "in that place or document",
    "whereas": "considering that / since",
    "forthwith": "immediately / without delay",
    "henceforth": "from this point forward",
    "shall": "must / will",
    "liability": "legal responsibility",
    "jurisdiction": "the authority of a court",
    "arbitration": "settling a dispute outside court",
    "tort": "a wrongful act leading to legal liability",
    "plaintiff": "the person bringing a lawsuit",
    "defendant": "the person being sued",
    "statute": "a written law passed by a legislature",
    "breach": "a violation of a law or agreement",
    "fiduciary": "involving trust / acting in someone's best interest",
    "lien": "a legal claim on property as security for a debt",
    "waiver": "voluntarily giving up a right",
    "stipulate": "demand or specify as part of an agreement",
    "rescind": "revoke / cancel / repeal",
    "subpoena": "a legal order to appear in court",
    "affidavit": "a sworn written statement used as evidence",
    "deposition": "a witness's sworn out-of-court testimony",
    "negligence": "failure to take proper care",
    "damages": "money claimed or awarded as compensation",
    "injunction": "a court order to do or stop doing something",
    "litigation": "the process of taking legal action",
    "settlement": "an agreement to resolve a dispute without trial",
    "covenant": "a formal agreement or promise",
    "encumbrance": "a claim or restriction on property",
    "estoppel": "prevented from denying something previously stated",
    "adjudicate": "to make a formal judgment on a dispute",
    "conveyance": "the legal process of transferring property",
    "promissory": "containing or involving a promise",
    "remuneration": "payment for work or services",
    "severability": "if one part is invalid, the rest still applies",
    "subordinate": "of lesser importance or rank",
    "viz.": "namely",
    "i.e.": "that is",
    "e.g.": "for example",
}

PROMPT = """You are a legal document simplifier. Your job is to take complex legal text and explain it in simple, everyday English that anyone can understand.

Follow this format:

PLAIN ENGLISH SUMMARY:
Write 2-4 sentences summarizing what the legal text means in simple words.

KEY POINTS:
• List each important obligation, right, or condition as a bullet point in plain language.

LEGAL TERMS DECODED:
• For each legal/Latin term found, write: "term" → simple meaning

WHAT THIS MEANS FOR YOU:
Write 1-2 sentences about the practical impact on the reader.

Keep it friendly, clear, and avoid legal jargon in your explanation."""

def local_simplify(text):
    if not text.strip():
        return "Please paste a legal document or clause to get a simplified explanation."
    lower = text.lower()
    replaced = text
    found_terms = []
    for term, simple in sorted(TERMS.items(), key=lambda x: -len(x[0])):
        if term.lower() in lower:
            found_terms.append((term, simple))
            replaced = re.sub(re.escape(term), simple, replaced, flags=re.IGNORECASE)
    sentences = re.split(r'(?<=[.;!?])\s+', replaced.strip())
    clean = [s.strip() for s in sentences if len(s.strip()) > 10]
    simplified_text = " ".join(clean) if clean else replaced
    parts = ["PLAIN ENGLISH SUMMARY:", simplified_text, ""]
    if found_terms:
        parts.append("LEGAL TERMS DECODED:")
        for t, s in found_terms[:20]:
            parts.append(f'• "{t}" → {s}')
        parts.append("")
    word_count = len(text.split())
    if word_count > 50:
        parts.append("WHAT THIS MEANS FOR YOU:")
        parts.append("This is a legal clause that defines specific obligations and rights. Read the simplified version above carefully to understand what you're agreeing to.")
    return "\n".join(parts)

async def call_api(url, key, model, text):
    async with httpx.AsyncClient(timeout=12) as c:
        r = await c.post(url, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json={
            "model": model,
            "messages": [
                {"role": "system", "content": PROMPT},
                {"role": "user", "content": f"Simplify this legal text:\n\n{text[:4000]}"}
            ],
            "max_tokens": 1500,
            "temperature": 0.3
        })
        data = r.json()
        if "choices" in data and len(data["choices"]) > 0:
            content = data["choices"][0].get("message", {}).get("content", "")
            if content and len(content) > 20:
                return content
    return None

APIS = [
    ("GROQ_API_KEY", "https://api.groq.com/openai/v1/chat/completions", "llama-3.3-70b-versatile"),
    ("OPENROUTER_API_KEY", "https://openrouter.ai/api/v1/chat/completions", "meta-llama/llama-3.3-70b-instruct:free"),
    ("HUGGINGFACE_API_KEY", "https://api-inference.huggingface.co/models/meta-llama/Llama-3.1-8B-Instruct/v1/chat/completions", "meta-llama/Llama-3.1-8B-Instruct"),
]

@app.post("/solve")
async def solve(req: Req):
    text = (req.data or "").strip()
    if not text:
        return {"output": "Please paste a legal document or clause to get a simplified explanation."}
    for env_key, url, model in APIS:
        key = os.environ.get(env_key, "")
        if not key:
            continue
        try:
            result = await call_api(url, key, model, text)
            if result:
                return {"output": result}
        except Exception:
            continue
    return {"output": local_simplify(text)}

BASE = pathlib.Path(__file__).parent

@app.get("/")
async def index():
    return HTMLResponse((BASE / "index.html").read_text())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
