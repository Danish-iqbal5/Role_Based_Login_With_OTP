# yourapp/utils.py
import random

def generate_otp():
    return f"{random.randint(100000, 999999)}"
