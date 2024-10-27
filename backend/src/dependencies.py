# app/dependencies.py

from fastapi import Depends

def get_current_user():
    # Simulación de un usuario con id 1
    class User:
        id = 1
    return User()
