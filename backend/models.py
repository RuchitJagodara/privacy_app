from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(120))
    password_hash = db.Column(db.String(255), nullable=False)
    profile_pic = db.Column(db.String(255))
    bio = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    posts = db.relationship('Post', backref='author', lazy=True, cascade='all, delete-orphan')
    stories = db.relationship('Story', backref='author', lazy=True, cascade='all, delete-orphan')
    face_detections = db.relationship('FaceDetection', backref='detected_user', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'profile_pic': self.profile_pic,
            'bio': self.bio,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Post(db.Model):
    """Post model"""
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    caption = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    face_detections = db.relationship('FaceDetection', backref='post', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.author.username,
            'full_name': self.author.full_name,
            'image_url': f'/api/posts/{self.id}/image',
            'caption': self.caption,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'face_count': len(self.face_detections)
        }


class Story(db.Model):
    """Story model (expires in 24 hours)"""
    __tablename__ = 'stories'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    # Relationships
    face_detections = db.relationship('FaceDetection', backref='story', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.author.username,
            'full_name': self.author.full_name,
            'image_url': f'/api/stories/{self.id}/image',
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_expired': self.expires_at < datetime.utcnow(),
            'face_count': len(self.face_detections)
        }


class FaceDetection(db.Model):
    """Face detection model - stores detected faces in posts/stories"""
    __tablename__ = 'face_detections'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True)
    story_id = db.Column(db.Integer, db.ForeignKey('stories.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Detected user (can be None if unknown)
    face_index = db.Column(db.Integer, nullable=False)  # Index in the encryption metadata
    bounding_box = db.Column(db.String(255))  # Stored as string: "x1,y1,x2,y2"
    confidence = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    approval_request = db.relationship('ApprovalRequest', backref='face_detection', uselist=False, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'post_id': self.post_id,
            'story_id': self.story_id,
            'user_id': self.user_id,
            'username': self.detected_user.username if self.detected_user else 'Unknown',
            'face_index': self.face_index,
            'bounding_box': self.bounding_box,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'approval_status': self.approval_request.status if self.approval_request else None
        }


class ApprovalRequest(db.Model):
    """Approval request model - tracks approval status for detected faces"""
    __tablename__ = 'approval_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    face_detection_id = db.Column(db.Integer, db.ForeignKey('face_detections.id'), nullable=False, unique=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # User who needs to approve
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    responded_at = db.Column(db.DateTime)
    
    # Relationships
    requester = db.relationship('User', foreign_keys=[requester_id])
    
    def to_dict(self):
        detection = self.face_detection
        content_type = 'post' if detection.post_id else 'story'
        content_id = detection.post_id if detection.post_id else detection.story_id
        
        # Get the uploader info
        if detection.post_id:
            uploader = detection.post.author
        else:
            uploader = detection.story.author
        
        return {
            'id': self.id,
            'face_detection_id': self.face_detection_id,
            'requester_id': self.requester_id,
            'status': self.status,
            'content_type': content_type,
            'content_id': content_id,
            'uploader': {
                'id': uploader.id,
                'username': uploader.username,
                'full_name': uploader.full_name
            },
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'responded_at': self.responded_at.isoformat() if self.responded_at else None
        }


class Notification(db.Model):
    """Notification model"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # face_detected, approval_granted, etc.
    message = db.Column(db.Text, nullable=False)
    related_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # User who triggered notification
    related_post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    related_story_id = db.Column(db.Integer, db.ForeignKey('stories.id'))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id])
    related_user = db.relationship('User', foreign_keys=[related_user_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'message': self.message,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'related_user': {
                'id': self.related_user.id,
                'username': self.related_user.username,
                'full_name': self.related_user.full_name
            } if self.related_user else None,
            'related_post_id': self.related_post_id,
            'related_story_id': self.related_story_id
        }
