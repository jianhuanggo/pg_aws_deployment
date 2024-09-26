import os
from _config import _config as _config_
from _util import _util_directory as _util_directory_
from _common import _common as _common_


@_common_.exception_handlers(logger=None)
def tts(text: str) -> None:
    from openai import OpenAI
    _config = _config_.PGConfigSingleton()
    _data_output = os.path.join(_config.config.get("default_data_dir"), "tts")
    _util_directory_.create_directory(_data_output)

    client = OpenAI(api_key=_config.config.get("api_key"))
    response = client.audio.speech.create(
        model="tts-1",
        voice="nova",
        input=text
    )


@_common_.exception_handlers(logger=None)
def read_audio_file(speech_file_path):
    import sounddevice as sd
    import soundfile as sf
    audio_data, sample_rate = sf.read(speech_file_path)
    sd.play(audio_data, sample_rate)
    sd.wait()
