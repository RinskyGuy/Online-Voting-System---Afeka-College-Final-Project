from abc import abstractmethod
from datetime import datetime
from utils.recognition.document_recognition.regex import Regex

ID = 'id'
DRIVING_LICENSE = 'driving_license'
PASSPORT = 'passport'

class LangEnum:
    HEB = 'heb',
    ENG = 'eng'
    
class Name:
    def __init__(self, name:str, lang:LangEnum, cls):
        if lang == LangEnum.ENG:
            name = name.upper()
        self.name, self.prev_name = self._get_names(name)
        self.lang = lang
        self.cls = cls
    
    def _get_names(self, name):
        names = name.split(' ')
        if len(names)>1:
            return (names[0], names[1].replace('(','').replace(')',''))
        else:
            return (names[0], None)
        
    def get_value(self):
        if self.cls == PassportData and self.prev_name is not None:
            return self.name + '<' + self.prev_name
        
        return self.name
    
    def clean_data(self):
        if self.lang == LangEnum.ENG:
            regex = '[A-Z]|[-() ]'
        
        else:
            regex = '[\u05d0-\u05ea]|[-() ]'
            
        return Regex.char_match(regex, self.get_value())
    
class GregDate:
    def __init__(self, date, cls, date_format = "%d.%m.%Y"):
        if isinstance(date, datetime):
            date = date.strftime(date_format)
        assert isinstance(date, str), "Date input should be of string or date types."
        self.value = date
        self.date_format = date_format
        self.cls = cls
        
    def get_value(self):
        if self.value != '':
            if self.cls != PassportData:
                return self.value
            return datetime.strptime(self.value, self.date_format).strftime("%y%m%d")
        return self.value
        
    def clean_data(self):
        regex = '[0-9]|[.]'
        return Regex.char_match(regex, self.get_value().split(' ')[0])

class HebDate:
    def __init__(self, heb_date:str):
        self.value = heb_date
    
    def get_value(self):
        return self.value
    
    def clean_data(self):
        regex = '[\u05d0-\u05ea]|[-"\' ]'
        return Regex.char_match(regex, self.get_value())

class Address:
    def __init__(self, address:str):
        self.value = address
    
    def get_value(self):
        return self.value
    
    def clean_data(self):
        regex = '[\u05d0-\u05ea0-9]|[-"\' ]'
        return Regex.char_match(regex, self.get_value())
    
class Num:
    def __init__(self, num):
        if not isinstance(num, str):
            num = str(num)
        # remove leading 0s
        while num.startswith('0'):
            num = num[1:]
            
        self.value = num
    
    def get_value(self):
        return self.value 
    
    def clean_data(self):
        regex = '[0-9]'
        return Regex.char_match(regex, self.get_value().split(' ')[0])
    
class IdNum(Num):    
    def clean_data(self):
        regex = '[0-9]'
        return Regex.char_match(regex, ''.join(self.get_value().split(' ')[::-1]))

class Gender:
    def __init__(self, gender:str):
        self.value = gender.upper()
    
    def get_value(self):
        return self.value
    
    def clean_data(self):
        regex = '[FM]'
        return Regex.char_match(regex, self.get_value())
    
class ConcatData:
    def __init__(self, data1:str, data2=None):
        if data2 is not None:
            assert isinstance(data2, str), 'Concat data should receive a single strings or two strings, ' +            f'but got a string and a {str(type(data2))}.'
            
            self.value = data1 + " " + data2
        else:
            self.value = data1
            
    def get_value(self):
        return self.value
    
    def clean_data(self):
        return self.get_value()
    
class MRZLine:
    def __init__(self, line_val:str, line_num:int):
        self.value = line_val
        self.line_num = line_num
        
    def get_value(self):
        return self.value
    
    def clean_data(self):
        if self.line_num == 0:
            regex = '[A-JL-Z]' # remove '<' and 'K'
        else:
            regex = '[ISRF0-9]'
                    
        return Regex.char_match(regex, self.value)


class DocData:   
    labels = ['id_num', 'birth_date', 'exp_date']

    @abstractmethod
    def __init__(self, values:dict):
        missing_label = False
        for label in self.labels:
            if label not in values:
                for key in list(values.keys()):
                    if key.startswith(label) or key.endswith(label):
                        break
                missing_label = True
                
            assert not missing_label, "Values must contain all keys: " + str(self.labels)
        
        id_num_digits = 9
        
        self.id_num = IdNum(values['id_num'])
        self.birth_date = GregDate(values['birth_date'], type(self))
        self.exp_date = GregDate(values['exp_date'], type(self))
    
    def get_values(self):
        return {label:value.clean_data() for label,value in self.values.items()}
        
class IdData(DocData):
    doc_type = ID
    labels = DocData.labels + ['heb_last_name', 'heb_first_name', 
                               'gen_date', 'heb_birth_date', 'heb_gen_date', 'heb_exp_date']

    def __init__(self, values:dict):
        super().__init__(values)
        self.heb_first_name = Name(values['heb_first_name'], LangEnum.HEB, type(self))
        self.heb_last_name = Name(values['heb_last_name'], LangEnum.HEB, type(self))
        self.gen_date = GregDate(values['gen_date'], type(self))
        self.heb_birth_date = HebDate(values['heb_birth_date'])
        self.heb_exp_date = HebDate(values['heb_exp_date'])
        self.heb_gen_date = HebDate(values['heb_gen_date'])
        self.values = self._get_values()
        
    def _get_values(self):
        return {label: value for label, value in                  zip(['heb_last_name', 'heb_first_name',
                 'heb_birth_date', 'birth_date',
                 'heb_gen_date', 'gen_date',
                 'heb_exp_date','id_num', 'exp_date'],[self.heb_last_name, 
                 self.heb_first_name, self.heb_birth_date, 
                 self.birth_date, 
                 self.heb_gen_date, self.gen_date, 
                 self.heb_exp_date, self.id_num,
                 self.exp_date])}
    
    
class DrivingLicenseData(DocData):
    doc_type = DRIVING_LICENSE
    labels = DocData.labels + ['last_name', 'first_name', 'heb_last_name', 'heb_first_name', 
                               'gen_date', 'address', 'license_num', 'unique_num']
        
    def __init__(self, values:dict):
        super().__init__(values)
        license_num_digits = 7
        unique_num_digits = 4
    
        self.first_name = Name(values['first_name'], LangEnum.ENG, type(self))
        self.last_name = Name(values['last_name'], LangEnum.ENG, type(self))
        self.heb_first_name = Name(values['heb_first_name'], LangEnum.HEB, type(self))
        self.heb_last_name = Name(values['heb_last_name'], LangEnum.HEB, type(self))
        self.gen_date = GregDate(values['gen_date'], type(self))
        self.address = Address(values['address'])
        self.license_num = Num(values['license_num'])
        self.unique_num = Num(values['unique_num'])
        self.values = self._get_values()
        
    def _get_values(self):
        return {label: value for label, value in                  zip(['heb_last_name', 'last_name',
                 'heb_first_name','first_name',
                 'birth_date','gen_date','exp_date','license_num', 
                 'id_num', 'unique_num', 'address'],[self.heb_last_name, 
                 self.last_name, self.heb_first_name, 
                 self.first_name,
                 self.birth_date, self.gen_date,
                 self.exp_date, self.license_num,
                 self.id_num, self.unique_num,
                 self.address])}
    
class PassportData(DocData):
    doc_type = PASSPORT
    labels = DocData.labels + ['last_name', 'first_name', 'passport_num', 'gender']
        
    def __init__(self, values:dict):
        if 'line1' in values and 'line2' in values:
            self.values = {'line1': MRZLine(values['line1'], 0), 'line2': MRZLine(values['line2'], 1)}
            self.labels = ['line1', 'line2']
            return 
        
        super().__init__(values)
        self.labels = ['line1', 'line2']
        passport_num_digits=8
        
        self.first_name = Name(values['first_name'], LangEnum.ENG, type(self))
        self.last_name = Name(values['last_name'], LangEnum.ENG, type(self))
        self.gender = Gender(values['gender'])
        self.passport_num = Num(values['passport_num'])
        self.values = self._get_values()
        
    def _get_values(self):
        line1=['P<ISR']
        line1.append(self.last_name.get_value())
        line1.append('<')
        line1.append(self.first_name.get_value())
        line1 = ''.join(line1)
       
        line2=[self.passport_num.get_value(), '<', 'xISR', 
               self.birth_date.get_value(), 'x', self.gender.get_value(), 
               self.exp_date.get_value(), 'x', 
               self.id_num.get_value()[0], '<',
               self.id_num.get_value()[1:-1], '<', self.id_num.get_value()[-1], 
               '<<<xx']

        line2 = ''.join(line2)
        return {'line1': MRZLine(''.join(line1), 0), 'line2': MRZLine(''.join(line2), 1)}

