import functools
import os
import uuid
from hmac import compare_digest
from urllib import request

from flask import Flask, make_response, jsonify, redirect
from flask_restful import reqparse, Api, Resource
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

load_dotenv()

app = Flask(__name__)
api = Api(app)

parser = reqparse.RequestParser()

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://" + \
                                        os.getenv("POSTGRES_USER") + ":" + os.getenv("POSTGRES_PASSWORD") + \
                                        "@" + os.getenv("POSTGRES_HOST") + ":" + os.getenv("POSTGRES_PORT") + \
                                        "/" + os.getenv("POSTGRES_DATABASE")

db = SQLAlchemy(app)


def is_valid(api_key):
    device = DeviceModel.find_by_device_key(api_key)
    if device and compare_digest(device.device_key, api_key):
        return True


def api_required(func):
    @functools.wraps(func)
    def decorator(*args, **kwargs):
        parser.add_argument('api_key', type=str, location='json')
        body = parser.parse_args()
        api_key = body['api_key']

        if not api_key:
            return {"message": "Please provide an API key"}, 400
        if is_valid(api_key):
            return func(*args, **kwargs)
        else:
            return {"message": "The provided API key is not valid"}, 403

    return decorator


class DeviceModel(db.Model):
    __tablename__ = 'devices'

    id = db.Column(db.Integer, primary_key=True)
    device_name = db.Column(db.String(80))
    device_key = db.Column(db.String(80))

    def __init__(self, device_name):
        self.device_name = device_name
        self.device_key = uuid.uuid4().hex

    def json(self):
        return {
            'device_name': self.device_name,
            'device_key': self.device_key,
        }

    @classmethod
    def find_by_name(cls, device_name):
        return cls.query.filter_by(device_name=device_name).first()

    @classmethod
    def find_by_device_key(cls, device_key):
        return cls.query.filter_by(device_key=device_key).first()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()


class ProjectModel(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), unique=True)
    status = db.Column(db.String())

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"<Project {self.id}, {self.name}, status: {self.status}>"


class Project(Resource):
    def get(self, project_id):
        # TODO: get the svg of the build status
        project: ProjectModel = db.session.get(ProjectModel, project_id)
        if not project:
            return make_response("", 404)
        color = "yellow"
        if project.status == 'success':
            color = "green"
        elif project.status == 'failed':
            color = "red"
        return redirect(get_badge("build", project.status, color, "github"), 202)

    @api_required
    def post(self, project_id):
        # TODO: set build status of project name
        parser.add_argument('status', type=str, location='json')
        args = parser.parse_args()
        project: ProjectModel = db.session.get(ProjectModel, project_id)
        if not project:
            return make_response("", 404)
        project.status = args['status']
        db.session.commit()
        return make_response(jsonify({"id": project.id, "project_name": project.name, "status": project.status}), 200)

    @api_required
    def put(self):
        # TODO: create a new project
        parser.add_argument('project_name', type=str, location='json')
        args = parser.parse_args()
        prj = ProjectModel(args['project_name'])
        db.session.add(prj)
        db.session.commit()
        return make_response(jsonify({"id": prj.id, "project_name": prj.name}), 200)


migrate = Migrate(app, db)


def get_badge(target: str, status: str, color: str, icon: str):
    return f"https://badgen.net/badge/{target}/{status}/{color}?icon={icon}"


api.add_resource(Project, '/projects/', '/projects/<project_id>')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug= True if os.getenv('DEBUG') == 'True' else False)
