import streamlit as st
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer
from transformers import T5ForConditionalGeneration, T5Tokenizer
import torch
import whisper
import re
import os

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="Multilingual Medical Assistant",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. Caching Models and Data ---
@st.cache_resource
def load_models_and_data():
    """
    Load all necessary models and data files.
    This function is cached to run only once.
    """
    with st.spinner("Loading AI models... This may take a moment on the first run."):
        # Embedding model for retrieval
        embedder = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')

        # Generative model for answering (loads on CPU)
        tokenizer = T5Tokenizer.from_pretrained("google/flan-t5-large")
        model = T5ForConditionalGeneration.from_pretrained("google/flan-t5-large")

        # ASR model for speech-to-text
        asr_model = whisper.load_model("base")

        # FAISS index and corpus data
        index = faiss.read_index('medical_faiss.index')
        corpus_df = pd.read_pickle('corpus_data.pkl')

    return embedder, tokenizer, model, asr_model, index, corpus_df

# --- 3. Main Application Logic ---
st.title("⚕️ Multilingual Medical Assistant (Colab Hosted)")
st.markdown("This AI assistant provides information from a medical knowledge base. **It is not a substitute for professional medical advice.**")

# Load all the components
embedder, tokenizer, model, asr_model, index, corpus_df = load_models_and_data()
st.success("Models loaded successfully! The assistant is ready.")


# --- Helper Functions ---
RED_FLAG_KEYWORDS = [
    "chest pain", "can't breathe", "severe bleeding", "unconscious", "stroke", "seizure", "suicide", "poison", "choking",
    "सीने में दर्द", "सांस नहीं ले पा रहा", "गंभीर रक्तस्रव", "बेहोश",
    "छातीत दुखणे", "श्वास घेऊ शकत नाही", "तीव्र रक्तस्त्राव", "बेशुद्ध",
    "மார்பு வலி", "மூச்சுவிட முடியவில்லை", "கடுமையான இரத்தப்போக்கு", "மயக்கம்",
    "বুকের ব্যথা", "শ্বাস নিতে পারছি না", "গুরুতর রক্তপাত", "অজ্ঞান"
]

def check_for_red_flags(text):
    for keyword in RED_FLAG_KEYWORDS:
        if re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE):
            return True
    return False

def get_rag_response(query, k=3):
    if not query:
        return ""

    query_embedding = embedder.encode([query])
    distances, indices = index.search(query_embedding, k)
    retrieved_docs = corpus_df.iloc[indices[0]]['answer'].tolist()
    context = "\n".join([f"- {doc}" for doc in retrieved_docs])

    prompt = f"""
    Answer the following question based ONLY on the provided context.

    Context:
    {context}

    Question: {query}
    """
    inputs = tokenizer(prompt, return_tensors="pt", max_length=1024, truncation=True)
    outputs = model.generate(**inputs, max_new_tokens=256, do_sample=False)
    answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return answer

# --- 4. User Interface Layout ---
input_method = st.radio("Choose your input method:", ("Text", "Audio"), horizontal=True)

user_query = ""

if input_method == "Text":
    user_query = st.text_area("Please enter your medical question:", height=100, placeholder="e.g., What are the symptoms of Dengue fever?")
else:
    audio_file = st.file_uploader("Upload an audio file (.wav, .mp3, etc.):", type=["wav", "mp3", "m4a", "ogg"])
    if audio_file:
        st.audio(audio_file)
        with open("temp_audio_file.tmp", "wb") as f:
            f.write(audio_file.getbuffer())
        
        with st.spinner("Transcribing audio..."):
            try:
                transcription_result = asr_model.transcribe("temp_audio_file.tmp", fp16=False)
                user_query = transcription_result['text']
                st.info(f"**Transcribed Text:** {user_query}")
            except Exception as e:
                st.error(f"Audio transcription failed. Error: {e}")
            finally:
                if os.path.exists("temp_audio_file.tmp"):
                    os.remove("temp_audio_file.tmp")

if st.button("Get Answer", type="primary", use_container_width=True):
    if user_query:
        with st.spinner("Searching knowledge base and generating answer..."):
            if check_for_red_flags(user_query):
                st.error("🚨 **Urgent Symptom Detected!**")
                st.warning("Your query may indicate a serious medical condition. Please consult a doctor immediately.")
            else:
                st.subheader("📝 Answer", divider="rainbow")
                response = get_rag_response(user_query)
                st.write(response)
    else:
        st.warning("Please provide a question first.")
