from app.database import SessionLocal
from app.models import Grade, Group, Permission, Role, Subject, User
from app.security import hash_password

def seed_data():
    db = SessionLocal()
    try:
        if db.query(Role).first():
            print("База даних вже ініціалізована.")
            return

        print("Заповнення бази даних тестовими даними...")

        r_admin = Role(name="admin", description="Повний доступ")
        r_teacher = Role(name="teacher", description="Викладач: оцінювання")
        r_student = Role(name="student", description="Студент: перегляд")
        db.add_all([r_admin, r_teacher, r_student])
        db.flush()

        p_read_grades = Permission(name="grades:read", description="Перегляд оцінок")
        p_write_grades = Permission(name="grades:write", description="Виставлення оцінок")
        p_manage_users = Permission(name="users:manage", description="Керування акаунтами")
        db.add_all([p_read_grades, p_write_grades, p_manage_users])
        db.flush()

        r_admin.permissions.extend([p_read_grades, p_write_grades, p_manage_users])
        r_teacher.permissions.extend([p_read_grades, p_write_grades])
        r_student.permissions.append(p_read_grades)

        group = Group(name="КН-31")
        subject = Subject(name="Безпека веб-застосунків")
        db.add_all([group, subject])
        db.flush()

        admin_user = User(
            username="admin",
            email="admin@university.edu",
            full_name="Адміністратор Системи",
            password_hash=hash_password("Admin123!@#"),
            roles=[r_admin],
        )
        teacher_user = User(
            username="teacher01",
            email="teacher@university.edu",
            full_name="Коваленко Іван Васильович",
            password_hash=hash_password("Teacher123!"),
            roles=[r_teacher],
        )
        student_user = User(
            username="student01",
            email="student@university.edu",
            full_name="Петренко Марія Олексіївна",
            password_hash=hash_password("Student123!"),
            group_id=group.id,
            roles=[r_student],
        )
        db.add_all([admin_user, teacher_user, student_user])
        db.flush()

        grade = Grade(
            student_id=student_user.id,
            subject_id=subject.id,
            grade=95,
            comment="Відмінно виконана практична робота",
            assigned_by=teacher_user.id,
        )
        db.add(grade)
        db.commit()
        print("База даних успішно наповнена!")
    except Exception as e:
        db.rollback()
        print(f"Помилка заповнення бази: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()