import streamlit as st
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


# Podcast customization
st.subheader("🎙️ Podcast Settings")
col1, col2, col3 = st.columns(3)

with col1:
    podcast_style = st.selectbox(
        "Podcast Style",
        ["educational", "conversational", "storytelling",
            "interview-style", "documentary"],
        help="Choose the overall style and approach for your podcast"
    )

with col2:
    target_duration = st.selectbox(
        "Target Duration",
        ["3-5 minutes", "5-8 minutes", "8-12 minutes", "12-15 minutes"],
        index=1,
        help="Approximate length of the final podcast"
    )

with col3:
    target_audience = st.selectbox(
        "Target Audience",
        ["general", "beginners", "professionals", "students", "experts"],
        help="Who is the primary audience for this podcast?"
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


def get_system_prompt(text_input, podcast_style="educational", target_duration="5-8 minutes", target_audience="general"):
    """Generate system prompt for transcript creation"""
    min_target_duration_minutes = int(target_duration.split()[0].split("-")[0])
    max_target_duration_minutes = int(target_duration.split()[0].split("-")[1])
    target_duration_words = min_target_duration_minutes * 100
    return f"""
You are an expert podcast script writer specializing in creating engaging, educational audio content. Your task is to transform the provided text into a natural, conversational podcast transcript.

**PODCAST SPECIFICATIONS:**
- Style: {podcast_style} podcast
- Target Duration: {target_duration} (approximately {target_duration_words} words)
- Target Audience: {target_audience} audience
- Format: Single narrator speaking directly to listeners

**SCRIPT STRUCTURE:**
1. **Hook (30-45 seconds)**: Start with an intriguing question, surprising fact, or compelling statement that grabs attention about the topic
2. **Introduction (30-60 seconds)**: Briefly introduce the topic and what listeners will learn
3. **Main Content ({min_target_duration_minutes - 2}-{max_target_duration_minutes -2} minutes)**: Present the key information in 2-4 digestible segments with smooth transitions
4. **Conclusion (30-45 seconds)**: Summarize key takeaways and end with a thought-provoking statement

**WRITING STYLE REQUIREMENTS:**
- Use conversational, natural language as if speaking to a friend
- Include rhetorical questions to engage listeners
- Add smooth transitions between topics ("Now that we've covered X, let's explore Y...")
- Use analogies and examples to explain complex concepts
- Include brief pauses indicated by natural sentence breaks
- Vary sentence length for natural rhythm
- Use active voice and present tense when possible

**CONTENT GUIDELINES:**
- Make complex ideas accessible without dumbing them down
- Include specific examples or case studies when relevant
- Add context for why this information matters to listeners
- Build concepts progressively from simple to complex
- Include actionable insights or takeaways

**FORMATTING RULES:**
- Write in plain text only (no markdown, HTML, or special characters)
- Use standard punctuation for natural speech patterns
- Do not include stage directions, speaker labels, or technical notes
- Do not use ALL CAPS, emojis, or excessive punctuation
- Write as a continuous script, not bullet points
- Do not include scene directions, speaker labels, or technical notes
- Do not include any audio/music/sound effects/background instructions.
- Enclose all tone and voice instructions in [ and ] tags.

**TONE AND VOICE:**
- Enthusiastic but not overly excited
- Authoritative yet approachable
- Curious and engaging
- Professional but conversational
- Add Tone and voice instructions in the transcript.


Transform this source material into an engaging podcast script:

{text_input}

Remember: This will be converted to audio, so prioritize clarity, natural flow, and listener engagement over visual formatting."""


def generate_transcript(text_input, api_key, model, podcast_style, target_duration, target_audience):
    """Generate transcript with error handling"""
    try:
        with st.spinner("🔄 Generating transcript..."):
            formatted_prompt = get_system_prompt(
                text_input, podcast_style, target_duration, target_audience)
            st.write(formatted_prompt)
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
    transcript, error = generate_transcript(
        text_input, API_KEY, TEXT_MODEL, podcast_style, target_duration, target_audience)

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
