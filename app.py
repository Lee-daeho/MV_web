from flask import Flask, render_template, request, send_from_directory, url_for, jsonify
import os
import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
from pinterest_crawler import PinterestCrawler
import openai
import time
import logging
########################TODO########################
'''
대화만들고 + 선택한 파일 어떻게 GPT로 올릴지 정하고 + aesthetic들 받아올때 어떤식으로 받아올지 다시정하고
'''
####################################################
app = Flask(__name__)
app.secret_key = 'daeho'

UPLOAD_FOLDER = 'uploads'
IMG_FOLDER = 'imgs'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['IMGS_FOLDER'] = IMG_FOLDER

aesthetic_dict = {}

assistant_id = 'asst_Pu75V8CkpsLdUab7JFpRUZjt'

client = openai.OpenAI(api_key=os.ggetenv['OPENAI_API_KEY'])

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'})
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'tmp.mp3')
        file.save(filepath)

        if not filepath.endswith('.mp3'):
            return jsonify({'message': "Please select mp3 file"})

        features = get_analysis(filepath)
        lyrics = "만나지 말잔 내 말 연락도 말란 내 말 너 진짜 그대로 할거니 그게 아닌데"
        title_singer = '다비치 - 8282'
        user_message = f"features : {features}, 제목 : {title_singer}, 가사 : {lyrics}"

        global thread_id
        thread = client.beta.threads.create()
        thread_id = thread.id

        message = client.beta.threads.messages.create(
        thread_id = thread.id,
        role="user",
        content=[
            {"type": "text", "text": user_message}
                ]        
        )

        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=assistant_id
        )

        while run.status == 'queued' or run.status == 'in_progress':
            time.sleep(0.5)

        if run.status == 'completed':
            messages = client.beta.threads.messages.list(
                thread_id=thread.id
            )
            # print(messages)
            # res_text = messages[0].content[0].text.value
            
            for res in messages:
                # print(f'{res.role.upper}')
                res_text = res.content[0].text.value
                print(f'{res.role.upper()}\n{res.content[0].text.value}\n')
                print('===================================================================')
                
                full_res = res.content[0].text.value.split('[')
                
                aes1 = full_res[1].split(']')[0]
                aes_res1 = full_res[2].split(']')[0]
                aes2 = full_res[3].split(']')[0]
                aes_res2 = full_res[4].split(']')[0]
                aes3 = full_res[5].split(']')[0]
                aes_res3 = full_res[6].split(']')[0]
                break
        #         print(aes1)
        #         print(aes_res1)
        #         print(aes2)
        #         print(aes_res2)
        #         print(aes3)
        #         print(aes_res3)
        #         break
        # else:
        #     print(run.status)

        aesthetic_reason = {aes1: aes_res1, aes2: aes_res2, aes3: aes_res3}
        set_aesthetic_dict(aesthetic_reason)

        return jsonify({'message': '파일이 성공적으로 업로드 되었습니다.', 'aes1':aes1, 'aes2':aes2, 'aes3':aes3})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/imgs/<path:filename>')
def imgs_file(filename):
    return send_from_directory(app.config['IMGS_FOLDER'], filename)

@app.route('/set_selected_images', methods=['POST'])
def set_selected_images():
    global selected_images
    selected_images = request.json.get('selected_images', [])
    print(f"Selected images: {selected_images}")
    return jsonify({"status": "Selected images saved successfully"})

@app.route('/select_img_togpt', methods=['POST'])
def img_to_gpt():
    global file_id
    global selected_images
    global cnt
    cnt = 0
    # if len(selected_images) > 1:
    #     selected_images = []
    #     return jsonify({"response": "하나의 이미지만 선택해주세요.", "images":"None"})
    # else:

    f = client.files.create(
        file=open(selected_images[-1].replace("%20",' ')[1:], "rb"),
        purpose="vision"
        )
    file_id = f.id

    return jsonify({"response": "업로드가 완료되었습니다. Assistant와 대화를 통해 prompt를 완성하세요.", "image":[selected_images[-1]]})

def fetch_images_and_return_response(aesthetic_key):
    image_folder = os.path.join(app.config['IMGS_FOLDER'], aesthetic_key)

    if not os.path.exists(image_folder):
        os.makedirs(image_folder)
        pc = PinterestCrawler(file_lengths=4, output_dir_path=image_folder)
        pc(keywords=[aesthetic_key])    ##################################aesthetic에 뒤에 object나 aesthetics나 core를 붙여서 이것저것 뽑아오기
        pc(keywords=[aesthetic_key+' objects'])
        pc(keywords=[aesthetic_key+' core aesthetic'])
    
    else:
        if len(os.listdir(image_folder)) == 0:
            pc = PinterestCrawler(output_dir_path=image_folder)
            pc(keywords=[aesthetic_key])

    images = [
        url_for('imgs_file', filename=os.path.join(aesthetic_key, file).replace('\\', '/')) 
        for file in os.listdir(image_folder) if file.endswith(('.png', '.jpg', '.jpeg'))
    ]
    
    return jsonify({'response_text': aesthetic_dict[aesthetic_key], 'images': images})

@app.route('/action1', methods=['POST'])
def action1():
    return fetch_images_and_return_response(list(aesthetic_dict.keys())[0])

@app.route('/action2', methods=['POST'])
def action2():
    return fetch_images_and_return_response(list(aesthetic_dict.keys())[1])

@app.route('/action3', methods=['POST'])
def action3():
    return fetch_images_and_return_response(list(aesthetic_dict.keys())[2])

@app.route('/process_message', methods=['POST'])
def process_message():
    user_message = request.json.get('message')
    
    if cnt == 0:
        message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=[
                {
                "type": "image_file",
                "image_file": {"file_id": file_id}}
            ]
        )        

        message = client.beta.threads.messages.create(
        thread_id = thread_id,
        role="assistant",
        content=[
            {"type":"text", "text": "해당 사진/그림의 어떤 점이 음악과 잘 어울린다고 생각하시나요?"}
        ])
        
    message = client.beta.threads.messages.create(
    thread_id = thread_id,
    role="user",
    content=[
        {"type":"text", "text": user_message}
    ])    

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

    while run.status == 'queued' or run.status == 'in_progress':
        time.sleep(0.5)

    if run.status == 'completed':
        messages = client.beta.threads.messages.list(
            thread_id=thread_id
        )
        # print(messages)
        # res_text = messages[0].content[0].text.value
        
        for res in messages:
            # print(f'{res.role.upper}')
            res_text = res.content[0].text.value
            break

    response_message = res_text
    return jsonify({'response': response_message})

@app.route('/upload_file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'response': '파일이 없습니다.'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'response': '파일이 선택되지 않았습니다.'})

    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        response_message = f"{file.filename} 파일이 성공적으로 업로드 되었습니다."
        return jsonify({'message': response_message})

def set_aesthetic_dict(res_dict):
    global aesthetic_dict
    aesthetic_dict = res_dict

def get_analysis(file):
    y, sr = librosa.load(file, sr=None)
    n_fft = 2048
    hop_length = 512
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=5, n_fft=n_fft, hop_length=hop_length)
    
    plt.figure(figsize=(10, 4))
    librosa.display.specshow(mfccs, sr=sr, hop_length=hop_length, x_axis='time')
    plt.colorbar()
    plt.title('MFCC')
    plt.tight_layout()
    plt.savefig(os.path.join(app.config['UPLOAD_FOLDER'], 'tmp.png'))

    features = {
        'Zero Crossing Rate': librosa.feature.zero_crossing_rate(y).mean(),
        'Spectral Centroid': librosa.feature.spectral_centroid(y=y, sr=sr).mean(),
        'Spectral Rolloff': librosa.feature.spectral_rolloff(y=y, sr=sr).mean(),
        'Chroma Feature': librosa.feature.chroma_stft(y=y, sr=sr).mean(),
        'Spectral Bandwidth': librosa.feature.spectral_bandwidth(y=y, sr=sr).mean(),
        'Spectral Contrast': librosa.feature.spectral_contrast(y=y, sr=sr).mean(),
        'Tonnetz': librosa.feature.tonnetz(y=y, sr=sr).mean(),
        'Tempo': librosa.beat.beat_track(y=y, sr=sr)[0],
        'RMS Energy': librosa.feature.rms(y=y).mean(),
        'MFCC': mfccs.mean(axis=1)
    }

    return features

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    if not os.path.exists(app.config['IMGS_FOLDER']):
        os.makedirs(app.config['IMGS_FOLDER'])
    app.run(debug=True)

        # message = client.beta.threads.messages.create(
        # thread_id = thread.id,
        # role="user",
        # content=[
        #     {"type": "text", "text": user_message}
        #         ]        
        # )

        # run = client.beta.threads.runs.create_and_poll(
        #     thread_id=thread.id,
        #     assistant_id=assistant_id
        # )

        # while run.status == 'queued' or run.status == 'in_progress':
        #     time.sleep(0.5)

        # if run.status == 'completed':
        #     messages = client.beta.threads.messages.list(
        #         thread_id=thread.id
        #     )
        #     # print(messages)
        #     # res_text = messages[0].content[0].text.value
            
        #     for res in messages:
        #         # print(f'{res.role.upper}')
        #         res_text = res.content[0].text.value
        #         print(f'{res.role.upper()}\n{res.content[0].text.value}\n')
        #         print('===================================================================')
                
        #         full_res = res.content[0].text.value.split('[')
                
        #         aes1 = full_res[1].split(']')[0]
        #         aes_res1 = full_res[2].split(']')[0]
        #         aes2 = full_res[3].split(']')[0]
        #         aes_res2 = full_res[4].split(']')[0]
        #         aes3 = full_res[5].split(']')[0]
        #         aes_res3 = full_res[6].split(']')[0]
        #         print(aes1)
        #         print(aes_res1)
        #         print(aes2)
        #         print(aes_res2)
        #         print(aes3)
        #         print(aes_res3)

        #         break
        # else:
        #     print(run.status)