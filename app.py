import gradio as gr
import tempfile
import zipfile
import os
from pathlib import Path
import json

# Import with error handling
try:
    import gemini_utils as gu
except ImportError:
    print("gemini_utils module not found. Please ensure it's installed and available.")
    exit()


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


def generate_transcript(text_input, api_key, text_model, podcast_style, target_duration, target_audience):
    """Generate transcript with error handling"""
    try:
        # Validate inputs
        errors = validate_inputs(text_input, api_key)
        if errors:
            return "\n".join([f"❌ {error}" for error in errors]), ""

        # Generate system prompt
        system_prompt = get_system_prompt(
            text_input, podcast_style, target_duration, target_audience)

        # Get transcript from Gemini
        response = gu.get_text_response(api_key, text_model, system_prompt)

        return "✅ Transcript generated successfully!", response.strip()
    except Exception as e:
        return f"❌ Error generating transcript: {str(e)}", ""


def generate_audio(transcript, api_key, audio_model):
    """Generate podcast audio with error handling"""
    try:
        if not transcript or transcript.strip() == "":
            return "❌ Transcript is empty. Please generate or enter a transcript first.", None

        if not api_key or api_key.strip() == "":
            return "❌ API key is required", None

        # Generate audio from transcript
        audio_data = gu.get_audio_response(api_key, audio_model, transcript)

        if audio_data is None:
            return "❌ Failed to generate audio", None

        # Save audio to temporary file
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_audio.write(audio_data)
        temp_audio.close()

        return "✅ Audio generated successfully!", temp_audio.name
    except Exception as e:
        return f"❌ Error generating audio: {str(e)}", None


def create_download_package(raw_text, system_prompt, transcript, audio_file):
    """Create a zip file with all content for download"""
    try:
        if not all([raw_text, transcript]):
            return "❌ Missing required content for download package", None

        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, "podcast_package.zip")

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add raw text
            zipf.writestr("01_raw_text.txt", raw_text)

            # Add system prompt if available
            if system_prompt:
                zipf.writestr("02_system_prompt.txt", system_prompt)

            # Add transcript
            zipf.writestr("03_transcript.txt", transcript)

            # Add metadata
            metadata = {
                "generated_by": "Podcast Generator",
                "content_type": "podcast_package",
                "files": ["raw_text.txt", "system_prompt.txt", "transcript.txt"]
            }

            if audio_file and os.path.exists(audio_file):
                # Copy audio file to zip
                zipf.write(audio_file, "04_podcast_audio.wav")
                metadata["files"].append("podcast_audio.wav")

            zipf.writestr("metadata.json", json.dumps(metadata, indent=2))

        return "✅ Download package created successfully!", zip_path
    except Exception as e:
        return f"❌ Error creating download package: {str(e)}", None


def update_character_count(text):
    """Update character count display"""
    if text:
        count = len(text)
        return f"Characters: {count:,}/10,000"
    return "Characters: 0/10,000"


# Create the Gradio interface
with gr.Blocks(title="🎙️ Podcast Generator", theme=gr.themes.Base()) as demo:
    # Header
    gr.Markdown("# 🎙️ Podcast Generator")
    gr.Markdown(
        "Transform your text into engaging podcast content with AI-generated transcripts and audio.")

    # Configuration Section
    with gr.Row():
        gr.Markdown("## ⚙️ Configuration")

    with gr.Accordion("Configuration"):
        with gr.Row():
            with gr.Column():
                text_model = gr.Dropdown(
                    choices=["gemma-3n-e4b-it", "gemini-2.0-flash",
                             "gemini-2.5-flash-preview-05-20"],
                    value="gemini-2.0-flash",
                    label="Text Model",
                    info="Select the model for transcript generation"
                )

            with gr.Column():
                audio_model = gr.Dropdown(
                    choices=["gemini-2.5-flash-preview-tts",
                             "gemini-2.5-pro-preview-tts"],
                    value="gemini-2.5-flash-preview-tts",
                    label="Audio Model",
                    info="Select the model for audio generation"
                )

        # API Key
        api_key = gr.Textbox(
            label="🔑 Gemini API Key",
            type="password",
            placeholder="Enter your Gemini API key here...",
            info="Your API key is required for transcript and audio generation"
        )

    # Podcast Settings
    with gr.Row():
        gr.Markdown("## 🎙️ Podcast Settings")

    with gr.Row():
        with gr.Column():
            podcast_style = gr.Dropdown(
                choices=["educational", "conversational",
                         "storytelling", "interview-style", "documentary"],
                value="educational",
                label="Podcast Style",
                info="Choose the overall style and approach"
            )

        with gr.Column():
            target_duration = gr.Dropdown(
                choices=["3-5 minutes", "5-8 minutes",
                         "8-12 minutes", "12-15 minutes"],
                value="5-8 minutes",
                label="Target Duration",
                info="Approximate length of the final podcast"
            )

        with gr.Column():
            target_audience = gr.Dropdown(
                choices=["general", "beginners",
                         "professionals", "students", "experts"],
                value="general",
                label="Target Audience",
                info="Primary audience for this podcast"
            )

    # Input Text Section
    with gr.Row():
        gr.Markdown("## 📄 Input Text")

    raw_text = gr.Textbox(
        label="Raw Text Source",
        placeholder="Enter the text you want to convert into a podcast...",
        lines=8,
        max_lines=15,
        info="This text will be used to generate the podcast transcript",
    )

    char_count = gr.Markdown("Characters: 0/10,000")

    # Update character count when text changes
    raw_text.change(fn=update_character_count,
                    inputs=raw_text, outputs=char_count)

    # Transcript Generation
    with gr.Row():
        gr.Markdown("## 📋 Transcript Generation")

    with gr.Row():
        generate_transcript_btn = gr.Button(
            "🔄 Generate Transcript", variant="primary", size="lg")

    transcript_status = gr.Markdown("")

    # Store system prompt for download package
    system_prompt_state = gr.State("")

    # Edit Transcript Section
    with gr.Row():
        gr.Markdown("## ✏️ Edit Transcript")

    transcript_editor = gr.Textbox(
        label="Generated Transcript",
        placeholder="Generated transcript will appear here. You can edit it before generating audio.",
        lines=10,
        max_lines=20,
        info="Edit the transcript as needed before generating audio",
    )

    # Audio Generation
    with gr.Row():
        gr.Markdown("## 🎙️ Audio Generation")

    with gr.Row():
        generate_audio_btn = gr.Button(
            "🎵 Generate Audio", variant="primary", size="lg")

    audio_status = gr.Markdown("")

    # Audio Player
    with gr.Row():
        gr.Markdown("## 🔊 Audio Player")

    audio_player = gr.Audio(
        label="Generated Podcast Audio",
        type="filepath",
        interactive=False
    )

    # Download Section
    with gr.Row():
        gr.Markdown("## 📦 Download Package")

    with gr.Row():
        download_btn = gr.Button(
            "📥 Create Download Package", variant="secondary", size="lg")

    download_status = gr.Markdown("")
    download_file = gr.File(label="Download Package", visible=False)

    # Event handlers
    def handle_transcript_generation(raw_text, api_key, text_model, podcast_style, target_duration, target_audience):
        status, transcript = generate_transcript(
            raw_text, api_key, text_model, podcast_style, target_duration, target_audience)
        system_prompt = get_system_prompt(
            raw_text, podcast_style, target_duration, target_audience) if transcript else ""
        return status, transcript, system_prompt

    def handle_audio_generation(transcript, api_key, audio_model):
        status, audio_path = generate_audio(transcript, api_key, audio_model)
        return status, audio_path

    def handle_download_creation(raw_text, system_prompt, transcript, audio_file):
        status, zip_path = create_download_package(
            raw_text, system_prompt, transcript, audio_file)
        if zip_path:
            return status, gr.File(value=zip_path, visible=True)
        return status, gr.File(visible=False)

    # Connect event handlers
    generate_transcript_btn.click(
        fn=handle_transcript_generation,
        inputs=[raw_text, api_key, text_model,
                podcast_style, target_duration, target_audience],
        outputs=[transcript_status, transcript_editor, system_prompt_state]
    )

    generate_audio_btn.click(
        fn=handle_audio_generation,
        inputs=[transcript_editor, api_key, audio_model],
        outputs=[audio_status, audio_player]
    )

    download_btn.click(
        fn=handle_download_creation,
        inputs=[raw_text, system_prompt_state,
                transcript_editor, audio_player],
        outputs=[download_status, download_file]
    )

# Launch the app
if __name__ == "__main__":
    demo.launch(
        share=False,
        server_name="0.0.0.0",
        server_port=7860,
        show_api=False
    )
