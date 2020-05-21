import numpy as np
import cv2 
from matplotlib import pyplot as plt

# read image as gray scale
im=cv2.imread("C:\\Users\\S.Nivedhitham\\SNivedhitha\\blob\\IMAGE DATA\\Test\\testsample1originalImage_1.bmp")
# create a copy for backup
im1=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
# blurring the image
blur=cv2.GaussianBlur(src=im1,ksize=(3,3),sigmaX = 0)
# converting the image to binary by applying adaptive threshold, if grater than threshold(calculated by function itself) 255 else 0
t=cv2.adaptiveThreshold(blur,255,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY,99,1)
# some pre processing image
erode_fg = cv2.erode(t,np.ones((1,1),np.uint8), iterations = 1)
plt.imshow(erode_fg)
# finding contours, which is a boundary of connected pixels 
contours, hierarchy = cv2.findContours(erode_fg, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE,5)  
# iterarting over contours .reshape(-1,2)
for (i, c) in enumerate(contours):
     # just a condition
     if (cv2.contourArea(c) > 700 and cv2.contourArea(c) < 2600):
         (x, y, w, h) = cv2.boundingRect(c)
         # extracting sub image/pixels of above mentioned co-ordinates from original image
         subImg = im[y : y + h,x : x + w ]
         # writing each contour as a separate image into destination
         cv2.imwrite(filename = "C:\\Users\\S.Nivedhitham\\SNivedhitha\\blob\\IMAGE DATA\\Contours\\Fungus\\Fungus_Lentil"+str(i)+".jpg", img = subImg)
         
        
