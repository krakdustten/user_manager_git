from flask import Flask, request, jsonify
import database_def as db
import error_json as err
import random
import email_handlr
from datetime import datetime, timedelta
import checkdata as chk

ALPHABET = "0123456789abcdef"
app = Flask(__name__)
s = db.session()


@app.route('/user/login/', methods=['POST'])
def login():
    data = request.get_json(silent=False)
    if 'username' not in data:
        return err.return_json_error(err.error.JSON_STRUCTURE_WRONG)
    elif 'password' not in data:
        ret = s.query(db.User).filter(db.User.name == data['username']).one()
        if ret:
            return jsonify(salt=ret.salt)
        return err.return_json_error(err.error.USER_NAME_NOT_FOUND)
    else:
        ret = chk.checkUser(s, username=data['username'], password=data['password'])
        if not ret['error']:
            user = ret['user']
            return jsonify(
                #id=user.id,
                currentID=user.currentID,
                validUntilID=user.validUntilID,
                rights=user.rights
            )
        return ret['return']


@app.route('/user/register/', methods=['POST'])
def register():
    data = request.get_json(silent=False)
    if ('salt' not in data) or \
            ('username' not in data) or \
            ('password' not in data) or \
            ('email' not in data):
        userID = ''.join(random.choice(ALPHABET) for i in range(128))
        return jsonify(salt=userID)
    else:
        ret = s.query(db.User).filter(db.User.name == data['username']).all()
        if ret:
            return err.return_json_error(err.error.USER_NAME_ALREADY_USED)
        else:
            newUser = db.User(name=data['username'],
                              email=data['email'],
                              password=data['password'],
                              salt=data['salt'],
                              confirmed=False)
            userID = ''.join(random.choice(ALPHABET) for i in range(128))
            timingID = datetime.now() + timedelta(days=7)
            newUser.currentID = userID
            newUser.validUntilID = timingID
            s.add(newUser)
            s.commit()
            email_handlr.sendConfirmation(userID, data['username'], data['email'])
            return jsonify(validUntilID=newUser.validUntilID)


@app.route('/user/register/confirm', methods=['GET'])
def registerConfirm():
    username = request.args.get('username', default='*', type=str)
    confirmID = request.args.get('confirmID', default='*', type=str)

    if ('confirmID' == '*') or ('username' == '*'):
        return err.return_json_error(err.error.JSON_STRUCTURE_WRONG)
    else:
        user = s.query(db.User).filter(db.User.name == username).all()
        if user:
            user = user[0]
            if not user.confirmed:
                if user.currentID == confirmID:
                    user.confirmed = True
                    user.validUntilID = datetime.now()
                    s.commit()
                    return "Successful"
                else:
                    return "Identification ID wrong."
            else:
                return "Already confirmed."
        else:
            return err.return_json_error(err.error.USER_NAME_NOT_FOUND)


@app.route('/user/remove/', methods=['POST'])
def userRemove():
    data = request.get_json(silent=False)
    if ('currentID' not in data) or ('username' not in data):
        return err.return_json_error(err.error.JSON_STRUCTURE_WRONG)
    else:
        user = chk.checkUser(s, username=data['username'], currentID=data['currentID'])
        if not user['error']:
            user = user['user']
            s.delete(user)
            s.commit()
            return jsonify(done=True)
        else:
            return user['return']


@app.route('/friend/add/', methods=['POST'])
def friendAdd():
    data = request.get_json(silent=False)
    if ('currentID' not in data) or ('username' not in data) or ('friendsname' not in data):
        return err.return_json_error(err.error.JSON_STRUCTURE_WRONG)
    else:
        user = chk.checkUser(s, username=data['username'], currentID=data['currentID'])
        friend = s.query(db.User).filter(db.User.name == data['friendsname']).all()
        if not user['error']:
            user = user['user']
            if friend:
                friend = friend[0]
                isFriend = s.query(db.UserFriend).filter(
                    db.or_(db.and_(db.UserFriend.user1 == user, db.UserFriend.user2 == friend),
                            db.and_(db.UserFriend.user1 == friend, db.UserFriend.user2 == user))).all()
                if isFriend:
                    return jsonify(done=False)
                friendship = db.UserFriend(user1=user, user2=friend, startTime=datetime.now(), accepted=False)
                s.add(friendship)
                s.commit()
                return jsonify(done=True)
            else:
                return err.return_json_error(err.error.FRIEND_NOT_FOUND)
        else:
            return user['return']


@app.route('/friend/remove/', methods=['POST'])
def friendRemove():
    data = request.get_json(silent=False)
    if ('currentID' not in data) or ('username' not in data) or ('friendsname' not in data):
        return err.return_json_error(err.error.JSON_STRUCTURE_WRONG)
    else:
        user = chk.checkUser(s, username=data['username'], currentID=data['currentID'])
        friend = s.query(db.User).filter(db.User.name == data['friendsname']).all()
        if not user['error']:
            user = user['user']
            if friend:
                friend = friend[0]
                isFriend = s.query(db.UserFriend).filter(
                    db.or_(db.and_(db.UserFriend.user1 == user, db.UserFriend.user2 == friend),
                           db.and_(db.UserFriend.user1 == friend, db.UserFriend.user2 == user))).all()
                if not isFriend:
                    return jsonify(done=False)
                s.delete(isFriend[0])
                s.commit()
                return jsonify(done=True)
            else:
                return err.return_json_error(err.error.FRIEND_NOT_FOUND)
        else:
            return user['return']


@app.route('/friend/', methods=['GET'])
def friendList():
    username = request.args.get('username', default='*', type=str)
    currentID = request.args.get('currentID', default='*', type=str)
    user = chk.checkUser(s, username=username, currentID=currentID)
    if not user['error']:
        user = user['user']
        friends = list()
        for friend in user.friends1:
            toAdd = {
                #'id': friend.id,
                'name': friend.user2.name,
                'startTime': friend.startTime,
                'accepted': friend.accepted,
                'askedby': "user"
            }
            friends.append(toAdd)
        for friend in user.friends2:
            toAdd = {
                #'id': friend.id,
                'name': friend.user1.name,
                'startTime': friend.startTime,
                'accepted': friend.accepted,
                'askedby': "friend"
            }
            friends.append(toAdd)
        return jsonify(friends)
    return user['return']


@app.route('/friend/accept/', methods=['POST'])
def friendAccept():
    data = request.get_json(silent=False)
    if ('currentID' not in data) or ('username' not in data) or ('friendsname' not in data):
        return err.return_json_error(err.error.JSON_STRUCTURE_WRONG)
    else:
        user = chk.checkUser(s, username=data['username'], currentID=data['currentID'])
        friend = s.query(db.User).filter(db.User.name == data['friendsname']).all()
        if not user['error']:
            user = user['user']
            if friend:
                friend = friend[0]
                friendship = s.query(db.UserFriend).filter(db.and_(db.UserFriend.user1 == friend, db.UserFriend.user2 == user)).all()
                if friendship:
                    friendship[0].accepted = True
                    s.commit()
                    return jsonify(done=True)
                return err.return_json_error(err.error.FRIEND_NOT_FOUND)
            else:
                return err.return_json_error(err.error.FRIEND_NOT_FOUND)
        else:
            return user['return']


@app.route('/message/new', methods=['POST'])
def messageNew():
    data = request.get_json(silent=False)
    if ('currentID' not in data) or ('username' not in data) or ('message' not in data) or ('receiver' not in data):
        return err.return_json_error(err.error.JSON_STRUCTURE_WRONG)
    else:
        user = chk.checkUser(s, username=data['username'], currentID=data['currentID'])
        receiver = s.query(db.User).filter(db.User.name == data['receiver']).all()
        if not user['error']:
            user = user['user']
            if receiver:
                receiver = receiver[0]
                mess = db.Message(receiver=receiver, sender=user, message=data['message'])
                s.add(mess)
                s.commit()
                return jsonify({
                    'id': mess.id,
                    'sender': mess.sender.name,
                    'receiver': mess.receiver.name,
                    'message': mess.message,
                    'sendTime': mess.sentTime,
                    'receiverRead': mess.receiverRead
                })
            else:
                return err.return_json_error(err.error.MESSAGE_RECEIVER_NOT_FOUND)
        else:
            return user['return']


@app.route('/message/remove', methods=['POST'])
def messageRemove():
    data = request.get_json(silent=False)
    if ('currentID' not in data) or ('username' not in data) or ('messageID' not in data):
        return err.return_json_error(err.error.JSON_STRUCTURE_WRONG)
    else:
        user = chk.checkUser(s, username=data['username'], currentID=data['currentID'])
        if not user['error']:
            user = user['user']
            mess = s.query(db.Message).filter(db.and_(db.Message.id == data['messageID'], db.Message.receiver == user)).all()
            if mess:
                s.delete(mess[0])
                s.commit()
                return jsonify(done=True)
            return jsonify(done=False)
        else:
            return user['return']


@app.route('/message/', methods=['GET'])
def messageList():
    username = request.args.get('username', default='*', type=str)
    currentID = request.args.get('currentID', default='*', type=str)
    user = chk.checkUser(s, username=username, currentID=currentID)
    if not user['error']:
        user = user['user']
        messagesReceived = list()
        messagesSent = list()
        for message in user.messagesReceived:
            toAdd = {
                'id': message.id,
                'sender': message.sender.name,
                'receiver': message.receiver.name,
                'message': message.message,
                'sendTime': message.sentTime,
                'receiverRead': message.receiverRead
            }
            messagesReceived.append(toAdd)
            if not message.receiverRead:
                message.receiverRead = True
                s.commit()
        for message in user.messagesSent:
            toAdd = {
                'id': message.id,
                'sender': message.sender.name,
                'receiver': message.receiver.name,
                'message': message.message,
                'sendTime': message.sentTime,
                'receiverRead': message.receiverRead
            }
            messagesSent.append(toAdd)
        return jsonify({'received': messagesReceived, 'sent': messagesSent})
    return user['return']


@app.route('/user/', methods=['GET'])
def userGet():
    username = request.args.get('username', default='*', type=str)
    user = s.query(db.User).filter(db.User.name == username).all()
    if user:
        user = user[0]
        return jsonify({
            'userID': user.id,
            'rights': user.rights
        })
    return err.return_json_error(err.error.JSON_STRUCTURE_WRONG)


@app.route('/team/create/', methods=['POST'])
def teamCreate():
    data = request.get_json(silent=False)
    if ('currentID' not in data) or ('username' not in data) or ('teamName' not in data):
        return err.return_json_error(err.error.JSON_STRUCTURE_WRONG)
    else:
        user = chk.checkUser(s, username=data['username'], currentID=data['currentID'])
        if not user['error']:
            user = user['user']
            if user.rights > 100:
                teamExist = s.query(db.Team).filter(db.Team.name==data['teamName']).all()
                if teamExist:
                    return err.return_json_error(err.error.TEAM_ALREADY_EXISTS)
                team = db.Team(name=data['teamName'])
                teammember = db.TeamUser(user=user, team=team, role=1000)
                s.add(team)
                s.add(teammember)
                s.commit()
                return jsonify({
                    "name": team.name,
                    "members": [{
                        "name": user.name
                    }]
                })
            else:
                return err.return_json_error(err.error.USER_NOT_PRIVILEGED)
        else:
            return user['return']


@app.route('/team/remove/', methods=['POST'])
def teamRemove():
    data = request.get_json(silent=False)
    if ('currentID' not in data) or ('username' not in data) or ('teamName' not in data):
        return err.return_json_error(err.error.JSON_STRUCTURE_WRONG)
    else:
        user = chk.checkUser(s, username=data['username'], currentID=data['currentID'])
        if not user['error']:
            user = user['user']
            if user.rights > 100:
                team = s.query(db.Team).filter(db.Team.name == data['teamName']).all()
                if team:
                    team = team[0]
                    teamuser = s.query(db.TeamUser).filter(db.and_(db.TeamUser.team == team, db.TeamUser.user == user)).all()
                    if teamuser:
                        teamuser = teamuser[0]
                        if teamuser.role >= 1000:
                            s.delete(team)
                            s.commit()
                            return jsonify(done=True)
                    return err.return_json_error(err.error.TEAM_ROLE_WAS_TOO_LOW)
                else:
                    return err.return_json_error(err.error.TEAM_NOT_FOUND)
            else:
                return err.return_json_error(err.error.USER_NOT_PRIVILEGED)
        else:
            return user['return']


@app.route('/team/', methods=['GET'])
def teamGet():
    username = request.args.get('username', default='*', type=str)
    currentID = request.args.get('currentID', default='*', type=str)
    teamName = request.args.get('teamName', default='*', type=str)
    if username == '*' or currentID == '*' or teamName == '*':
        return err.return_json_error(err.error.JSON_STRUCTURE_WRONG)
    user = chk.checkUser(s, username, currentID=currentID)
    if not user['error']:
        user = user['user']
        team = s.query(db.Team).filter(db.Team.name == teamName).all()
        if team:
            team = team[0]
            isPartOfTeam = s.query(db.TeamUser).filter(db.and_(db.TeamUser.team == team, db.TeamUser.user == user)).all()
            if isPartOfTeam:
                members = list()
                for teamuser in team.teamUser:
                    toAdd = {
                        # 'id': friend.id,
                        'name': teamuser.user.name,
                        'enrollTime': teamuser.enrollTime,
                        'role': teamuser.role
                    }
                    members.append(toAdd)
                return jsonify({
                    "name": team.name,
                    "members": members
                })
            else:
                return err.return_json_error(err.error.TEAM_ROLE_WAS_TOO_LOW)
        else:
            return err.return_json_error(err.error.TEAM_NOT_FOUND)
    else:
        return user['return']
    return err.return_json_error(err.error.JSON_STRUCTURE_WRONG)


@app.route('/team/member/add', methods=['POST'])
def teamMemberAdd():
    data = request.get_json(silent=False)
    if ('currentID' not in data) or ('username' not in data) or ('teamName' not in data) or ('userNameToAdd' not in data) or ('userRoleToAdd' not in data):
        return err.return_json_error(err.error.JSON_STRUCTURE_WRONG)
    else:
        user = chk.checkUser(s, username=data['username'], currentID=data['currentID'])
        if not user['error']:
            user = user['user']
            team = s.query(db.Team).filter(db.Team.name == data['teamName']).all()
            if team:
                team = team[0]
                teamuser = s.query(db.TeamUser).filter(db.and_(db.TeamUser.team == team, db.TeamUser.user == user)).all()
                if teamuser:
                    teamuser = teamuser[0]
                    if teamuser.role >= 100:
                        newuser = s.query(db.User).filter(db.User.name == data['userNameToAdd'])
                        if newuser:
                            newuser = newuser[0]
                            teamnewuser = s.query(db.TeamUser).filter(db.and_(db.TeamUser.team == team, db.TeamUser.user == newuser)).all()
                            if teamnewuser:
                                return err.return_json_error(err.error.TEAM_USER_EXISTS)
                            else:
                                teamnewuser = db.TeamUser(user=newuser, team=team, role=data['userRoleToAdd'])
                                s.add(teamnewuser)
                                s.commit()
                                return jsonify(done=True)
                        else:
                            return err.return_json_error(err.error.USER_NAME_NOT_FOUND)
                    else:
                        return err.return_json_error(err.error.TEAM_ROLE_WAS_TOO_LOW)
                else:
                    return err.return_json_error(err.error.TEAM_ROLE_WAS_TOO_LOW)
            else:
                return err.return_json_error(err.error.TEAM_NOT_FOUND)
        else:
            return user['return']


@app.route('/team/member/remove', methods=['POST'])
def teamMemberRemove():
    data = request.get_json(silent=False)
    if ('currentID' not in data) or ('username' not in data) or ('teamName' not in data) or ('userNameToRemove' not in data):
        return err.return_json_error(err.error.JSON_STRUCTURE_WRONG)
    else:
        user = chk.checkUser(s, username=data['username'], currentID=data['currentID'])
        if not user['error']:
            user = user['user']
            team = s.query(db.Team).filter(db.Team.name == data['teamName']).all()
            if team:
                team = team[0]
                teamuser = s.query(db.TeamUser).filter(db.and_(db.TeamUser.team == team, db.TeamUser.user == user)).all()
                if teamuser:
                    teamuser = teamuser[0]
                    if teamuser.role >= 100:
                        newuser = s.query(db.User).filter(db.User.name == data['userNameToRemove'])
                        if newuser:
                            newuser = newuser[0]
                            teamnewuser = s.query(db.TeamUser).filter(db.and_(db.TeamUser.team == team, db.TeamUser.user == newuser)).all()
                            if teamnewuser:
                                teamnewuser = teamnewuser[0]
                                s.delete(teamnewuser)
                                s.commit()
                                return jsonify(done=True)
                            else:
                                return err.return_json_error(err.error.TEAM_USER_DOESNT_EXISTS)
                        else:
                            return err.return_json_error(err.error.USER_NAME_NOT_FOUND)
                    else:
                        return err.return_json_error(err.error.TEAM_ROLE_WAS_TOO_LOW)
                else:
                    return err.return_json_error(err.error.TEAM_ROLE_WAS_TOO_LOW)
            else:
                return err.return_json_error(err.error.TEAM_NOT_FOUND)
        else:
            return user['return']


@app.route('/team/member/role', methods=['POST'])
def teamMemberRoleSet():
    data = request.get_json(silent=False)
    if ('currentID' not in data) or ('username' not in data) or ('teamName' not in data) or ('userNameToChange' not in data) or ('userRole' not in data):
        return err.return_json_error(err.error.JSON_STRUCTURE_WRONG)
    else:
        user = chk.checkUser(s, username=data['username'], currentID=data['currentID'])
        if not user['error']:
            user = user['user']
            team = s.query(db.Team).filter(db.Team.name == data['teamName']).all()
            if team:
                team = team[0]
                teamuser = s.query(db.TeamUser).filter(db.and_(db.TeamUser.team == team, db.TeamUser.user == user)).all()
                if teamuser:
                    teamuser = teamuser[0]
                    if teamuser.role >= 100:
                        newuser = s.query(db.User).filter(db.User.name == data['userNameToChange'])
                        if newuser:
                            newuser = newuser[0]
                            teamnewuser = s.query(db.TeamUser).filter(db.and_(db.TeamUser.team == team, db.TeamUser.user == newuser)).all()
                            if teamnewuser:
                                teamnewuser = teamnewuser[0]
                                teamnewuser.role = data['userRole']
                                s.commit()
                                return jsonify(done=True)
                            else:
                                return err.return_json_error(err.error.TEAM_USER_DOESNT_EXISTS)
                        else:
                            return err.return_json_error(err.error.USER_NAME_NOT_FOUND)
                    else:
                        return err.return_json_error(err.error.TEAM_ROLE_WAS_TOO_LOW)
                else:
                    return err.return_json_error(err.error.TEAM_ROLE_WAS_TOO_LOW)
            else:
                return err.return_json_error(err.error.TEAM_NOT_FOUND)
        else:
            return user['return']


# s = db.session()
# data = s.query(db.User).filter(db.User.name.startswith("t")).all()
# newUser = db.User(name="Good", email="mail", password="no", salt="salty")
# for user in data:
#     friends = db.UserFriend(user1=newUser, user2=user)
#     print(friends.user1_id)
#     s.add(friends)
# s.add(newUser)
# s.commit()



if __name__ == '__main__':
    app.run()
