from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sympy as sp

app = FastAPI(title="Math App AI Engine")

# מבנה הבקשה שמתקבלת מהאפליקציה
class MathProblem(BaseModel):
    expression: str  # למשל: "x**2 - 5*x + 6 = 0" או "x**3 + 2*x"
    type: str        # "solve" לפתרון משוואות או "derivative" לנגזרות

@app.get("/")
def root():
    return {"message": "שרת המתמטיקה פעיל ועובד!"}

@app.post("/solve")
def solve_math(problem: MathProblem):
    x = sp.Symbol('x')
    try:
        if problem.type == "solve":
            # פתרון משוואות אלגבריות
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
            # חישוב נגזרת (חדו"א)
            func = sp.sympify(problem.expression)
            diff_func = sp.diff(func, x)
            
            steps = [
                f"1. הפונקציה המקורית: f(x) = {func}",
                f"2. גזירה לפי כללי החדו\"א: f'(x) = {diff_func}",
                f"3. פישוט הביטוי: f'(x) = {sp.simplify(diff_func)}"
            ]
            return {"status": "success", "derivative": str(diff_func), "steps": steps}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"שגיאה בפענוח: {str(e)}")