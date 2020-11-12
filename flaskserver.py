from flask import Flask,redirect,url_for,render_template,request,Response,session
import pandas as pd
import openpyxl
import io
import random
from flask_cors import CORS
import cv2
import numpy as np
import os
import time
import csv
import pyrebase
import datetime

config = {
    "apiKey": "AIzaSyC7anEGZjCoJpx0vi6MlxAi8STgDTsg-58",
    "authDomain": "examiner-12283.firebaseapp.com",
    "databaseURL": "https://examiner-12283.firebaseio.com",
    "projectId": "examiner-12283",
   "storageBucket": "examiner-12283.appspot.com",
    "messagingSenderId": "322728363476",
    "appId": "1:322728363476:web:08086079df4594ac954241",
    "measurementId": "G-PRH1THY3CB"
}

firebase = pyrebase.initialize_app(config)

db = firebase.database()
auth=firebase.auth()
storage = firebase.storage();




app = Flask(__name__)
CORS(app)



app.secret_key = b'_**$5#y7312L"F4Q8z\n\xec]/$*'

@app.route('/')
def start():
    return render_template("home.html")

@app.route('/student')
def student():
    return render_template("student.html")

@app.route('/login')
def login():
    return render_template("signin.html")

@app.route('/signup')
def signup():
    return render_template("signup.html")

@app.route('/download')
def download():
    return render_template("download_answer.html")

@app.route('/upload')
def upload():
    return render_template("question_upload.html")

@app.route('/answerscriptupload')
def answerscriptupload():
    return render_template("answerscriptupload.html")

@app.route('/pincheck',methods = ["POST"])
def pincheck():
    studentname = request.form.get("studentname");
    db.child("dept").child("student").push(studentname)
    pin = request.form.get("pin");
    dept =db.child("dept").child("teacher").get()
    for teacher in dept.each():
        if teacher.val()['pin']==pin:
            location = pin + "/" +"Questions"
            duration = teacher.val() ['duration']
            schedule = teacher.val() ['schedule']
            schedule = schedule.split('T')
            print(schedule)

	    
            
            link =storage.child(location).get_url(None)
            print(link)
            session['link'] = link
            session['schedule2'] = schedule[0]
            session['schedule1'] = schedule[1]
            session['pin'] = pin
            session['studentname'] = studentname
            starting = schedule[1].split(':')
            duration = duration.split(':')
            duration[0] = int(duration[0])
            duration[1] = int(duration[1])
            starting[0] = int(starting[0])
            starting[1] = int(starting[1])
            date = schedule[0].split('-')
	    
            reqhour = starting[0] + duration [0]
            reqhour = reqhour % 12
            print(reqhour)
            print(date)
            reqmin = starting[1] + duration [1]
            if(reqmin > 60):
                 reqhour = reqhour + 1
                 reqmin = reqmin % 60
            print(reqmin)
            starting[0] = starting[0] % 12
            print(starting[0])
            print(starting[1])         
            data = {'starting_hour':starting[0],'starting_minute':starting[1],'link':link,'year':date[0],'month':date[1],'date':date[2],'ending_hour':reqhour, 'ending_minute':reqmin}
            return render_template("camera.html",data=data)
    else :
            return render_template("student.html",t="Incorrect Pin")
    

@app.route('/signupvalues',methods = ["POST"])
def signupvalues():
    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    print(password)
    pin=0
    schedule="2020-10-04T17:11"
    duration=0
    data = {'name':name ,'email':email ,'pin':pin ,'schedule':schedule ,'duration':duration}
    db.child("dept").child("teacher").push(data)
    auth.create_user_with_email_and_password(email,password)
    return render_template("signin.html")

@app.route('/loginvalues',methods = ["POST"])
def loginvalues():
    email = request.form.get("email")
    password = request.form.get("password")
    session['Email'] = email
    try:
        auth.sign_in_with_email_and_password(email,password)
    except :
        return render_template("signin.html",t="Incorrect Email_id / password")
    return render_template("question_upload.html")

@app.route('/uploadquestionpaper',methods = ["GET","POST"])
def uploadquestionpaper():
    email =  session['Email']
    print(email)
    captcha = request.form.get("captcha")
    schedule = request.form.get("time")
    duration = request.form.get("duration")
    dept =db.child("dept").child("teacher").get()
    for teacher in dept.each():
        if teacher.val()['email']==email:
            db.child("dept").child("teacher").child(teacher.key()).update({'pin':captcha,'schedule':schedule,'duration':duration})
    file = request.files["file"]
    print(captcha)
    print(schedule)
    location = captcha + "/" +"Questions"
    storage.child(location).put(file)
    print(file.filename)
    link =storage.child(location).get_url(None)
    print(link)
    return render_template("question_upload.html",t="Successfully Uploaded")

@app.route('/uploadanswerscript',methods = ["GET","POST"])
def uploadanswerscript():
    file = request.files["file"]
    studentname = session['studentname']
    pin = session['pin'] 
    print(file.filename)
    location = pin + "/" +studentname
    storage.child(location).put(file)
    link =storage.child(location).get_url(None)
    name = pin + ".csv"
    if os.path.exists(name):
         append_write = 'a' # append if already exists
    else:
         append_write = 'w' # make a new file if not
    with open(name,append_write, newline='') as file:
        writer = csv.writer(file)
        writer.writerow([studentname,link])
    return render_template("answerscriptupload.html",t="Successfully uploaded")



@app.route('/downloadanswers' ,methods = ["POST"])
def teacherdownload():
    pin = request.form.get("captcha")
    filename = pin + ".csv"
    location1 = pin + "/" +"Answerscript.csv"
    storage.child(location1).put(filename)
    location2 = pin + "/" +"Examiner.csv"
    filename1 = pin + "_examiner.csv"
    storage.child(location2).put(filename1)
    link1 = storage.child(location1).get_url(None)
    link2 = storage.child(location2).get_url(None)
    data = {'link1':link1,'link2':link2}
    return render_template("download_answer.html" , link1=link1,link2=link2)

@app.route('/detects')
def detection():
    schedule1 = session['schedule1']
    schedule2 = session['schedule2']  
    pin = session['pin'] 
    studentname = session['studentname']
    session['studentname'] = studentname 
    link =session['link']
    session['pin'] = pin 
    now = datetime.datetime.now()
    now = now.strftime("%Y-%m-%d %H:%M:%S")
    data = {'time':schedule1,'link':link,'date':schedule2}
    #Loading YOLO
    net = cv2.dnn.readNet("yolov3.weights","yolov3.cfg")
    classes = []
    with open("coco.names","r") as f:
        classes = [line.strip() for line in f.readlines()]
    layer_names = net.getLayerNames()
    outputlayers = [layer_names[i[0]  - 1] for i in net.getUnconnectedOutLayers()]


    #process image
    #process image
    if os.path.exists(r"C:\Users\sanja\Downloads\image.png"):
        img = cv2.imread(r"C:\Users\sanja\Downloads\image.png")
    else:
        time.sleep(30) 
        img = cv2.imread(r"C:\Users\sanja\Downloads\image.png")
    height, width, channels = img.shape
    #Object detection blob is to extract feature from the image
    blob = cv2.dnn.blobFromImage(img, 0.00392, (640, 480), (0, 0, 0), True, crop=False)

    #this blob is passed to yolo
    net.setInput(blob)
    outs = net.forward(outputlayers)
    
    #showing info
    class_ids=[]
    confidences = []
    objects = []
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5: #0-1
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                x = int(center_x  - w/2)
                y = int(center_y  - h/2)
                #cv2.circle(img , (center_x,center_y), 10, (0,255,0), 2)
                objects.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    indexes = cv2.dnn.NMSBoxes(objects, confidences, 0.5, 0.4)#to reduce the multiple detection(noices)
    for i in range(len(objects)):
        if i in indexes:
            x, y, w, h = objects[i]
            lable = str(classes[class_ids[i]])
            name = pin +"_examiner"+ ".csv"
            if os.path.exists(name):
                 append_write = 'a' # append if already exists
            else:
                 append_write = 'w' # make a new file if not
            with open(name,append_write, newline='') as file:
                 writer = csv.writer(file)
                 writer.writerow([studentname,now,lable])
            print(lable)   

    #cv2.imshow("Downloads/image.png", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    if os.path.exists(r"C:\Users\sanja\Downloads\image.png"):
        os.remove(r"C:\Users\sanja\Downloads\image.png")
    
    time.sleep(10)
    return render_template("camera.html",data=data)
    

if __name__ == "__main__":
    app.run(port=8080, debug=True)
