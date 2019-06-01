import cv2
import face_recognition
import numpy as np
import datetime
import smtplib
from email.message import EmailMessage
import glob

# store array of all encodings in ram, using priority to rank for efficiency
# load all photos of known people into ram with their encodings

class Encoding:

    def __init__(self, encoding, rank, name):
        self.encoding = encoding
        self.rank = rank
        self.name = name

response_0 = " has entered your room at "
response_1 = "Unknown Person has entered your room at "
match = False
now = datetime.datetime.now()
trial = 15
encodings = []
email = now
temp1 = now
unknownEncodings = []
unknownCount = 0

def rotateImage(image, angle):
  image_center = tuple(np.array(image.shape[1::-1]) / 2)
  rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0)
  result = cv2.warpAffine(image, rot_mat, image.shape[1::-1], flags=cv2.INTER_LINEAR)
  return result


def rerank(index, ncodings):
    if index > 0 and ncodings[index-1].rank < ncodings[index].rank:
        temp = ncodings[index]
        while index > 0 and ncodings[index-1].rank < ncodings[index].rank:
            ncodings[index] = ncodings[index-1]
            index -= 1

        ncodings[index] = temp


for filename in glob.glob('faces/*.jpg'):
    print(filename)
    test = face_recognition.load_image_file(filename)
    obj = Encoding(face_recognition.face_encodings(test)[0], 0, filename[6:len(filename)-4])
    encodings.append(obj)


print("Done Warmup")
vc = cv2.VideoCapture(0)

if vc.isOpened():  # try to get the first frame
    rval, frame = vc.read()
else:
    rval = False


while rval:
    frame = rotateImage(frame, 90)
    now = datetime.datetime.now()
    name1 = ""

    if (now-temp1).microseconds >= 250000:
        msg = EmailMessage()
        temp1 = datetime.datetime.now()
        processed = True

        cv2.imwrite("person"+str(unknownCount)+".jpg", frame)

        unknown = face_recognition.load_image_file("person"+str(unknownCount)+".jpg")
        tempVar = face_recognition.face_encodings(unknown)
        
        if len(tempVar) > 0:
            unknownEncodings.append(tempVar[0])
            tempDate = datetime.datetime.now()

            while unknownCount < 24: #snap images for one second 
                rval, frame = vc.read()
                frame = rotateImage(frame, 90)
                cv2.imwrite("person"+str(unknownCount)+".jpg", frame)
                unknownCount += 1

            unknownCount -= 1

            while unknownCount > 0:  #load all snapped images in and find all faces
                unknown = face_recognition.load_image_file("person"+str(unknownCount)+".jpg")
                var1 = face_recognition.face_encodings(unknown)
                
                if len(var1) > 0:
                    unknownEncodings.append(var1[0])
              
                unknownCount -= 1

            print("Of 24 snapped frames: "+str(len(unknownEncodings))+" frames contained useful data")

            for z in range(len(unknownEncodings)):
                for x in range(min(len(encodings),trial)):
                    if face_recognition.compare_faces([encodings[x].encoding], unknownEncodings[z], .6)[0]:
                        encodings[x].rank += 1
                        print(encodings[x].name)
                        match = True
                        name1 = encodings[x].name
                        rerank(x, encodings)
                        break;
                if match:
                    print("Match found at Frame: ",z)
                    break

            if(now-email).total_seconds() > 120 and name1 != "Your Name":
                try:
                    s = smtplib.SMTP_SSL('smtp.gmail.com',465)
                    s.ehlo()
                    s.login('YourEmail', 'YourPassword')
                    response = "\n"

                    if match:
                        response += name1+response_0+now.strftime('%m/%d/%Y/%H')
                    else:
                        response += response_1+now.strftime('%m/%d/%Y/%H')

                    s.sendmail("mathius934@gmail.com", "mathius934@gmail.com",response)
                    s.quit()
                    email = datetime.datetime.now()

                except:
                    print("fail to connect to email client")
    
    unknownEncodings.clear()
    rval,frame = vc.read()
    match = False
