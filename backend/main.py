from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from starlette.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import List
from math import floor

import models as models

# Подключение к локальному серверу
app = FastAPI()
engine = create_engine('mysql+mysqlconnector://root:@localhost/maindb6')

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


def get_replies(msg_id, db: Session = Depends(get_db)):
    return db.query(models.Reply).filter(models.Reply.post_id == msg_id).all()

# Получаем вопросы-посты
@app.get("/get_messages")
async def get_messages(posts: list = Depends(get_all_posts)):
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
@app.get("/get_chats")
async def get_chats(chats: list = Depends(get_all_chats)):
    return [chat.chat_id for chat in chats]


# Получаем сведения о посте с вопросом
@app.get("/get_message/{msg_id}")
async def get_message(post: dict = Depends(get_post)):
    return {
        'username': post.username,
        'date': parse_timestamp(post.date),
        'text': post.message_text,
        'chat_id': post.chat_id
    }
    

@app.get("/get_replies/{msg_id}")
async def get_replies(replies: dict = Depends(get_replies)):
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


@app.post("/new_reply/")
async def add_reply(reply: models.Reply_Insert, db: Session = Depends(get_db)):
    try:
        db_reply = models.Reply(**reply.dict(), date=get_date())
        db.add(db_reply)
        db.commit()
        db.refresh(db_reply)
        return db_reply
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred while adding reply: {str(e)}")
    
    
# @app.post("/login/")
# async def login(username: str, password: str, db: Session = Depends(get_db)):
#     user = db.query(models.PrivateUser).filter(models.PrivateUser.username == username).first()
#     if user is None or user.password != password:
#         raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль")
#     return {"username": user.username, "user_id": user.user_id}