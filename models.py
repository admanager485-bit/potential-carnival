from datetime import datetime

from app import db
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint


# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=True)
    first_name = db.Column(db.String, nullable=True)
    last_name = db.Column(db.String, nullable=True)
    profile_image_url = db.Column(db.String, nullable=True)
    
    # Subscription fields
    subscription_status = db.Column(db.String, default='free')  # 'free' or 'paid'
    stripe_customer_id = db.Column(db.String, nullable=True)
    subscription_end_date = db.Column(db.DateTime, nullable=True)
    
    # Usage tracking
    generations_today = db.Column(db.Integer, default=0)
    last_generation_date = db.Column(db.Date, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime,
                           default=datetime.now,
                           onupdate=datetime.now)

# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.String, db.ForeignKey(User.id))
    browser_session_key = db.Column(db.String, nullable=False)
    user = db.relationship(User)

    __table_args__ = (UniqueConstraint(
        'user_id',
        'browser_session_key',
        'provider',
        name='uq_user_browser_session_key_provider',
    ),)

# User content generations
class Generation(db.Model):
    __tablename__ = 'generations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    niche = db.Column(db.String, nullable=False)
    topic = db.Column(db.String, nullable=False)
    tone = db.Column(db.String, nullable=False)
    posts = db.Column(db.Text, nullable=False)  # JSON string of generated posts
    hashtags = db.Column(db.Text, nullable=False)  # JSON string of hashtags
    schedule = db.Column(db.Text, nullable=False)  # JSON string of posting schedule
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationship
    user = db.relationship('User', backref='generations')

# Stripe payment tracking
class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    stripe_payment_intent_id = db.Column(db.String, nullable=False)
    amount = db.Column(db.Integer, nullable=False)  # amount in cents
    status = db.Column(db.String, nullable=False)  # 'succeeded', 'pending', 'failed'
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationship
    user = db.relationship('User', backref='payments')