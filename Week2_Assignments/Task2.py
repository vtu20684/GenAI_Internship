# Task 2: Lists and Arrays

import random
import numpy as np

# 2.1: Create a list of 10 random integers
lis = [random.randint(1, 25) for _ in range(10)]
print("Original List:", lis)

# 2.2.1: Add and remove elements
lis.append(26)
print("List after adding 26:", lis)

removed_value = lis[5]
lis.remove(removed_value)
print(f"List after removing element {removed_value}:", lis)

# 2.2.2: Find the maximum and minimum values
print("\n--- List Statistics ---")
print("Maximum Value:", max(lis))
print("Minimum Value:", min(lis))

# 2.2.3: Sort the list
lis.sort()
print("Sorted List:", lis)

# 2.3: Convert the list into a NumPy array
arr = np.array(lis)

# 2.3.1: Calculate Mean, Median, and Standard Deviation
mean = np.mean(arr)
median = np.median(arr)
stddev = np.std(arr)

print("\n--- NumPy Calculations ---")
print(f"Mean: {mean:.2f}")
print(f"Median: {median}")
print(f"Standard Deviation: {stddev:.2f}")
