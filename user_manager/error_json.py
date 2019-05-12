from flask import jsonify
from enum import Enum


def return_json_error(errorID):
    return jsonify(
        error=errorID.explaination,
        errorID=errorID.number
    )


class error(Enum):
    FUNC_NOT_IMPLEMENTED = (5, "Function not implemented.")
    JSON_STRUCTURE_WRONG = (101, "Invalid JSON structure.")
    USER_NAME_NOT_FOUND = (514, "User not found.")
    USER_NAME_OR_PASS_NOT_FOUND = (515, "User not found.")
    USER_NAME_ALREADY_USED = (513, "Username already used.")
    USER_LOGIN_EXPIRED = (512, "Login expired.")
    USER_NOT_LOGGED_IN = (511, "User not logged in.")
    USER_NOT_CONFIRMED = (516, "User not confirmed.")
    USER_NOT_PRIVILEGED = (551, "User not privileged.")
    FRIEND_NOT_FOUND = (611, "Friend not found.")
    MESSAGE_NOT_FOUND = (711, "Message not found.")
    MESSAGE_RECEIVER_NOT_FOUND = (712, "Message receiver not found.")
    TEAM_ALREADY_EXISTS = (815, "Team already exists.")
    TEAM_NOT_FOUND = (814, "Team was not found.")
    TEAM_ROLE_WAS_TOO_LOW = (854, "Team role was to low.")
    TEAM_USER_EXISTS = (816, "Team already had this user.")
    TEAM_USER_DOESNT_EXISTS = (817, "Team didn't have this user.")

    def __init__(self, number, explaination):
        self.number = number
        self.explaination = explaination

