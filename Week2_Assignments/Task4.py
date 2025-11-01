# Task 4: File Handling

# 4.1: Create a text file named ai_students.txt
# 4.2: Write details of at least 5 students (name, marks, grade)

students = [
    {"name": "Akshita", "marks": 88, "grade": "B"},
    {"name": "Neha", "marks": 94, "grade": "A"},
    {"name": "Rohan", "marks": 72, "grade": "C"},
    {"name": "Kiran", "marks": 79, "grade": "B"},
    {"name": "Meera", "marks": 97, "grade": "A"}
]

# Write data to file
with open("ai_students.txt", "w") as f:
    for s in students:
        f.write(f"{s['name']},{s['marks']},{s['grade']}\n")

# 4.3: Read the file and display students who scored above 75 marks
print("\n--- Students Who Scored Above 75 ---")
with open("ai_students.txt", "r") as f:
    for line in f:
        name, marks, grade = line.strip().split(",")
        if int(marks) > 75:
            print(f"{name} - Marks: {marks}, Grade: {grade}")
