import numpy as np
import cv2
from scipy import fftpack
import matplotlib.pyplot as plt

tag_size = 160
pre_process_kernel = np.ones((7,7), np.uint8)

def get_mask(shape, r):
    #create a circular low pass filter or radius r 
    row, col, i = shape
    x_mid = int(row / 2)
    y_mid = int(col / 2)
    x, y = np.ogrid[:row, :col]
    # if x**2 + y**2 is less that r**2 (circle area formula) then make that index false
    mask_area = ((x - x_mid)**2) + ((y - y_mid)**2) <= r*r 
    mask = np.ones((row, col), np.uint8)
    # make all the false indices as 0 in the mask
    mask[mask_area] = 0
    return mask

def pre_process(image_prep):
    gray = cv2.cvtColor(image_prep, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray,(7,7),cv2.BORDER_DEFAULT)
    img_erosion = cv2.morphologyEx(blurred, cv2.MORPH_OPEN, pre_process_kernel)
    ret, thresh = cv2.threshold(np.uint8(img_erosion), 170, 255, cv2.THRESH_BINARY)

    fft_frame = fftpack.fft2(thresh, axes = (0, 1))
    fft_frame2 = fftpack.fftshift(fft_frame)
    low_pass_image = fft_frame2 * get_mask(image_prep.shape, 100)

    low_pass_image = fftpack.ifftshift(low_pass_image)
    low_pass_image = fftpack.ifft2(low_pass_image)
    low_pass_image = np.abs(low_pass_image)

    return low_pass_image

def getCorrectOrientation(my_tag):
    cnt = 0
    while my_tag[3, 3] != 255:
        if cnt > 3:
            return my_tag, -1
        my_tag = np.rot90(my_tag)
        cnt += 1
    # print("IN Correct Orientation")
    # print(my_tag)
    return my_tag, cnt

def rotate_tag(pts, count):
    tag_crn_list = list(pts.copy())
    for i in range (count):
        rot = tag_crn_list.pop(-1)
        tag_crn_list.insert(0, rot)
    return np.array(tag_crn_list) 

def tag_ID(tag):
    tag_ID = tag[1:3, 1:3]
    tag_ID_1d = tag_ID.flatten()
    tag_ID_1d[tag_ID_1d == 255] = 1
    # print(tag_ID_1d)
    tag_ID_num = int(tag_ID_1d[0] * pow(2,0) + tag_ID_1d[1] * pow(2,1)+ tag_ID_1d[3] * pow(2,2)+ tag_ID_1d[2] * pow(2,3))

    return tag_ID_num

def process_tag(tag_img, Rotate = None):
    full_tag = np.zeros((8, 8))
    resized_img = tag_img.copy()
    gray = cv2.cvtColor(resized_img, cv2.COLOR_BGR2GRAY)
    ret, resized_img = cv2.threshold(np.uint8(gray), 170, 255, cv2.THRESH_BINARY)
    section_size = int(tag_size / 8)
    for i in range(0, 8):
        for j in range(0, 8):
            section = resized_img[section_size*i:section_size*(i+1), section_size*j:section_size*(j+1)]
            val = np.average(section)
            if val > 200:
                full_tag[i][j] = 255
    main_tag = full_tag[2:6, 2:6]
    my_tag, count = getCorrectOrientation(main_tag)
    tagID = tag_ID(my_tag)
    if Rotate is not None:
        cnr_pts = rotate_tag(Rotate, count)
        return tagID, cnr_pts
    else:
        return tagID, None