from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model , UserMixin):
    id = db.Column(db.Integer , primary_key = True)
    username = db.Column(db.String(30) , unique = True , nullable = False)
    email = db.Column(db.String(50) , unique = True , nullable = False)
    password = db.Column(db.String(200) , nullable = False)
    is_active = db.Column(db.Boolean , default = False)

class RoleRequirement(db.Model):
    __tablename__ = 'role_requirements'
    role_id = db.Column(db.Integer , primary_key = True)
    role_name = db.Column(db.String(200) , nullable = False)
    description = db.Column(db.Text , nullable = False)