import os
import io
import struct  # For binary packing/unpacking
import piexif
import piexif.helper
from PIL import Image, ImageDraw
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# --- 1. Key Management ---

def get_master_kek():
    """
    Simulates fetching a static, app-wide master key (KEK).
    """
    return b'g\x06\x88\x91\xcb\xfd\xaa\r:9\x0b\xdf\x84\x97I\x9e\x15O\x06\xb7\x8cC\x11\xa3\x11\xe6\x1a\xd6B\x87A\xfc'

# --- 2. Core Encryption Function (UPDATED) ---

def encrypt_image(original_path: str, regions: list) -> bytes:
    """
    Encrypts regions using the "Pixelate-and-Patch" algorithm.
    Uses a strong 32x32 pixelation for aesthetics and storage efficiency.
    """
    print("--- Encryption Process Started ('Pixelate-and-Patch' Algorithm) ---")
    
    # --- 1. Setup ---
    master_kek = get_master_kek()
    aesgcm_kek = AESGCM(master_kek)
    
    dek = AESGCM.generate_key(bit_length=256)
    aesgcm_dek = AESGCM(dek)
    
    original_image = Image.open(original_path)
    public_image = original_image.copy()
    
    metadata_payload = bytearray()

    # --- 2. Encrypt the DEK and add to payload ---
    nonce_kek = os.urandom(12)
    encrypted_dek = aesgcm_kek.encrypt(nonce_kek, dek, None)
    
    metadata_payload.extend(nonce_kek)
    metadata_payload.extend(encrypted_dek)

    # --- 3. Process Patches & Create "Pixelated" Blocks ---
    
    metadata_payload.extend(struct.pack('>H', len(regions))) # Add patch count
    
    # *** THIS IS THE FIX ***
    # Increased block size for stronger, more aesthetic pixelation
    PIXEL_BLOCK_SIZE = 32 
    
    for region in regions:
        # A. Create a "pixelated" block
        
        # 1. Crop the region from the public image
        patch_to_pixelate = public_image.crop(region)
        w, h = patch_to_pixelate.size
        
        # 2. Pixelate: downsize to a tiny block, then scale back up
        # We use max(1, ...) to avoid divide-by-zero on tiny images
        small = patch_to_pixelate.resize(
            (max(1, w // PIXEL_BLOCK_SIZE), max(1, h // PIXEL_BLOCK_SIZE)), 
            Image.Resampling.NEAREST
        )
        pixelated_patch = small.resize((w, h), Image.Resampling.NEAREST)
        
        # 3. Paste the low-entropy pixelated block back
        public_image.paste(pixelated_patch, region)

        # B. Get the original, unblurred patch
        original_patch = original_image.crop(region)
        
        # C. Save patch as an efficient, medium-quality JPEG
        patch_io = io.BytesIO()
        original_patch.save(patch_io, format="JPEG", quality=75) # 75 quality
        patch_plaintext_bytes = patch_io.getvalue()
        
        # D. Encrypt the patch bytes
        nonce_data = os.urandom(12)
        ciphertext = aesgcm_dek.encrypt(nonce_data, patch_plaintext_bytes, None)
        
        # E. Append raw binary data to the payload
        metadata_payload.extend(struct.pack('>HHHH', region[0], region[1], region[2], region[3]))
        metadata_payload.extend(nonce_data)
        metadata_payload.extend(struct.pack('>I', len(ciphertext)))
        metadata_payload.extend(ciphertext)
    
    print(f"Processed {len(regions)} regions (32x32 pixelation).")

    # --- 4. Create Final JPEG File ---
    
    # A. Inject raw binary payload into the 'MakerNote' tag
    exif_dict = {"Exif": {piexif.ExifIFD.MakerNote: bytes(metadata_payload)}}
    exif_bytes = piexif.dump(exif_dict)
    
    # B. Save the public image (with pixelated blocks)
    final_file_io = io.BytesIO()
    public_image.save(
        final_file_io,
        format="JPEG",
        quality=85, # Save base at 85
        exif=exif_bytes
    )
    
    print("--- Encryption Process Finished ---")
    return final_file_io.getvalue()


# --- 3. Core Decryption Function (For temporary, in-memory viewing) ---

def decrypt_image(encrypted_file_data: bytes, indices_to_decrypt: list[int] = None) -> Image.Image:
    """
    Decrypts the binary MakerNote payload and stitches *only* the
    patches specified in `indices_to_decrypt`.
    
    This is for temporary, in-memory decryption.
    """
    print(f"\n--- Decryption Process Started (Requesting indices: {indices_to_decrypt}) ---")
    
    # --- 1. Setup ---
    master_kek = get_master_kek()
    aesgcm_kek = AESGCM(master_kek)
    
    encrypted_image = Image.open(io.BytesIO(encrypted_file_data))
    decrypted_image = encrypted_image.copy() # Start with the "pixelated" image
    
    if not indices_to_decrypt:
        print("No indices specified. Returning pixelated image.")
        return decrypted_image

    # --- 2. Read and Parse EXIF Metadata ---
    try:
        if "exif" not in encrypted_image.info:
            print("Error: No EXIF data found.")
            return None
            
        exif_data = piexif.load(encrypted_image.info["exif"])
        
        if piexif.ExifIFD.MakerNote not in exif_data["Exif"]:
            print("Error: No MakerNote found in EXIF data.")
            return None
            
        payload_bytes = exif_data["Exif"][piexif.ExifIFD.MakerNote]
        payload_stream = io.BytesIO(payload_bytes)

    except Exception as e:
        print(f"Error reading metadata: {e}")
        return None

    # --- 3. Decrypt the DEK (Reverse Envelope) ---
    try:
        # Read the KEK nonce (12 bytes) and encrypted DEK (48 bytes)
        nonce_kek = payload_stream.read(12)
        encrypted_dek = payload_stream.read(48)
        
        dek = aesgcm_kek.decrypt(nonce_kek, encrypted_dek, None)
        aesgcm_dek = AESGCM(dek)
    except Exception as e:
        print(f"CRITICAL: Failed to decrypt DEK. Error: {e}")
        return None

    # --- 4. Parse All Patches, Decrypt Selectively ---
    try:
        patch_count = struct.unpack('>H', payload_stream.read(2))[0]
        print(f"File contains {patch_count} encrypted patches.")
        
        all_patches_info = []

        # Loop 1: Parse ALL patch data from the stream
        for _ in range(patch_count):
            patch_data = {}
            patch_data['box'] = tuple(struct.unpack('>HHHH', payload_stream.read(8)))
            patch_data['nonce_data'] = payload_stream.read(12)
            cipher_len = struct.unpack('>I', payload_stream.read(4))[0]
            patch_data['ciphertext'] = payload_stream.read(cipher_len)
            all_patches_info.append(patch_data)
        
        print(f"Successfully parsed all {patch_count} patches.")

        # Loop 2: Decrypt and stitch ONLY the requested patches
        patches_stitched = 0
        for index_to_check in indices_to_decrypt:
            if index_to_check >= len(all_patches_info):
                print(f"Warning: Index {index_to_check} is out of bounds. Skipping.")
                continue
            
            try:
                patch_info = all_patches_info[index_to_check]
                box = patch_info['box']
                patch_plaintext_bytes = aesgcm_dek.decrypt(
                    patch_info['nonce_data'], 
                    patch_info['ciphertext'], 
                    None
                )
                patch_image = Image.open(io.BytesIO(patch_plaintext_bytes))
                decrypted_image.paste(patch_image, box)
                print(f"Decrypted and stitched patch {index_to_check} (box: {box}).")
                patches_stitched += 1
                
            except Exception as e:
                print(f"Failed to decrypt patch {index_to_check} (box: {box}). Error: {e}")

    except Exception as e:
        print(f"Failed to parse patch stream. Error: {e}")

    print(f"--- Decryption Finished. {patches_stitched} patches restored. ---")
    return decrypted_image


# --- 4. Function to permanently reveal a patch (Unchanged) ---

def permanently_reveal_patches(encrypted_file_data: bytes, indices_to_reveal: list[int]) -> bytes:
    """
    Reads an encrypted file, decrypts specified patches, pastes them
    onto the image, and saves a *new* file with the patch
    metadata permanently removed to save space.
    
    This is a destructive, "burn-in" operation.
    """
    print(f"\n--- Permanent Reveal Started (Revealing indices: {indices_to_reveal}) ---")

    # --- 1. Setup & Load ---
    master_kek = get_master_kek()
    aesgcm_kek = AESGCM(master_kek)
    
    encrypted_image = Image.open(io.BytesIO(encrypted_file_data))
    # This is the canvas we will modify
    new_public_image = encrypted_image.copy()
    
    if not indices_to_reveal:
        print("No indices specified. Returning original file data.")
        return encrypted_file_data

    # --- 2. Read, Parse, and Decrypt DEK ---
    try:
        exif_data = piexif.load(encrypted_image.info["exif"])
        payload_bytes = exif_data["Exif"][piexif.ExifIFD.MakerNote]
        payload_stream = io.BytesIO(payload_bytes)
        
        nonce_kek = payload_stream.read(12)
        encrypted_dek = payload_stream.read(48)
        
        dek = aesgcm_kek.decrypt(nonce_kek, encrypted_dek, None)
        aesgcm_dek = AESGCM(dek)
    except Exception as e:
        print(f"CRITICAL: Failed to decrypt DEK. Cannot proceed. Error: {e}")
        return None

    # --- 3. Parse All Patches & Create New Metadata ---
    new_metadata_payload = bytearray()
    # Add KEK info back, as it's needed for the *other* patches
    new_metadata_payload.extend(nonce_kek)
    new_metadata_payload.extend(encrypted_dek)
    
    patches_to_keep_binary = bytearray()
    patches_kept_count = 0
    patches_revealed_count = 0
    
    try:
        patch_count = struct.unpack('>H', payload_stream.read(2))[0]
        
        for i in range(patch_count):
            # Read the full binary data for this patch
            box_bytes = payload_stream.read(8)
            nonce_data = payload_stream.read(12)
            cipher_len_bytes = payload_stream.read(4)
            cipher_len = struct.unpack('>I', cipher_len_bytes)[0]
            ciphertext = payload_stream.read(cipher_len)
            
            if i in indices_to_reveal:
                # REVEAL this patch
                print(f"Revealing patch {i}...")
                patch_plaintext_bytes = aesgcm_dek.decrypt(nonce_data, ciphertext, None)
                patch_image = Image.open(io.BytesIO(patch_plaintext_bytes))
                
                # Paste it onto the canvas
                box = tuple(struct.unpack('>HHHH', box_bytes))
                new_public_image.paste(patch_image, box)
                patches_revealed_count += 1
            else:
                # KEEP this patch
                patches_kept_count += 1
                patches_to_keep_binary.extend(box_bytes)
                patches_to_keep_binary.extend(nonce_data)
                patches_to_keep_binary.extend(cipher_len_bytes)
                patches_to_keep_binary.extend(ciphertext)
        
        # Add the *new* patch count to the payload
        new_metadata_payload.extend(struct.pack('>H', patches_kept_count))
        # Add the binary data for all patches we are keeping
        new_metadata_payload.extend(patches_to_keep_binary)
        
        print(f"Revealed {patches_revealed_count} patches. Kept {patches_kept_count} patches.")

    except Exception as e:
        print(f"Failed to parse or rewrite patch stream. Error: {e}")
        return None

    # --- 4. Save New File with Updated Metadata ---
    exif_dict = {"Exif": {piexif.ExifIFD.MakerNote: bytes(new_metadata_payload)}}
    exif_bytes = piexif.dump(exif_dict)
    
    final_file_io = io.BytesIO()
    new_public_image.save(
        final_file_io,
        format="JPEG",
        quality=85,
        exif=exif_bytes
    )
    
    print("--- Permanent Reveal Finished ---")
    return final_file_io.getvalue()


# --- 5. Main Execution Example ---

if __name__ == "__main__":
    
    # 1. --- SETUP ---
    original_file = "Aditya.jpeg"
    
    # !!! TODO: YOU MUST UPDATE THESE COORDINATES !!!
    # Define the regions (x1, y1, x2, y2) you want to encrypt in your 'photo.jpg'
    blur_regions = [
        (145, 145, 1050, 1005),   # Example: Box around PII
        (295, 145, 550, 205)   # Example: Box around confidential project name
    ]
    # ------------------
    
    if not os.path.exists(original_file):
        print(f"'{original_file}' not found. Generating a default example.")
        print("Please provide your own 'photo.jpg' and update 'blur_regions' next time.")
        img = Image.new('RGB', (600, 400), color='#FFFFFF')
        d = ImageDraw.Draw(img)
        d.text((20, 20), "Project Phoenix - Quarterly Report", fill='black')
        d.text((50, 150), "SSN: 123-456-7890", fill='black')
        d.text((300, 150), "Acquisition Target: X-Corp", fill='red')
        img.save(original_file, "JPEG", quality=95)
    
    original_size = os.path.getsize(original_file)
    print(f"\nOriginal 'photo.jpg' size: {original_size / 1024:.2f} KB")

    # 2. Encrypt the image
    encrypted_file_data = encrypt_image(original_file, blur_regions)
    
    # 3. Save the new single file
    encrypted_file_name = "photo_encrypted.jpg"
    with open(encrypted_file_name, 'wb') as f:
        f.write(encrypted_file_data)
        
    encrypted_size = len(encrypted_file_data)
    print(f"\nSaved encrypted file to '{encrypted_file_name}'")
    
    # 4. Check the size constraint
    size_ratio = encrypted_size / original_size
    print(f"New encrypted file size: {encrypted_size / 1024:.2f} KB")
    print(f"SIZE RATIO: {size_ratio:.2f}x (Target: < 1.5x)")
    
    if size_ratio < 1.5:
        print("✅ SUCCESS: Storage constraint met.")
    else:
        print("❌ FAILURE: Storage constraint NOT met.")

    # 5. --- DEMONSTRATE TEMPORARY DECRYPTION ---
    
    # Decrypt ONLY patch 0
    decrypted_image_v1 = decrypt_image(encrypted_file_data, indices_to_decrypt=[0])
    if decrypted_image_v1:
        decrypted_file_v1 = "photo_decrypted_temp_patch_0.jpg"
        decrypted_image_v1.save(decrypted_file_v1, "JPEG", quality=95)
        print(f"\nSaved temporary decryption (patch 0) to '{decrypted_file_v1}'")

    # 6. --- DEMONSTRATE PERMANENT REVEAL ---
    
    # Permanently reveal patch 0 and remove its metadata
    revealed_file_data = permanently_reveal_patches(encrypted_file_data, indices_to_reveal=[0])
    
    if revealed_file_data:
        revealed_file_name = "photo_revealed_patch_0.jpg"
        with open(revealed_file_name, 'wb') as f:
            f.write(revealed_file_data)
        
        revealed_size = len(revealed_file_data)
        print(f"\nSaved *permanently revealed* file to '{revealed_file_name}'")
        print(f"New file size: {revealed_size / 1024:.2f} KB (should be smaller than {encrypted_size / 1024:.2f} KB)")
        
        # 7. --- VERIFY PERMANENT REVEAL ---
        
        # Try to decrypt patch 1 (which is now index 0)
        print("\nVerifying new file: checking for patch 1 (which is now index 0)...")
        test_img_1 = decrypt_image(revealed_file_data, indices_to_decrypt=[0])
        if test_img_1:
            test_img_1.save("test_reveal_patch_1_as_0.jpg", "JPEG", quality=95)
            print("...Patch 1 (now at index 0) successfully decrypted from new file.")
            
        # Try to decrypt patch index 1 (which no longer exists)
        print("\nVeriying new file: checking for index 1 (should fail)...")
        test_img_0 = decrypt_image(revealed_file_data, indices_to_decrypt=[1])
        # This will just print a warning, as expected.
        
        print("\nTest complete.")