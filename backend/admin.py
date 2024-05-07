from fastapi import Depends, HTTPException
from pydantic import BaseModel

import models as models
from utils import (
    reuseable_oauth,
    validate_token,
    Session,
    get_db
)


class User_admin(BaseModel):
    user_id: int
    is_admin: int


def get_all_users(db: Session = Depends(get_db)):
    return db.query(models.PrivateUser).distinct().all()


def get_users(users: dict = Depends(get_all_users), token: str = Depends(reuseable_oauth)):
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


def delete_message(msg_id: int, token: str = Depends(reuseable_oauth),
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


def delete_reply(reply_id: int, token: str = Depends(reuseable_oauth), db: Session = Depends(get_db)):
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


def change_admin(user_in, token: str = Depends(reuseable_oauth),
                 db: Session = Depends(get_db)):
    is_authenticated = validate_token(token)
    if is_authenticated:
        try:
            # Находим пользователя по user_id
            user = db.query(models.PrivateUser).filter(models.PrivateUser.user_id == user_in.user_id).first()
            if user:
                # Обновляем поле is_admin
                user.is_admin = bool(user_in.is_admin)
                db.commit()
                return {"message": f"Статус администратора для пользователя {user_in.user_id} успешно обновлен"}
            else:
                raise HTTPException(status_code=404, detail="Пользователь не найден")
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500,
                                detail=f"Произошла ошибка при обновлении статуса администратора: {str(e)}")
    else:
        raise HTTPException(status_code=401, detail="Не авторизован")