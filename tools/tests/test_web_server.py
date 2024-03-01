from flask import Flask, request, jsonify,send_file
import os
import base64

app = Flask(__name__)

UPLOAD_FOLDER = 'temp'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/process_all', methods=['POST'])
def handle_all():
    # 获取文本数据
    text_data = request.form.get('text')
    character = request.form.get('character')
    chat_status = request.form.get('chat_status')
    print("text_data:", text_data)
    print("character:", character)
    print("chat_status:", chat_status)

    # 保存并处理语音文件
    audio_file = request.files.get('audio')
    if audio_file:
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_file.filename)
        audio_file.save(audio_path)
        # 这里可以加入语音处理逻辑
        # processed_audio_path = os.path.join(app.config['UPLOAD_FOLDER'], 'processed_' + audio_file.filename)
        # send_file(processed_audio_path, as_attachment=True)
        with open(audio_path, 'rb') as audio_file:
            audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')

    # 保存并处理图像文件
    image_file = request.files.get('image')
    if image_file:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_file.filename)
        image_file.save(image_path)
        # 这里可以加入图像处理逻辑

    # 合并处理结果
    # 此处可以添加将文本、语音和图像数据合并处理的逻辑
    # combined_result = f"Processed text: {text_data}, audio: {audio_path if audio_file else 'None'}, audio_base64: {audio_base64 if audio_file else 'None'}, image: {image_path if image_file else 'None'}"

    # 返回处理后的数据
    # return jsonify({'text': text_data, 'audio': audio_path if audio_file else 'None', 'audio_base64': audio_base64 if audio_file else 'None', 'image': image_path if image_file else 'None'})
    return jsonify({'text': "B", 'audio_base64': audio_base64, 'audio': {'sample_rate': 22050, 'CHUNK': 4096, 'FORMAT': 16, 'CHANNELS': 1}})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
