import cv2
import numpy as np
import time 

cap = cv2.VideoCapture('./Video_Dominosteine.mp4')


def distance(a, b):
    # square_root ((xa-xb)^2 + (ya-yb)^2)
    return(np.sqrt((a[0]-b[0])**2+(a[1]-b[1])**2))


def change_min_rad(*args):
    global min_radius 
    min_radius = args[0]
def change_max_rad(*args):
    global max_radius
    max_radius = args[0]


def find_the_domino(filterX):
    ret, thresh0 = cv2.threshold(
        filterX, 0, 255, cv2.THRESH_OTSU )
    ret, thresh1 = cv2.threshold(
        filterX, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY)
    rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
    dilation = cv2.dilate(thresh1, rect_kernel, iterations=3)
    cntrs, _ = cv2.findContours(
        dilation, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    #draw a rectangle around the domino
    if len(cntrs) == 1:
        x, y, w, h = cv2.boundingRect(cntrs[0])
        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 255, 255), 2)
        return True
    else : 
        return False


tfreeze = 0.5
t = time.time()
p_time = t
t_last_check = t - 2
last_check_1 = (0, 0)
last_check_2 = (0, 0)
last_written = (0, 0)

min_radius = 10
max_radius = 20
max_points = 12
play = True


window_name = 'program'
 
with open('output.txt', 'w') as f:

    #create trackbars
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
    cv2.createTrackbar('min_radius', window_name, min_radius, 50, change_min_rad)
    cv2.createTrackbar('max_radius', window_name,max_radius, 100, change_max_rad)

    #analyse video 
    while cap.isOpened():
        if play : 
            ret, frame = cap.read()
            #preprocessing the image
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) 
            gaussian_blur = cv2.GaussianBlur(gray, (5, 5), 0)
            gradient = cv2.Sobel(gaussian_blur, cv2.CV_8U, 1, 0, ksize=3)
            
            ret, umbral = cv2.threshold(gradient, 100,
                                        150, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            morphology = cv2.morphologyEx(
                umbral, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
            
            contours, _ = cv2.findContours(
                morphology, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)



            #finding the domino
            only_domino_in_frame = find_the_domino(gaussian_blur)

            
        
        centers = [] # center of circles
        bbox = None # bounding box of the middle line
        h_min = 9999
        red = 10  #intetially wrong value to filter out unexpected results 

        if len(contours) < 30 : #this line is expendable but used to speed up the processess
            for i in contours:
                test = True  #verifying for duplicate circles 
                #  outer circle of the contour
                (x, y), radius = cv2.minEnclosingCircle(i)
                center = (round(x), round(y)) #location of the center in pixels
                radius = round(radius)

                #verifying if it's a circle  
                if radius >= min_radius and radius <= max_radius:

                    if len(centers) == 0:
                        centers.append(center)
                    else:
                        for i in centers:
                            d = distance(i, (x, y))
                            if d < 8:  # a duplicate circle
                                test = False
                        if test:
                            centers.append(center)
                #if it's a line
                else:
                    x, y, w, h = cv2.boundingRect(i)
                    if h < h_min :
                        h_min = h
                        bbox = [x, y, w, h] #middle line coordinates

        #if the frame is not empty        
        if len(centers) < max_points  :
            # middle line exists 
            if bbox != None:

                x, y, w, h = bbox[0], bbox[1], bbox[2], bbox[3]
                p1 = (x, y+h)
                p2 = (x+w, y)
                cv2.line(frame, p1, p2, (255, 255, 0), 2)  # draw middle line


                # linear equation:  fx = ax + b
                a = -h/w   #the slope become a= h/w for the different orientation of the middle line
                b = (y+h) - a * x  
                fx = np.poly1d([a, b])

                #determining which side of the domino the circles belong to 
                red = 0
                green = 0
                
                for i in centers:
                    cx, cy = i[0], i[1]
                    img_cx = fx(cx) 
                    if cy > img_cx:
                        cv2.circle(frame, (cx, cy), 10, (0, 255, 0), 2)
                        green += 1
                    else:
                        cv2.circle(frame, (cx, cy), 12, (0, 0, 255), 2)
                        red += 1
                #displaying the circle count
                cv2.putText(
                    frame, f'red = {red}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2)
                cv2.putText(
                    frame, f'green = {green}', (50, 100),cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2)


        # write inside the output file
        t = time.time()
        fps = round(1/(t-p_time))
        cv2.putText(frame,f'fps = {fps}' , (800,50),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255))
        p_time = t
        if t >= (t_last_check+tfreeze):
            t_last_check = t
            if red <= 6 and red > 0 and green > 0 and green <= 6 :
                if (red, green) == last_check_1:
                    if (last_check_1 != last_check_2):
                        if (red, green) != last_written:
                            last_written = (red, green)
                            f.write(f'{last_check_1}\n')
                    else:
                        last_check_2 = last_check_1
                        last_check_1 = (red, green)
                else:
                    last_check_2 = last_check_1
                    last_check_1 = (red, green)
        

        
        #show image 
        cv2.imshow(window_name, frame)

        # hotkeys
        key = cv2.waitKey(5)
        if key == ord('q'): #press "q" to quit program
            break
        elif key == ord('p'):  #press "p" to pause/play video 
            play = not play
            
    
    cap.release()
    cv2.destroyAllWindows()
