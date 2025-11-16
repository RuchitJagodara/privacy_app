# PrivacyGram - Privacy-Focused Social Media Application

## Overview

PrivacyGram is a privacy-first social media application similar to Instagram, where all faces in uploaded images are automatically blurred until the individuals approve their appearance. This ensures that people maintain control over their online presence.

## Features

### Core Features
- **Automatic Face Detection**: Uses face recognition to detect all faces in uploaded photos
- **Privacy-First Blurring**: All detected faces are automatically blurred using advanced encryption
- **Approval System**: Individuals receive notifications when their face is detected and can approve/reject
- **Selective Unblurring**: Only approved faces are shown; others remain blurred
- **Instagram-Like Interface**: Clean, modern UI with posts, stories, and feed
- **24-Hour Stories**: Stories expire after 24 hours, just like Instagram
- **Face Registration**: Users can register their face for automatic recognition

### Technical Features
- **Advanced Encryption**: Uses AES-GCM encryption with envelope encryption (KEK/DEK)
- **Pixelation Algorithm**: 32x32 pixel blocks for aesthetic privacy protection
- **Efficient Storage**: Encrypted metadata stored in EXIF, minimal size overhead
- **Real-Time Processing**: Fast face detection and encryption on upload

## Architecture

```
privacy_app/
├── backend/
│   ├── app.py                 # Main Flask application
│   ├── models.py              # Database models
│   └── services/
│       ├── face_service.py    # Face recognition service
│       ├── blur_service.py    # Image encryption/decryption
│       └── notification_service.py  # Notification management
├── frontend/
│   ├── index.html             # Main HTML
│   └── static/
│       ├── css/
│       │   └── style.css      # Styles
│       └── js/
│           └── app.js         # Frontend JavaScript
├── Face_Recognition/
│   ├── main.py                # Original face recognition code
│   └── faces/                 # Registered face images
├── trial.py                   # Image encryption/decryption algorithms
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Webcam (optional, for face registration)

### Step 1: Clone the Repository
```bash
cd /Users/pranjalgaur/Desktop/Project_Course/privacy_app
```

### Step 2: Install Dependencies

#### For macOS/Linux:
```bash
# Install system dependencies for face_recognition (dlib)
brew install cmake
brew install boost
brew install boost-python3

# Install Python dependencies
pip install -r requirements.txt
```

#### For Windows:
```bash
# Install Visual Studio Build Tools first
# Then install Python dependencies
pip install -r requirements.txt
```

**Note**: `dlib` can be tricky to install. If you face issues:
- On macOS: Use `brew install dlib`
- On Windows: Download precompiled wheel from [here](https://github.com/sachadee/Dlib)
- On Ubuntu: `sudo apt-get install cmake libboost-all-dev`

### Step 3: Set Up the Database

The database will be created automatically on first run, but you can initialize it manually:

```bash
cd backend
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database created!')"
```

### Step 4: Register Test Faces

Add test face images to the `Face_Recognition/faces/` folder:
- Name each image file with the username (e.g., `john.jpg`, `alice.jpg`)
- Use clear, front-facing photos
- The system will automatically encode these faces for recognition

## Running the Application

### Step 1: Start the Backend Server

```bash
cd backend
python app.py
```

The backend API will run on `http://localhost:5000`

### Step 2: Start the Frontend Server

Open a new terminal:

```bash
cd frontend
python -m http.server 8000
```

The frontend will run on `http://localhost:8000`

### Step 3: Access the Application

Open your browser and go to: `http://localhost:8000`

## Usage Guide

### 1. Register an Account
- Click "Register" on the login page
- Enter username, email, and password
- Click "Register"

### 2. Register Your Face (Important!)
- After logging in, go to your Profile
- Click "Register Your Face"
- Upload a clear photo of your face
- This allows the system to recognize you in photos

### 3. Create a Post
- Click "Create Post" button
- Select an image with faces
- Add a caption
- Click "Post"
- The system will:
  - Detect all faces
  - Blur them automatically
  - Send notifications to recognized individuals

### 4. Handle Approval Requests
- When your face is detected, you'll receive a notification
- Click on the notification
- Review the post/story
- Click "Approve" to allow your face to be shown
- Click "Reject" to keep your face blurred

### 5. View Posts
- Approved faces will be shown clearly
- Non-approved faces remain blurred
- You'll see a notice indicating how many faces need approval

### 6. Create Stories
- Click "Your Story" in the stories section
- Upload an image
- Stories expire after 24 hours

## API Endpoints

### Authentication
- `POST /api/register` - Register new user
- `POST /api/login` - Login
- `POST /api/logout` - Logout
- `GET /api/me` - Get current user

### Posts
- `POST /api/posts` - Create post (with face detection)
- `GET /api/posts` - Get all posts (feed)
- `GET /api/posts/<id>` - Get specific post
- `GET /api/posts/<id>/image` - Get post image (with selective unblurring)
- `DELETE /api/posts/<id>` - Delete post

### Stories
- `POST /api/stories` - Create story
- `GET /api/stories` - Get active stories
- `GET /api/stories/<id>/image` - Get story image

### Approvals
- `GET /api/approvals/pending` - Get pending approval requests
- `POST /api/approvals/<id>/approve` - Approve request
- `POST /api/approvals/<id>/reject` - Reject request

### Notifications
- `GET /api/notifications` - Get all notifications

### User
- `GET /api/users/<id>` - Get user profile
- `GET /api/users/<id>/posts` - Get user's posts
- `POST /api/users/register-face` - Register face for recognition

## Database Schema

### Users
- `id`, `username`, `email`, `full_name`, `password_hash`, `profile_pic`, `bio`, `created_at`

### Posts
- `id`, `user_id`, `image_path`, `caption`, `created_at`

### Stories
- `id`, `user_id`, `image_path`, `created_at`, `expires_at`

### Face Detections
- `id`, `post_id`, `story_id`, `user_id`, `face_index`, `bounding_box`, `confidence`, `created_at`

### Approval Requests
- `id`, `face_detection_id`, `requester_id`, `status`, `created_at`, `responded_at`

### Notifications
- `id`, `user_id`, `type`, `message`, `related_user_id`, `related_post_id`, `related_story_id`, `is_read`, `created_at`

## How It Works

### Face Detection Flow
1. User uploads an image
2. Backend detects all faces using face_recognition library
3. Each face is compared against registered faces
4. Identified users are linked to their accounts

### Blurring Flow
1. All detected face regions are passed to the blur service
2. Faces are encrypted using AES-GCM with envelope encryption
3. Original face patches stored as encrypted metadata in EXIF
4. Pixelated versions displayed in the image
5. Encrypted image saved to disk

### Approval Flow
1. For each detected face, an approval request is created
2. Notification sent to the detected user
3. User reviews the post/story
4. User approves or rejects

### Unblurring Flow
1. When viewing a post, backend checks approval status
2. For approved faces, decrypt their patches from EXIF metadata
3. Stitch decrypted patches onto the pixelated image
4. Return dynamically generated image to frontend

## Security Considerations

### Encryption
- Master KEK (Key Encryption Key) stored securely
- DEK (Data Encryption Key) generated per image
- AES-GCM with 256-bit keys
- Nonces prevent replay attacks

### Privacy
- Faces blurred by default
- Opt-in display (approval required)
- Users control their appearance
- Metadata stored efficiently

### Authentication
- Password hashing with Werkzeug
- Session-based authentication with Flask-Login
- CORS protection enabled

## Troubleshooting

### Common Issues

**Issue**: `face_recognition` won't install
- **Solution**: Install dlib first, then face_recognition. See installation section.

**Issue**: No faces detected
- **Solution**: Make sure faces are registered in `Face_Recognition/faces/` folder

**Issue**: CORS errors
- **Solution**: Check that flask-cors is installed and enabled in app.py

**Issue**: Database errors
- **Solution**: Delete `backend/privacy_app.db` and restart the app to recreate

**Issue**: Images not displaying
- **Solution**: Check that the uploads folder exists and has write permissions

## Future Enhancements

- [ ] Real-time notifications using WebSockets
- [ ] Mobile app (React Native)
- [ ] Video support with frame-by-frame processing
- [ ] Group photo tagging
- [ ] Privacy settings per post
- [ ] Temporary access links
- [ ] Advanced face matching with confidence thresholds
- [ ] Bulk approval/rejection
- [ ] Export controls for data portability

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - See LICENSE file for details

## Credits

- Face recognition powered by [face_recognition](https://github.com/ageitgey/face_recognition)
- Encryption using Python's cryptography library
- Frontend inspired by Instagram's design
- Built with Flask, SQLAlchemy, and modern web technologies

## Contact

For questions or issues, please open an issue on GitHub.

---

**Built with privacy in mind. Your face, your choice.** 🔒

Here's a research paper on how you can unblur gaussian blur, to retrieve the face data
https://arxiv.org/html/2506.12344v1


Algorithmic blurring which results into a very efficient method, but doesn't provide a good ux design.
https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=b0be7bf447b6774c9ca0f6168c48582812e4d9c3
