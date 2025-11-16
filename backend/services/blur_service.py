import os
import io
import sys
from PIL import Image

# Add parent directory to path to import encryption functions
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the encryption/decryption functions from trial.py
from trial import encrypt_image, decrypt_image, permanently_reveal_patches


class BlurService:
    """Service for blurring and unblurring faces using the encryption algorithm"""
    
    def blur_image(self, image_path, face_regions):
        """
        Blur (encrypt) faces in an image
        
        Args:
            image_path: Path to the original image
            face_regions: List of tuples (x1, y1, x2, y2) for face bounding boxes
        
        Returns:
            Encrypted image data as bytes
        """
        try:
            if not face_regions:
                # If no faces, just return the original image as JPEG bytes
                with open(image_path, 'rb') as f:
                    return f.read()
            
            # Use the encrypt_image function from trial.py
            encrypted_data = encrypt_image(image_path, face_regions)
            return encrypted_data
            
        except Exception as e:
            print(f"Error blurring image: {str(e)}")
            raise
    
    def unblur_faces(self, encrypted_image_data, face_indices):
        """
        Unblur (decrypt) specific faces from an encrypted image
        
        Args:
            encrypted_image_data: Encrypted image as bytes
            face_indices: List of face indices to decrypt
        
        Returns:
            PIL Image with selected faces unblurred
        """
        try:
            if not face_indices:
                # If no faces to decrypt, return the blurred image
                return Image.open(io.BytesIO(encrypted_image_data))
            
            # Use the decrypt_image function from trial.py
            decrypted_image = decrypt_image(encrypted_image_data, face_indices)
            return decrypted_image
            
        except Exception as e:
            print(f"Error unblurring faces: {str(e)}")
            raise
    
    def permanently_unblur_faces(self, encrypted_image_data, face_indices):
        """
        Permanently unblur (reveal) specific faces and remove their encryption metadata
        
        Args:
            encrypted_image_data: Encrypted image as bytes
            face_indices: List of face indices to permanently reveal
        
        Returns:
            New encrypted image data with revealed faces burned in
        """
        try:
            if not face_indices:
                return encrypted_image_data
            
            # Use the permanently_reveal_patches function from trial.py
            revealed_data = permanently_reveal_patches(encrypted_image_data, face_indices)
            return revealed_data
            
        except Exception as e:
            print(f"Error permanently unblurring faces: {str(e)}")
            raise
    
    def get_face_count(self, encrypted_image_data):
        """
        Get the number of encrypted faces in an image
        
        Args:
            encrypted_image_data: Encrypted image as bytes
        
        Returns:
            Number of encrypted faces
        """
        try:
            import piexif
            import struct
            
            encrypted_image = Image.open(io.BytesIO(encrypted_image_data))
            
            if "exif" not in encrypted_image.info:
                return 0
            
            exif_data = piexif.load(encrypted_image.info["exif"])
            
            if piexif.ExifIFD.MakerNote not in exif_data["Exif"]:
                return 0
            
            payload_bytes = exif_data["Exif"][piexif.ExifIFD.MakerNote]
            payload_stream = io.BytesIO(payload_bytes)
            
            # Skip KEK nonce (12 bytes) and encrypted DEK (48 bytes)
            payload_stream.read(60)
            
            # Read patch count
            patch_count = struct.unpack('>H', payload_stream.read(2))[0]
            
            return patch_count
            
        except Exception as e:
            print(f"Error getting face count: {str(e)}")
            return 0
