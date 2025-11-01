# Task 3: Dictionaries and Sets

# 3.1: Create a dictionary named 'student' with keys: name, course, marks
student = {
    "name": "Akshita",
    "course": "Generative AI",
    "marks": 90
}

# 3.2: Add a new key 'grade' based on marks
if student["marks"] >= 90:
    student["grade"] = "A"
elif student["marks"] >= 70:
    student["grade"] = "B"
else:
    student["grade"] = "C"

# 3.3: Print all keys and values using a loop
print("\n--- Student Dictionary ---")
for key, value in student.items():
    print(f"{key.capitalize()}: {value}")

# 3.4: Create two sets of AI tools
ai_tools1 = {"ChatGPT", "Claude", "Gemini"}
ai_tools2 = {"Gemini", "Perplexity", "ChatGPT"}

# Perform set operations
print("\n--- Set Operations ---")
print(f"AI Tools Set 1: {ai_tools1}")
print(f"AI Tools Set 2: {ai_tools2}")
print(f"\nUnion: {ai_tools1 | ai_tools2}")
print(f"Intersection: {ai_tools1 & ai_tools2}")
print(f"Difference (ai_tools1 - ai_tools2): {ai_tools1 - ai_tools2}")
print(f"Difference (ai_tools2 - ai_tools1): {ai_tools2 - ai_tools1}")
