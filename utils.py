import speech_recognition as sr

recognition = sr.Recognizer()

def get_text_from_audio(audio_path, language='id-ID'):
	 with sr.AudioFile(audio_path) as source:
			audio = recognition.record(source)
			try:
				return recognition.recognize_google(audio, language=language)
			except:
				return "Error"