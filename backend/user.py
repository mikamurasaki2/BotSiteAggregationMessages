from fastapi import (
    Depends,
    Query)
from sqlalchemy import desc
from typing import List
from math import floor
from pydantic import field_validator, Field

import models

from utils import *


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
    """
    Функция для получения времени и преобразования по Мск
    """
    return floor(datetime.utcnow().timestamp()) + 3 * 60 * 60


def parse_timestamp(timestamp):
    """
    Функция для визуального отображения времени ДД ММ ГГ в ЧЧ:ММ
    """
    dt = datetime.fromtimestamp(timestamp)
    month = models.month_names[dt.month - 1]
    return f"{dt.day} {month} {dt.year} в {dt.hour:02d}:{dt.minute:02d}"


def to_timestamp(date):
    dt = datetime.strptime(date, '%Y-%m-%d')
    timestamp = dt.timestamp()
    return int(timestamp)


def get_all_posts(
        chat_id: List[str] = Query(None), des='true', date_from='', date_to='',
        db: Session = Depends(get_db), token: str = Depends(reuseable_oauth)):
    """
    Функция для получения всех постов из бд с учетом сортировок
    """
    token_data = verify_token(token)
    user_id = token_data.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    chats_can_view = db.query(models.User).filter(models.User.user_id == user_id).all()
    chat_ids_can_view = [chat.chat_id for chat in chats_can_view]

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

    #if not validate_token(token):
    #    query = query.filter(models.Message.chat_id.in_(chat_ids_can_view))
        
    if validate_token(token):
        if user_id == 1:
            return query.all()
        else:
            return query.filter(models.Message.chat_id.in_(chat_ids_can_view))
    else:
        return query.filter(models.Message.chat_id.in_(chat_ids_can_view))

    #return query.all()


def get_all_chats(db: Session = Depends(get_db)):
    """
    Функция для получения всех чатов
    """
    return db.query(models.Message).distinct().all()


def get_post(msg_id, db: Session = Depends(get_db)):
    """
    Функция для получения конкретного поста по его id
    """
    return db.query(models.Message).filter(models.Message.message_id == msg_id).first()


def get_replies(msg_id, admin_sort='false', db: Session = Depends(get_db)):
    """
    Функция для визуального отображения комментариев, отправленных админами
    """
    if admin_sort == 'true':
        return (
            db.query(models.Reply).join(models.Reply.user).filter(models.Reply.post_id == msg_id).order_by(
                models.PrivateUser.is_admin.desc()).all()
        )
    else:
        return db.query(models.Reply).join(models.Reply.user).filter(models.Reply.post_id == msg_id).all()


def get_all_users(db: Session = Depends(get_db)):
    """
    Функция для получения всех пользователей
    """
    return db.query(models.PrivateUser, models.User.user_first_name, models.User.user_last_name).outerjoin(models.User, models.PrivateUser.user_id == models.User.user_id)


def get_messages(posts: list = Depends(get_all_posts), token: str = Depends(reuseable_oauth),
                 db: Session = Depends(get_db)):
    """
    Функция для получения постов для админа и обычного пользователя
    """
    if validate_token(token):   
        token_data = verify_token(token)
        user_id = token_data.get("id")
        if user_id == 1:
            return [
            {
                'username': post.username,
                'date': parse_timestamp(post.date),
                'text': post.message_text,
                'chat_id': post.chat_id,
                'id': post.message_id,
                'chatname': post.chat_username,
                'name': db.query(models.PrivateUser).filter(models.PrivateUser.user_id == post.user_id).first().user_first_name if db.query(models.PrivateUser).filter(models.PrivateUser.user_id == post.user_id).first() else (db.query(models.User).filter(models.User.user_id == post.user_id).first().user_first_name if db.query(models.User).filter(models.User.user_id == post.user_id).first() else None),
                'last_name': db.query(models.PrivateUser).filter(models.PrivateUser.user_id == post.user_id).first().user_last_name if db.query(models.PrivateUser).filter(models.PrivateUser.user_id == post.user_id).first() else (db.query(models.User).filter(models.User.user_id == post.user_id).first().user_last_name if db.query(models.User).filter(models.User.user_id == post.user_id).first() else None),
                'is_admin_answer': post.is_admin_answer,
                'msg_id': post.message_id,
                'msg_type': post.question_type
            }
            for post in posts
        ]
        else:
            return [
            {
                'username': post.username,
                'date': parse_timestamp(post.date),
                'text': post.message_text,
                'chat_id': post.chat_id,
                'id': post.message_id,
                'chatname': post.chat_username,
                'name': db.query(models.PrivateUser).filter(models.PrivateUser.user_id == post.user_id).first().user_first_name if db.query(models.PrivateUser).filter(models.PrivateUser.user_id == post.user_id).first() else (db.query(models.User).filter(models.User.user_id == post.user_id).first().user_first_name if db.query(models.User).filter(models.User.user_id == post.user_id).first() else None),
                'last_name': db.query(models.PrivateUser).filter(models.PrivateUser.user_id == post.user_id).first().user_last_name if db.query(models.PrivateUser).filter(models.PrivateUser.user_id == post.user_id).first() else (db.query(models.User).filter(models.User.user_id == post.user_id).first().user_last_name if db.query(models.User).filter(models.User.user_id == post.user_id).first() else None),
                'is_admin_answer': post.is_admin_answer,
                'msg_id': post.message_id,
                'msg_type': post.question_type
            }
            for post in posts 
        ]
        
    else:
        token_data = verify_token(token)
        user_id = token_data.get("id")
        return [
            {
                'username': post.username,
                'date': parse_timestamp(post.date),
                'text': post.message_text,
                'chat_id': post.chat_id,
                'id': post.message_id,
                'chatname': post.chat_username,
                'name': db.query(models.PrivateUser).filter(models.PrivateUser.user_id == post.user_id).first().user_first_name if db.query(models.PrivateUser).filter(models.PrivateUser.user_id == post.user_id).first() else (db.query(models.User).filter(models.User.user_id == post.user_id).first().user_first_name if db.query(models.User).filter(models.User.user_id == post.user_id).first() else None),
                'last_name': db.query(models.PrivateUser).filter(models.PrivateUser.user_id == post.user_id).first().user_last_name if db.query(models.PrivateUser).filter(models.PrivateUser.user_id == post.user_id).first() else (db.query(models.User).filter(models.User.user_id == post.user_id).first().user_last_name if db.query(models.User).filter(models.User.user_id == post.user_id).first() else None),
                'is_admin_answer': post.is_admin_answer,
                'msg_id': post.message_id,
                'msg_type': post.question_type
            }
            for post in posts 
        ]

def get_chats(chats: list = Depends(get_all_chats), token: str = Depends(reuseable_oauth)):
    """
    Функция для получения списка чатов для админа и обычного пользователя
    """
    if validate_token(token):
        token_data = verify_token(token)
        user_id = token_data.get("id")
        if user_id == 1:
            return [
                {
                    'chat_id': chat.chat_id,
                    'chat_username': chat.chat_username,
                    'chat_type': chat.question_type,
                    'msg_id': chat.message_id
                }
                for chat in chats]
        else:
            db = next(get_db())
            chat_ids = [user.chat_id for user in db.query(models.User).filter(models.User.user_id == user_id).all()]
            chats = db.query(models.Message).filter(models.Message.chat_id.in_(chat_ids)).all()
            return [
                {
                    'chat_id': chat.chat_id,
                    'chat_username': chat.chat_username,
                    'chat_type': chat.question_type
                }
                for chat in chats]
    else:
        db = next(get_db())
        token_data = verify_token(token)
        user_id = token_data.get("id")
        chat_ids = [user.chat_id for user in db.query(models.User).filter(models.User.user_id == user_id).all()]
        chats = db.query(models.Message).filter(models.Message.chat_id.in_(chat_ids)).all()
        return [
            {
                'chat_id': chat.chat_id,
                'chat_username': chat.chat_username,
                'chat_type': chat.question_type
            }
            for chat in chats]


def get_message(post: dict = Depends(get_post), token: str = Depends(reuseable_oauth),
                db: Session = Depends(get_db)):
    """
    Функция получения данных поста
    """
    validate_token(token)
    token_data = verify_token(token)
    user_id = token_data.get("id")
    user = db.query(models.User).filter(models.User.user_id == post.user_id).first()
    user_private = db.query(models.PrivateUser).filter(models.PrivateUser.user_id == post.user_id).first()
    return {
        'username': post.username,
        'date': parse_timestamp(post.date),
        'text': post.message_text,
        'chat_id': post.chat_id,
        'chatname': post.chat_username,
        'name': user_private.user_first_name if user_private else (user.user_first_name if user else None),
        'last_name': user_private.user_last_name if user_private else (user.user_last_name if user else None),
    }


def get_replies_(replies: dict = Depends(get_replies), token: str = Depends(reuseable_oauth)):
    """
    Функция для получения реплаев/ответов
    """
    validate_token(token)
    data = list()
    db = get_db()
    context = next(db)

    for reply in replies:
        private_user = context.query(models.PrivateUser).filter(models.PrivateUser.user_id == reply.user_id).first()
        if private_user:
            data.append({
                'username': reply.username,
                'date': parse_timestamp(reply.date),
                'text': reply.message_text,
                'chat_id': reply.chat_id,
                'id': reply.id,
                'name': private_user.user_first_name,
                'last_name': private_user.user_last_name,
                'is_admin': reply.user.is_admin,
                'user_id': reply.user_id
            })
            continue
        else:
            default_user = context.query(models.User).filter(models.User.user_id == reply.user_id).first()
            if default_user:
                data.append({
                    'username': reply.username,
                    'date': parse_timestamp(reply.date),
                    'text': reply.message_text,
                    'chat_id': reply.chat_id,
                    'id': reply.id,
                    'name': private_user.user_first_name,
                    'last_name': private_user.user_last_name,
                    'is_admin': reply.user.is_admin,
                    'user_id': reply.user_id
                })
                continue
            else:
                data.append({
                    'username': reply.username,
                    'date': parse_timestamp(reply.date),
                    'text': reply.message_text,
                    'chat_id': reply.chat_id,
                    'id': reply.id,
                    'name': '',
                    'last_name': '',
                    'is_admin': reply.user.is_admin,
                    'user_id': reply.user_id
                })

    return data;


def add_reply(reply: models.Reply_Insert, db: Session = Depends(get_db),
              token: str = Depends(reuseable_oauth)):
    """
    Функция для отправки комментария в веб-приложении с проверкой роли пользователя.
    Если комментарий отправлен админом, то тогда пост получает статус "Админ дал ответ"
    """
    is_admin = validate_token(token)

    if is_admin:
        message_to_update = db.query(models.Message).filter(models.Message.message_id == reply.post_id).first()

        if message_to_update:
            # Смена статуса поста на "Админ дал ответ"
            message_to_update.is_admin_answer = 1
            db.commit()

    try:
        db_reply = models.Reply(**reply.model_dump(), date=get_date())
        db.add(db_reply)
        db.commit()
        db.refresh(db_reply)
        return db_reply
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred while adding reply: {str(e)}")


def login(view_user: User, db: Session = Depends(get_db)):
    """
    Функция для авторизации и проверки на суперюзера
    """
    user = db.query(models.PrivateUser).filter(models.PrivateUser.user_id == view_user.username).first()
    if user is None or user.password != do_hash(view_user.password):
        raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль")
    else:
        if user.is_admin == 1:
            if user.user_id == 1:
                return {
                    "access_token": "supersecretadmintokenkey123",
                    "refresh_token": create_refresh_token(user.username, user.user_id),
                    "admin_token": "supersecretadmintokenkey123",
                    "id": "1"
                }
            else:
                return {
                    "access_token": "secretadmintokenkey123" + str(user.user_id),
                    "refresh_token": create_refresh_token(user.username, user.user_id),
                    "admin_token": "secretadmintokenkey123" + str(user.user_id),
                    "id": str(user.user_id)
                }
        else:
            return {
                "access_token": create_access_token(user.username, user.user_id),
                "refresh_token": create_refresh_token(user.username, user.user_id),
                "admin_token": ""
            }
            

def get_question_types(posts: list = Depends(get_messages), token: str = Depends(reuseable_oauth),
                       db: Session = Depends(get_db)):
    """
    Функция для получения постов для админа и обычного пользователя
    """
    if validate_token(token):   
        return [
            {
            'question_type': db.query(models.Message).filter(models.Message.user_id == post.user_id).question_type.all()
            } 
            for post in posts]
    else:
        token_data = verify_token(token)
        user_id = token_data.get("id")
        return [
            {
            'question_type': db.query(models.Message).filter(models.Message.user_id == post.user_id).question_type.all()
            } 
            for post in posts]
    
    