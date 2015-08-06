from app import db
import datetime

#Basic user model
class User(db.Document):
    username = db.StringField(required=True)
    password = db.StringField(required=True)
    name = db.StringField()
    imgPath = db.StringField()
    friends = db.ListField(db.ReferenceField('User'))
    tagline = db.StringField()
    bio = db.StringField()
    city = db.StringField()
    state = db.StringField()
    meta = {'allow_inheritance': True}

#Basic post model
class Post(db.Document):
    content = db.StringField(required=True)
    author = db.ReferenceField(User, required=True)
    datetime = db.DateTimeField(default=datetime.datetime.now)
    tags = db.ListField(db.StringField())
    comments = db.ListField(db.ReferenceField('Comment'))
    meta = {'allow_inheritance': True}

#Basic comment model
class Comment(db.Document):
    content = db.StringField(required=True)
    author = db.ReferenceField(User, required=True)
    datetime = db.DateTimeField(default=datetime.datetime.now)