#!/usr/bin/python3

import numpy as np
import cv2
import cv2.aruco as aruco
import time
import math
from PIL import Image, ImageTk

class Vision:
    def __init__(self):
        self.cap = cv2.VideoCapture(2)
        # self.cap.set(cv2.CAP_PROP_FPS, 60)
        # self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1024)
        # self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 768)
        self.width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.markerL = dict(area=0, c=None, limit=3100)
        self.markerR = dict(area=0, c=None, limit=3100)
        self.par1 = 70
        self.frame = None

    def setMarker(self, mid, area, center):
        if mid == 3:
            self.markerL["area"] = area
            self.markerL["c"] = center
        if mid == 4:
            self.markerR["area"] = area
            self.markerR["c"] = center
        # print("{} {}".format(self.markerR["area"], self.markerL["area"]))

    def getTilt(self):
        tilt = 1.0*self.markerL["area"]/self.markerR["area"]
        print("tilt: {} {} {}".format(tilt, self.markerL["area"], self.markerR["area"]))
        return tilt

    @property
    def isTilted(self):
        return abs(self.getTilt() - 1) > 0.05
    
    def processFrame(self):
        ret, frame = self.cap.read()

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        aruco_dict = aruco.Dictionary_get(aruco.DICT_4X4_100)
        arucoParameters = aruco.DetectorParameters_create()

        corners, ids, rejectedImgPoints = aruco.detectMarkers(
            gray, aruco_dict, parameters=arucoParameters)
        
        if len(corners) < 2:
            return 0
        
        # if corners[0][0][0][0] > corners[1][0][0][0]:
        #     temp = corners[0]
        #     corners[0] = corners[1]
        #     corners[1] = temp

        M = cv2.moments(corners[0])
        c1x = int(M["m10"] / M["m00"])
        c1y = int(M["m01"] / M["m00"])
        area1 = cv2.contourArea(corners[0])
        mid1 = ids[0][0]
        self.setMarker(mid1, area1, (c1x,c1y))

        M = cv2.moments(corners[1])
        c2x = int(M["m10"] / M["m00"])
        c2y = int(M["m01"] / M["m00"])
        area2 = cv2.contourArea(corners[1])
        mid2 = ids[1][0]
        self.setMarker(mid2, area2, (c2x,c2y))
        
        x1 = tuple(corners[0][0][2])
        x2 = tuple(corners[1][0][1])
        x3 = tuple(corners[1][0][0])
        x4 = tuple(corners[0][0][3])
        cv2.circle(frame, tuple(x1), 5, (0,0,255), 1)
        cv2.circle(frame, tuple(x2), 5, (0,255,0), 1)
        cv2.circle(frame, tuple(x3), 5, (255,0,0), 1)
        cv2.circle(frame, tuple(x4), 5, (0,255,255), 1)

        points = np.array([[x1,x2,x3,x4]], dtype='int32')
        height = frame.shape[0]
        width = frame.shape[1]
        mask = np.zeros((height, width), dtype=np.uint8)
        cv2.fillPoly(mask, points, (255))

        res = cv2.bitwise_and(frame, frame, mask=mask)
        res = cv2.polylines(res, [points], isClosed=False, color=(255, 255, 255), thickness=4) 

        x,y,w,h = cv2.boundingRect(points) # returns (x,y,w,h) of the rect
        cropped = res[y:y+h, x:x+w]

        gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
        im_bw = cv2.threshold(gray, self.par1, 255, cv2.THRESH_BINARY)[1]
        contours, hierarchy = cv2.findContours(im_bw, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE) 
        
        contours = list(filter(lambda c: cv2.contourArea(c) >  500, contours))
        contours = list(filter(lambda c: cv2.contourArea(c) < 30000, contours))

        border = 30
        offsetX = int(x1[0])
        offsetY = int(x1[1]-2*border)
        cv2.drawContours(frame, contours, -1, (255, 255, 0), 3, offset=(offsetX, offsetY))
        
        # TODO: add condition here
        frame = aruco.drawDetectedMarkers(frame, corners, ids)
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # to RGB
        image = Image.fromarray(image) # to PIL format
        image = ImageTk.PhotoImage(image) # to ImageTk format
        self.image = image

        if contours:
            (x,y), radius = cv2.minEnclosingCircle(contours[0])

            bx,by = (int(x)+offsetX, int(y)+offsetY)
            x1,y1 = self.markerL["c"]
            x2,y2 = self.markerR["c"]
            d1 = math.sqrt((bx - x1)**2 + (by - y1)**2)
            d2 = math.sqrt((bx - x2)**2 + (by - y2)**2)
            self.pos = d1/(d1+d2)
            print("pos {}".format(self.pos))
            # cv2.circle(frame, (bx,by), 5, (255,0,255), 2)
            return 2

        
        return 1

    def close(self):
        self.cap.release()

def returnCameraIndexes():
    # checks the first 10 indexes.
    index = 0
    arr = []
    i = 10
    while i > 0:
        cap = cv2.VideoCapture(index)
        if cap.read()[0]:
            arr.append(index)
            cap.release()
        index += 1
        i -= 1
    return arr


if __name__=="__main__":  
    st = Vision()
    try:
        st.run()
    except KeyboardInterrupt:
        print("exiting")
    st.cleanup()


