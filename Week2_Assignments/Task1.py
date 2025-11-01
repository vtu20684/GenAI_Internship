# Task 1: Python Basics & Operators

# 1.1: Accept two numbers from the user
n1 = int(input("Enter the first number: "))
n2 = int(input("Enter the second number: "))

# 1.2: Perform all basic arithmetic operations
add = n1 + n2
sub = n1 - n2
mul = n1 * n2
div = n1 / n2 if n2 != 0 else "Undefined (division by zero)"
mod = n1 % n2 if n2 != 0 else "Undefined (modulus by zero)"
power = n1 ** n2

print("\n--- Arithmetic Operations ---")
print(f"Addition: {add}")
print(f"Subtraction: {sub}")
print(f"Multiplication: {mul}")
print(f"Division: {div}")
print(f"Modulus: {mod}")
print(f"Power: {power}")

# 1.3: Demonstrate use of comparison and logical operators
print("\n--- Comparison Operators ---")
print(f"{n1} > {n2} : {n1 > n2}")
print(f"{n1} < {n2} : {n1 < n2}")
print(f"{n1} == {n2} : {n1 == n2}")
print(f"{n1} != {n2} : {n1 != n2}")

print("\n--- Logical Operators ---")
if (n1 > 0) and (n2 > 0):
    print("Both numbers are positive.")
else:
    print("At least one number is not positive.")

if (n1 > 0) or (n2 > 0):
    print("At least one number is positive.")
else:
    print("Both numbers are non-positive.")

if not (n1 > n2):
    print(f"{n1} is not greater than {n2}.")
else:
    print(f"{n1} is greater than {n2}.")

# 1.4: Formatted summary output using f-strings
print("\n--- Formatted Summary ---")
print(f"Numbers entered: {n1} and {n2}")
print(f"Sum: {add}")
print(f"Difference: {sub}")
print(f"Product: {mul}")
print(f"Division: {div if isinstance(div, str) else round(div, 2)}")
print(f"Modulus: {mod}")
print(f"Power: {power}")
print(f"Is {n1} greater than {n2}? {'Yes' if n1 > n2 else 'No'}")
