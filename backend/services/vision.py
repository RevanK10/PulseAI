import cv2
import numpy as np

def anonymize_patient_image(image_bytes: bytes) -> bytes:
    """Decodes image, blurs facial regions for privacy, and returns sanitized JPEG bytes."""
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        return image_bytes

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

    for (x, y, w, h) in faces:
        roi = img[y:y+h, x:x+w]
        blurred_roi = cv2.GaussianBlur(roi, (99, 99), 30)
        img[y:y+h, x:x+w] = blurred_roi

    _, encoded_img = cv2.imencode('.jpg', img)
    return encoded_img.tobytes()