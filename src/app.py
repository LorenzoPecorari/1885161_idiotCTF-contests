from flask import Flask, request, jsonify, Response
# from flask_cors import CORS

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import sqlalchemy
import json

from mail_sender_utils import MailSender

app = Flask(__name__)
# CORS(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ctf_contests.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Modello dell'utente
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username
        }

# Modello del contest
class Contest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    admin_id = db.Column(db.Integer, nullable=False)
    start_datetime = db.Column(db.DateTime, nullable=False)
    end_datetime = db.Column(db.DateTime, nullable=False)
    participants = db.relationship("User", secondary="contest_participants", backref="contests")

    def to_dict(self):
        return {
            "type": "Contest",
            "id": self.id,
            "name": self.name,
            "admin_id": self.admin_id,
            "start_datetime": self.start_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "end_datetime": self.end_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "participants": [user.to_dict() for user in self.participants]
        }

# Tabella di associazione tra contest e partecipanti
contest_participants = db.Table("contest_participants",
    db.Column("contest_id", db.Integer, db.ForeignKey("contest.id"), primary_key=True),
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True)
)

#creazione del db
@app.cli.command("create-db")
def create_db():
    """Creates the database."""
    with app.app_context():
        db.create_all()
    print("Database created!")

def make_json_response(data, status_code=200):
    return Response(response=json.dumps(data), status=status_code)

def success_dict(status="success", data=None):
    return  {"status": status } if data is None else  {"status": status, "data":data }

def error_dict(err_desc):
    return {"status": "error", "error_description": err_desc}


# Operazione CREATE: Creare un nuovo contest
@app.route("/contests", methods=["POST"])
def create_contest():
    data = request.get_json()
    name = data["name"]
    admin_id = data["admin_id"]
    start_datetime = datetime.strptime(data["start_datetime"], "%Y-%m-%d %H:%M:%S")
    end_datetime = datetime.strptime(data["end_datetime"], "%Y-%m-%d %H:%M:%S")

    # Creazione del contest
    contest = Contest(name=name, admin_id=admin_id, start_datetime=start_datetime, end_datetime=end_datetime)
    
    db.session.add(contest)
    db.session.commit()
    resp_dict = success_dict("created", data={"count":1, "objects":[contest.to_dict()]})
    return make_json_response(resp_dict, 201)


# Operazione JOIN: Add new partecipant to contest
@app.route("/contests/<int:contest_id>/add_new_partecipant", methods=["POST"])
def add_contestant(contest_id):
    data = request.get_json()
    name = data["username"]
    user = User.query.filter_by(username=name).one_or_none()
    if user is None:
        user  = User(username=name)
        print(user.to_dict())
        db.session.add(user)
    contest = Contest.query.filter_by(id=contest_id).one()
    contest.participants.append(user)
    try:
        db.session.commit()
        mailSender=MailSender()
        mailSender.user_notification(name)
    except sqlalchemy.exc.IntegrityError as e:
        return make_json_response(error_dict("partecipant already added before"))
    return make_json_response(success_dict())

# Operazione READ: Ottenere l'elenco di tutti i contest
@app.route("/contests", methods=["GET"])
def get_contests():
    contests = Contest.query.all()
    resp_dict = success_dict(data={"count":len(contests), "objects":
                    [contest.to_dict() for contest in contests]})
    return make_json_response(resp_dict)

# Operazione READ: Ottenere un singolo contest per ID
@app.route("/contests/<int:contest_id>", methods=["GET"])
def get_contest(contest_id):
    contest = Contest.query.filter_by(id=contest_id).one()
    return make_json_response(success_dict(data={"count":1, "objects":[contest.to_dict()]}))

# Operazione UPDATE: Modificare un contest
@app.route("/contests/<int:contest_id>", methods=["PUT"])
def update_contest(contest_id):
    contest = Contest.query.filter_by(id=contest_id).one()
    data = request.get_json()

    contest.name = data.get("name", contest.name)
    contest.start_datetime = datetime.strptime(data.get("start_datetime"), "%Y-%m-%d %H:%M:%S")
    contest.end_datetime = datetime.strptime(data.get("end_datetime"), "%Y-%m-%d %H:%M:%S")

    # Aggiornamento dei partecipanti
    if "participants" in data:
        contest.participants.clear()
        for user_id in data["participants"]:
            user = User.query.get(user_id)
            if user:
                contest.participants.append(user)

    db.session.commit()
    return make_json_response(success_dict(data={"count":1, "objects":[contest.to_dict()]}))

# Operazione DELETE: Eliminare un contest
@app.route("/contests/<int:contest_id>", methods=["DELETE"])
def delete_contest(contest_id):
    contest = Contest.query.filter_by(id=contest_id).one()
    db.session.delete(contest)
    db.session.commit()
    return make_json_response(success_dict(), 204) # changed from success_dict to success_dict() for calling the method

@app.route("/contests/users", methods=["GET"])
def get_contests_users():
    users=User.query.all()
    resp_dict = success_dict(data={"count":len(users), "objects":
                    [user.to_dict() for user in users]})
    return make_json_response(resp_dict)

@app.route("/contests/get_user_by_email/<string:email>", methods=["GET"])
def get_user(email):
    user = User.query.filter_by(username=email).one()
    return make_json_response(success_dict(data={"count":1, "objects":[user.to_dict()]}))

@app.route("/contests/getcontestsbyuser/<int:user_id>", methods=["GET"])
def get_contests_by_users(user_id):
    contests = Contest.query.join(contest_participants).filter(contest_participants.c.user_id == user_id).all()
    resp_dict = success_dict(data={"count":len(contests), "objects":
                    [contest.to_dict() for contest in contests]})
    return make_json_response(resp_dict)

@app.errorhandler(ValueError)
def handle_exception(error):
    response = jsonify(error_dict(str(error)))
    response.status_code = 400
    return response

@app.errorhandler(AssertionError)
def handle_exception(error):
    response = jsonify(error_dict(str(error)))
    response.status_code = 400
    return response

@app.errorhandler(sqlalchemy.exc.NoResultFound)
def handle_exception(error):
    response = jsonify(error_dict(str(error)))
    response.status_code = 404
    return response


@app.errorhandler(Exception)
def handle_exception(error):
    response = jsonify(error_dict(str(error)))
    response.status_code = 500
    return response


if __name__ == "__main__":
    app.run(debug=True)
    # app.run(debug=True, port = 49132)
