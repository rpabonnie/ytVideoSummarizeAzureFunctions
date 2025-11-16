"""Quick test to verify media_resolution parameter works"""
from google.genai import types

# Test that we can create a config with media_resolution
config = types.GenerateContentConfig(
    media_resolution=types.MediaResolution.MEDIA_RESOLUTION_LOW
)

print(f"✅ Config created successfully!")
print(f"Media Resolution: {config.media_resolution}")
print(f"Type: {type(config.media_resolution)}")
