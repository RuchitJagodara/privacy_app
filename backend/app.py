from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import sys

# Add parent directory to path to import trial.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import db, User, Post, Story, FaceDetection, ApprovalRequest
from services.face_service import FaceRecognitionService
from services.blur_service import BlurService
from services.notification_service import NotificationService
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///privacy_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'posts'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'stories'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'profile_pics'), exist_ok=True)

db.init_app(app)
CORS(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize services
face_service = FaceRecognitionService()
blur_service = BlurService()
notification_service = NotificationService()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ==================== AUTH ROUTES ====================

@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    user = User(
        username=data['username'],
        email=data['email'],
        full_name=data.get('full_name', ''),
        password_hash=generate_password_hash(data['password'])
    )
    
    db.session.add(user)
    db.session.commit()
    
    login_user(user)
    
    return jsonify({
        'message': 'User registered successfully',
        'user': user.to_dict()
    }), 201


@app.route('/api/login', methods=['POST'])
def login():
    """Login user"""
    data = request.get_json()
    
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    login_user(user, remember=data.get('remember', False))
    
    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict()
    }), 200


@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    """Logout user"""
    logout_user()
    return jsonify({'message': 'Logout successful'}), 200


@app.route('/api/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current logged in user"""
    return jsonify(current_user.to_dict()), 200


# ==================== POST ROUTES ====================

@app.route('/api/posts', methods=['POST'])
@login_required
def create_post():
    """Create a new post with face detection and blurring"""
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    caption = request.form.get('caption', '')
    
    if file.filename == '':
        return jsonify({'error': 'No image selected'}), 400
    
    # Save original image temporarily
    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_' + file.filename)
    file.save(temp_path)
    
    try:
        # Step 1: Detect faces and get their regions
        detected_faces = face_service.detect_faces_in_image(temp_path)
        
        # Step 2: Blur all faces in the image
        blur_regions = [face['box'] for face in detected_faces]
        encrypted_image_data = blur_service.blur_image(temp_path, blur_regions)
        
        # Step 3: Save the blurred image
        post_filename = f"post_{current_user.id}_{datetime.utcnow().timestamp()}.jpg"
        post_path = os.path.join(app.config['UPLOAD_FOLDER'], 'posts', post_filename)
        
        with open(post_path, 'wb') as f:
            f.write(encrypted_image_data)
        
        # Step 4: Create post record
        post = Post(
            user_id=current_user.id,
            image_path=post_path,
            caption=caption
        )
        db.session.add(post)
        db.session.flush()  # Get post.id
        
        # Step 5: Create face detection records and approval requests
        for idx, face_data in enumerate(detected_faces):
            detected_user_id = face_data.get('user_id')
            
            face_detection = FaceDetection(
                post_id=post.id,
                user_id=detected_user_id,
                face_index=idx,
                bounding_box=str(face_data['box']),
                confidence=face_data.get('confidence', 0)
            )
            db.session.add(face_detection)
            db.session.flush()
            
            # Create approval request if user is identified
            if detected_user_id:
                approval = ApprovalRequest(
                    face_detection_id=face_detection.id,
                    requester_id=detected_user_id,
                    status='pending'
                )
                db.session.add(approval)
                
                # Send notification
                notification_service.send_face_detection_notification(
                    detected_user_id,
                    current_user.id,
                    post.id,
                    is_story=False
                )
        
        db.session.commit()
        
        # Clean up temp file
        os.remove(temp_path)
        
        return jsonify({
            'message': 'Post created successfully',
            'post': post.to_dict(),
            'faces_detected': len(detected_faces)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({'error': str(e)}), 500


@app.route('/api/posts', methods=['GET'])
@login_required
def get_posts():
    """Get all posts (feed)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    posts = Post.query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'posts': [post.to_dict() for post in posts.items],
        'total': posts.total,
        'pages': posts.pages,
        'current_page': page
    }), 200


@app.route('/api/posts/<int:post_id>', methods=['GET'])
@login_required
def get_post(post_id):
    """Get a specific post"""
    post = Post.query.get_or_404(post_id)
    return jsonify(post.to_dict()), 200


@app.route('/api/posts/<int:post_id>/image', methods=['GET'])
@login_required
def get_post_image(post_id):
    """Get post image with selective unblurring based on approvals"""
    post = Post.query.get_or_404(post_id)
    
    # Get approved face indices for current viewing context
    approved_indices = []
    
    # Get all face detections for this post
    face_detections = FaceDetection.query.filter_by(post_id=post_id).all()
    
    for detection in face_detections:
        # Check if there's an approved request
        approval = ApprovalRequest.query.filter_by(
            face_detection_id=detection.id,
            status='approved'
        ).first()
        
        if approval:
            approved_indices.append(detection.face_index)
    
    # Read the encrypted image
    with open(post.image_path, 'rb') as f:
        encrypted_data = f.read()
    
    # Decrypt approved faces
    if approved_indices:
        decrypted_image = blur_service.unblur_faces(encrypted_data, approved_indices)
        img_io = io.BytesIO()
        decrypted_image.save(img_io, 'JPEG', quality=95)
        img_io.seek(0)
        return send_file(img_io, mimetype='image/jpeg')
    else:
        # Return fully blurred image
        return send_file(post.image_path, mimetype='image/jpeg')


@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
@login_required
def delete_post(post_id):
    """Delete a post"""
    post = Post.query.get_or_404(post_id)
    
    if post.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Delete image file
    if os.path.exists(post.image_path):
        os.remove(post.image_path)
    
    db.session.delete(post)
    db.session.commit()
    
    return jsonify({'message': 'Post deleted successfully'}), 200


# ==================== STORY ROUTES ====================

@app.route('/api/stories', methods=['POST'])
@login_required
def create_story():
    """Create a new story with face detection and blurring"""
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'error': 'No image selected'}), 400
    
    # Save original image temporarily
    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_' + file.filename)
    file.save(temp_path)
    
    try:
        # Step 1: Detect faces
        detected_faces = face_service.detect_faces_in_image(temp_path)
        
        # Step 2: Blur all faces
        blur_regions = [face['box'] for face in detected_faces]
        encrypted_image_data = blur_service.blur_image(temp_path, blur_regions)
        
        # Step 3: Save the blurred image
        story_filename = f"story_{current_user.id}_{datetime.utcnow().timestamp()}.jpg"
        story_path = os.path.join(app.config['UPLOAD_FOLDER'], 'stories', story_filename)
        
        with open(story_path, 'wb') as f:
            f.write(encrypted_image_data)
        
        # Step 4: Create story record (expires in 24 hours)
        story = Story(
            user_id=current_user.id,
            image_path=story_path,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db.session.add(story)
        db.session.flush()
        
        # Step 5: Create face detection records
        for idx, face_data in enumerate(detected_faces):
            detected_user_id = face_data.get('user_id')
            
            face_detection = FaceDetection(
                story_id=story.id,
                user_id=detected_user_id,
                face_index=idx,
                bounding_box=str(face_data['box']),
                confidence=face_data.get('confidence', 0)
            )
            db.session.add(face_detection)
            db.session.flush()
            
            # Create approval request
            if detected_user_id:
                approval = ApprovalRequest(
                    face_detection_id=face_detection.id,
                    requester_id=detected_user_id,
                    status='pending'
                )
                db.session.add(approval)
                
                # Send notification
                notification_service.send_face_detection_notification(
                    detected_user_id,
                    current_user.id,
                    story.id,
                    is_story=True
                )
        
        db.session.commit()
        os.remove(temp_path)
        
        return jsonify({
            'message': 'Story created successfully',
            'story': story.to_dict(),
            'faces_detected': len(detected_faces)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({'error': str(e)}), 500


@app.route('/api/stories', methods=['GET'])
@login_required
def get_stories():
    """Get all active stories (not expired)"""
    stories = Story.query.filter(
        Story.expires_at > datetime.utcnow()
    ).order_by(Story.created_at.desc()).all()
    
    return jsonify({
        'stories': [story.to_dict() for story in stories]
    }), 200


@app.route('/api/stories/<int:story_id>/image', methods=['GET'])
@login_required
def get_story_image(story_id):
    """Get story image with selective unblurring"""
    story = Story.query.get_or_404(story_id)
    
    # Check if expired
    if story.expires_at < datetime.utcnow():
        return jsonify({'error': 'Story expired'}), 404
    
    # Get approved face indices
    approved_indices = []
    face_detections = FaceDetection.query.filter_by(story_id=story_id).all()
    
    for detection in face_detections:
        approval = ApprovalRequest.query.filter_by(
            face_detection_id=detection.id,
            status='approved'
        ).first()
        
        if approval:
            approved_indices.append(detection.face_index)
    
    # Read and process image
    with open(story.image_path, 'rb') as f:
        encrypted_data = f.read()
    
    if approved_indices:
        decrypted_image = blur_service.unblur_faces(encrypted_data, approved_indices)
        img_io = io.BytesIO()
        decrypted_image.save(img_io, 'JPEG', quality=95)
        img_io.seek(0)
        return send_file(img_io, mimetype='image/jpeg')
    else:
        return send_file(story.image_path, mimetype='image/jpeg')


# ==================== APPROVAL ROUTES ====================

@app.route('/api/approvals/pending', methods=['GET'])
@login_required
def get_pending_approvals():
    """Get all pending approval requests for current user"""
    face_detections = FaceDetection.query.filter_by(user_id=current_user.id).all()
    
    pending_approvals = []
    for detection in face_detections:
        approval = ApprovalRequest.query.filter_by(
            face_detection_id=detection.id,
            status='pending'
        ).first()
        
        if approval:
            pending_approvals.append(approval.to_dict())
    
    return jsonify({
        'approvals': pending_approvals
    }), 200


@app.route('/api/approvals/<int:approval_id>/approve', methods=['POST'])
@login_required
def approve_request(approval_id):
    """Approve a face detection request"""
    approval = ApprovalRequest.query.get_or_404(approval_id)
    
    # Verify this is the correct user
    if approval.requester_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    approval.status = 'approved'
    approval.responded_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'message': 'Approval granted',
        'approval': approval.to_dict()
    }), 200


@app.route('/api/approvals/<int:approval_id>/reject', methods=['POST'])
@login_required
def reject_request(approval_id):
    """Reject a face detection request"""
    approval = ApprovalRequest.query.get_or_404(approval_id)
    
    if approval.requester_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    approval.status = 'rejected'
    approval.responded_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'message': 'Approval rejected',
        'approval': approval.to_dict()
    }), 200


# ==================== NOTIFICATION ROUTES ====================

@app.route('/api/notifications', methods=['GET'])
@login_required
def get_notifications():
    """Get all notifications for current user"""
    notifications = notification_service.get_user_notifications(current_user.id)
    return jsonify({'notifications': notifications}), 200


# ==================== USER PROFILE ROUTES ====================

@app.route('/api/users/<int:user_id>', methods=['GET'])
@login_required
def get_user_profile(user_id):
    """Get user profile"""
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict()), 200


@app.route('/api/users/<int:user_id>/posts', methods=['GET'])
@login_required
def get_user_posts(user_id):
    """Get all posts by a specific user"""
    posts = Post.query.filter_by(user_id=user_id).order_by(Post.created_at.desc()).all()
    return jsonify({
        'posts': [post.to_dict() for post in posts]
    }), 200


# ==================== FACE REGISTRATION ====================

@app.route('/api/users/register-face', methods=['POST'])
@login_required
def register_face():
    """Register user's face for recognition"""
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'error': 'No image selected'}), 400
    
    # Save face image for recognition
    face_filename = f"{current_user.username}.jpg"
    face_path = os.path.join('Face_Recognition', 'faces', face_filename)
    
    file.save(face_path)
    
    # Re-encode faces
    face_service.encode_faces()
    
    return jsonify({'message': 'Face registered successfully'}), 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
