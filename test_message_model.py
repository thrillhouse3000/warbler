import os
from unittest import TestCase
from models import db, Message, User

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

db.create_all()

class MessageModelTestCase(TestCase):
    """Test model for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        user = User.signup("user1", "user1@test.com", "pwd", None)
        user.id = 11

        db.session.commit()

        user = User.query.get(11)

        self.user = user

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_message_model(self):
        """Does basic model work?"""

        m = Message(text='text', user_id=self.user.id)

        db.session.add(m)
        db.session.commit()

        self.assertEqual(len(self.user.messages), 1)
        self.assertEqual(self.user.messages[0].text, 'text')
    
    def test_message_likes(self):
        """Does message like functionality work"""
        m = Message(text='text', user_id=self.user.id)

        db.session.add(m)
        db.session.commit()

        self.user.likes.append(m)

        db.session.commit()

        self.assertEqual(len(self.user.likes), 1)
        self.assertEqual(self.user.likes[0].id, m.id)
  