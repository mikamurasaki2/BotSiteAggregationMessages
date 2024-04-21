from fastapi import (
    FastAPI,
    Depends,
    Query,
    HTTPException,
    Path,
    status)
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from starlette.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import List
from math import floor
from pydantic import BaseModel, field_validator, Field
from fastapi.security import OAuth2PasswordBearer

import models as models

from utils import (
    verify_password,
    get_hashed_password,
    create_access_token,
    create_refresh_token,
    validate_token
)


# Подключение к локальному серверу
#app = FastAPI()
# engine = create_engine('mysql+mysqlconnector://root:@localhost/maindb6')
# reuseable_oauth = OAuth2PasswordBearer(
#     tokenUrl="/login",
#     scheme_name="JWT"
# )
app = FastAPI()
engine = create_engine('mysql+mysqlconnector://root:root@localhost/maindb')
reuseable_oauth = OAuth2PasswordBearer(
    tokenUrl="/login",
    scheme_name="JWT"
)



Session = sessionmaker(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Подключение к бд
def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


def get_date():
    return floor(datetime.utcnow().timestamp()) + 3 * 60 * 60

# Доработать парсер времени
def parse_timestamp(timestamp):
    dt = datetime.fromtimestamp(timestamp)
    month = models.month_names[dt.month - 1]
    return f"{dt.day} {month} {dt.year} в {dt.hour}:{dt.minute}"


# Получаем все вопросы-посты подряд
def get_all_posts(chat_id: List[str] = Query(None), des='true', db: Session = Depends(get_db)):
    if des == 'true' and chat_id is not None:
        return db.query(models.Message).filter(models.Message.chat_id.in_(chat_id)).order_by(
            desc(models.Message.date)).all()
    elif des == 'false' and chat_id is not None:
        return db.query(models.Message).filter(models.Message.chat_id.in_(chat_id)).order_by(
            models.Message.date).all()
    elif des == 'false' and chat_id is None:
        return db.query(models.Message).order_by(models.Message.date).all()
    elif des == 'true' and chat_id is None:
        return db.query(models.Message).order_by(desc(models.Message.date)).all()
    else:
        raise Exception("Invalid arguments")


# Получаем все чаты из бд
def get_all_chats(db: Session = Depends(get_db)):
    return db.query(models.Message.chat_id).distinct().all()


# Получаем вопросы-посты из бд
def get_post(msg_id, db: Session = Depends(get_db)):
    return db.query(models.Message).filter(models.Message.id == msg_id).first()

# Удалить пост
def delete_post(msg_id, db: Session = Depends(get_db)):
    post = db.query(models.Message).filter(models.Message.id == msg_id).first()
    if post:
        db.delete(post)
        db.commit()
        return 0
    else:
        return 1

def get_replies(msg_id, db: Session = Depends(get_db)):
    return db.query(models.Reply).filter(models.Reply.post_id == msg_id).all()

# Получаем вопросы-посты
@app.get("/api/get_messages")
async def get_messages(posts: list = Depends(get_all_posts), token: str = Depends(reuseable_oauth)):
    validate_token(token)
    return [
        {
            'username': post.username,
            'date': parse_timestamp(post.date),
            'text': post.message_text,
            'chat_id': post.chat_id,
            'id': post.id,
            'chatname': post.chat_username
        }
        for post in posts
    ]

# Получаем все айди чатов. В будущем заменить на названия чатов
@app.get("/api/get_chats")
async def get_chats(chats: list = Depends(get_all_chats), token: str = Depends(reuseable_oauth)):
    validate_token(token)
    return [chat.chat_id for chat in chats]


# Получаем сведения о посте с вопросом
@app.get("/api/get_message/{msg_id}")
async def get_message(post: dict = Depends(get_post), token: str = Depends(reuseable_oauth)):
    validate_token(token)
    return {
        'username': post.username,
        'date': parse_timestamp(post.date),
        'text': post.message_text,
        'chat_id': post.chat_id
    }

    

@app.delete("/api/delete_message/{msg_id}")
async def delete_message(msg_id: int = Path(...)):
    try:
        res = delete_post(msg_id)
        if res == 0:
            return {"message": msg_id}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Message with ID {msg_id} not found",
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

@app.get("/api/get_replies/{msg_id}")
async def get_replies(replies: dict = Depends(get_replies), token: str = Depends(reuseable_oauth)):
    validate_token(token)
    return [
        {
            'username': reply.username,
            'date': parse_timestamp(reply.date),
            'text': reply.message_text,
            'chat_id': reply.chat_id,
            'id': reply.id
        }
        for reply in replies
    ]


@app.post("/api/new_reply/")
async def add_reply(reply: models.Reply_Insert, db: Session = Depends(get_db), token: str = Depends(reuseable_oauth)):
    validate_token(token)
    try:
        db_reply = models.Reply(**reply.dict(), date=get_date())
        db.add(db_reply)
        db.commit()
        db.refresh(db_reply)
        return db_reply
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred while adding reply: {str(e)}")


class User(BaseModel):
    username: str = Field(min_length=5)
    password: str = Field(min_length=6)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v) -> str:
        if not v.isalnum():
            raise ValueError("Username must contain only letters and digits")
        return v


@app.post("/api/login/")
async def login(view_user: User, db: Session = Depends(get_db)):
    user = db.query(models.PrivateUser).filter(models.PrivateUser.username == view_user.username).first()
    if user is None or user.password != view_user.password:
        raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль")
    return {
        "access_token": create_access_token(user.username),
        "refresh_token": create_refresh_token(user.username),
    }