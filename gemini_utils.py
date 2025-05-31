import os
from google import genai
from google.genai import types
import mimetypes
import audio_utils as au
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_text_response(API_KEY=None, model=None, contents=None):
    client = genai.Client(
        api_key=API_KEY or os.environ.get("GEMINI_API_KEY"),
    )

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=contents),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        response_mime_type="text/plain",
    )

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )

    return response.text.strip()


def get_audio_response(API_KEY=None, model=None, contents=None):
    client = genai.Client(
        api_key=API_KEY or os.environ.get("GEMINI_API_KEY"),
    )

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=contents),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        response_modalities=[
            "audio",
        ],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name="Charon"
                )
            )
        ),
    )

    audio_data = None

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if (
            chunk.candidates is None
            or chunk.candidates[0].content is None
            or chunk.candidates[0].content.parts is None
        ):
            continue
        if chunk.candidates[0].content.parts[0].inline_data and chunk.candidates[0].content.parts[0].inline_data.data:
            inline_data = chunk.candidates[0].content.parts[0].inline_data
            data_buffer = inline_data.data
            file_extension = mimetypes.guess_extension(inline_data.mime_type)
            if file_extension is None:
                file_extension = ".wav"
                data_buffer = au.convert_to_wav(
                    inline_data.data, inline_data.mime_type)

            audio_data = data_buffer
        else:
            print(chunk.text)

    return audio_data


if __name__ == "__main__":
    model = "gemma-3n-e4b-it"
    contents = "Hi!"
    get_text_response(model, contents)
