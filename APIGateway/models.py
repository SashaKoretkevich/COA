from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
import re

class userCreate(BaseModel):
    firstName: str = Field(..., min_length=3, max_length=30, description="Имя, от 3 до 30 символов")
    secondName: str = Field(..., min_length=3, max_length=30, description="Фамилия, от 3 до 30 символов")
    userName: str = Field(..., min_length=3, max_length=20, description="Ник, от 3 до 20 символов")
    mail: EmailStr = Field(..., description="Электронная почта")
    password: str = Field(..., min_length=10, max_length=20, description="Пароль, от 10 до 20 знаков")
    age: int
    gender: str
    status: str = Field(..., min_length=3, max_length=30, description="Статус, от 3 до 30 знаков")
    phoneNumber: str = Field(..., description="Номер телефона в международном формате, начинающийся с '+'")

    @field_validator('age')
    def check_age(cls, value):
        if value < 14:
            raise ValueError('Возраст должен быть больше 14 лет')
        return value
    @field_validator('phoneNumber')
    def validate_phone_number(cls, value: str) -> str:
        if not re.match(r'^\+\d{11}$', value):
            raise ValueError('Номер телефона должен начинаться с "+" и содержать 11 цифр')
        return value
    @field_validator('gender')
    def validate_gender(cls, value: str) -> str:
        if not value == "Male" and not value == "Female":
            raise ValueError('Неправильно указан пол')
        return value

class userLogin(BaseModel):
    userName: Optional[str] = Field(None, min_length=3, max_length=20, description="Ник, от 3 до 20 символов")
    mail: Optional[EmailStr] = Field(None, description="Электронная почта")
    password: str = Field(..., min_length=10, max_length=20, description="Пароль, от 10 до 20 знаков")


class userUpdate(BaseModel):
    firstName: str = Field(..., min_length=3, max_length=30, description="Имя, от 3 до 30 символов")
    secondName: str = Field(..., min_length=3, max_length=30, description="Фамилия, от 3 до 30 символов")
    age: int
    gender: str
    status: str = Field(..., min_length=3, max_length=30, description="Статус, от 3 до 30 знаков")
    phoneNumber: str = Field(..., description="Номер телефона в международном формате, начинающийся с '+'")
    token: Optional[str] = None
    
    @field_validator('age')
    def check_age(cls, value):
        if value < 14:
            raise ValueError('Возраст должен быть больше 14 лет')
        return value
    @field_validator('phoneNumber')
    def validate_phone_number(cls, value: str) -> str:
        if not re.match(r'^\+\d{11}$', value):
            raise ValueError('Номер телефона должен начинаться с "+" и содержать 11 цифр')
        return value
    @field_validator('gender')
    def validate_gender(cls, value: str) -> str:
        if not value == "Male" and not value == "Female":
            raise ValueError('Неправильно указан пол')
        return value

