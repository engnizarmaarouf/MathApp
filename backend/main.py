import os
import json
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sympy as sp
from openai import OpenAI
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# ==========================================
# 1. Database Configuration (PostgreSQL / SQLite Fallback)
# ==========================================
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.strip():
    DATABASE_URL = DATABASE_URL.strip()
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
        
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    print("Using PostgreSQL Database from environment.")
else:
    print("Warning: DATABASE_URL is not set. Falling back to local SQLite.")
    engine = create_engine("sqlite:///./app_data.db", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class QuizHistoryDB(Base):
    __tablename__ = "quiz_history"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String(100), nullable=True)
    question = Column(Text, nullable=True)
    student_answer = Column(Text, nullable=True)
    correct_solution = Column(Text, nullable=True)
    evaluation = Column(Text, nullable=True)
    timestamp = Column(String(50), nullable=True)

# יצירת הטבלאות בבטחה בעליית השרת
try:
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
except Exception as e:
    print(f"Warning: Database initialization error: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# 2. FastAPI & OpenAI Initialization
# ==========================================
app = FastAPI(title="Math & Physics AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# ==========================================
# 3. Request Schemas
# ==========================================
class SolveRequest(BaseModel):
    expression: str
    type: str = "solve"  # 'solve' or 'derivative'

class TutorRequest(BaseModel):
    question: str
    topic: str = "general"

class GenerateQuizRequest(BaseModel):
    topic: str = "חדווא"
    difficulty: str = "בינוני"

class EvaluateQuizRequest(BaseModel):
    question: str
    student_answer: str
    correct_solution: Optional[str] = ""
    topic: str = "חדווא"

# ==========================================
# 4. API Endpoints
# ==========================================
@app.get("/")
def read_root():
    return {"status": "success", "message": "שרת המתמטיקה והפיזיקה פעיל ומחובר למסד הנתונים בענן!"}

@app.post("/solve")
def solve_math(req: SolveRequest):
    try:
        x = sp.Symbol('x')
        expr = sp.sympify(req.expression)
        steps = []

        if req.type == "derivative":
            steps.append(f"פונקציה מקורית: f(x) = {expr}")
            derivative = sp.diff(expr, x)
            steps.append(f"נגזרת ראשונה: f'(x) = {derivative}")
            simplified = sp.simplify(derivative)
            if simplified != derivative:
                steps.append(f"נגזרת מופשטת: f'(x) = {simplified}")
        else:
            steps.append(f"משוואה לקבלת פתרון: {expr} = 0")
            solutions = sp.solve(expr, x)
            steps.append(f"פתרונות עבור x: {solutions}")

        return {"status": "success", "steps": steps}
    except Exception as e:
        return {"status": "error", "message": f"שגיאה בחישוב המתמטי: {str(e)}"}

@app.post("/tutor")
def ask_tutor(req: TutorRequest):
    if not client:
        return {"status": "error", "reply": "מפתח OpenAI API אינו מוגדר בשרת."}
    try:
        prompt = (
            "אתה מורה פרטי מומחה למתמטיקה ופיזיקה ברמת 5 יחידות לימוד בתיכון. "
            "ענה בעברית, בצורה ברורה, מעודדת ומפורטת צעד אחר צעד.\n\n"
            f"שאילת התלמיד (נושא {req.topic}): {req.question}"
        )
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "אתה מורה פרטי סבלני ומקצועי למתמטיקה ופיזיקה."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=600
        )
        reply = response.choices[0].message.content.strip()
        return {"status": "success", "reply": reply}
    except Exception as e:
        return {"status": "error", "reply": f"שגיאה בפנייה ל-AI: {str(e)}"}

@app.post("/generate-quiz")
def generate_quiz(req: GenerateQuizRequest):
    if not client:
        return {
            "status": "success",
            "data": {
                "question": "חשב את הנגזרת של הפונקציה: f(x) = 3x^2 + 5x - 2",
                "hint": "השתמש בחוק החזקות להורדת המעריך.",
                "solution": "f'(x) = 6x + 5"
            }
        }
    try:
        prompt = (
            f"צור שאלת תרגול במתמטיקה בנושא '{req.topic}' ברמת קושי '{req.difficulty}' ברמת 5 יחידות לימוד.\n"
            "החזר את התשובה בפורמט JSON בלבד, עם המפתחות:\n"
            "{\n"
            '  "question": "נוסח השאלה בעברית",\n'
            '  "hint": "רמז קצר לתלמיד",\n'
            '  "solution": "הפתרון המלא והסופי"\n'
            "}"
        )
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "אתה מחבר בחינות מתמטיקה ופיזיקה. החזר JSON בלבד."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        content = json.loads(response.choices[0].message.content)
        return {"status": "success", "data": content}
    except Exception as e:
        return {
            "status": "success",
            "data": {
                "question": "גזור את הפונקציה f(x) = x^3 - 4x",
                "hint": "גזור כל איבר בנפרד",
                "solution": "f'(x) = 3x^2 - 4"
            }
        }

@app.post("/evaluate-quiz")
def evaluate_quiz(req: EvaluateQuizRequest, db: Session = Depends(get_db)):
    try:
        if client:
            prompt = (
                f"שאלה: {req.question}\n"
                f"תשובת התלמיד: {req.student_answer}\n"
                f"פתרון נכון ייחוס: {req.correct_solution}\n\n"
                "הערך את תשובת התלמיד בעברית בצורה בונה. קבע אם התשובה נכונה, חלקית, או שגויה, והסבר בקצרה."
            )
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "אתה מורה המעריך פתרונות תלמידים במתמטיקה."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400
            )
            eval_text = response.choices[0].message.content.strip()
        else:
            eval_text = "תשובתך נקלטה בהצלחה ונשמרה במסד הנתונים!"

        new_entry = QuizHistoryDB(
            topic=req.topic,
            question=req.question,
            student_answer=req.student_answer,
            correct_solution=req.correct_solution,
            evaluation=eval_text,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        db.add(new_entry)
        db.commit()
        db.refresh(new_entry)

        return {"status": "success", "evaluation": eval_text}
    except Exception as e:
        return {"status": "error", "message": f"שגיאה בהערכת התשובה: {str(e)}"}

@app.get("/history")
def get_history(db: Session = Depends(get_db)):
    try:
        records = db.query(QuizHistoryDB).order_by(QuizHistoryDB.id.desc()).limit(20).all()
        history_list = [
            {
                "id": r.id,
                "topic": r.topic,
                "question": r.question,
                "student_answer": r.student_answer,
                "correct_solution": r.correct_solution,
                "evaluation": r.evaluation,
                "timestamp": r.timestamp
            }
            for r in records
        ]
        return {"status": "success", "history": history_list}
    except Exception as e:
        return {"status": "error", "message": str(e), "history": []}