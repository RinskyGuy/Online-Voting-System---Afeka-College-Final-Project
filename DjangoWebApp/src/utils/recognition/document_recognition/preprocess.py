import cv2
import numpy as np
from utils.recognition.document_recognition.documents import ID, PASSPORT
from utils.debug import DebugToFile, DebugToPlt
from utils.recognition.face_recognition.face_detector import detector
import os

HEIGHT = 1024
WIDTH = int(1.6*HEIGHT)

class ImageManipulation:    
    def noise_removal(self, image, dilation_kernel=2, dilation_iterations=1, 
                      erosion_kernel=2, erosion_iterations=1, 
                      morph_kernel=2, blur_kernel=3):
        image = self.dilation(image, kernel=dilation_kernel, iterations=dilation_iterations)
        image = self.erosion(image, kernel=erosion_kernel, iterations=erosion_iterations)
        image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, np.ones((morph_kernel, morph_kernel), np.uint8))
        image = cv2.medianBlur(image, blur_kernel)
        return image
    
    def brightness_contrast(self, image, brightness, contrast):
        image = np.int16(image)
        image = image * (contrast/127+1) - contrast + brightness
        image = np.clip(image, 0, 255)
        image = np.uint8(image)
        return image
    
    def dilation(self, image, kernel=2, iterations=1):
        if isinstance(kernel, int):
            kernel = np.ones((kernel,kernel), np.uint8)
            
        image = cv2.bitwise_not(image) # inverse
        image = cv2.dilate(image, kernel, iterations=iterations)
        image = cv2.bitwise_not(image) # inverse back
        return image
    
    def erosion(self, image, kernel=2, iterations=1):
        if isinstance(kernel, int):
            kernel = np.ones((kernel,kernel), np.uint8)
            
        image = cv2.bitwise_not(image) # inverse
        image = cv2.erode(image, kernel, iterations=iterations)
        image = cv2.bitwise_not(image) # inverse back
        return image

    def binarization(self, image, threshold=10, inverse=True, apply_brightness_contrast=True, apply_noise_removal=True):  
        assert len(image.shape) > 2, "Input should be color image."
        image = self.__get_gray(image, apply_brightness_contrast, apply_noise_removal)
        
        if inverse:
            return cv2.threshold(image, threshold, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        else:
            return cv2.threshold(image, threshold, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    
    # Rotate the image around its center
    def image_rotation(self, image, angle, prefix=''):
        h, w = image.shape[:2] # image shape has 3 dimensions
        image_center = (w // 2, h // 2) # getRotationMatrix2D needs coordinates in reverse order (width, height) compared to shape
        
        rotation_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0)
        
        # rotation calculates the cos and sin, taking absolutes of those.
        abs_cos = abs(rotation_mat[0,0]) 
        abs_sin = abs(rotation_mat[0,1])

        # find the new width and height bounds
        bound_w = int(h * abs_sin + w * abs_cos)
        bound_h = int(h * abs_cos + w * abs_sin)

        # subtract old image center (bringing image back to origo) and adding the new image center coordinates
        rotation_mat[0, 2] += bound_w/2 - image_center[0]
        rotation_mat[1, 2] += bound_h/2 - image_center[1]

        # rotate image with the new bounds and translated rotation matrix
        image = cv2.warpAffine(image, rotation_mat, (bound_w, bound_h))
        
        if hasattr(self, 'debug'):
            self.debug.debug_single_img(image, prefix+'rotated')
                
        return image    
            
    def __get_single_channel_gray(self, image, channel):
        single_channel = image.copy()
        if channel.startswith('b'):
            single_channel[:, :, 1] = 0
            single_channel[:, :, 2] = 0
        elif channel.startswith('g'):
            single_channel[:, :, 0] = 0
            single_channel[:, :, 2] = 0
        elif channel.startswith('r'):
            single_channel[:, :, 0] = 0
            single_channel[:, :, 1] = 0
        return cv2.cvtColor(single_channel, cv2.COLOR_BGR2GRAY)
    
    def __get_gray(self, image, apply_brightness_contrast=True, apply_noise_removal=True, prefix=''):
        channels = ['r','g','b']
        max_vals = {}
        imgs = {}
        
        if apply_brightness_contrast:
            image = self.brightness_contrast(image, brightness=30, contrast=75)
        if apply_noise_removal:
            image = self.noise_removal(image)
        
        for channel in channels:
            gray_image = self.__get_single_channel_gray(image, channel)
            max_vals[np.max(gray_image)] = gray_image
            if hasattr(self, 'debug'):
                imgs[prefix+channel] = gray_image
                
        if hasattr(self, 'debug'):
            self.debug.debug_multiple_imgs(list(imgs.values()), list(imgs.keys()))
        # get the image channel with minimum max_value
        # -> the objective is to choose higher contrast and not brigther image (which may have araised text)
        gray_image = max_vals[np.min(list(max_vals.keys()))]
        
        return gray_image


# In[ ]:


class Contours:  
    def __pad_with_zeros(self, image, pad_with_zeros):
        assert len(pad_with_zeros)==2, 'Padding must contain fraction for height and width (if no padding for an axis set to 0).'
        num_rows = int(pad_with_zeros[0]*image.shape[0])
        num_cols = int(pad_with_zeros[1]*image.shape[1])
        
        if num_rows != 0:
            image[image.shape[0]-num_rows:,:] = 0
            image[:num_rows,:] = 0
        if num_cols != 0:
            image[:,image.shape[1]-num_cols:] = 0
            image[:,:num_cols] = 0
            
        return image
    
    def __get_white_pixel_percentage(self, image):
        return cv2.countNonZero(image)/(image.shape[0]*image.shape[1])

    def __get_mask(self, image, kernel_size, mask_type='eroded', pad_with_zeros=None, prefix=''):
        assert mask_type == 'dilated' or mask_type == 'eroded', f'mask type can be eroded or dilated, but got {mask_type}.'
        image_manipulation = ImageManipulation()
        
        if isinstance(kernel_size, int):
            kernel_size = (kernel_size,kernel_size)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)
        image = image_manipulation.binarization(image, 10)
        
        if mask_type == 'eroded':
            mask = image_manipulation.erosion(image, kernel, iterations=2)
        else:
            mask = cv2.bitwise_not(image_manipulation.dilation(image, kernel, iterations=2))
        
        if hasattr(self, 'debug'):
            self.debug.debug_single_img(mask, prefix+mask_type)
            
        if pad_with_zeros is not None:
            mask = self.__pad_with_zeros(mask, pad_with_zeros)
        
        return mask

    def get_largest_area(self, image, threshold=0.5, prefix='largest_area_'):
        kernel_size = int(HEIGHT/6)
        
        eroded_mask = self.__get_mask(image, kernel_size=kernel_size, prefix=prefix)
        dilated_mask = self.__get_mask(image, kernel_size=kernel_size, mask_type='dilated', prefix=prefix)
        
        mask_size_eroded = self.__get_white_pixel_percentage(eroded_mask)
        mask_size_dilated = self.__get_white_pixel_percentage(dilated_mask)
        
        if  mask_size_dilated >= threshold and mask_size_dilated <= mask_size_eroded:
            image = dilated_mask
        else:
            image = eroded_mask
                    
        if hasattr(self, 'debug'):
            self.debug.debug_single_img(image, prefix+ 'mask')
            
        contours,hierarchy = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key = cv2.contourArea, reverse = True)
        
        # Find largest contour and surround in min area box
        largest_contour = contours[0]
        
        return cv2.boundingRect(largest_contour)
    
    def get_contours(self, image, kernel_size, pad_with_zeros=None, prefix='countours_'):          
        image = self.__get_mask(image, kernel_size, pad_with_zeros=pad_with_zeros, prefix=prefix)
        
        if hasattr(self, 'debug'):
            self.debug.debug_single_img(image, prefix+'mask')
            
        # Find all contours
        contours,hierarchy = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return contours
    
    def get_horizontal_contours(self, image, kernel_size, pad_with_zeros=None, by_area=True):
        contours = self.get_contours(image, kernel_size=kernel_size, pad_with_zeros=pad_with_zeros) 
        if by_area:
            contours = sorted(contours, key=cv2.contourArea, reverse=True) # sort by area
        else:
            contours = sorted(contours, key=lambda x: cv2.boundingRect(x)[1]) # sort by y
        return contours


class CropManipulation(Contours):
    # crop border and get main area of text 
    def remove_border(self, image):  
        x,y,w,h = self.get_largest_area(image)
        
        if hasattr(self, 'debug'):
            #cv2.imwrite(os.path.join(dir_name, 'Removed_border.jpg'), image)
            self.debug.debug_single_img(image, 'remove_border')
            
        return image[y:y+h, x:x+w]


    # add border if text is close to border
    def add_border(self, image, size):
        # top bottom left right
        if isinstance(size, int):
            return cv2.copyMakeBorder(image, size, size, size, size, cv2.BORDER_CONSTANT, value=(255,255,255))
        else:
            if len(size)==2: # "size must be an int or containg two values- size[0] = height and size[1] = width."
                return cv2.copyMakeBorder(image, size[0], size[0], size[1], size[1], cv2.BORDER_CONSTANT, value=(255,255,255))
            assert len(size)==4, "size must be an int or containg two or four values."
            return cv2.copyMakeBorder(image, size[0], size[1], size[2], size[3], cv2.BORDER_CONSTANT, value=(255,255,255))
    
    def crop_mrz(self, image, kernel_size=(85,40)):
        top = 0
        min_row_y = image.shape[0] - int(0.35*image.shape[0])
        max_row_y = image.shape[0] - int(0.15*image.shape[0])
                
        contours = self.get_horizontal_contours(image, kernel_size, pad_with_zeros=(0, 0.3), by_area=False)
    
        kernel_w, kernel_h = kernel_size    
        while len(contours) == 1 and kernel_h-5 > 0:
            kernel_h -= 5
            contours = self.get_horizontal_contours(image, (kernel_w, kernel_h), pad_with_zeros=(0, 0.3), by_area=False)
            
        for i in range(len(contours)-1, 0 , -1):
            x,y,w,h = cv2.boundingRect(contours[i])
            if y < min_row_y and kernel_h-5 > 0:
                return self.crop_mrz(image, kernel_size=(kernel_w, kernel_h-5))
            
            if y < max_row_y:
                top = y
                break
                        
        if hasattr(self, 'debug'):
            self.debug.debug_single_img(image[top:,:], 'mrz')
        
        return image[top:,:]

class Deskew(Contours, ImageManipulation):   
    def __get_avg(self, contours, image_shape, axis='h'):
        assert axis == 'h' or axis == 'w', f'Axis can be h or w, bu got {axis}.'
        
        vals = []
        for i in range(len(contours)): 
            rect = cv2.minAreaRect(contours[i])
            (xc, yc), (w, h), angle = rect
            if axis == 'h' and h<0.5*image_shape:
                vals.append(h)
            elif w < 0.5*image_shape:
                vals.append(w)
        return np.mean(vals)
    
    def __get_max(self, contours, image_h, image_w, axis='w'):
        assert axis == 'h' or axis == 'w', f'Axis can be h or w, bu got {axis}.'
        
        max_val = None
        for i in range(len(contours)): 
            rect = cv2.minAreaRect(contours[i])
            (xc, yc), (w, h), angle = rect
            if xc-w/2>0.02*image_w and yc-h/2>0.05*image_h and xc+w/2<image_w-0.1*image_w and yc+h/w<image_h-0.1*image_h:
                if axis == 'h' and w<0.5*image_w:
                    if max_val is None or h>max_val:
                        max_val = h
                elif h<0.3*image_h:
                    if max_val is None or w>max_val:
                        max_val = w
                    
        return max_val
        
    def __get_angle(self, image, doc_type):
        if doc_type == PASSPORT:
            kernel_x = 45
            kernel_y = 10
            
        else:
            kernel_x = 35
            kernel_y = 5
        
        if doc_type == PASSPORT:
            contours = self.get_horizontal_contours(image, kernel_size=(kernel_x, kernel_y), pad_with_zeros=(0, 0.3))
      
            if hasattr(self, 'debug'):
                cpy = image.copy()
                
            for i in range(len(contours)): 
                rect = cv2.minAreaRect(contours[i])
                (xc, yc), (w, h), angle = rect
                if yc>0.05*image.shape[0] and yc<image.shape[0]-0.05*image.shape[0] and xc>0.05*image.shape[1] and xc<image.shape[1]-0.05*image.shape[1]:
                    if hasattr(self, 'debug'):
                        box = cv2.boxPoints(rect) # cv2.boxPoints(rect) for OpenCV 3.x
                        box = np.int0(box)
                        cpy = cv2.drawContours(cpy,[box],0,(255,0,0),3)

                    # check valid row/block in doc
                    if w>0.2*image.shape[1] and h<0.3*image.shape[0]:
                        if hasattr(self, 'debug'):
                            box = cv2.boxPoints(rect) # cv2.boxPoints(rect) for OpenCV 3.x
                            box = np.int0(box)
                            cpy = cv2.drawContours(cpy,[box],0,(0,0,255),5)
                            self.debug.debug_single_img(cpy, 'rotation_rect')

                        return angle
        
        else:
            # get horizontal contours sorted by area size
            contours = self.get_horizontal_contours(image, kernel_size=(kernel_x, kernel_y))

            avg_height = self.__get_avg(contours, image.shape[0])
            avg_width = self.__get_avg(contours, image.shape[1], axis='w')

            for i in range(len(contours)-1, -1, -1): 
                rect = cv2.minAreaRect(contours[i])
                (xc, yc), (w, h), angle = rect

                # check valid row/block in doc
                if h>avg_height and w>avg_width:
                    if hasattr(self, 'debug'):
                        box = cv2.boxPoints(rect) # cv2.boxPoints(rect) for OpenCV 3.x
                        box = np.int0(box)
                        self.debug.debug_single_img(cv2.drawContours(image.copy(),[box],0,(255,0,0),2), 'rotation_rect')
                        #cv2.imwrite(os.path.join(dir_name, 'Rotation_rect.jpg'), cv2.drawContours(image.copy(),[box],0,(0,0,255),2))

                    return angle
        return 0
    
    # Deskew 
    def deskew(self, image, doc_type): 
        angle = self.__get_angle(image, doc_type) #, inverse=True, debug=debug)
        image = self.image_rotation(image, angle)
        if image.shape[0] > image.shape[1]: # doc supose to have w > h
            image = self.image_rotation(image, 90)
            
        return image

class ImageProcessing(CropManipulation, Deskew):
    def __init__(self, image, doc_type, min_erosion_iterations, debug_dir=None, debug_type=None):
        self.__initialize_image(image)
        self.doc_type = doc_type
        self.erosion_iterations = min_erosion_iterations
        self.__initialize_debug(debug_dir, debug_type)
        
    def __initialize_debug(self, debug_dir, debug_type):
        if debug_type is not None:
            assert debug_type=='file' or debug_type=='plt', f'Expected debug_type value to be "file" "plt" or "wandb" (or None), but got {debug_type}.'
            if debug_type == 'file' and debug_dir is not None:
                curr_dir = str(self.erosion_iterations)
                self.debug = DebugToFile(os.path.join(debug_dir, curr_dir))
            elif debug_type == 'plt':
                self.debug = DebugToPlt()
           
    def __initialize_image(self, image):
        if isinstance(image, str): # assume path was given
            image = cv2.imread(image)

        self.image = image
            
    def __call__(self):
        self.__debug(self.image.copy(), 'original')
        
        # rotate 90 deg if vertical
        image = self.__rotate_if_vertical(self.image.copy())
        
        # resize
        image = cv2.resize(image, (WIDTH,HEIGHT))
        
        # increase brightness-contrast
        image = self.__increase_brightness_contrast(image)
        self.__debug(image, 'brightness_contrast')
        
        # remove borders
        image = self.remove_border(image)
   
        image = self.deskew(image, self.doc_type)
        image, bbox = self.__check_orientation(image)
            
        self.__debug(image, 'deskew')
        
        # remove borders
        image = self.remove_border(image)
        
        # resize
        image = cv2.resize(image, (WIDTH,HEIGHT))
        
        return self.__get_doc_image(image, bbox)
    
    def __rotate_if_vertical(self, image):
        if image.shape[0] > image.shape[1]: # doc supose to have w > h
            image = self.image_rotation(image, 90)
        return image
    
    def __increase_brightness_contrast(self, image):
        average_pixel_value = np.average(image)
        
        if self.doc_type == PASSPORT:
            if average_pixel_value < 130:
                image = self.brightness_contrast(image, brightness=50, contrast=65)
            elif average_pixel_value < 160:
                image = self.brightness_contrast(image, brightness=20, contrast=80)
            elif average_pixel_value < 180:
                image = self.brightness_contrast(image, brightness=0, contrast=80)
            else:
                image = self.brightness_contrast(image, brightness=-20, contrast=80)
        else:
            if average_pixel_value < 130:
                image = self.brightness_contrast(image, brightness=80, contrast=60)
            elif average_pixel_value < 160:
                image = self.brightness_contrast(image, brightness=40, contrast=60)
            elif average_pixel_value < 180:
                image = self.brightness_contrast(image, brightness=20, contrast=80)
            else:
                image = self.brightness_contrast(image, brightness=-20, contrast=80)

        return image
        
    def __get_doc_image(self, image, bbox):
        if bbox is None:
            # if no face detected try OCR for both options
            rotated_image = self.image_rotation(image, 180)
                
        if self.doc_type == PASSPORT:
            image = self.crop_mrz(image)
            image = self.add_border(image, int(0.1*HEIGHT))
            
            if bbox is None:
                rotated_image = self.crop_mrz(rotated_image)
                rotated_image = self.add_border(rotated_image, int(0.1*HEIGHT))
        
        doc_image = self.__binarize_doc_image(image)
        rotated_doc = self.__binarize_doc_image(rotated_image) if bbox is None else None
        
        self.erosion_iterations+=1
            
        return (doc_image, rotated_doc)
    
    def __binarize_doc_image(self, image):
        if self.doc_type != PASSPORT and self.erosion_iterations!=0:
            image = self.dilation(image)
            image = self.erosion(image, iterations=self.erosion_iterations)
            image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, np.ones((2, 2), np.uint8))

        self.__debug(image, 'doc')
        
        if self.doc_type == PASSPORT:
            average_pixel_value = np.average(image)
            image = self.binarization(image, threshold=average_pixel_value, inverse=False, apply_brightness_contrast=False, apply_noise_removal=False)
            
        else:
            image = self.binarization(image, threshold=10, inverse=False)
        
        self.__debug(image, 'binarized_doc')
        
        return image
    
    def __check_orientation(self, image):
        bbox = detector.get_detection(image)
        if bbox is not None and self.__is_upside_down(image.shape[1], bbox[0]):
            image = self.image_rotation(image, 180)
        
        return image, bbox
       
    def __is_upside_down(self, image_w, face_x):
        # if image not in expected side as in document - it's upside down
        if self.doc_type == ID:
            # for id expected to be on the right 
            # (face to end of doc < start of doc to face)
            return True if face_x < image_w - face_x else False
        # for driving license/passport expected to be on the left
        # (start of doc to face < face to end of doc)
        return True if face_x > image_w - face_x else False
    
    def __debug(self, image, title):
        if hasattr(self, 'debug'):
            self.debug.debug_single_img(image, title)