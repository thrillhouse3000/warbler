import os
from unittest import TestCase
from models import db, Message, User

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False

class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        user1 = User.signup("user1", "user1@test.com", "pwd", None)
        user1.id = 11
        user2 = User.signup("user2", "user2@test.com", "pwd", None)
        user2.id = 22
        db.session.commit()

        user1 = User.query.get(11)
        user2 = User.query.get(22)

        self.user1 = user1
        self.user2 = user2

        m = Message(text='test-message', user_id=self.user1.id)

        db.session.add(m)
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_add_message(self):
        """Test message creation"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id
            res = c.post('/messages/new', data={'text': 'hello'})

            self.assertEqual(res.status_code, 302)
            m = Message.query.all()
            self.assertEqual(m[1].text, 'hello')

    def test_add_no_session(self):
        """Test authorization for message creation"""
        with self.client as c:
            res = c.post('/messages/new', data={'text': 'hello'}, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn("Access unauthorized", str(res.data))
        
    def test_add_bad_user(self):
        """Test authentication for message creation"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 32747298348
            res = c.post('/messages/new', data={'text': 'hello'}, follow_redirects=True)

            self.assertEqual(res.status_code, 200)
            self.assertIn("Access unauthorized", str(res.data))
    
    def test_message_details(self):
        """Test message show route"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id
            m = Message.query.get(1)
            res = c.get(f'/messages/{m.id}')

            self.assertEqual(res.status_code, 200)
            self.assertIn(m.text, str(res.data))


    def test_bad_message_show(self):
        """Test show route for non-existent message"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id
            res = c.get('/messages/23402934809')

            self.assertEqual(res.status_code, 404)
    
    def test_delete_message(self):
        """Test message delete route"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id
            res = c.post('/messages/1/delete')

            self.assertEqual(res.status_code, 302)

            m = Message.query.all()

            self.assertEqual(len(m), 0)
    
    def test_unauthorized_delete(self):
        """Test delete route for unauthorized user"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user2.id
            res = c.post('/messages/1/delete', follow_redirects=True)

            self.assertEqual(res.status_code, 200)
            self.assertIn("Access unauthorized", str(res.data))

    def test_unauthenticated_delete(self):
        """Test delete route for unauthenticated user"""
        with self.client as c:
            res = c.post('/messages/1/delete', follow_redirects=True)

            self.assertEqual(res.status_code, 200)
            self.assertIn("Access unauthorized", str(res.data))

            m = Message.query.get(1)
            self.assertIsNotNone(m)
