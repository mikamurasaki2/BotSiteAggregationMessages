from fastapi import (
    Depends,
    Query,
    HTTPException)
from sqlalchemy import desc
from datetime import datetime
from typing import List
from math import floor
from pydantic import BaseModel, field_validator, Field

import models

from utils import (
    create_access_token,
    create_refresh_token,
    validate_token,
    reuseable_oauth,
    Session,
    get_db
)


class User(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v) -> str:
        if not v.isalnum():
            raise ValueError("Username must contain only letters and digits")
        return v


def get_date():
    return floor(datetime.utcnow().timestamp()) + 3 * 60 * 60


def parse_timestamp(timestamp):
    dt = datetime.fromtimestamp(timestamp)
    month = models.month_names[dt.month - 1]
    return f"{dt.day} {month} {dt.year} в {dt.hour}:{dt.minute}"


def to_timestamp(date):
    dt = datetime.strptime(date, '%Y-%m-%d')
    timestamp = dt.timestamp()
    return int(timestamp)


def get_all_posts(chat_id: List[str] = Query(None), des='true', date_from='', date_to='',
                  db: Session = Depends(get_db)):
    query = db.query(models.Message)
    if chat_id is not None:
        query = query.filter(models.Message.chat_id.in_(chat_id))

    if des == 'true':
        query = query.order_by(desc(models.Message.date))
    elif des == 'false':
        query = query.order_by(models.Message.date)

    if date_from:
        query = query.filter(models.Message.date >= to_timestamp(date_from))
    if date_to:
        query = query.filter(models.Message.date <= to_timestamp(date_to))

    return query.all()


def get_all_chats(db: Session = Depends(get_db)):
    return db.query(models.Message).distinct().all()


def get_post(msg_id, db: Session = Depends(get_db)):
    return db.query(models.Message).filter(models.Message.message_id == msg_id).first()


def get_replies(msg_id, admin_sort='false', db: Session = Depends(get_db)):
    if admin_sort == 'true':
        return (
            db.query(models.Reply).join(models.Reply.user).filter(models.Reply.post_id == msg_id).order_by(
                models.PrivateUser.is_admin.desc()).all()
        )
    else:
        return db.query(models.Reply).join(models.Reply.user).filter(models.Reply.post_id == msg_id).all()


def get_all_users(db: Session = Depends(get_db)):
    return db.query(models.PrivateUser).distinct().all()


def get_messages(posts: list = Depends(get_all_posts), token: str = Depends(reuseable_oauth),
                 db: Session = Depends(get_db)):
    validate_token(token)
    return [
        {
            'username': post.username,
            'date': parse_timestamp(post.date),
            'text': post.message_text,
            'chat_id': post.chat_id,
            'id': post.message_id,
            'chatname': post.chat_username,
            'name': db.query(models.User).filter(models.User.user_id == post.user_id).first().user_first_name,
            'last_name': db.query(models.User).filter(models.User.user_id == post.user_id).first().user_last_name
        }
        for post in posts
    ]


def get_chats(chats: list = Depends(get_all_chats), token: str = Depends(reuseable_oauth)):
    validate_token(token)
    return [
        {
            'chat_id': chat.chat_id,
            'chat_username': chat.chat_username
        }
        for chat in chats]


def get_message(post: dict = Depends(get_post), token: str = Depends(reuseable_oauth),
                db: Session = Depends(get_db)):
    validate_token(token)
    return {
        'username': post.username,
        'date': parse_timestamp(post.date),
        'text': post.message_text,
        'chat_id': post.chat_id,
        'chatname': post.chat_username,
        'name': db.query(models.User).filter(models.User.user_id == post.user_id).first().user_first_name,
        'last_name': db.query(models.User).filter(models.User.user_id == post.user_id).first().user_last_name
    }


def get_replies_(replies: dict = Depends(get_replies), token: str = Depends(reuseable_oauth)):
    validate_token(token)
    return [
        {
            'username': reply.username,
            'date': parse_timestamp(reply.date),
            'text': reply.message_text,
            'chat_id': reply.chat_id,
            'id': reply.id,
            'name': reply.user.user_first_name,
            'last_name': reply.user.user_last_name,
            'is_admin': reply.user.is_admin
        }
        for reply in replies
    ]


def add_reply(reply: models.Reply_Insert, db: Session = Depends(get_db),
              token: str = Depends(reuseable_oauth)):
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


def login(view_user: User, db: Session = Depends(get_db)):
    user = db.query(models.PrivateUser).filter(models.PrivateUser.user_id == view_user.username).first()
    if user is None or user.password != view_user.password:
        raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль")
    else:
        if user.is_admin == 1:
            return {
                "access_token": "supersecretadmintokenkey123",
                "refresh_token": create_refresh_token(user.username),
                "admin_token": "supersecretadmintokenkey123"
            }
        else:
            return {
                "access_token": create_access_token(user.username),
                "refresh_token": create_refresh_token(user.username),
                "admin_token": ""
            }
