# PrivacyGram - Complete Application Overview

## 🎯 Project Summary

**PrivacyGram** is a privacy-focused social media application similar to Instagram, where user privacy is paramount. When users upload photos, all detected faces are automatically blurred using advanced encryption. Individuals receive notifications when their face is detected and can approve or reject their appearance. Only approved faces are unblurred when viewing the content.

## 📁 Project Structure

```
privacy_app/
│
├── backend/                          # Backend API (Flask)
│   ├── app.py                       # Main Flask application with all routes
│   ├── models.py                    # Database models (SQLAlchemy)
│   ├── services/
│   │   ├── face_service.py         # Face detection and recognition
│   │   ├── blur_service.py         # Image encryption/decryption
│   │   └── notification_service.py # Notification management
│   └── uploads/                     # User-uploaded images (auto-created)
│
├── frontend/                         # Frontend UI
│   ├── index.html                   # Main HTML page
│   └── static/
│       ├── css/
│       │   └── style.css           # Styling (Instagram-like)
│       └── js/
│           └── app.js              # Frontend JavaScript (API calls, UI)
│
├── Face_Recognition/                 # Face recognition module
│   ├── main.py                      # Original face recognition code
│   └── faces/                       # Registered face images
│       ├── user1.jpg               # Face images named by username
│       └── user2.jpg
│
├── trial.py                         # Image encryption/decryption algorithms
├── requirements.txt                 # Python dependencies
├── setup.py                         # Setup and initialization script
├── start.sh                         # Convenience script to start app
├── .env.example                     # Environment configuration template
├── .gitignore                       # Git ignore rules
├── README.md                        # Full documentation
├── QUICKSTART.md                    # Quick start guide
└── PROJECT_OVERVIEW.md              # This file

```

## 🏗️ Architecture

### Backend (Flask)
- **Framework**: Flask with SQLAlchemy ORM
- **Authentication**: Flask-Login with session-based auth
- **Database**: SQLite (can easily switch to PostgreSQL)
- **API Style**: RESTful JSON API with CORS support

### Frontend
- **Technology**: Vanilla JavaScript (no frameworks)
- **Style**: Instagram-inspired UI with clean, modern design
- **Communication**: Fetch API for backend communication

### Face Recognition
- **Library**: face_recognition (based on dlib)
- **Method**: Face encoding comparison with tolerance threshold
- **Storage**: Face images stored in Face_Recognition/faces/

### Image Encryption
- **Algorithm**: AES-GCM (256-bit)
- **Method**: Envelope encryption (KEK/DEK pattern)
- **Storage**: Encrypted patches in EXIF MakerNote
- **Visual**: 32x32 pixelation for blurred areas

## 🔄 Complete Workflow

### 1. User Registration
```
User fills registration form
  ↓
Backend creates user account
  ↓
User registers face image
  ↓
Face encoded and stored
```

### 2. Post/Story Creation
```
User uploads image with faces
  ↓
Backend detects all faces
  ↓
Faces compared to registered users
  ↓
All faces encrypted/blurred
  ↓
Approval requests created
  ↓
Notifications sent to detected users
  ↓
Encrypted image saved
```

### 3. Approval Process
```
User receives notification
  ↓
User views post preview
  ↓
User approves or rejects
  ↓
Approval status saved in database
```

### 4. Viewing Content
```
User requests post/story
  ↓
Backend checks approvals
  ↓
Approved faces decrypted on-the-fly
  ↓
Mixed image (blurred + clear) returned
  ↓
Frontend displays image
```

## 💾 Database Schema

### Tables

**users**
- Primary user accounts
- Stores credentials, profile info

**posts**
- User posts with images
- Links to user, stores image path

**stories**
- Temporary posts (24h expiry)
- Similar to posts but with expiry

**face_detections**
- Records of detected faces
- Links to posts/stories and users
- Stores face index for decryption

**approval_requests**
- Tracks approval status
- Links detection to requester
- Status: pending/approved/rejected

**notifications**
- User notifications
- Face detection alerts
- Approval responses

### Relationships
```
User → Posts (1:many)
User → Stories (1:many)
User → Face Detections (1:many)
Post → Face Detections (1:many)
Story → Face Detections (1:many)
Face Detection → Approval Request (1:1)
```

## 🔐 Security & Privacy

### Encryption Details
1. **Master KEK**: App-wide key encryption key
2. **Per-Image DEK**: Unique data encryption key per image
3. **Face Patches**: Original face regions encrypted
4. **Metadata**: Stored in EXIF MakerNote
5. **Pixelation**: 32x32 blocks for visual privacy

### Authentication
- Password hashing with Werkzeug
- Session-based with secure cookies
- Login required for all protected routes

### Privacy Features
- Default blur for all faces
- Opt-in display (approval required)
- Selective decryption
- Notification system
- User control over appearance

## 🚀 API Endpoints

### Authentication
```
POST   /api/register          # Register new user
POST   /api/login             # Login
POST   /api/logout            # Logout
GET    /api/me                # Get current user
```

### Posts
```
POST   /api/posts             # Create post (upload + detect + blur)
GET    /api/posts             # Get feed
GET    /api/posts/<id>        # Get specific post
GET    /api/posts/<id>/image  # Get image (dynamic unblurring)
DELETE /api/posts/<id>        # Delete post
```

### Stories
```
POST   /api/stories           # Create story
GET    /api/stories           # Get active stories
GET    /api/stories/<id>/image # Get story image
```

### Approvals
```
GET    /api/approvals/pending         # Get pending approvals
POST   /api/approvals/<id>/approve    # Approve
POST   /api/approvals/<id>/reject     # Reject
```

### Users
```
GET    /api/users/<id>              # Get profile
GET    /api/users/<id>/posts        # Get user posts
POST   /api/users/register-face     # Register face
```

### Notifications
```
GET    /api/notifications    # Get all notifications
```

## 🎨 Frontend Features

### Pages
1. **Auth Page**: Login/Register
2. **Feed**: Posts from all users
3. **Stories**: 24-hour temporary content
4. **Notifications**: Alerts and updates
5. **Profile**: User posts and settings

### Key UI Components
- **Post Card**: Image, caption, user info
- **Story Viewer**: Swipeable stories
- **Upload Modal**: Image selection and preview
- **Approval Modal**: Review and approve/reject
- **Notification Badge**: Unread count

### Interactive Features
- Real-time notification polling
- Image preview before upload
- Face approval workflow
- Dynamic image loading
- Responsive design

## 📦 Dependencies

### Core Libraries
- **Flask**: Web framework
- **SQLAlchemy**: ORM
- **face_recognition**: Face detection
- **Pillow**: Image processing
- **cryptography**: Encryption
- **opencv-python**: Computer vision
- **piexif**: EXIF manipulation

### Frontend
- Vanilla JavaScript
- Fetch API
- CSS3 with Flexbox/Grid

## 🔧 Configuration

### Environment Variables (.env)
- `SECRET_KEY`: Flask secret key
- `DATABASE_URL`: Database connection
- `UPLOAD_FOLDER`: Upload directory
- `FACE_RECOGNITION_TOLERANCE`: Match threshold

### Customization Points
1. **Encryption strength**: Change key sizes in trial.py
2. **Face tolerance**: Adjust recognition sensitivity
3. **Story expiry**: Modify 24-hour default
4. **Pixelation level**: Change block size
5. **Image quality**: Adjust JPEG quality

## 🧪 Testing Scenarios

### Basic Flow
1. Register 2 users (Alice, Bob)
2. Both register faces
3. Alice uploads group photo
4. Bob gets notification
5. Bob approves
6. Photo shows Bob's face clearly

### Edge Cases
- Unknown faces (no match)
- Multiple faces per person
- Partially visible faces
- Different lighting/angles
- Expired stories
- Rejected approvals

## 📈 Performance Considerations

### Optimization
- Face encoding cached in memory
- Lazy image loading
- Pagination for feed
- Efficient EXIF storage
- Compressed JPEG quality

### Scalability
- Can switch to PostgreSQL
- Add Redis for caching
- Use Celery for background tasks
- CDN for image delivery
- WebSockets for real-time notifications

## 🚀 Deployment Considerations

### Production Checklist
- [ ] Change SECRET_KEY
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable HTTPS
- [ ] Set up proper CORS origins
- [ ] Use Gunicorn/uWSGI for Flask
- [ ] Serve frontend via Nginx
- [ ] Add rate limiting
- [ ] Enable logging
- [ ] Set up monitoring
- [ ] Regular database backups

### Environment Setup
```bash
# Production environment
export FLASK_ENV=production
export DATABASE_URL=postgresql://...
export SECRET_KEY=<strong-random-key>
```

## 🛠️ Development Workflow

### Running Development
```bash
# Terminal 1: Backend
cd backend
python app.py

# Terminal 2: Frontend
cd frontend
python -m http.server 8000
```

### Adding Features
1. Update database models (models.py)
2. Add API endpoints (app.py)
3. Create service methods (services/)
4. Update frontend (app.js, style.css)
5. Test workflow end-to-end

## 📚 Learning Resources

### Technologies Used
- Flask: https://flask.palletsprojects.com/
- face_recognition: https://github.com/ageitgey/face_recognition
- SQLAlchemy: https://www.sqlalchemy.org/
- AES-GCM: https://cryptography.io/

## 🐛 Common Issues & Solutions

### Face Recognition Not Working
- Check dlib installation
- Verify face images in faces/
- Ensure good quality photos
- Check tolerance setting

### Images Not Displaying
- Check uploads folder exists
- Verify file permissions
- Check CORS settings
- Ensure correct image paths

### Database Errors
- Delete DB and recreate
- Check SQLAlchemy version
- Verify model relationships

## 🎯 Future Enhancements

### Planned Features
- [ ] WebSocket real-time notifications
- [ ] Video support with frame processing
- [ ] Mobile app (React Native)
- [ ] Advanced privacy settings
- [ ] Group chats
- [ ] Direct messaging
- [ ] Photo filters
- [ ] Location tagging
- [ ] Hashtags and search
- [ ] User blocking

### Technical Improvements
- [ ] Redis caching
- [ ] Celery background tasks
- [ ] GraphQL API
- [ ] TypeScript frontend
- [ ] Docker containerization
- [ ] Kubernetes deployment
- [ ] CI/CD pipeline
- [ ] Automated testing

## 📞 Support

For issues or questions:
1. Check README.md
2. Check QUICKSTART.md
3. Review this overview
4. Open GitHub issue

## 🎉 Success Criteria

The application successfully:
✅ Detects faces in uploaded images
✅ Automatically blurs all faces
✅ Identifies registered users
✅ Sends notifications to detected users
✅ Allows approval/rejection
✅ Selectively unblurs approved faces
✅ Maintains privacy by default
✅ Provides Instagram-like experience

---

**Built with privacy at its core. Your face, your choice.** 🔒
