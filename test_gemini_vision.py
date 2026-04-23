import os
from google import genai
import PIL.Image
import io

gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", "AIzaSyDnk22nR_MI63OkVvOGEZ-9YbmRfZeruyQ"))

# Create a dummy image
img = PIL.Image.new('RGB', (100, 100), color = 'white')

response = gemini_client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[img, "Describe this image in 5 words"]
)
print(response.text)
