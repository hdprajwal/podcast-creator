# import streamlit as st
# import gemini_utils as gu

# st.title("Podcast Generator")
# st.markdown("This is just a playground to test a POC for a podcast generator.")

# # Initialize session state variables if they don't exist
# if 'transcript' not in st.session_state:
#     st.session_state.transcript = None
# if 'is_transcript_generated' not in st.session_state:
#     st.session_state.is_transcript_generated = False

# # UI elements to select the model and API key
# TEXT_MODEL = st.selectbox("Select the text model to use", [
#     "gemma-3n-e4b-it", "gemini-2.0-flash", "gemini-2.5-flash-preview-05-20"], key="text_model")

# AUDIO_MODEL = st.selectbox("Select the audio model to use", [
#     "gemini-2.5-flash-preview-tts", "gemini-2.5-pro-preview-tts"], key="audio_model")

# API_KEY = st.text_input("Enter your Gemini API key",
#                         type="password", key="api_key")


# def get_system_prompt(text_input):
#     return f"""
#     You are a helpful assistant that generates a transcript for a educational video from a given text input.
#     The transcript should follow the following format:
#     [Tone: This is a transcript for an educational video, so choose the appropriate tone]
#     <text>
#     [Tone: adjust to the tone of the text]
#     <text>
#     [Tone: adjust to the tone of the text]
#     <text>
#     [Tone: adjust to the tone of the text]

#     The Transcript should not use any markdown or html tags.
#     The Transcript should not use any special characters.
#     The Transcript should not use any emojis.
#     The Transcript should not include any details like the scene details or the speaker details.

#     Generate the transcript for the following text:
#     {text_input}
#     """


# def generate_transcript(text_input):
#     st.write("Generating transcript...")
#     formatted_prompt = get_system_prompt(text_input)
#     response = gu.get_text_response(API_KEY, TEXT_MODEL, formatted_prompt)
#     return response


# def generate_podcast(transcript):
#     st.write("Generating podcast...")
#     MODEL = "gemini-2.5-flash-preview-tts"
#     audio_data = gu.get_audio_response(API_KEY, MODEL, transcript)

#     return audio_data


# def get_edited_transcript():
#     edited_transcript = st.text_area(
#         "Edit the transcript",
#         height=200,
#         key="edited_transcript",
#         value=st.session_state.transcript if st.session_state.transcript else ""
#     )
#     return edited_transcript


# def save_binary_file(file_name, data):
#     f = open(file_name, "wb")
#     f.write(data)
#     f.close()
#     print(f"File saved to to: {file_name}")


# text_input = st.text_area("Enter your text here",
#                           height=200, key="text_input")
# generate_transcript_button = st.button("Generate Transcript")

# if generate_transcript_button:
#     response = generate_transcript(text_input)
#     st.session_state.transcript = response.strip()
#     st.session_state.is_transcript_generated = True

# if st.session_state.is_transcript_generated:
#     st.write("Transcript generated")
#     edited_transcript = get_edited_transcript()

#     generate_podcast_button = st.button("Generate Podcast")
#     if generate_podcast_button:
#         podcast = generate_podcast(edited_transcript)
#         st.audio(podcast, format="audio/wav")

#         save_podcast_button = st.button("Save Podcast")
#         if save_podcast_button:
#             save_binary_file("podcast.wav", podcast)


import streamlit as st
import os
from pathlib import Path

# Import with error handling
try:
    import gemini_utils as gu
except ImportError:
    st.error(
        "gemini_utils module not found. Please ensure it's installed and available.")
    st.stop()

st.title("🎙️ Podcast Generator")
st.markdown("This is a playground to test a POC for a podcast generator.")

# Initialize session state variables
if 'transcript' not in st.session_state:
    st.session_state.transcript = None
if 'is_transcript_generated' not in st.session_state:
    st.session_state.is_transcript_generated = False
if 'generated_audio' not in st.session_state:
    st.session_state.generated_audio = None

# Configuration section
st.subheader("⚙️ Configuration")
col1, col2 = st.columns(2)

with col1:
    TEXT_MODEL = st.selectbox(
        "Select the text model to use",
        ["gemma-3n-e4b-it", "gemini-2.0-flash", "gemini-2.5-flash-preview-05-20"],
        key="text_model"
    )

with col2:
    AUDIO_MODEL = st.selectbox(
        "Select the audio model to use",
        ["gemini-2.5-flash-preview-tts", "gemini-2.5-pro-preview-tts"],
        key="audio_model"
    )

API_KEY = st.text_input(
    "🔑 Enter your Gemini API key",
    type="password",
    key="api_key",
    help="Your API key is required to generate transcripts and audio"
)


def validate_inputs(text_input, api_key):
    """Validate user inputs before processing"""
    errors = []

    if not api_key or api_key.strip() == "":
        errors.append("API key is required")

    if not text_input or text_input.strip() == "":
        errors.append("Text input is required")

    if len(text_input.strip()) > 10000:  # Reasonable limit
        errors.append("Text input is too long (max 10,000 characters)")

    return errors


def get_system_prompt(text_input):
    """Generate system prompt for transcript creation"""
    return f"""
    You are a helpful assistant that generates a transcript for an educational video from a given text input.
    The transcript should follow the following format:
    [Tone: This is a transcript for an educational video, so choose the appropriate tone]
    <text>
    [Tone: adjust to the tone of the text]
    <text>
    [Tone: adjust to the tone of the text]
    <text>
    [Tone: adjust to the tone of the text]

    The Transcript should not use any markdown or html tags.
    The Transcript should not use any special characters.
    The Transcript should not use any emojis.
    The Transcript should not include any details like the scene details or the speaker details.

    Generate the transcript for the following text:
    {text_input}
    """


def generate_transcript(text_input, api_key, model):
    """Generate transcript with error handling"""
    try:
        with st.spinner("🔄 Generating transcript..."):
            formatted_prompt = get_system_prompt(text_input)
            response = gu.get_text_response(api_key, model, formatted_prompt)
            return response.strip(), None
    except Exception as e:
        return None, f"Error generating transcript: {str(e)}"


def generate_podcast(transcript, api_key, model):
    """Generate podcast audio with error handling"""
    try:
        with st.spinner("🎵 Generating podcast audio..."):
            audio_data = gu.get_audio_response(api_key, model, transcript)
            return audio_data, None
    except Exception as e:
        return None, f"Error generating podcast: {str(e)}"


def save_binary_file(file_name, data):
    """Save binary file with proper error handling"""
    try:
        file_path = Path(file_name)
        with open(file_path, "wb") as f:
            f.write(data)
        return str(file_path.absolute()), None
    except Exception as e:
        return None, f"Error saving file: {str(e)}"


def get_edited_transcript():
    """Get edited transcript from text area"""
    return st.text_area(
        "📝 Edit the transcript",
        height=200,
        key="edited_transcript",
        value=st.session_state.transcript if st.session_state.transcript else "",
        help="You can edit the generated transcript before creating the podcast"
    )


# Main content section
st.subheader("📄 Input Text")
text_input = st.text_area(
    "Enter your text here",
    height=200,
    key="text_input",
    placeholder="Enter the text you want to convert into a podcast...",
    help="This text will be used to generate an educational podcast transcript"
)

# Character count
if text_input:
    char_count = len(text_input)
    st.caption(f"Characters: {char_count:,}/10,000")

# Generate transcript section
st.subheader("📋 Transcript Generation")

# Validate inputs before showing button
validation_errors = validate_inputs(text_input, API_KEY)

if validation_errors:
    for error in validation_errors:
        st.error(f"❌ {error}")

generate_transcript_button = st.button(
    "🔄 Generate Transcript",
    disabled=bool(validation_errors),
    help="Generate a podcast transcript from your input text"
)

if generate_transcript_button and not validation_errors:
    transcript, error = generate_transcript(text_input, API_KEY, TEXT_MODEL)

    if error:
        st.error(error)
    else:
        st.session_state.transcript = transcript
        st.session_state.is_transcript_generated = True
        st.success("✅ Transcript generated successfully!")

# Show transcript editing section if transcript is generated
if st.session_state.is_transcript_generated:
    st.subheader("✏️ Edit Transcript")
    edited_transcript = get_edited_transcript()

    # Generate podcast section
    st.subheader("🎙️ Podcast Generation")

    if not edited_transcript.strip():
        st.warning(
            "⚠️ Transcript is empty. Please add content before generating podcast.")

    generate_podcast_button = st.button(
        "🎵 Generate Podcast",
        disabled=not edited_transcript.strip(),
        help="Generate audio podcast from the transcript"
    )

    if generate_podcast_button and edited_transcript.strip():
        podcast_data, error = generate_podcast(
            edited_transcript, API_KEY, AUDIO_MODEL)

        if error:
            st.error(error)
        else:
            st.session_state.generated_audio = podcast_data
            st.success("✅ Podcast generated successfully!")

            # Audio playback
            st.subheader("🔊 Listen to Your Podcast")
            st.audio(podcast_data, format="audio/wav")

# Display existing audio if available
elif st.session_state.generated_audio:
    st.subheader("🔊 Your Generated Podcast")
    st.audio(st.session_state.generated_audio, format="audio/wav")

st.markdown("---")
st.markdown("*Built with Streamlit and Gemini AI*")
