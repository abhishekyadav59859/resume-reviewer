from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
import os
import httpx
import PyPDF2
import io

load_dotenv()

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/review")
async def review_resume(file: UploadFile = File(...)):
    content = await file.read()
    
    if file.filename.endswith(".pdf"):
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
    else:
        text = content.decode("utf-8", errors="ignore")
    
    
    text = text[:3000]

    prompt = f"""
    You are an expert resume reviewer. Review this resume and give:
    1. Overall Score (out of 10)
    2. Strong Points (3 points)
    3. Weak Points (3 points)
    4. Suggestions to improve (3 points)
    
    Resume:
    {text}
    """

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek/deepseek-r1-0528:free",
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            },
            timeout=60
        )

    result = response.json()
    if "choices" not in result:
        return {"feedback": f"API Error: {result}"}
    reply = result["choices"][0]["message"]["content"]
    return {"feedback": reply}