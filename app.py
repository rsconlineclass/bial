import os
import openai
import streamlit as st
from googleapiclient.discovery import build
from PyPDF2 import PdfReader
from PIL import Image
from dotenv import load_dotenv
import tempfile

# Load environment variables from .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")
search_engine_id = os.getenv("SEARCH_ENGINE_ID")

# Google search API function
def google_search(query):
    service = build("customsearch", "v1", developerKey=google_api_key)
    res = service.cse().list(q=query, cx=search_engine_id).execute()
    return res.get('items', [])

# Process text files
def process_text_file(uploaded_file):
    return uploaded_file.read().decode("utf-8")

# Process PDF files
def process_pdf_file(uploaded_file):
    pdf_reader = PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# Save image temporarily to send it to GPT-4 Vision
def process_image_file(image_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
        img = Image.open(image_file)
        img.save(tmp_file, format="PNG")
        return tmp_file.name

# Chat interaction with GPT-4 or GPT-4 Vision
def interact_with_gpt4(message, context, image_path=None):
    # Add the virtual assistant system prompt here
    system_prompt = """
    You are BLR Pulse, a virtual assistant at Kempegowda International Airport (Bangalore). 
    You provide real-time flight information, airport navigation, travel assistance, dining and shopping suggestions, and help with transportation. 
    Offer clear and helpful responses tailored to the needs of travelers at BLR Airport. Be friendly, calm, and efficient, ensuring a seamless airport experience.
    """

    messages = [{"role": "system", "content": f"{system_prompt} Context: {context}"}]
    messages.append({"role": "user", "content": message})

    if image_path:
        # OpenAI expects the image file to be uploaded in 'files'
        with open(image_path, "rb") as img_file:
            response = openai.ChatCompletion.create(
                model="gpt-4-vision",  # Vision model for handling image content
                messages=messages,
                files=[{"image": img_file}]
            )
    else:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Standard GPT-4 model for text-based interactions
            messages=messages,
        )

    return response['choices'][0]['message']['content']

# Streamlit web app
st.title("BIAL PASSENGER HELPDESK")

# File uploader for text, PDFs, and images
uploaded_file = st.file_uploader("Upload your ticket (PDF):", type=["pdf",])
context = ""
image_path = None

if uploaded_file:
    file_type = uploaded_file.type

    # Process based on file type
    if file_type == "text/plain":
        context = process_text_file(uploaded_file)
        st.write("Text file uploaded.")
    
    elif file_type == "application/pdf":
        context = process_pdf_file(uploaded_file)
        st.write("PDF file uploaded and processed.")

    elif file_type.startswith("image"):
        st.image(uploaded_file)
        image_path = process_image_file(uploaded_file)
        st.write("Image file uploaded.")
    
    else:
        st.error("Unsupported file type")

# Chatbox for user input
user_input = st.text_input("Ask something related to the context or chat with the assistant")

if user_input:
    # Interact with GPT-4 Vision if image is uploaded, else GPT-4
    assistant_response = interact_with_gpt4(user_input, context, image_path)
    st.write(f"Assistant: {assistant_response}")
    
# Optional web search during chat
if st.button("Search the web for more information"):
    search_results = google_search(user_input)
    if search_results:
        st.write("Relevant websites found (showing top 5):")
        for i, result in enumerate(search_results[:5]):  # Limit to top 5 results
            st.write(f"{i + 1}. [{result['title']}]({result['link']})")
            st.write(result['snippet'])
    else:
        st.write("No relevant information found.")




