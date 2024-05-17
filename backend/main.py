from fastapi import (
    FastAPI,
    Depends, )
from starlette.middleware.cors import CORSMiddleware

import models
import admin
import user

from utils import (
    reuseable_oauth,
    Session,
    get_db
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# USER

@app.get("/api/get_messages")
async def get_messages_route(posts: list = Depends(user.get_all_posts), token: str = Depends(reuseable_oauth),
                             db: Session = Depends(get_db)):
    """
    Эндпоинт для получения всех постов из бд
    """
    return user.get_messages(posts, token, db)


@app.get("/api/get_chats")
async def get_chats_route(chats: list = Depends(user.get_all_chats), token: str = Depends(reuseable_oauth)):
    """
    Эндпоинт для получения всех чатов из бд
    """
    return user.get_chats(chats, token)


@app.get("/api/get_question_types")
async def get_question_types_route(posts: list = Depends(user.get_all_posts), token: str = Depends(reuseable_oauth)):
    """
    Эндпоинт для получения всех чатов из бд
    """
    return user.get_question_types(posts, token)


@app.get("/api/get_message/{msg_id}")
async def get_message_route(post: dict = Depends(user.get_post), token: str = Depends(reuseable_oauth),
                            db: Session = Depends(get_db)):
    """
    Эндпоинт для получения конкретного поста
    """
    return user.get_message(post, token, db)


@app.get("/api/get_replies/{msg_id}")
async def get_replies_route(replies: dict = Depends(user.get_replies), token: str = Depends(reuseable_oauth)):
    """
    Эндпоинт для получения всех комментариев из бд
    """
    return user.get_replies_(replies, token)


@app.post("/api/new_reply/")
async def add_reply_route(reply: models.Reply_Insert, db: Session = Depends(get_db),
                          token: str = Depends(reuseable_oauth)):
    """
    Эндпоинт для отправки комментария из веб-приложения
    """
    return user.add_reply(reply, db, token)


@app.post("/api/login/")
async def login_route(view_user: user.User, db: Session = Depends(get_db)):
    """
    Эндпоинт для авторизации
    """
    return user.login(view_user, db)


# ADMIN

@app.get("/api/get_users")
async def get_users_route(users: dict = Depends(admin.get_all_users), token: str = Depends(reuseable_oauth)):
    """
    Эндпоинт для получения всех пользователей из бд в панели администратора (Управление пользователями)
    """
    return admin.get_users(users, token)


@app.delete("/api/delete_message/{msg_id}")
async def delete_message_route(msg_id: int, token: str = Depends(reuseable_oauth),
                               db: Session = Depends(get_db)):
    """
    Эндпоинт для удаления поста
    """
    return admin.delete_message(msg_id, token, db)


@app.delete("/api/delete_reply/{reply_id}")
async def delete_message_route(reply_id: int, token: str = Depends(reuseable_oauth), db: Session = Depends(get_db)):
    """
    Эндпоинт для удаления комментария
    """
    return admin.delete_reply(reply_id, token, db)


@app.post("/api/change_admin_status/")
async def change_admin_route(user_in: admin.User_admin, token: str = Depends(reuseable_oauth),
                             db: Session = Depends(get_db)):
    """
    Эндпоинт для смены роли пользователя
    """
    return admin.change_admin(user_in, token, db)

@app.delete("/api/delete_user/{user_id}")
async def delete_user_route(user_id: int, token: str = Depends(reuseable_oauth),
                             db: Session = Depends(get_db)):
    """
    Эндпоинт для удаления пользователя
    """
    return admin.delete_user(user_id, token, db)