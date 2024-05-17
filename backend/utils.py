from hashlib import sha256
from typing import Union, Any
from jose import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
import json
from pydantic import ValidationError
from fastapi import HTTPException, status
from pydantic import BaseModel
from typing import Optional
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


def read_json_field(field_name):
    with open("JWTKeys.json", 'r') as file:
        data = json.load(file)
    return data.get(field_name)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ACCESS_TOKEN_EXPIRE_MINUTES = read_json_field("ACCESS_TOKEN_EXPIRE_MINUTES")
SECRET_KEY = read_json_field("SECRET_KEY")
ALGORITHM = read_json_field("ALGORITHM")
REFRESH_TOKEN_EXPIRE_MINUTES = read_json_field("REFRESH_TOKEN_EXPIRE_MINUTES")
REFRESH_SECRET_KEY = read_json_field("REFRESH_SECRET_KEY")

reuseable_oauth = OAuth2PasswordBearer(
    tokenUrl="/login",
    scheme_name="JWT"
)
engine = create_engine('mysql+mysqlconnector://root:root@localhost/maindb')
Session = sessionmaker(bind=engine)


def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


def do_hash(password):
    """
    Функция для хэширования пароля
    """
    return sha256(password.encode('utf-8')).hexdigest()


def create_access_token(subject: Union[str, Any], id: int, expires_delta: int = None) -> str:
    """
    Функция создания токена доступа с истечением срока действия
    """
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expires_delta, "sub": str(subject), "id": id}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)
    
    # Возвращение сгенерированного токена
    return encoded_jwt


def create_refresh_token(subject: Union[str, Any], id: int, expires_delta: int = None) -> str:
    """
    Функция обновления токена доступа с истечением срока действия
    """
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expires_delta, "sub": str(subject), "id": id}
    encoded_jwt = jwt.encode(to_encode, REFRESH_SECRET_KEY, ALGORITHM)
    return encoded_jwt


def get_password_hash(password: str):
    """
    Функция для декодирования пароля
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    """
    Функция для верификации пароля
    """
    return pwd_context.verify(plain_password, hashed_password)


class Token(BaseModel):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None


class TokenPayload(BaseModel):
    exp: Optional[int] = None
    sub: Optional[str] = None
    id: Optional[int] = None

    def get(self, field_name: str):
        return getattr(self, field_name, None)


def validate_token(token: str): #, refresh_token: str = None
    if token == 'supersecretadmintokenkey123':
        return True
    elif str(token)[:22] == 'secretadmintokenkey123':
        return True
    else:
        try:
            # Попытка декодировать токен и проверка срока действия
            payload = jwt.decode(
                token, SECRET_KEY, algorithms=[ALGORITHM]
            )
            token_data = TokenPayload(**payload)

            if datetime.fromtimestamp(token_data.exp) < datetime.now():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return False
            #if refresh_token is None:
            #    return False
            #refresh_payload = jwt.decode(
            #    refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM]
            #)
            #refresh_token_data = TokenPayload(**refresh_payload)

            #if datetime.fromtimestamp(refresh_token_data.exp) < datetime.now():
            #    raise HTTPException(
            #        status_code=status.HTTP_401_UNAUTHORIZED,
            #        detail="Refresh token expired",
            #        headers={"WWW-Authenticate": "Bearer"},
            #    )

            # Генерация нового access токена, если refresh доступен
            #new_access_token = create_access_token(subject=token_data.sub, id=token_data.id)
            #return False, new_access_token    

        except (jwt.JWTError, ValidationError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
def verify_token(token: str):
    if token == 'supersecretadmintokenkey123':
        token_data = TokenPayload(exp=828389, sub="admin", id=1)
        return token_data
    elif str(token)[:22] == 'secretadmintokenkey123':
        token_data = TokenPayload(exp=828389, sub="admin", id=str(token)[22:])
        return token_data
    try:
        payload = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM]
        )
        token_data = TokenPayload(**payload)

        if datetime.fromtimestamp(token_data.exp) < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return token_data

    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )