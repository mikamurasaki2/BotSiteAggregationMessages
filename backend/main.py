from fastapi import FastAPI, Depends, Query
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from starlette.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import List

import models as models

# Подключение к локальному серверу
app = FastAPI()
engine = create_engine('mysql+mysqlconnector://root:@localhost/maindb')

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


# Получаем вопросы-посты
@app.get("/get_messages")
async def get_messages(posts: list = Depends(get_all_posts)):
    return [
        {
            'username': post.username,
            'date': (post.date),
            'text': post.message_text,
            'chat_id': post.chat_id,
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