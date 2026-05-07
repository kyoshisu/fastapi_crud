from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Student, Grade
import csv
from typing import List

def load_csv_background(csv_path: str):
    db = SessionLocal()
    try:
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
        print(f"✅ Загрузка завершена: {len(students_cache)} студентов, {db.query(Grade).count()} оценок")
    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
    finally:
        db.close()


def delete_students_background(student_ids: List[int]):
    db = SessionLocal()
    try:
        deleted_count = 0
        for student_id in student_ids:
            student = db.query(Student).filter(Student.id == student_id).first()
            if student:
                db.delete(student)
                deleted_count += 1
        
        db.commit()
        print(f"✅ Удалено {deleted_count} студентов")
    except Exception as e:
        print(f"❌ Ошибка удаления: {e}")
    finally:
        db.close()