from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional


# Базовая схема пользователя
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=2, max_length=50)


# Схема для регистрации
class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=72)
    confirm_password: str

    @validator('password')
    def validate_password_length(cls, v):
        # Проверяем длину в байтах для bcrypt
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Пароль слишком длинный')
        return v

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Пароли не совпадают')
        return v


# Схема для входа
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Схема для ответа
class User(UserBase):
    id: int
    is_active: bool
    is_verified: bool

    class Config:
        from_attributes = True


# Схема для токена
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[int] = None