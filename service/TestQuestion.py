from db import db
from model.model import TestQuestion


class TestQuestionService:

    def insert(self, test_content, test_type):
        testQuestion = TestQuestion(test_content, test_type)
        db.session.add(testQuestion)
        db.session.commit()
