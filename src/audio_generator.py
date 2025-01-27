from google.cloud import texttospeech
from dotenv import load_dotenv
import os

class AudioGenerator:
    def __init__(self, language_code="en-US", voice_name="en-US-Neural2-I", gender="MALE"):
        # Carregar variáveis de ambiente do arquivo .env na pasta anterior
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
        load_dotenv(dotenv_path=env_path)

        # Configurações da voz
        self.language_code = language_code
        self.voice_name = voice_name
        self.gender = gender

        # Inicializa o cliente do Google TTS
        self.client = texttospeech.TextToSpeechClient()

    def narrate_text_with_ssml(self, ssml_text, output_file="output.mp3"):
        """
        Método para gerar o áudio a partir do texto SSML.

        :param ssml_text: Texto em SSML a ser sintetizado.
        :param output_file: Caminho do arquivo de saída (padrão: 'output.mp3').
        """
        # Configuração do texto a ser sintetizado usando SSML
        synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)

        # Configuração da voz
        voice = texttospeech.VoiceSelectionParams(
            language_code=self.language_code,  # Código do idioma
            name=self.voice_name,  # Nome da voz
            ssml_gender=getattr(texttospeech.SsmlVoiceGender, self.gender)  # Gênero da voz
        )

        # Configuração do arquivo de saída
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3  # Formato do áudio (MP3)
        )

        # Solicitação ao Google TTS
        response = self.client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        # Salvar o áudio no arquivo especificado
        with open("../tmp/" + output_file, "wb") as out:
            out.write(response.audio_content)
            print(f"Audio content written to file: {output_file}")


# Exemplo de uso da classe AudioGenerator

# Texto para narrar com SSML
ssml_text_to_narrate = """
<speak>
    In the vast expanse of the universe, humanity was always considered fragile.
    <break time="500ms"/>
    But... <break time="300ms"/> it was their resilience—<prosody pitch="+10%">forged on a chaotic world</prosody>—that made them <emphasis level="moderate">unique</emphasis> among the stars.
    <break time="700ms"/>
    Isn't it amazing? <prosody pitch="-10%">A species that overcame such odds...</prosody>
</speak>
"""

# Criar uma instância de AudioGenerator
audio_generator = AudioGenerator(language_code="en-US", voice_name="en-US-Neural2-I", gender="MALE")

# Chamar o método para gerar o áudio com SSML
audio_generator.narrate_text_with_ssml(ssml_text_to_narrate)
