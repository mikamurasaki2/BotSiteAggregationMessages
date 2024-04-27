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

# import backend.models as models
import models

# from backend.utils import (
from utils import (
    verify_password,
    get_hashed_password,
    create_access_token,
    create_refresh_token,
    validate_token
)

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


def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


def get_date():
    return floor(datetime.utcnow().timestamp()) + 3 * 60 * 60


def parse_timestamp(timestamp):
    dt = datetime.fromtimestamp(timestamp)
    month = models.month_names[dt.month - 1]
    return f"{dt.day} {month} {dt.year} в {dt.hour}:{dt.minute}"


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


def get_all_chats(db: Session = Depends(get_db)):
    return db.query(models.Message).distinct().all()


def get_post(msg_id, db: Session = Depends(get_db)):
    return db.query(models.Message).filter(models.Message.message_id == msg_id).first()


def get_replies(msg_id, db: Session = Depends(get_db)):
    return db.query(models.Reply).filter(models.Reply.post_id == msg_id).all()


def get_all_users(db: Session = Depends(get_db)):
    return db.query(models.PrivateUser).distinct().all()


@app.get("/api/get_messages")
async def get_messages(posts: list = Depends(get_all_posts), token: str = Depends(reuseable_oauth)):
    validate_token(token)
    return [
        {
            'username': post.username,
            'date': parse_timestamp(post.date),
            'text': post.message_text,
            'chat_id': post.chat_id,
            'id': post.message_id,
            'chatname': post.chat_username
        }
        for post in posts
    ]


@app.get("/api/get_chats")
async def get_chats(chats: list = Depends(get_all_chats), token: str = Depends(reuseable_oauth)):
    validate_token(token)
    return [
        {
            'chat_id': chat.chat_id,
            'chat_username': chat.chat_username
        }
        for chat in chats]


@app.get("/api/get_message/{msg_id}")
async def get_message(post: dict = Depends(get_post), token: str = Depends(reuseable_oauth)):
    validate_token(token)
    return {
        'username': post.username,
        'date': parse_timestamp(post.date),
        'text': post.message_text,
        'chat_id': post.chat_id,
        'chatname': post.chat_username
    }


@app.get("/api/get_users")
async def get_users(users: dict = Depends(get_all_users), token: str = Depends(reuseable_oauth)):
    is_admin = validate_token(token)
    if is_admin:
        return [
            {
                "user_id": user.user_id,
                "username": user.username,
                "is_admin": user.is_admin
            }
            for user in users]
    else:
        raise HTTPException(status_code=403, detail=f"Auth Error. User is not admin")


@app.delete("/api/delete_message/{msg_id}")
async def delete_message(msg_id: int, token: str = Depends(reuseable_oauth),
                         db: Session = Depends(get_db)):
    is_admin = validate_token(token)
    if is_admin:
        try:
            post = db.query(models.Message).filter(models.Message.message_id == msg_id).first()
            if post:
                db.delete(post)
                db.commit()
                return {"message": "Message deleted successfully"}
            else:
                raise HTTPException(status_code=404, detail="Message not found")
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"An error occurred while deleting message: {str(e)}")
    else:
        raise HTTPException(status_code=403, detail=f"Auth Error. User is not admin")


@app.delete("/api/delete_reply/{reply_id}")
async def delete_message(reply_id: int, token: str = Depends(reuseable_oauth), db: Session = Depends(get_db)):
    is_admin = validate_token(token)
    if is_admin:
        try:
            reply = db.query(models.Reply).filter(models.Reply.id == reply_id).first()
            if reply:
                db.delete(reply)
                db.commit()
                return {"message": "Reply deleted successfully"}
            else:
                raise HTTPException(status_code=404, detail="Message not found")
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"An error occurred while deleting message: {str(e)}")
    else:
        raise HTTPException(status_code=500, detail=f"An error occurred while deleting message.")


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
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v) -> str:
        if not v.isalnum():
            raise ValueError("Username must contain only letters and digits")
        return v


@app.post("/api/login/")
async def login(view_user: User, db: Session = Depends(get_db)):
    user = db.query(models.PrivateUser).filter(models.PrivateUser.user_id == view_user.username).first()
    if user is None or user.password != view_user.password:
        raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль")
    else:
        if user.username == 'admin':
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