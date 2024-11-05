from flask import Flask, render_template, request, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import load_img, img_to_array
import numpy as np
import io
from io import BytesIO
import base64
from PIL import Image
import os
import uuid

# Initialize Flask app
app = Flask(__name__, template_folder='./template')

#config DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:K_AE5A((m%*C?!r>)4w$sGPo$Bq$@database-app.ctekoqmq854p.us-east-1.rds.amazonaws.com:3306/meat_db'
UPLOAD_FOLDER = './picture'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
db = SQLAlchemy(app)

#create schma
class meat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(30), nullable=False)
    path = db.Column(db.String(100), nullable=False)

    #reply path function
    def __repr__(self):
        return '<Path %r>' %self.label


# Function to save base64 image to file
def save_base64_image(base64_string, folder, filename):
    image_data = base64.b64decode(base64_string.split(',')[1])
    img = Image.open(io.BytesIO(image_data))
    img.save(os.path.join(folder, filename))
    return os.path.join(folder, filename)

# Load your pre-trained model
model_path = "./meat_freshness_model_add_layer.h5"
try:
    model = load_model(model_path)
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/classify', methods=['POST'])
def classify():
    # Validate file or captured image input
    if 'file' not in request.files and 'captured_image' not in request.form:
        return render_template('index.html', error="No file or image captured")

    img = None

    # Check if the image was uploaded via file input
    if 'file' in request.files and request.files['file'].filename != '':
        file = request.files['file']
        try:
            img = Image.open(file.stream)  # Load image from the uploaded file stream
        except Exception as e:
            return render_template('index.html', error=f"Error reading uploaded image: {str(e)}")
    
    # Check if the image was captured via webcam
    elif 'captured_image' in request.form and request.form['captured_image'] != '':
        captured_image = request.form['captured_image']
        try:
            header, encoded = captured_image.split(',', 1)
            img_data = io.BytesIO(base64.b64decode(encoded))  # Decode the base64 image
            img = Image.open(img_data)
        except Exception as e:
            return render_template('index.html', error=f"Error processing captured image: {str(e)}")
    
    if img is None:
        return render_template('index.html', error="No valid image found")

    # Convert image to RGB if it has an alpha channel (RGBA)
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    

    # Resize image to the required input size for the model (128x128)
    img = img.resize((128, 128))
    img_array = img_to_array(img)  # Convert image to numpy array
    img_array = img_array / 255.0  # Normalize the image
    img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension

    # Make prediction using the model
    predictions = model.predict(img_array)
    class_labels = ['Spoiled', 'Half-fresh', 'Fresh']  # Adjust labels based on your model's output
    result = class_labels[np.argmax(predictions)]  #กำหนดชื่อคลาสที่คุณต้องการใช้ ไม่ต้องตรงกับใน model ก็ได้ เเต่วางใน index array เดียวกัน

    # Convert the image to a base64 string for displaying it in the result template
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    img_data_url = f"data:image/png;base64,{img_str}"

    return render_template('result.html', result=result, img_data=img_data_url)

@app.route('/submit_choice', methods=['POST'])
def submit_choice():
    user_choice = request.form.get('choice')
    img_data = request.form.get('img_data_forward')

    print(f"img_data : {img_data}")

    print(f"User Choice: {user_choice}")
    print(f"Image Data: {img_data}")

    filename = f"{uuid.uuid4().hex}.png"  # Generate unique filename

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])  # Create folder if it doesn't exist

    # Check if the image was uploaded via file input
    if img_data and img_data.startswith("data:image/png;base64,"):  # Captured image
        try:
            save_base64_image(img_data, UPLOAD_FOLDER, filename)
            upload = meat(path=filename, label=user_choice)
            db.session.add(upload)
            db.session.commit()
        except Exception as e:
            print(f"Error saving base64 image: {e}")

    elif img_data and not img_data.startswith("data:image/png;base64,"):  # Uploaded file
        upload = meat(path=filename, label=user_choice)
        db.session.add(upload)
        db.session.commit()
        try:
            img_data.save(filename)  # Save the uploaded file directly
        except Exception as e:
            print(f"Error saving uploaded file: {e}")
        else:
            print("No valid file found.")


    return render_template('index.html')

@app.route('/meatnu')
def meatnu():
    return render_template('meatnu.html')

@app.route('/deals')
def deals():
    return render_template('deals.html')

@app.route('/half')
def half():
    return render_template('half.html')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True, use_reloader=False)
