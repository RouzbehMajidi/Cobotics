import cv2
import time
import numpy as np
import math
import serial
from serial.serialutil import SerialException
import os
import imutils
from objective import Objective
import sys
import matplotlib.pyplot as plt

distances = []
moving_avg_size = 15

DEMO_MODE = True

average_frame_rate = 5

#Constants
cm_per_pixel_area = (90.25/18448)*1.6
cm_per_pixel_cir = (38/490)*1.6

width = 480

morph = 7
low_canny = 50
canny = 200
extra_shift = 50 #px

matching_algorithm = cv2.TM_SQDIFF_NORMED

#Defaults
font = cv2.FONT_HERSHEY_SIMPLEX

#Load in training image(s)
template=cv2.imread('software/train/train_test_actual.jpg')
#cv2.imshow("", template)
template=cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
w, h = template.shape[::-1]

def transform_frame(approximation, x1, y1):
    #Shift Points
    #Top Left
    approximation[0][0][0] += x1-15
    approximation[0][0][1] += y1-15
    #Bottom Left
    approximation[1][0][0] += x1-15
    approximation[1][0][1] += y1+15
    #Bottom Right
    approximation[2][0][0] += x1+15
    approximation[2][0][1] += y1+15
    #Top Right
    approximation[3][0][0] += x1+15
    approximation[3][0][1] += y1-15

def running_mean(x, N):
    cumsum = np.cumsum(np.insert(x, 0, 0))
    return (cumsum[N:] - cumsum[:-N]) / float(N)

def getLatestDistance(ser):
    distance = 31
    global distances
    while ser.inWaiting() > 0:
        distance = int(float(ser.readline().strip()))
        distances.append(distance)

    if len(distances) > moving_avg_size:
        distances = distances[len(distances)-moving_avg_size:]
        distance = running_mean(distances,10)[-1]

    return distance

def find_objective():
    objective = None

    LOCK_TIME = 2.5*average_frame_rate #frames
    LOCK_TIMER = 0

    try:
        ser = serial.Serial('/dev/cu.usbserial-141230', 9600)
        # ser = serial.Serial('COM7', 9600)
    except Exception as err:
        ser = None
        print("Distance measurement not available: " + str(err))

    kernel = cv2.getStructuringElement( cv2.MORPH_RECT, ( morph, morph ) )

    video_capture = cv2.VideoCapture(0)

    dimensions_cm = 0

    #Main Processing Loop
    while not objective:
        #Get frame
        ret, image = video_capture.read()

        #Scale frame
        image = imutils.resize(image, width=width)

        #Flip and copy frame
        image = cv2.flip(image, 90)
        frame = np.copy(image)

        blurred = cv2.GaussianBlur(frame, (5,5), 0)

        gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, 1, 10, 120 )
        open = cv2.morphologyEx(gray, cv2.MORPH_OPEN, (5,5))


        #Apply matching algorithm (Normalized Squared Difference)
        res = cv2.matchTemplate(open,template,matching_algorithm)

        #Get bounds
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

        #Get box bounds
        top_left = min_loc
        bottom_right = (top_left[0] + w, top_left[1] + h)

        x1 = top_left[0]-int(w/2)
        y1 = top_left[1]-int(h/2)
        x2 = top_left[0]+int(1.5*w)
        y2 = top_left[1]+int(1.5*h)

        if x1 < 0:
            x1 = 0
        if y1 < 0:
            y1 = 0;

        if not(top_left[0] == 0 and top_left[1] == 0):
            cv2.rectangle(image,(x1, y1), (x2, y2), 255, 2)

        #Crop to scan area and copy to new variable
        scan_area = np.copy(frame[(y1):(y2), (x1):(x2)])

        #Filter
        blurred = cv2.GaussianBlur(scan_area, (5,5), 0)
        gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY )
        gray = cv2.bilateralFilter( gray, 1, 10, 120 )

        #Canny
        edges = cv2.Canny(gray, low_canny, canny )
        contour_image, contours, hierarchy = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE )

        if ser:
            try:
                distance = getLatestDistance(ser)
                # print("Distance: " + str(distance) + " cm")
                image = cv2.putText(image, "Distance: " + str(distance) + " cm", (0,240), font,0.5,(0,255,0),2)
            except ValueError as e:
                distance = None
                print(e)
                image = cv2.putText(image, "Distance measurement not available", (0,120), font,0.5,(0,0,255),2)
        else:
            distance = None

        if distance and not distance == -1:
            cm_per_pixel_area_norm = cm_per_pixel_area*1.04*(distance/31.0)
        else:
            cm_per_pixel_area_norm = cm_per_pixel_area


        for cont in contours:
            area = cv2.contourArea(cont)

            if area < 1000:
                continue

            arc_len = cv2.arcLength( cont, True )
            approximation = cv2.approxPolyDP( cont, 0.1 * arc_len, True )

            if ( len( approximation ) == 4 ):
                transform_frame(approximation, x1, y1)

                cv2.drawContours(image,[approximation],-1,( 111, 63, 228 ),2)

                x1_s = approximation[0][0][0]
                x2_s = approximation[2][0][0]
                y1_s = approximation[0][0][1]
                y2_s = approximation[2][0][1]

                center_x = int(x1_s + (x2_s-x1_s)/2)
                center_y = int(y1_s + (y2_s-y1_s)/2)

                center = (center_x-extra_shift,center_y)
                side1 = (center_x-extra_shift - 10,y2_s)
                side2 = (x1_s, center_y-extra_shift - 10)

                area_cm = round(area*cm_per_pixel_area_norm,2)
                dimensions_cm = round(math.sqrt(area*cm_per_pixel_area_norm),2)

                image = cv2.putText(image, str(area_cm) + " cm^2", center, font,0.5,(0,255,0),2)
                image = cv2.putText(image, str(dimensions_cm) + " cm", side1, font,0.5,(0,255,0),2)
                image = cv2.putText(image, str(dimensions_cm) + " cm", side2, font,0.5,(0,255,0),2)

                if(LOCK_TIMER >= LOCK_TIME):
                    image = cv2.putText(image, "Objective Locked", (0,260), font,0.5,(255,0,255),2)
                    print("\nObjective Locked")
                    print("Distance", distance, "cm")
                    objective = Objective(dimensions_cm,dimensions_cm,dimensions_cm)
                    break
                else:
                    image = cv2.putText(image, "Locking {0:.2f}".format((LOCK_TIMER/LOCK_TIME)*100) + "%", (0,260), font,0.5,(0,0,255),2)
                    sys.stdout.write('\r')
                    sys.stdout.write("Locking {0:.2f}".format((LOCK_TIMER/LOCK_TIME)*100) + "%")
                    sys.stdout.flush()
                    LOCK_TIMER += 1
            else:
                if LOCK_TIMER > 0:
                    LOCK_TIMER -= 1

        if(not DEMO_MODE):
            cv2.imshow("Gray",gray)
            cv2.imshow("Blurred",blurred)
            cv2.imshow("Canny",edges)
            cv2.imshow("Contours",contour_image)

        cv2.imshow("Camera Feed",image)

        if cv2.waitKey(27) & 0xFF == ord('q') :
            break

        if (cv2.waitKey(99) & 0xFF == ord('c')):
            cv2.imwrite( '../cache/object.jpg', frame )
            break

    video_capture.release()

    cv2.destroyAllWindows()

    cv2.imshow("Camera Feed",image)

    while True:
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    return objective

if __name__ == "__main__":
    find_objective()
