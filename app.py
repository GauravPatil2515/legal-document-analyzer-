from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import httpx, os, re

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class Req(BaseModel):
    data: str

LEGAL_TERMS = {
    "hereinafter": "from now on", "whereas": "since", "thereof": "of that",
    "hereby": "by this", "notwithstanding": "despite", "pursuant to": "according to",
    "indemnify": "protect from loss", "indemnification": "protection from loss",
    "aforementioned": "mentioned earlier", "herein": "in this document",
    "shall": "will", "thereof": "of that", "therein": "in that",
    "forthwith": "immediately", "henceforth": "from now on",
    "inter alia": "among other things", "pro rata": "proportionally",
    "bona fide": "genuine", "de facto": "in practice", "ipso facto": "by that fact",
    "mutatis mutandis": "with necessary changes", "prima facie": "at first sight",
    "viz.": "namely", "i.e.": "that is", "e.g.": "for example",
    "liability": "legal responsibility", "jurisdiction": "legal authority",
    "arbitration": "dispute resolution outside court", "tort": "wrongful act causing harm",
    "plaintiff": "person who sues", "defendant": "person being sued",
    "statute": "written law", "breach": "violation", "fiduciary": "trust-based",
    "lien": "legal claim on property", "waiver": "giving up a right",
    "stipulate": "require as a condition", "rescind": "cancel",
    "null and void": "invalid and unenforceable", "force majeure": "unforeseeable circumstances",
    "quid pro quo": "something for something", "subpoena": "court order to appear",
    "affidavit": "sworn written statement", "deposition": "sworn testimony outside court",
    "amicus curiae": "friend of the court", "habeas corpus": "produce the person in court",
    "in lieu of": "instead of", "pro bono": "free of charge",
    "caveat emptor": "buyer beware", "due diligence": "careful investigation",
}

def local_simplify(text):
    if not text.strip():
        return "Please paste a legal document or clause to get a simplified explanation."
    lower = text.lower()
    result = text
    for term, simple in sorted(LEGAL_TERMS.items(), key=lambda x: -len(x[0])):
        result = re.sub(re.escape(term), simple, result, flags=re.IGNORECASE)
    sentences = re.split(r'(?<=[.!?])\s+', result.strip())
    simplified = []
    for s in sentences:
        s = s.strip()
        if len(s) > 10:
            simplified.append(s)
    out = " ".join(simplified) if simplified else result
    found = [f"• \"{t}\" → {s}" for t, s in LEGAL_TERMS.items() if t in lower]
    summary = f"SIMPLIFIED VERSION:\n{out}"
    if found:
        summary += "\n\nKEY TERMS EXPLAINED:\n" + "\n".join(found[:15])
    return summary

async def try_groq(text):
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        return None
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {key}"}, json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": "You simplify legal documents into plain English. Be concise and clear. List key terms and their meanings."}, {"role": "user", "content": f"Simplify this legal text:\n\n{text[:3000]}"}], "max_tokens": 1024})
        return r.json()["choices"][0]["message"]["content"]

async def try_openrouter(text):
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        return None
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.post("https://openrouter.ai/api/v1/chat/completions", headers={"Authorization": f"Bearer {key}"}, json={"model": "meta-llama/llama-3.3-70b-instruct:free", "messages": [{"role": "system", "content": "You simplify legal documents into plain English. Be concise."}, {"role": "user", "content": f"Simplify this legal text:\n\n{text[:3000]}"}], "max_tokens": 1024})
        return r.json()["choices"][0]["message"]["content"]

@app.post("/solve")
async def solve(req: Req):
    text = req.data.strip()
    if not text:
        return {"output": "Please paste a legal document or clause to get a simplified explanation."}
    for fn in [try_groq, try_openrouter]:
        try:
            r = await fn(text)
            if r:
                return {"output": r}
        except Exception:
            continue
    return {"output": local_simplify(text)}

@app.get("/")
async def index():
    with open("index.html") as f:
        return HTMLResponse(f.read())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
