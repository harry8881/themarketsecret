cat > resize_logo.py <<'EOF'
from PIL import Image

original = Image.open("/Users/harrymark/Downloads/IMG_5904.jpg")
resized = original.resize((200, 80))  # Width, Height in pixels
resized.save("static/images/logo.jpg", quality=85)
print("Logo resized successfully!")
EOF
