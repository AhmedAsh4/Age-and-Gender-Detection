import cv2
import torch
import torchvision.transforms as T
from mtcnn import MTCNN
from PIL import Image
from collections import Counter
import psycopg2
from datetime import datetime

def readConfig():
    with open('config.txt', 'r') as f:
        vars=f.read().strip().split()
    dbname = vars[2]
    user = vars[5]
    password = vars[8]
    host = vars[11]
    port = vars[14]
    return dbname,user,password,host,port

dbname,user,password,host,port=readConfig()

model = torch.load('best.torchscript')
ageModel = torch.load('bestAge.torchscript')

transform = T.Compose([
    T.Resize((224, 224)),
    T.ToTensor(),
])

detector = MTCNN()

def insert_to_database(statement=None,queries=None):
    try:
        connection = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port )
        
        cursor = connection.cursor()

        if queries:
            for query in queries:
                cursor.execute(query)
        elif statement:
            cursor.execute(statement)

        cursor.close()
        connection.commit()
        connection.close()
        print("Commit Successful")

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL:", error)

def predict_gender(face):
    gender_prediction = transform(face).unsqueeze(0) 
    output = model(gender_prediction)
    gender_prediction = output.argmax(dim=1)
    return gender_prediction,torch.max(output).item()

def predict_age(face):
    ages = {0: '0~2', 1: '10~19', 2: '20~29', 3: '3~9', 4: '30~39', 5: '40~49', 6: '50~59', 7: '60~69', 8: '70+'}
    age_prediction = transform(face).unsqueeze(0) 
    output = ageModel(age_prediction)
    _, age_prediction_index = output.max(dim=1) 
    age_prediction = ages[age_prediction_index.item()] 
    return age_prediction,torch.max(output).item()

def predictions(image,x,y,w,h):
    cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)
    face_roi = image[y:y+h, x:x+w]
    pil_image = Image.fromarray(face_roi)
    gender_prediction,gender_confidence = predict_gender(pil_image)
    age_prediction,age_confidence = predict_age(pil_image)

    return gender_prediction,gender_confidence,age_prediction,age_confidence,image

def predict_image(filepath):
    image = cv2.imread(filepath)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = detector.detect_faces(image)

    predictionsGender=[]
    predictionsAge=[]
    queries = []

    for result in results:
        x, y, w, h = result['box']
        confidence = result['confidence']

        if confidence < 0.9:
            continue

        gender_prediction,gender_confidence,age_prediction,age_confidence,image = predictions(image,x,y,w,h)
        prediction_text = ("F" if gender_prediction > 0 else "M")
        predictionsGender.append(prediction_text)
        predictionsAge.append(age_prediction)

        queries.append(f"""SELECT InsertData('ahmed','uploaded','{filepath}',
                                '[{x},{y},{x+w},{y+h}]','{prediction_text}',{gender_confidence},
                                '{age_prediction}',{age_confidence});""")

        cv2.putText(image, prediction_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    max_width = 900
    max_height = 720

    height, width, _ = image.shape
    aspect_ratio = width / height
    if width > max_width or height > max_height:
        if aspect_ratio > 1:  # Landscape orientation
            target_width = max_width
            target_height = int(target_width / aspect_ratio)
        else:  # Portrait orientation
            target_height = max_height
            target_width = int(target_height * aspect_ratio)
        image = cv2.resize(image, (target_width, target_height))
        

    base_y = image.shape[0] - 30
    for i, (category, count) in enumerate(Counter(predictionsGender).items()):
        count_text =  f"{category}:{count}"
        text_x = 5 
        text_y = base_y - (i * 40)
        cv2.putText(image, count_text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    base_y = image.shape[0] - 30
    for i, (category, count) in enumerate(Counter(predictionsAge).items()):
        count_text =  f"{category}:{count}"
        text_size = cv2.getTextSize(count_text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
        text_x = image.shape[1] - text_size[0] - 5
        text_y = base_y - (i * 40)
        cv2.putText(image, count_text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    insert_to_database(queries=queries)

    return Image.fromarray(image)

def predict_camera(frame):
    if not hasattr(predict_camera, 'frame_counter'):
        predict_camera.frame_counter = 0
    
    predict_camera.frame_counter += 1

    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    face_locations = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    for (x, y, w, h) in face_locations:
        gender_prediction, gender_confidence, age_prediction, age_confidence, frame = predictions(frame, x, y, w, h)
        gender_pred = "F" if gender_prediction > 0 else "M"
        prediction_text = f"{gender_pred} Age: {age_prediction}"

        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(frame, prediction_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        if predict_camera.frame_counter % 30 == 0:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
            insert_to_database(statement=f"""SELECT InsertData('ahmed','Camera','Camera:{current_time}',
                                    '[{x},{y},{x+w},{y+h}]','{gender_pred}',{gender_confidence},
                                    '{age_prediction}',{age_confidence});""")
    if predict_camera.frame_counter == 30:
        predict_camera.frame_counter = 0

    return frame
