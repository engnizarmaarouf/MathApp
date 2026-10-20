import os
import sqlite3
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sympy as sp
import io
import base64
from PIL import Image
from openai import OpenAI

app = FastAPI(title="Math & Physics AI Engine - Cloud Edition")

# --- הגדרת הרשאות CORS לגישה מהדפדפן בענן ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- הגדרת מסד הנתונים SQLite ---
DB_FILE = "app_data.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT DEFAULT 'תלמיד 5 יחידות',
            topic TEXT,
            question TEXT,
            student_answer TEXT,
            evaluation TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- הגדרת מפתח ה-API של OpenAI מתוך משתני הסביבה בענן ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY_HERE")
client = OpenAI(api_key=OPENAI_API_KEY)

FORMULAS_DATABASE = {
    "geometry": [
        {"name": "משפט פיתגורס", "formula": "a² + b² = c²", "desc": "במשולש ישר זווית, סכום ריבועי הניצבים שווה לריבוע היתר."},
        {"name": "משפט הסינוסים", "formula": "a / sin(α) = b / sin(β) = c / sin(γ) = 2R", "desc": "יחס בין צלע לסינוס הזווית שממולה שווה לקוטר המעגל החוסם."},
        {"name": "משפט הקוסינוסים", "formula": "c² = a² + b² - 2ab·cos(γ)", "desc": "חישוב צלע במשולש כללי לפי שתי צלעות והזווית ביניהן."},
        {"name": "סכום זוויות במשולש", "formula": "α + β + γ = 180°", "desc": "סכום הזוויות הפנימיות בכל משולש הוא 180 מעלות."}
    ],
    "physics_mechanics": [
        {"name": "חוק שני של ניוטון", "formula": "F_net = m · a", "desc": "שקול הכוחות הפועלים על גוף שווה למכפלת מסתו בתאוצתו."},
        {"name": "אנרגיה קינטית", "formula": "E_k = ½ · m · v²", "desc": "אנרגיית תנועה של גוף בעל מסה m ומהירות v."},
        {"name": "אנרגיה פוטנציאלית כובדית", "formula": "E_p = m · g · h", "desc": "אנרגיה אגורה בגוף כתוצאה מגובהו מעל פני הקרקע."},
        {"name": "מתקף ומתקף-תנופה", "formula": "J = Δp = F · Δt", "desc": "שינוי בתנע שווה למתקף הכוח הפועל על הגוף."}
    ],
    "physics_electricity": [
        {"name": "חוק אוהם", "formula": "V = I · R", "desc": "מתח במעגל שווה למכפלת הזרם בהתנגדות."},
        {"name": "חוק קולון", "formula": "F = k · |q1 · q2| / r²", "desc": "כוח חשמלי בין שני מטענים נקודתיים."},
        {"name": "הספק חשמלי", "formula": "P = V · I = I² · R", "desc": "קצב המרת אנרגיה חשמלית לרכיב."}
    ]
}

class MathProblem(BaseModel):
    expression: str
    type: str

class TutorRequest(BaseModel):
    question: str
    topic: str = "general"

class QuizGenerateRequest(BaseModel):
    topic: str
    difficulty: str

class QuizEvaluateRequest(BaseModel):
    question: str
    student_answer: str
    correct_solution: str
    topic: str = "חדווא"

@app.get("/")
def root():
    return {"message": "שרת המתמטיקה והפיזיקה פעיל בענן!"}

@app.get("/formulas/{category}")
def get_formulas(category: str):
    if category in FORMULAS_DATABASE:
        return {"status": "success", "data": FORMULAS_DATABASE[category]}
    return {"status": "error", "message": "קטגוריה לא נמצאה"}

@app.post("/solve")
def solve_math(problem: MathProblem):
    x = sp.Symbol('x')
    try:
        if problem.type == "solve":
            lhs, rhs = problem.expression.split('=') if '=' in problem.expression else (problem.expression, '0')
            eq = sp.Eq(sp.sympify(lhs), sp.sympify(rhs))
            solutions = sp.solve(eq, x)
            steps = [
                f"1. ניסוח המשוואה: {sp.pretty(eq)}",
                f"2. העברת אגפים ופישוט: {sp.pretty(sp.simplify(sp.sympify(lhs) - sp.sympify(rhs)))} = 0",
                f"3. פתרון סופי: x = {solutions}"
            ]
            return {"status": "success", "solutions": [str(s) for s in solutions], "steps": steps}

        elif problem.type == "derivative":
            func = sp.sympify(problem.expression)
            diff_func = sp.diff(func, x)
            steps = [
                f"1. הפונקציה המקורית: f(x) = {func}",
                f"2. גזירה לפי כללי החדו\"א: f'(x) = {diff_func}",
                f"3. פישוט הביטוי: f'(x) = {sp.simplify(diff_func)}"
            ]
            return {"status": "success", "derivative": str(diff_func), "steps": steps}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"שגיאה בפענוח הביטוי: {str(e)}")

@app.post("/ocr-scan")
async def scan_image(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        base64_image = base64.b64encode(contents).decode('utf-8')

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "פענח את התרגיל או השאלה מהתמונה. ספק נוסח מדויק ופתרון מפורט בעברית."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=1000
        )
        extracted_text = response.choices[0].message.content
        return {"status": "success", "detected_text": extracted_text}
    except Exception as e:
        return {"status": "error", "message": f"שגיאה בפענוח התמונה: {str(e)}"}

@app.post("/tutor")
def ai_tutor(req: TutorRequest):
    try:
        system_prompt = "אתה מורה פרטי מומחה למתמטיקה ופיזיקה 5 יחידות. ספק הסברים מפורטים בעברית צעד-אחר-צעד."
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"נושא: {req.topic}\nשאלה: {req.question}"}
            ],
            temperature=0.3
        )
        reply = response.choices[0].message.content
        return {"status": "success", "reply": reply}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"שגיאה בתקשורת עם ה-AI: {str(e)}")

@app.post("/generate-quiz")
def generate_quiz(req: QuizGenerateRequest):
    try:
        prompt = (
            f"צור שאלת תרגול במתמטיקה לבגרות 5 יחידות בנושא {req.topic} ברמת קושי: {req.difficulty}.\n"
            "החזר אך ורק מבנה JSON תקין במבנה הבא:\n"
            '{"question": "נוסח השאלה", "hint": "רמז", "solution": "הפתרון המלא"}'
        )
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        raw_text = response.choices[0].message.content.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:-3].strip()
        
        quiz_data = json.loads(raw_text)
        return {"status": "success", "data": quiz_data}
    except Exception:
        return {
            "status": "success",
            "data": {
                "question": f"פתור את המשוואה הבאה ברמת 5 יחידות ({req.topic}): x^2 - 7x + 12 = 0",
                "hint": "השתמש בנוסחת השורשים.",
                "solution": "x1 = 3, x2 = 4"
            }
        }

@app.post("/evaluate-quiz")
def evaluate_quiz(req: QuizEvaluateRequest):
    try:
        prompt = (
            f"השאלה שנשאלה: {req.question}\n"
            f"תשובת התלמיד: {req.student_answer}\n"
            f"הפתרון הנכון: {req.correct_solution}\n\n"
            "הערך את תשובת התלמיד וספק משוב פדגוגי בעברית."
        )
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        evaluation = response.choices[0].message.content

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO student_history (topic, question, student_answer, evaluation, timestamp) VALUES (?, ?, ?, ?, ?)",
            (req.topic, req.question, req.student_answer, evaluation, datetime.now().strftime("%Y-%m-%d %H:%M"))
        )
        conn.commit()
        conn.close()

        return {"status": "success", "evaluation": evaluation}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"שגיאה בהערכת התשובה: {str(e)}")

@app.get("/history")
def get_history():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT topic, question, student_answer, evaluation, timestamp FROM student_history ORDER BY id DESC LIMIT 10")
        rows = cursor.fetchall()
        conn.close()

        history = [
            {
                "topic": row[0],
                "question": row[1],
                "student_answer": row[2],
                "evaluation": row[3],
                "timestamp": row[4]
            }
            for row in rows
        ]
        return {"status": "success", "history": history}
    except Exception as e:
        return {"status": "error", "message": str(e)}