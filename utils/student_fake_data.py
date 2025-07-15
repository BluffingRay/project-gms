from faker import Faker
import random
from database_client import supabase

faker = Faker()

def generate_fake_students(n=10):
    year_levels = ["1st Year", "2nd Year", "3rd Year", "4th Year"]
    enrollment_status = ["Enrolled", "Not Enrolled", "Graduated", "Dropped"]
    programs = ["BSCS", "BSIT", "BSEd"]

    fake_students = []

    for _ in range(n):
        fake_students.append({
            "studentid": faker.unique.uuid4()[:8],
            "firstname": faker.first_name(),
            "lastname": faker.last_name(),
            "middlename": faker.first_name(),
            "gender": random.choice(["Male", "Female"]),
            "dateofbirth": faker.date_of_birth(minimum_age=18, maximum_age=25).isoformat(),
            "emailaddress": faker.email(),
            "yearlevel": random.choice(year_levels),
            "program": random.choice(programs),
            "section": faker.random_letter().upper(),
            "enrollmentstatus": random.choice(enrollment_status)
        })

    supabase.table("students").insert(fake_students).execute()


from services.curriculum_service import add_curriculum_subject

def insert_fake_curriculum_data():
    subjects = [
        {"program": "JD", "yearlevel": "1st Year", "term": "1st Semester", "code": "JD101", "name": "Introduction to Law", "units": 3},
        {"program": "JD", "yearlevel": "1st Year", "term": "2nd Semester", "code": "JD102", "name": "Legal Writing", "units": 3},
        {"program": "BSCS", "yearlevel": "1st Year", "term": "1st Semester", "code": "CS101", "name": "Intro to Programming", "units": 3},
        {"program": "BSCS", "yearlevel": "2nd Year", "term": "1st Semester", "code": "CS201", "name": "Data Structures", "units": 3},
        {"program": "BSED-English", "yearlevel": "1st Year", "term": "1st Semester", "code": "ENG101", "name": "English Grammar", "units": 3},
        {"program": "BSED-Math", "yearlevel": "1st Year", "term": "1st Semester", "code": "MATH101", "name": "Basic Algebra", "units": 3},
    ]

    for subject in subjects:
        add_curriculum_subject(subject)

