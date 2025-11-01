# Task 5: Real-World Mini Project
# File: ai_prompt_logger.py

import datetime

print("\n--- AI Prompt Logger ---")

# 5.1: Accept user input (simulating an AI prompt)
prompt = input("Enter your AI prompt: ")

# 5.2 & 5.3: Save the prompt text in a file with a timestamp
timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Append new prompt entries to the file
with open("prompt_history.txt", "a") as file:
    file.write(f"[{timestamp}] {prompt}\n")

print("\nPrompt saved successfully to 'prompt_history.txt'!")
print(f"Timestamp: {timestamp}")
