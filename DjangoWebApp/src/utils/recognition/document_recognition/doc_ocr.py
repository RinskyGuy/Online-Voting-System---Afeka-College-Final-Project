import shutil 
import os
from collections.abc import Iterable
from abc import ABCMeta
import pytesseract
import numpy as np
import pandas as pd
import re
from utils.recognition.document_recognition.regex import Regex
from utils.recognition.document_recognition.preprocess import ImageProcessing
from utils.recognition.document_recognition.similarity import StringSimilarity
from utils.recognition.document_recognition.documents import DocData, IdData, DrivingLicenseData, PassportData
from utils.recognition.document_recognition.tesseract_configs import tesseract_dir, lang_paths
from django.contrib.staticfiles.storage import staticfiles_storage
import cv2
from utils.recognition.thresholds import TextVerification

if os.name == 'nt':
    pytesseract.pytesseract.tesseract_cmd = staticfiles_storage.path(os.path.join(tesseract_dir, 'tesseract.exe'))

if lang_paths is not None:
    assert isinstance(lang_paths, Iterable), f'Expected lang_path to be an iterable containing language files path, but got {type(lang_paths)}.'
    for lang_path in lang_paths:
        if isinstance(lang_path, str) and lang_path.endswith('.traineddata'):
            tessdata_path = staticfiles_storage.path(os.path.join(tesseract_dir, 'tessdata'))
            tessdata_files = os.listdir(tessdata_path)
            lang = os.path.split(lang_path)[1]

            if lang not in tessdata_files:
                shutil.copy(lang_path, tessdata_path)

class DataBuilder:
    def __init__(self, pred_values, doc_cls:DocData):
        assert isinstance(doc_cls, DocData), f'Input of true values must be of DocData object, but got {str(type(pred_values))}.'
        self.cls = type(doc_cls)
        self.labels = list(doc_cls.values.keys())
        self.pred_values = pred_values
        self._initialize_data()
        
    def set_data(self, label, pred_data, dist):
        self._assert_pred_data(pred_data)
        self.data[pred_data] = {'label':label, 'dist':dist}

    def is_best_match(self, pred_data, dist):
        if self.data[pred_data] is None or dist < self.data[pred_data]['dist']:
            return True
        return False
    
    def build(self):
        values = {}
        labels = []
        
        for data, match in self.data.items():
            if match is not None:
                values[match['label']] = self._get_pred_value(data)
                labels.append(match['label'])
        
        missing_labels = [label for label in self.labels if label not in labels]
        for label in missing_labels:
            values[label] = ''
            
        self.doc_data = self.cls(values)
        
    def _initialize_data(self):
        self.data = {(row_num, col_num):None for row_num,row in enumerate(self.pred_values) for col_num in range(len(row))}
        
    def _get_pred_value(self, data):
        return self.pred_values[data[0]][data[1]]
            
    def _assert_pred_data(self, pred_data):
        assert (isinstance(pred_data, tuple) or isinstance(pred_data, list)) and len(pred_data) == 2, "Input should be a list/tuple of row and col indexes."
        
class PassportDataBuilder(DataBuilder):
    def __init__(self, pred_values, doc_cls:DocData):
        assert isinstance(doc_cls, PassportData), f'Input of true values must be of PassportData object, but got {str(type(pred_values))}.'
        super().__init__(pred_values, doc_cls)
        self.data = {row_num:None for row_num,row in enumerate(pred_values)}
    
    def _initialize_data(self):
        self.data = {row_num:None for row_num,row in enumerate(self.pred_values)}
        
    def _get_pred_value(self, data):
        return self.pred_values[data]
    
    def _assert_pred_data(self, pred_data):
        assert isinstance(pred_data, int) , "Input should be a int index of row."

class OCR: 
    @classmethod
    def ocr(self, image, lang='eng+heb+ara'):
        data = pytesseract.image_to_data(image, lang=lang)
        data_lst = list(map(lambda x:x.split('\t'), data.split('\n')))
        return pd.DataFrame(data_lst[1:], columns=data_lst[0])
    
    @classmethod
    def get_lines_df(self, data_df):
        return data_df[data_df['level']=='4']
    
    @classmethod
    def get_words_df(self, data_df):
        return data_df[data_df['level']=='5']
    
    @classmethod
    def sort_words_by_height(self, words_df):
        words_df = words_df.assign(my_col=lambda d: d['top'].astype(float))
        words_df = words_df.sort_values(by=['top'])
        return words_df
    
class DocOCR(OCR, metaclass=ABCMeta):    
    @staticmethod 
    def __init__(self): # abstract class
        pass
    
    def _get_lines(self, image, lines_df):
        lines=[]
        #max_row_height = self.get_row_avg_height(lines_df) * threshold    
        for index, row in lines_df.iterrows():
            y,h = float(row['top'])/image.shape[0], float(row['height'])/image.shape[0]
            if h <= 0.2:
                lines.append([y, y+h])
        return lines
    
    def _get_regex(self):
        heb_regex = '[\u05d0-\u05ea]|[-"\']'
        eng_regex = '[A-Z]'
        date_regex = '[0-9]|[\.]'

        regex = heb_regex + '|'  + eng_regex + '|' + date_regex
        
        return regex
    
    def _get_punctuation(self):
        return "!#$%&\\'()*+:;=><?[\\\\]^`{|}~\\"
    
    def _clean_data(self, val):
        regex = self._get_regex()
        for char in val:
            if not re.match(regex, char):
                if char != ' ':
                    val = val.replace(char,'$')
        
        # remove special chars
        punctuation = self._get_punctuation()
        
        table_punctuation = str.maketrans('','',punctuation)
        return val.translate(table_punctuation)
    
    def _validate_data(self, val): 
        if val == '' and val == ' ':
            return False
        
        if len(val) <= 2:
            punctuation = ".,!#$%&\\()*+:;=><?[\\\\]^`{|}~\\-"
            for char in val:
                if char in punctuation:
                    return False
        return True
    
    def _get_rows_values(self, image):
        data_df = self.ocr(image)
        words_df = self.get_words_df(data_df)
        words_df = self.sort_words_by_height(words_df)
        lines_df = self.get_lines_df(data_df)
        lines = self._get_lines(image, lines_df)
        
        rows = []
        line = 0
        for i in range(len(words_df.index.values)):
            row_idx = words_df.index.values[i]
            middle = float(words_df.loc[row_idx, 'top'])/image.shape[0]+(float(words_df.loc[row_idx, 'height'])/image.shape[0])/2
            if line >= len(lines):
                break

            if lines[line][0] <= middle and lines[line][1] >= middle:
                words = []

                while lines[line][0] <= middle and lines[line][1] >= middle:
                    x1 = float(words_df.loc[row_idx, 'left'])/image.shape[1]
                    x2 = x1 + float(words_df.loc[row_idx, 'width'])/image.shape[1]
                    words.append({'x1': x1, 'x2': x2, 'text': words_df.loc[row_idx, 'text']})
              
                    i+=1
                    if i < len(words_df.index.values):
                        row_idx = words_df.index.values[i]
                        middle = float(words_df.loc[row_idx, 'top'])/image.shape[0]+(float(words_df.loc[row_idx, 'height'])/image.shape[0])/2

                    else:
                        break
               
                rows.append(sorted(words, key=lambda r: r['x1']))
                line += 1
        return rows
    
    def _get_avg_distance(self, rows):
        distances = []
        for row in rows:
            for i in range(len(row)):
                if i != 0:
                    distances.append(row[i]['x1']-row[i-1]['x2'])
                    
        return np.mean(np.array(distances))
    
    def _get_image_values(self, image):
        values = []
        rows = self._get_rows_values(image)
        avg_distance = self._get_avg_distance(rows)
        
        for row in rows:
            cols = []
            col = []
            curr_row = []
            
            for word_num in range(len(row)):

                word = self._clean_data(row[word_num]['text'])
                if not self._validate_data(word):
                    continue
                                
                if len(curr_row) != 0 and row[word_num]['x1'] > curr_row[-1]['x2']+avg_distance:
                    if len(col) > 0:
                        col = col[::-1]
                        cols.append(' '.join(col))
                        col = []

                col.append(word)
                curr_row.append(row[word_num])
                
            if len(col) > 0:
                col = col[::-1]
                cols.append(' '.join(col))
            if len(cols) > 0:
                values.append(cols)

        return values
 
    def _get_builder(self, pred_values, true_data):
        return DataBuilder(pred_values, true_data)
    
    def _match_data(self, pred_values, true_data):
        builder = self._get_builder(pred_values, true_data)
        for label in true_data.labels: 
            self._find_best_match(label, builder, true_data.values[label].get_value())
                
        return builder

    def _find_best_match(self, label, builder, true_word):
        row_idx, col_idx = 0, 0
        min_dist = None
        found = False

        for row_num, row in enumerate(builder.pred_values):
            for col_num, col in enumerate(row):
                dist = StringSimilarity.levenshtein_distance(col, true_word)
                
                if min_dist is None or dist < min_dist:
                    if builder.is_best_match((row_num,col_num), dist):
                        min_dist = dist
                        row_idx = row_num
                        col_idx = col_num

                if min_dist == 0:
                    found = True
                    break

            if found:
                break
        
        if min_dist is not None:
            builder.set_data(label, (row_idx, col_idx), min_dist)
        
    def _get_distances(self, image, true_data, debug=None, postfix=''):
        try:
            distances = {}
            labels = []

            pred_values = self._get_image_values(image)
            if debug is not None and hasattr(debug, 'debug_dir'):
                debug_dir = debug.debug_dir
                data_path = os.path.join(debug_dir, 'data')
                if not os.path.exists(data_path):
                    os.makedirs(data_path)
                with open(os.path.join(data_path, 'ocr_preds'+postfix+'.txt'), 'w', encoding='utf8') as f: 
                    f.write(str(pred_values))

            builder = self._match_data(pred_values, true_data)

            builder.build()
            for data, match in builder.data.items():
                if match is not None:
                    distances[match['label']] = match['dist']
                    labels.append(match['label'])

            missing_labels = [label for label in builder.labels if label not in labels]
            for label in missing_labels:
                distances[label] = None

            return distances
        
        except AssertionError as err_msg:
            print(err_msg)
            return None
    
    def _get_cleaned_distances(self, image, true_data, debug=None, postfix=''):
        try:
            distances = {} 

            pred_values = self._get_image_values(image)
            if debug is not None and hasattr(debug, 'debug_dir'):
                debug_dir = debug.debug_dir
                data_path = os.path.join(debug_dir, 'data')
                if not os.path.exists(data_path):
                    os.makedirs(data_path)
                with open(os.path.join(data_path, 'ocr_preds'+postfix+'.txt'), 'w', encoding='utf8') as f: 
                    f.write(str(pred_values))
                
            true_data = self._assert_data_type(true_data)

            builder = self._match_data(pred_values, true_data)
            
            builder.build()        
            cleaned_ocr_data = builder.doc_data.get_values()
            cleaned_true_data = true_data.get_values()
            
            if debug is not None and hasattr(debug, 'debug_dir'):
                labels = list(cleaned_true_data.keys())
                with open(os.path.join(data_path, 'true_kvps'+postfix+'.txt'), 'w', encoding='utf8') as f: 
                    f.write(str(cleaned_true_data))
                with open(os.path.join(data_path, 'pred_kvps.txt'), 'w', encoding='utf8') as f: 
                    f.write(str(cleaned_ocr_data))
                    
            for label in cleaned_true_data:
                if cleaned_ocr_data[label] == '':
                    distances[label] = None
                    continue
                dist = StringSimilarity.levenshtein_distance(cleaned_ocr_data[label], cleaned_true_data[label])
                distances[label] = dist

            return distances
        
        except AssertionError as err_msg:
            print(err_msg)
            return None
    
class MatchData(DocOCR):  
    min_erosion_iters=0
    max_erosion_iters=3
    
    def __init__(self):
        return
    
    def text_distances(self, doc_image, true_data, clean=True, debug=None, postfix=''):
        if not clean:
            return self._get_distances(doc_image, true_data, debug=debug, postfix=postfix)
        return self._get_cleaned_distances(doc_image, true_data, debug=debug, postfix=postfix)
    
  
    
    def _get_avg_similarity(self, similarity):
        total_dist, num_labels = 0, 0
        for label, dist in similarity.items():
            if dist is not None:
                total_dist += dist
                num_labels += 1
                
        if num_labels != 0:
            return total_dist/num_labels
        else:
            return 1
        
    def _get_mean_similarity(self, similarity, true_data):
        if isinstance(true_data, DocData):
            true_data = true_data.get_values()
        assert isinstance(true_data, dict), f'true data must be a dict of labels and values, but got {type(true_data)}.'
        
        for label, value in true_data.items():
            if similarity[label] is not None:
                similarity[label] = similarity[label]/len(value)

        return similarity
    
    def __get_similarity(self, true_data, preprocess, clean=True):                   
        # if face detected than correctly oriented and rotated_doc_image is None
        # else try OCR for both options of doc image
        doc_images = preprocess()
        similarity = self.text_distances(doc_images[0], true_data, clean=clean, debug=None if not hasattr(preprocess, 'debug') else preprocess.debug)
        if doc_images[1] is not None:
            rotated_doc_similarity = self.text_distances(doc_images[1], true_data, clean=clean, 
                                                         debug=None if not hasattr(preprocess, 'debug') else preprocess.debug, postfix='_flipped')
            if self._get_avg_similarity(rotated_doc_similarity) < self._get_avg_similarity(similarity):
                similarity = rotated_doc_similarity
        
        return self._get_mean_similarity(similarity, true_data)
    
    def _get_best_similarity(self, curr_similarity, true_data, preprocess, clean):
        similarity = self.__get_similarity(true_data, preprocess, clean=clean)
        best_similarity = {}
        
        labels = list(similarity.keys())
        distances = zip(list(similarity.values()), list(curr_similarity.values()))
        for label, (dist1, dist2) in zip(labels, distances):
            if dist1 is not None and dist2 is not None:
                dist = dist1 if dist1<dist2 else dist2
            elif dist1 is not None: 
                dist = dist1
            elif dist2 is not None:
                dist = dist2
            else:
                dist = None
                
            best_similarity[label] = dist
        
        return best_similarity
    
    def match_data(self, image, true_data, clean=True, debug_dir=None, debug_type=None):
        if not isinstance(image, np.ndarray):
            # return RGB ndarray format
            image = np.array(image)
            if image.shape[2] > 3: # RGBA -> RGB
                image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
        else:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
        #true_vector = true_data['face_vector']                                              
        true_data = self._assert_data_type(true_data)
        
        preprocess = ImageProcessing(image, self._get_doc_type(), min_erosion_iterations=self.min_erosion_iters,
                                     debug_dir=debug_dir, debug_type=debug_type)
        
        similarity = self.__get_similarity(true_data, preprocess, clean=clean)

        while preprocess.erosion_iterations <= self.max_erosion_iters:
            similarity = self._get_best_similarity(similarity, true_data, preprocess, clean=clean)
            
        return similarity
    
    def get_avg_distances(self, image, true_data, clean=True, debug_dir=None, debug_type=None):
        distances = self.match_data(image, true_data, clean=clean, debug_dir=debug_dir, debug_type=debug_type)
        
        avg_distances = {}
        num_nan = 0
        total_dist = 0
        fields = list(distances.keys())
        
        for field in fields:
            if field.endswith('distance'):
                avg_distances[field] = distances[field]
            else:
                if pd.isna(distances[field]):
                    num_nan+=1
                else:
                    total_dist += distances[field]
        
        num_text_fields = len(distances)
        if num_text_fields-num_nan > 0:
            avg_distances = {'avg_text_distance':total_dist/(num_text_fields-num_nan),
                             'num_null_vals':num_nan}
        else:
            avg_distances = {'avg_text_distance':None,
                             'num_null_vals':num_nan}
        return avg_distances
    
    def text_match(self, image, true_data, clean=True, debug_dir=None, debug_type=None):
        avg_distances = self.get_avg_distances(image, true_data, clean, debug_dir, debug_type)
        if avg_distances['avg_text_distance'] is not None and avg_distances['avg_text_distance'] <= TextVerification.thresholds[self._get_doc_type()]:
            return True
        return False
        
class MatchId(MatchData):
    def _assert_data_type(self, true_data):
        if isinstance(true_data, dict):
            true_data = IdData(true_data)
        assert type(true_data) == IdData, "Input data must be valid id data."
        return true_data
    
    def _get_doc_type(self):
        return IdData.doc_type
    
    def _get_regex(self):
        arab_regex = '[\u0600-\u06ff]'            
        return super()._get_regex() + '|' + arab_regex
    
    def _validate_data(self, val): 
        heb_regex = '[\u05d0-\u05ea]|[-"\']'
        eng_regex = '[A-Z]'
        date_regex = '[0-9]|[.]'

        regex = heb_regex + '|'  + eng_regex + '|' + date_regex

        val = val.replace(" ", "")
        for char in val:
            if not Regex.regex_match(regex, char):
                return False
                
        return super()._validate_data(val) and True
    
class MatchDrivingLicense(MatchData):
    def _assert_data_type(self, true_data):
        if isinstance(true_data, dict):
            true_data = DrivingLicenseData(true_data)
        assert type(true_data) == DrivingLicenseData, "Input data must be valid driving license data."
        return true_data
    
    def _get_doc_type(self):
        return DrivingLicenseData.doc_type
    
class MatchPassport(MatchData):
    min_erosion_iters=0
    max_erosion_iters=2
    
    def _assert_data_type(self, true_data):
        if isinstance(true_data, dict):
            true_data = PassportData(true_data)
        assert type(true_data) == PassportData, "Input data must be valid passport data."
        return true_data
    
    def _get_doc_type(self):
        return PassportData.doc_type
    
    def _get_regex(self):
        regex = '[xA-Z0-9]|<'
        return regex
    
    def _get_punctuation(self):
        return "!#$%&\\'()*+:;=>?[\\\\]^`{|}~\\"
    
    def _get_image_values(self, image):
        pred_values = super()._get_image_values(image)
        return [''.join(row) for row in pred_values]
    
    def _get_builder(self, pred_values, true_data):
        return PassportDataBuilder(pred_values, true_data)
    
    
    def _find_best_match(self, label, builder, true_word):
        row_idx = -1
        min_dist = None
        found = False

        for row_num, row in enumerate(builder.pred_values):
            dist = StringSimilarity.levenshtein_distance(row, true_word)
            if min_dist is None or dist < min_dist:
                if builder.is_best_match(row_num, dist):
                    min_dist = dist
                    row_idx = row_num

            if min_dist == 0:
                found = True
                break

            if found:
                break

        if min_dist is not None:
            builder.set_data(label, row_idx, min_dist)

id_ocr = MatchId()
driving_license_ocr = MatchDrivingLicense()
passport_ocr = MatchPassport()


