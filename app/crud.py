from app.models import Student, Grade, User
from sqlalchemy.orm import Session
from sqlalchemy import distinct
from typing import List, Dict, Any
import csv

def create_student(db: Session, last_name: str, first_name: str, faculty: str) -> Student:
    student = Student(last_name=last_name, first_name=first_name, faculty=faculty)
    db.add(student)
    db.commit()
    db.refresh(student)
    return student

def create_grade(db: Session, student_id: int, course: str, score: int) -> Grade:
    grade = Grade(student_id=student_id, course=course, score=score)
    db.add(grade)
    db.commit()
    db.refresh(grade)
    return grade

def get_student(db: Session, student_id: int) -> Student:
    return db.query(Student).filter(Student.id == student_id).first()

def get_students(db: Session, skip: int = 0, limit: int = 100) -> List[Student]:
    return db.query(Student).offset(skip).limit(limit).all()

def get_grades_by_student(db: Session, student_id: int) -> List[Grade]:
    return db.query(Grade).filter(Grade.student_id == student_id).all()

def update_student(db: Session, student_id: int, last_name: str = None, first_name: str = None, faculty: str = None) -> Student:
    student = get_student(db, student_id)
    if not student:
        return None
    if last_name:
        student.last_name = last_name
    if first_name:
        student.first_name = first_name
    if faculty:
        student.faculty = faculty
    db.commit()
    db.refresh(student)
    return student

def update_grade(db: Session, grade_id: int, course: str = None, score: int = None) -> Grade:
    grade = db.query(Grade).filter(Grade.id == grade_id).first()
    if not grade:
        return None
    if course:
        grade.course = course
    if score is not None:
        grade.score = score
    db.commit()
    db.refresh(grade)
    return grade

def delete_student(db: Session, student_id: int) -> bool:
    student = get_student(db, student_id)
    if not student:
        return False
    db.delete(student)
    db.commit()
    return True

def delete_grade(db: Session, grade_id: int) -> bool:
    grade = db.query(Grade).filter(Grade.id == grade_id).first()
    if not grade:
        return False
    db.delete(grade)
    db.commit()
    return True

def get_students_by_faculty(db: Session, faculty: str) -> List[Student]:
    return db.query(Student).filter(Student.faculty == faculty).all()

def get_unique_courses(db: Session) -> List[str]:
    courses = db.query(distinct(Grade.course)).all()
    return [c[0] for c in courses]

def get_students_low_grade_by_course(db: Session, course: str, threshold: int = 30) -> List[Dict]:
    """Студенты с оценкой ниже threshold по выбранному курсу"""
    results = db.query(Student, Grade).join(Grade).filter(
        Grade.course == course,
        Grade.score < threshold
    ).all()
    
    return [
        {
            "student_id": student.id,
            "full_name": f"{student.last_name} {student.first_name}",
            "faculty": student.faculty,
            "course": grade.course,
            "score": grade.score
        }
        for student, grade in results
    ]

def get_average_score_by_faculty(db: Session, faculty: str) -> float:
    """Средний балл по факультету"""
    students = db.query(Student).filter(Student.faculty == faculty).all()
    if not students:
        return 0.0
    
    student_ids = [s.id for s in students]
    grades = db.query(Grade).filter(Grade.student_id.in_(student_ids)).all()
    
    if not grades:
        return 0.0
    
    avg = sum(g.score for g in grades) / len(grades)
    return round(avg, 2)

def load_csv_to_db(db: Session, csv_path: str = "students.csv"):
    """Загрузка данных из CSV в БД"""
    db.query(Grade).delete()
    db.query(Student).delete()
    db.commit()
    
    students_cache = {}
    
    with open(csv_path, "r", encoding="utf-8") as file:
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
    return len(students_cache), db.query(Grade).count()

def export_to_csv(db: Session, csv_path: str = "exported.csv"):
    """Выгрузка всех данных в CSV (задание 5*)"""
    students = db.query(Student).all()
    
    with open(csv_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Фамилия", "Имя", "Факультет", "Курс", "Оценка"])
        
        for student in students:
            for grade in student.grades:
                writer.writerow([
                    student.last_name,
                    student.first_name,
                    student.faculty,
                    grade.course,
                    grade.score
                ])
    
    return f"Экспортировано в {csv_path}"