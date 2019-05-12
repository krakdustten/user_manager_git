import error_json as err
import database_def as db
from datetime import datetime, timedelta
import random

ALPHABET = "0123456789abcdef"


def checkUser(session, username="_", password="_", currentID="_"):
    user = 0
    if currentID == "_":
        user = session.query(db.User).filter(db.and_(db.User.name == username, db.User.password == password)).one()
        if user:
            if user.confirmed:
                currentID = ''.join(random.choice(ALPHABET) for i in range(128))
                timingID = datetime.now() + timedelta(days=1)
                user.currentID = currentID
                user.validUntilID = timingID
                session.commit()
            else:
                return {'error': True, 'return': err.return_json_error(err.error.USER_NOT_CONFIRMED)}
        else:
            return {'error': True, 'return': err.return_json_error(err.error.USER_NOT_LOGGED_IN)}
    else:
        user = session.query(db.User).filter(db.and_(db.User.name == username, db.User.currentID == currentID)).all()
        if user:
            user = user[0]
            if user.validUntilID <= datetime.now():
                return {'error': True, 'return': err.return_json_error(err.error.USER_LOGIN_EXPIRED)}
            if not user.confirmed:
                return {'error': True, 'return': err.return_json_error(err.error.USER_NOT_CONFIRMED)}
        else:
            return {'error': True, 'return': err.return_json_error(err.error.USER_NOT_LOGGED_IN)}
    return {'error': False, 'user': user}
