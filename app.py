from flask import Flask, render_template, jsonify, request
from datetime import datetime
from openai import OpenAI
import os
import json
from utils import get_text_from_audio

app = Flask(__name__)

API_KEY = open("API_KEY", "r").read()

REMOVE_AUDIO_FILE = True

client = OpenAI(
    # This is the default and can be omitted
    api_key=API_KEY,
)


# create folder to save audio file if not exists
folder = "audio"
if not os.path.exists(folder):
	os.makedirs(folder)



@app.route("/")
def home():
	 return render_template('index.html')


@app.route("/upload-file", methods=["POST"])
def upload_file():

	# get audio file from the form and also all the data
	file = request.files.get("audio")
	language = request.form.get("language")
	responseData = request.form.get("data")
	userLang = request.form.get("user_lang")

	# if no file uploaded return error
	if not file:
		return jsonify({"error": "No file uploaded"})

	# define path for the file
	currDate = datetime.now().strftime("%Y%m%d%H%M%S")
	file_path = f"{folder}/{currDate}.wav"
	file_path_mmpeg = os.path.join(folder, "ffmpeg-" + currDate + ".wav")

	# save file from the form / recording to the folder
	with open(file_path, "wb") as f:
		f.write(file.read())

	#convert audio to 16k mono channel wav for better recognition
	os.system(f"ffmpeg -i {file_path} -acodec pcm_s16le -ac 1 -ar 16000 {file_path_mmpeg}")

	# get text from audio
	text = get_text_from_audio(file_path_mmpeg, language=userLang)
	print(text)

	#remove audio files because we already have the text
	if REMOVE_AUDIO_FILE:
		os.remove(file_path)
		os.remove(file_path_mmpeg)

	# if error from audio recognition return error
	if text == "Error":
		return jsonify({"error": "Error reading audio file"})
	
	# json response data
	jsonData = json.loads(responseData)

	# initial messages data, and role system for the first message so it tell openai what to do
	messages = [
		{
			"role": "system", "content": "You have to reply to the question based on user input (LANGUAGE)"
		}
	]

	# loop through the json data and append it to the messages
	for jsData in jsonData:
		messages.append(jsData)

	# append the user input text based on the recording to the messages
	messages.append(
		{
			"role": "user", "content": text + f" ({language})"
		}
	)

	response = client.chat.completions.create(
		model="gpt-3.5-turbo",
		messages=messages,
		max_tokens=4000
	)

	# append the response from openai to the messages for context on the following conversation later that read from responseData
	messages.append({
		"role": "assistant", "content": response.choices[0].message.content
	})

	#pop the first index of the messages because it's the system message, user doesn't need to know about it
	messages.pop(0)

	# return the messages
	return jsonify({"error": False, "message": "File uploaded successfully", "data": messages})


if __name__ == "__main__":
	app.run(debug=True)