from db import db

class TestQuestion(db.Model):
    __tablename__ = 'test_question'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    question_content = db.Column(db.String(1000))
    question_type = db.Column(db.Integer)

    def __init__(self, question_content, question_type):
        self.question_content = question_content
        self.question_type = question_type

    def __repr__(self):
        return '<TestQuestion %r>' % self.name