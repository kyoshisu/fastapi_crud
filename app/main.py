from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db, engine
from app.models import Base
from app.auth import router as auth_router
from app.dependencies import require_auth
from app.background_tasks import load_csv_background, delete_students_background
from app import crud

Base.metadata.create_all(bind=engine)

app = FastAPI(title="University API with Auth")

app.include_router(auth_router)

@app.post("/tasks/load-csv")
def task_load_csv(csv_path: str, background_tasks: BackgroundTasks, _=Depends(require_auth)):
    background_tasks.add_task(load_csv_background, csv_path)
    return {"message": "Фоновая загрузка запущена", "csv_path": csv_path}

@app.post("/tasks/delete-students")
def task_delete_students(student_ids: List[int], background_tasks: BackgroundTasks, _=Depends(require_auth)):
    background_tasks.add_task(delete_students_background, student_ids)
    return {"message": "Фоновое удаление запущено", "student_ids": student_ids}

@app.post("/students")
def create_student(last_name: str, first_name: str, faculty: str, db: Session = Depends(get_db), _=Depends(require_auth)):
    return crud.create_student(db, last_name, first_name, faculty)

@app.get("/students")
def read_students(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), _=Depends(require_auth)):
    return crud.get_students(db, skip, limit)

@app.get("/students/{student_id}")
def read_student(student_id: int, db: Session = Depends(get_db), _=Depends(require_auth)):
    student = crud.get_student(db, student_id)
    if not student:
        raise HTTPException(404, "Студент не найден")
    return student

@app.put("/students/{student_id}")
def update_student(student_id: int, last_name: str = None, first_name: str = None, faculty: str = None, db: Session = Depends(get_db), _=Depends(require_auth)):
    student = crud.update_student(db, student_id, last_name, first_name, faculty)
    if not student:
        raise HTTPException(404, "Студент не найден")
    return student

@app.delete("/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db), _=Depends(require_auth)):
    if not crud.delete_student(db, student_id):
        raise HTTPException(404, "Студент не найден")
    return {"message": "Студент удалён"}

@app.post("/grades")
def create_grade(student_id: int, course: str, score: int, db: Session = Depends(get_db), _=Depends(require_auth)):
    student = crud.get_student(db, student_id)
    if not student:
        raise HTTPException(404, "Студент не найден")
    return crud.create_grade(db, student_id, course, score)

@app.get("/students/{student_id}/grades")
def read_student_grades(student_id: int, db: Session = Depends(get_db), _=Depends(require_auth)):
    return crud.get_grades_by_student(db, student_id)

@app.put("/grades/{grade_id}")
def update_grade(grade_id: int, course: str = None, score: int = None, db: Session = Depends(get_db), _=Depends(require_auth)):
    grade = crud.update_grade(db, grade_id, course, score)
    if not grade:
        raise HTTPException(404, "Оценка не найдена")
    return grade

@app.delete("/grades/{grade_id}")
def delete_grade(grade_id: int, db: Session = Depends(get_db), _=Depends(require_auth)):
    if not crud.delete_grade(db, grade_id):
        raise HTTPException(404, "Оценка не найдена")
    return {"message": "Оценка удалена"}

@app.get("/faculty/{faculty}/students")
def get_students_by_faculty(faculty: str, db: Session = Depends(get_db), _=Depends(require_auth)):
    return crud.get_students_by_faculty(db, faculty)

@app.get("/courses/unique")
def get_unique_courses(db: Session = Depends(get_db), _=Depends(require_auth)):
    return {"courses": crud.get_unique_courses(db)}

@app.get("/courses/{course}/low-grades")
def get_low_grade_students(course: str, threshold: int = 30, db: Session = Depends(get_db), _=Depends(require_auth)):
    return crud.get_students_low_grade_by_course(db, course, threshold)

@app.get("/faculty/{faculty}/average-score")
def get_average_score(faculty: str, db: Session = Depends(get_db), _=Depends(require_auth)):
    avg = crud.get_average_score_by_faculty(db, faculty)
    return {"faculty": faculty, "average_score": avg}

@app.post("/export-csv")
def export_csv(db: Session = Depends(get_db), _=Depends(require_auth)):
    result = crud.export_to_csv(db)
    return {"message": result}