import os
from unittest import TestCase
from models import db, User, Message, Likes, Follows

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False

class UserViewsTestCase(TestCase):
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

        m = Message(id=1, text='message-test', user_id=self.user1.id)
        db.session.add(m)
        db.session.commit()

        l = Likes(user_id=self.user2.id, message_id=1)
        db.session.add(l)
        db.session.commit()

        f = Follows(user_being_followed_id=self.user1.id, user_following_id=self.user2.id)
        db.session.add(f)
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_user_index(self):
        """Test user index route"""
        with self.client as c:
            res = c.get('/users')

            self.assertIn('@user1', str(res.data))
            self.assertIn('@user2', str(res.data))
    
    def test_search(self):
        """See if search works"""
        with self.client as c:
            res = c.get('/users?q=user1')

            self.assertIn('@user1', str(res.data))
            self.assertNotIn('@user2', str(res.data))
    
    def test_user_details(self):
        """Does user details route work"""
        with self.client as c:
            res = c.get(f'/users/{self.user1.id}')

            self.assertEqual(res.status_code, 200)
            self.assertIn('@user1', str(res.data))
    
    def test_details_with_likes(self):
        """Are likes displayed correctly"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user2.id
            res = c.get(f'/users/{self.user2.id}/likes')            
            
            self.assertEqual(res.status_code, 200)
            self.assertIn('@user2', str(res.data))
            self.assertIn('message-test', str(res.data))
    
    def test_add_like(self):
        """Does like adding functionality work"""
        m = Message(id=2, text='message-test2', user_id=self.user2.id)
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id
            res = c.post(f'/users/handle_like/2', follow_redirects=True)            
            
            self.assertEqual(res.status_code, 200)

            l = Likes.query.filter(Likes.message_id==2).all()

            self.assertEqual(len(l), 1)
            self.assertEqual(l[0].user_id, self.user1.id)
    
    def test_remove_like(self):
        """Can a user remove likes"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user2.id
            res = c.post(f'/users/handle_like/1', follow_redirects=True)            
            
            self.assertEqual(res.status_code, 200)

            l = Likes.query.filter(Likes.message_id==1).all()

            self.assertEqual(len(l), 0)
    
    def test_unauthenticated_like(self):
        """Can unauthenticated users add likes"""
        m = Message(id=2, text='message-test2', user_id=self.user2.id)
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            res = c.post(f'/users/handle_like/2', follow_redirects=True)            
            
            self.assertEqual(res.status_code, 200)
            self.assertIn('Access unauthorized', str(res.data))

            l = Likes.query.all()

            self.assertEqual(len(l), 1)
    
    def test_add_follow(self):
        """Can a user follow other users"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id
            res = c.post('/users/follow/22', follow_redirects=True)

            self.assertEqual(res.status_code, 200)
            self.assertIn('@user2', str(res.data))

            f = Follows.query.filter(Follows.user_following_id==self.user1.id).all()

            self.assertEqual(len(f), 1)
            self.assertEqual(f[0].user_being_followed_id, 22)
    
    def test_remove_follow(self):
        """Can a user unfollow other users"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user2.id
            res = c.post('/users/stop-following/11', follow_redirects=True)

            self.assertEqual(res.status_code, 200)
            self.assertNotIn('@user1', str(res.data))

            f = Follows.query.filter(Follows.user_following_id==self.user2.id).all()

            self.assertEqual(len(f), 0)
    
    def test_show_followers(self):
        """Test followers show route"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id
            res = c.get(f'/users/{self.user1.id}/followers')            
            
            self.assertEqual(res.status_code, 200)
            self.assertIn('@user2', str(res.data))
            
            f = Follows.query.filter(Follows.user_being_followed_id==self.user1.id).all()

            self.assertEqual(len(f), 1)
            self.assertEqual(f[0].user_being_followed_id, 11)
            
    
    def test_show_following(self):
        """Test following show route"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user2.id
            res = c.get(f'/users/{self.user2.id}/following')   
            
            self.assertEqual(res.status_code, 200)
            self.assertIn('@user1', str(res.data))

            f = Follows.query.filter(Follows.user_following_id==self.user2.id).all()

            self.assertEqual(len(f), 1)
            self.assertEqual(f[0].user_following_id, 22)
    
    def test_unauthorized_followers(self):
        """Can unauthorized users see followers"""
        with self.client as c:
            res = c.get(f'/users/{self.user1.id}/followers', follow_redirects=True)

            self.assertEqual(res.status_code, 200)
            self.assertIn('Access unauthorized', str(res.data))
        
    def test_unauthorized_following(self):
        """Can unathorized users see followings"""
        with self.client as c:
            res = c.get(f'/users/{self.user1.id}/following', follow_redirects=True)

            self.assertEqual(res.status_code, 200)
            self.assertIn('Access unauthorized', str(res.data))
        

            
    
