# PrivacyGram - Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### 1. Install Dependencies

```bash
# Make sure you have Python 3.8+ installed
python --version

# Install required packages
pip install -r requirements.txt
```

**Note**: If `face_recognition` installation fails:
- **macOS**: `brew install cmake && pip install dlib && pip install face_recognition`
- **Ubuntu**: `sudo apt-get install cmake libboost-all-dev && pip install face_recognition`
- **Windows**: Download dlib wheel from [here](https://github.com/sachadee/Dlib)

### 2. Run Setup Script

```bash
python setup.py
```

This will:
- Check all dependencies
- Create necessary folders
- Initialize the database
- Verify face images

### 3. Add Test Face Images

Add at least one face image to recognize:

```bash
# Copy your photo to the faces folder
cp /path/to/your/photo.jpg Face_Recognition/faces/yourusername.jpg
```

**Important**: Name the file with the username you'll use to register!

### 4. Start the Application

#### Option A: Use the start script (Recommended for Unix/Mac)
```bash
chmod +x start.sh
./start.sh
```

#### Option B: Start manually

Terminal 1 - Backend:
```bash
cd backend
python app.py
```

Terminal 2 - Frontend:
```bash
cd frontend
python -m http.server 8000
```

### 5. Open the App

Go to: **http://localhost:8000**

### 6. First Time Setup

1. **Register an account**
   - Username must match your face image filename
   - Example: If your face image is `john.jpg`, register as `john`

2. **Register your face**
   - Click on Profile
   - Click "Register Your Face"
   - Upload the same photo you put in the faces folder

3. **Create your first post**
   - Click "Create Post"
   - Upload an image with faces
   - Watch the magic happen!

## 📸 Testing the App

### Test Scenario 1: Single User
1. Register as User A
2. Register your face
3. Create a post with your photo
4. You should see approval requests
5. Approve them to see your face unblurred

### Test Scenario 2: Multiple Users
1. Add multiple face images to `Face_Recognition/faces/`
   - `alice.jpg`
   - `bob.jpg`
2. Register accounts for Alice and Bob
3. Each should register their face
4. Alice uploads a group photo with both faces
5. Bob receives notification
6. Bob can approve/reject his appearance

## 🎯 Key Features to Test

- ✅ Upload post with faces → All faces blurred
- ✅ Receive notification when detected
- ✅ Approve/reject appearance
- ✅ Approved faces unblurred
- ✅ Create stories (expire in 24h)
- ✅ View feed with selective unblurring

## ⚠️ Troubleshooting

### "No faces detected"
- Ensure face images are in `Face_Recognition/faces/`
- Use clear, front-facing photos
- Check file format (JPG, JPEG, PNG)

### "Connection error"
- Check backend is running on port 5000
- Check frontend is running on port 8000
- Look for errors in terminal

### "Import errors"
- Run `pip install -r requirements.txt` again
- Check Python version (need 3.8+)

### "Database errors"
- Delete `backend/privacy_app.db`
- Restart the backend server

## 📱 Using the App

### Navigation
- **Home** 🏠 - View feed
- **Notifications** 🔔 - See alerts
- **Profile** 👤 - Your posts and settings
- **Logout** 🚪 - Sign out

### Creating Content
- **Post**: Permanent, with caption
- **Story**: Disappears after 24 hours

### Privacy Controls
- **Automatic**: All faces blurred by default
- **Notification**: You're alerted when detected
- **Control**: Approve or reject per post/story

## 🔐 How It Works

1. **Upload** → Image sent to server
2. **Detect** → Face recognition identifies faces
3. **Blur** → All faces encrypted/pixelated
4. **Notify** → Detected users get alerts
5. **Approve** → Users choose to appear
6. **Unblur** → Approved faces decrypted on-the-fly

## 📚 Next Steps

- Read the full README.md for detailed documentation
- Explore the API endpoints
- Customize the encryption algorithm in trial.py
- Add more test users and faces
- Try creating stories

## 💡 Tips

- Use high-quality face photos for better recognition
- Keep face images consistent (same person)
- Test with different lighting conditions
- Try group photos with multiple faces
- Experiment with approval/rejection flows

---

**Need help?** Check the full README.md or open an issue on GitHub.

**Ready to go?** Start creating privacy-first content! 🎉
