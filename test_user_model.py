"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc
from models import db, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
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

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_user_follow(self):
        """Can user follow another user"""
        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertEqual(len(self.user1.following), 1)
        self.assertEqual(len(self.user2.following), 0)
        self.assertEqual(len(self.user1.followers), 0)
        self.assertEqual(len(self.user2.followers), 1)

        self.assertEqual(self.user2.followers[0].id, self.user1.id)
        self.assertEqual(self.user1.following[0].id, self.user2.id)
    
    def test_user_is_following(self):
        """Is user following other user"""
        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertTrue(self.user1.is_following(self.user2))
        self.assertFalse(self.user2.is_following(self.user1))
    
    def test_user_is_followed(self):
        """Is user following other user"""
        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertTrue(self.user2.is_followed_by(self.user1))
        self.assertFalse(self.user1.is_followed_by(self.user2))
       
    def test_signup(self):
        """test signup method"""
        u = User.signup('test', 'test@test.test', 'password', None)
        uid = 99
        u.id = uid
        db.session.commit()

        test_user = User.query.get(uid)
        self.assertIsNotNone(test_user)
        self.assertEqual(test_user.username, 'test')
        self.assertEqual(test_user.email, 'test@test.test')
        self.assertNotEqual(test_user.password, 'password')
    
    def test_badusername_signup(self):
        """test signup method error handling"""
        u = User.signup(None, 'test@test.test', 'password', None)
        uid = 98
        u.id = uid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_bademail_signup(self):
        """test signup method error handling"""
        u = User.signup('test', None, 'password', None)
        uid = 97
        u.id = uid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_badpassword_signup(self):
        """test signup method error handling"""
        with self.assertRaises(ValueError) as context:
            User.signup('test', 'test@test.test', '', None)
        with self.assertRaises(ValueError) as context:
            User.signup('test', 'test@test.test', None, None)

    def test_auth(self):
        """test authentication method"""
        u = User.authenticate(self.user1.username, 'pwd')
        self.assertTrue(u)
        self.assertEqual(u.id, 11)

    def test_badusername_auth(self):
        """test authentincation error handling"""
        self.assertFalse(User.authenticate('badbad', 'pwd'))
    
    def test_badpassword_auth(self):
        """test authentincation error handling"""
        self.assertFalse(User.authenticate(self.user1.username, 'badpwd'))


    

