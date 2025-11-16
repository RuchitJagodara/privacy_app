#!/usr/bin/env python3
"""
Setup script for PrivacyGram application
This script initializes the database and checks dependencies
"""

import os
import sys

def check_dependencies():
    """Check if all required packages are installed"""
    print("Checking dependencies...")
    
    required_packages = [
        'flask',
        'flask_cors',
        'flask_login',
        'flask_sqlalchemy',
        'PIL',
        'face_recognition',
        'cv2',
        'numpy',
        'cryptography',
        'piexif'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'PIL':
                __import__('PIL')
            elif package == 'cv2':
                __import__('cv2')
            else:
                __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print("\n⚠️  Missing packages detected!")
        print("Please install them using:")
        print("pip install -r requirements.txt")
        return False
    
    print("\n✓ All dependencies installed!")
    return True


def create_directories():
    """Create necessary directories"""
    print("\nCreating directories...")
    
    directories = [
        'backend/uploads',
        'backend/uploads/posts',
        'backend/uploads/stories',
        'backend/uploads/profile_pics',
        'Face_Recognition/faces'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Created {directory}")
    
    print("\n✓ All directories created!")


def initialize_database():
    """Initialize the database"""
    print("\nInitializing database...")
    
    # Change to backend directory
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    os.chdir(backend_dir)
    
    try:
        from app import app, db
        
        with app.app_context():
            db.create_all()
            print("✓ Database created successfully!")
            
            # Check if there are any users
            from models import User
            user_count = User.query.count()
            print(f"✓ Current users in database: {user_count}")
            
        return True
    except Exception as e:
        print(f"✗ Error creating database: {e}")
        return False


def check_face_images():
    """Check if there are any registered faces"""
    print("\nChecking for registered faces...")
    
    faces_dir = os.path.join('Face_Recognition', 'faces')
    
    if not os.path.exists(faces_dir):
        print(f"⚠️  Faces directory not found: {faces_dir}")
        return False
    
    face_files = [f for f in os.listdir(faces_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if not face_files:
        print("⚠️  No face images found!")
        print(f"Please add face images to {faces_dir}")
        print("Name each file as: username.jpg")
        return False
    
    print(f"✓ Found {len(face_files)} registered face(s):")
    for face_file in face_files:
        print(f"  - {face_file}")
    
    return True


def print_instructions():
    """Print instructions to run the application"""
    print("\n" + "="*60)
    print("SETUP COMPLETE!")
    print("="*60)
    print("\nTo run the application:")
    print("\n1. Start the backend server:")
    print("   cd backend")
    print("   python app.py")
    print("\n2. In a new terminal, start the frontend server:")
    print("   cd frontend")
    print("   python -m http.server 8000")
    print("\n3. Open your browser and go to:")
    print("   http://localhost:8000")
    print("\n" + "="*60)
    print("\nIMPORTANT:")
    print("- Register an account first")
    print("- Go to Profile and register your face for recognition")
    print("- Add face images to Face_Recognition/faces/ folder")
    print("- Name them as: username.jpg (matching registered usernames)")
    print("="*60 + "\n")


def main():
    """Main setup function"""
    print("="*60)
    print("PrivacyGram Setup Script")
    print("="*60 + "\n")
    
    # Change to project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Initialize database
    if not initialize_database():
        print("\n⚠️  Database initialization failed!")
        print("You can try initializing it manually later.")
    
    # Check face images
    check_face_images()
    
    # Print instructions
    print_instructions()


if __name__ == '__main__':
    main()
