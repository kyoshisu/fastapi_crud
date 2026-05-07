from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db, engine
from app.models import Base, Student, Grade

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.post("/load-csv")
def load_csv(db: Session = Depends(get_db)):
    import csv

    db.query(Grade).delete()
    db.query(Student).delete()
    db.commit()
    
    students_cache = {}
    
    with open("students.csv", "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            key = (row["Фамилия"], row["Имя"], row["Факультет"])
            
            if key not in students_cache:
                student = Student(
                    last_name=row["Фамилия"],
                    first_name=row["Имя"],
                    faculty=row["Факультет"]
                )
                db.add(student)
                db.flush()
                students_cache[key] = student.id
            
            grade = Grade(
                student_id=students_cache[key],
                course=row["Курс"],
                score=int(row["Оценка"])
            )
            db.add(grade)
    
    db.commit()
    return {"message": "Данные загружены"}

@app.get("/students")
def get_students(db: Session = Depends(get_db)):
    students = db.query(Student).all()
    return students

@app.get("/students/{student_id}")
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(404, "Студент не найден")
    return student

@app.get("/students/{student_id}/grades")
def get_student_grades(student_id: int, db: Session = Depends(get_db)):
    grades = db.query(Grade).filter(Grade.student_id == student_id).all()
    return grades

@app.get("/stats/faculty/{faculty}")
def get_faculty_stats(faculty: str, db: Session = Depends(get_db)):
    students = db.query(Student).filter(Student.faculty == faculty).all()
    student_ids = [s.id for s in students]
    grades = db.query(Grade).filter(Grade.student_id.in_(student_ids)).all()
    
    avg_score = sum(g.score for g in grades) / len(grades) if grades else 0
    
    return {
        "faculty": faculty,
        "student_count": len(students),
        "grade_count": len(grades),
        "average_score": round(avg_score, 2)
    }