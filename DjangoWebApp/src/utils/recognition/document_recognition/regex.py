from functools import reduce
from datetime import datetime
from pyluach import dates  # for hebrew dates
import re

class Regex:
    compatible = [['0','o','O'], ['<','K','k'], ['1','l','i'], ['x']+[str(num) for num in range(10)]]
    
    def regex_match(regex, val):
        if re.match(regex, val):
            return True
        return False
    
    def char_match(regex, val):
        for char in val:
            if not re.match(regex, char):
                match = False
                for match_set in Regex.compatible:
                    if char in match_set:
                        for char2 in match_set:
                            if char2 != char and re.match(regex, char2):
                                val = val.replace(char,char2)
                                match = True
                                break
                        break
                
                if not match:
                    val = val.replace(char,'$')
                    
        table_punctuation = str.maketrans('','','$')
        return val.translate(table_punctuation)


class DateValidator(Regex):
    @staticmethod
    def is_heb_date(val):
        # hebrew dates
        month_regex = '(תשרי|חשוון|כסלו|טבת|שבט|אדר|ניסן|אייר|סיוון|תמוז|אב|אלול)'

        # א',ב',ג',..,ט',י',י"א,..,י"ד, ט"ו, ט"ז, י"ז, י"ח, י"ט, כ', כ"א, .., כ"ט, ל
        # א=u05D0- ט=u05D8
        # י=u05D9 א=u05D0- ד=u05D3 | ז=u05D6- ט=u05D8
        # ט=u05D8 ו=u05D5- ז=u05D6
        # כ=u05DB א=u05D0- ט=u05D8
        # ל=u05DC
        day_regex = '(([\u05d0-\u05d9]|[\u05db-\u05dc])\')|(\u05d9"([\u05d0-\u05d3]|[\u05d6-\u05d8]))' + \
        '|(\u05d8"[\u05d5-\u05d6])|(\u05db"[\u05d0-\u05d8])'

        # תר"ס=1900, תרס"א=1901, .., תר"ע=1910
        # תר"פ=1920, .., ת"ש=1940, תש"א=1941, .., תש"ט=1949, תש"י=1950
        # תש"כ=1960, תש"ל=1970, תש"מ=1980, תש"נ=1990, תש"ס=2000, תש"ע=2010, תש"פ=2020
        # תר"[ס-צ] | תר[ס-צ]"[א-ט]
        # ת"ש | תש"[א-ט] | תש[י-פ]"[א-ט]
        # ת=u05EA, ר=u05E8, ש=u05E9, ס=u05E1, צ=u05E6, י=u05D9, פ=u05E4, א=u05D0, ט=u05D8
        year_regex = '\u05ea((\u05e8"[\u05e1-\u05e6])|(\u05e8[\u05e1-\u05e6]"[\u05d0-\u05d8]))' + \
        '|\u05ea(("\u05e9)|(\u05e9"[\u05d0-\u05e4])|(\u05e9[\u05d9-\u05e4]"[\u05d0-\u05d8]))'

        date_regex = day_regex + ' ' + month_regex + ' ' + year_regex + '$'

        return DateValidator.regex_match(date_regex, val)
    
    @staticmethod
    def is_gregorian_date(val, format='DD.MM.YY'):
        if format == 'DD.MM.YY':
            separator = '.'
        elif format == 'DD/MM/YY':
            separator = '/'
        else:
            return False
        
        val = val.split(separator)
        
        # 19xy - 200x, 201x, 2020/2021/2022
        year_regex = '((^19[0-9][0-9]$)|(^20[0-1][0-9]$)|(^202[0-2]$))' 
        
        # 01, 02, ...., 11, 12
        month_regex = '((^0?[1-9]$)|(^1[0-2]$))' 
        
        # 01, 02, ...., 09 or 1, 2, ...., 9 or 10, 11, ...., 31
        day_regex = '((^0?[1-9]$)|(^[1-2][0-9]$)|(^3[0-1]$))'    
        
        return DateValidator.regex_match(day_regex, val[0]) and DateValidator.regex_match(month_regex, val[1]) and DateValidator.regex_match(year_regex, val[2])
    
    @staticmethod
    def is_before(start_date, end_date):
        if not (start_date <= end_date):
            return False
    
        return True
    
    @staticmethod
    def date_to_str(date_val, format='%d.%m.%Y'):
        if isinstance(date_val, datetime):
            date_val = date_val.strftime(format)
        return date_val
                 
    @staticmethod
    def str_to_date(date_val, format='%d.%m.%Y'):
        if isinstance(date_val, str):
            date_val = datetime.strptime(date_val, format)
        return date_val

    @staticmethod
    def get_heb_date(date_val, format='%d.%m.%Y'):
        if isinstance(date_val, str):
            date_val = datetime.strptime(date_val, format)
            
        date_val = dates.GregorianDate(date_val.year, date_val.month, date_val.day)
        return date_val.to_heb().hebrew_date_string()
    
class StringValidator(Regex):
    @staticmethod
    def hex_chars(val, size):
        hex_regex = "(^[0-9A-F]\{" + str(size) + "}$)|(^[0-9a-f]{" + str(size) + "}$)"
        return StringValidator.regex_match(hex_regex, val)
    
    @staticmethod
    def heb_chars_count(val, frac=0.6):
        regex = '[\u05d0-\u05ea]'
        count = 0
        
        for char in val:
            if re.match(regex, char):
                count += 1
                
        if count/len(val) > frac:
            return True
        return False
    
    # https://www.upnext.co.il/articles/israeli-id-numer-validation/
    @staticmethod
    def validate_id_num(val):
        if len(val) != 9:
            return False

        seq = "121212121"
        result = []
        
        for digit1, digit2 in zip(val,seq):
            digit1, digit2 = ord(digit1)-48, ord(digit2)-48
            
            if digit1 < 0 or digit2 < 0 or digit1 > 9 or digit2 > 9:
                return False
            
            result.append(digit1*digit2)
        
        for i in range(len(result)):
            if result[i]>9:
                num = str(result[i])
                result[i] = ord(num[0])-48 + ord(num[1])-48
        
        sum_result = reduce((lambda x, y: x + y), result)
        if sum_result%10 != 0:
            return False
        
        return True

    @staticmethod
    def capitalize(val):
        separator = None
        
        if ' ' in val:
            separator = ' '            
            
        elif '-' in val:
            seprator = '-'
        
        if separator is not None:
            capitalized = []
            vals = val.split(seprator)
            for val in vals:
                capitalized.append(val.capitalize())
            val = seprator.join(capitalized)
        
        return val  
    
class NameValidator(Regex):
    @staticmethod
    def validate_eng_name(val):
        name_regex = '[A-Za-z]+([ -][A-Z]+)?'
        name_regex = f'({name_regex}( \({name_regex}\))?$)'
        return NameValidator.regex_match(name_regex, val)
    
    @staticmethod
    # hebrew alphabet א=u05D0- ת=u05EA
    # contains at least two letters
    # may or may not contain '-' in name (בת-אל)
    def validate_heb_name(val):
        name_regex = '[\u05d0-\u05ea]+([ -][\u05d0-\u05ea]+)?'
        name_regex = f'({name_regex}( \({name_regex}\))?$)'
        return NameValidator.regex_match(name_regex, val)