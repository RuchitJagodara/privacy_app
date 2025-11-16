import os
import sys
import face_recognition
import numpy as np
from PIL import Image

# Add parent directory to path to import from Face_Recognition folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class FaceRecognitionService:
    """Service for face recognition and detection"""
    
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_user_ids = {}
        self.encode_faces()
    
    def encode_faces(self):
        """Encode all faces from the Face_Recognition/faces folder"""
        faces_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                 'Face_Recognition', 'faces')
        
        if not os.path.exists(faces_dir):
            print(f"Warning: Faces directory not found at {faces_dir}")
            return
        
        self.known_face_encodings = []
        self.known_face_names = []
        
        for image_file in os.listdir(faces_dir):
            if image_file.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_path = os.path.join(faces_dir, image_file)
                try:
                    face_image = face_recognition.load_image_file(image_path)
                    face_encodings = face_recognition.face_encodings(face_image)
                    
                    if len(face_encodings) > 0:
                        face_encoding = face_encodings[0]
                        username = os.path.splitext(image_file)[0]
                        
                        self.known_face_encodings.append(face_encoding)
                        self.known_face_names.append(username)
                        
                        print(f"Encoded face for: {username}")
                    else:
                        print(f"Warning: No face found in {image_file}")
                        
                except Exception as e:
                    print(f"Error encoding {image_file}: {str(e)}")
        
        print(f"Total faces encoded: {len(self.known_face_encodings)}")
    
    def detect_faces_in_image(self, image_path):
        """
        Detect and identify faces in an image
        
        Returns:
            List of dicts with:
            - box: (x1, y1, x2, y2) bounding box
            - username: identified username or 'Unknown'
            - user_id: user ID if found in database (you'll need to query this)
            - confidence: confidence score
        """
        try:
            # Load image
            image = face_recognition.load_image_file(image_path)
            
            # Find face locations and encodings
            face_locations = face_recognition.face_locations(image)
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            detected_faces = []
            
            for face_encoding, face_location in zip(face_encodings, face_locations):
                # Match against known faces
                matches = face_recognition.compare_faces(
                    self.known_face_encodings, 
                    face_encoding, 
                    tolerance=0.6
                )
                
                username = "Unknown"
                user_id = None
                confidence = 0.0
                
                if len(self.known_face_encodings) > 0:
                    face_distances = face_recognition.face_distance(
                        self.known_face_encodings, 
                        face_encoding
                    )
                    best_match_index = np.argmin(face_distances)
                    
                    if matches[best_match_index]:
                        username = self.known_face_names[best_match_index]
                        confidence = 1 - face_distances[best_match_index]
                        
                        # Import here to avoid circular dependency
                        from models import User
                        user = User.query.filter_by(username=username).first()
                        if user:
                            user_id = user.id
                
                # Convert face location from (top, right, bottom, left) to (x1, y1, x2, y2)
                top, right, bottom, left = face_location
                
                detected_faces.append({
                    'box': (left, top, right, bottom),  # (x1, y1, x2, y2)
                    'username': username,
                    'user_id': user_id,
                    'confidence': float(confidence)
                })
            
            return detected_faces
            
        except Exception as e:
            print(f"Error detecting faces: {str(e)}")
            return []
    
    def detect_faces_in_video_frame(self, frame):
        """
        Detect faces in a video frame (for real-time detection)
        
        Args:
            frame: numpy array (BGR format from OpenCV)
        
        Returns:
            List of detected faces with bounding boxes and names
        """
        # Convert BGR to RGB
        rgb_frame = frame[:, :, ::-1]
        
        # Find faces
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        detected_faces = []
        
        for face_encoding, face_location in zip(face_encodings, face_locations):
            matches = face_recognition.compare_faces(
                self.known_face_encodings,
                face_encoding,
                tolerance=0.6
            )
            
            username = "Unknown"
            confidence = 0.0
            
            if len(self.known_face_encodings) > 0:
                face_distances = face_recognition.face_distance(
                    self.known_face_encodings,
                    face_encoding
                )
                best_match_index = np.argmin(face_distances)
                
                if matches[best_match_index]:
                    username = self.known_face_names[best_match_index]
                    confidence = 1 - face_distances[best_match_index]
            
            top, right, bottom, left = face_location
            
            detected_faces.append({
                'box': (left, top, right, bottom),
                'username': username,
                'confidence': float(confidence)
            })
        
        return detected_faces
    
    def register_new_face(self, image_path, username):
        """
        Register a new face for recognition
        
        Args:
            image_path: Path to the face image
            username: Username to associate with this face
        
        Returns:
            Success boolean
        """
        try:
            faces_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                     'Face_Recognition', 'faces')
            
            # Create faces directory if it doesn't exist
            os.makedirs(faces_dir, exist_ok=True)
            
            # Copy/save the image to faces directory
            target_path = os.path.join(faces_dir, f"{username}.jpg")
            
            # Load and save to ensure proper format
            face_image = face_recognition.load_image_file(image_path)
            face_encodings = face_recognition.face_encodings(face_image)
            
            if len(face_encodings) == 0:
                print("No face found in the image")
                return False
            
            # Save the image
            pil_image = Image.fromarray(face_image)
            pil_image.save(target_path)
            
            # Re-encode all faces
            self.encode_faces()
            
            return True
            
        except Exception as e:
            print(f"Error registering face: {str(e)}")
            return False
