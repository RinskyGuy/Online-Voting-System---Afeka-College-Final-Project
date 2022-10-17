import os
import pandas as pd
import random
import string
import random
from functools import reduce
from PIL import Image, ImageFont, ImageDraw 
from datetime import date, timedelta, datetime
from pyluach import dates  # for hebrew dates
import ast
from utils.recognition.document_recognition.documents import ID, DRIVING_LICENSE, PASSPORT
from django.contrib.staticfiles.storage import staticfiles_storage

TOP_LEFT = 'top_left'
TOP_RIGHT = 'top_right'

ID_LENGTH = 9
LICENSE_NUM_LENGTH = 7
PASSPORT_NUM_LENGTH = 8
UNIQUE_LICENSE_NUM_LENGTH = 4

#ID_DOC = 'id'
#DRIVING_LICENSE_DOC = 'driving_license'
#PASSPORT_DOC = 'passport'

HEB_STR = 'hebrew string'
ENG_STR = 'english string'
NUM = 'numeric'
HEB_DATE = 'hebrew date'
GEORGIAN_DATE = 'georgian date'

root_dir = staticfiles_storage.path('doc_generation')
data_dir = os.path.join(root_dir, 'data')
dest_path = os.path.join(root_dir, 'docs')

class DocGenerator:
    def __init__(self, img_path, gender=None):
        self.gender = random.choice(['F','M']) if gender is None else gender
        self.first_name = self._gen_first_name()
        self.last_name = self._gen_last_name()
        self.id_num = self._gen_id_num()
        self.gen_date, self.exp_date = self._gen_doc_dates()
        self.birth_date = self._gen_birth_date()
        self.img_path = img_path
        
    def generate_data(self, data=None):
        self.first_name = self.first_name if data is None else data['heb_first_name'] + '%' + data['first_name']
        self.last_name = self.last_name if data is None else data['heb_last_name'] + '%' + data['last_name']
        self.id_num = self.id_num if data is None else data['id_num']
        self.birth_date = self.birth_date if data is None else data['birth_date']
        
        return {'first_name':self.first_name,
                'last_name':self.last_name,
                'id_num':self.id_num,
                'birth_date':self.birth_date,
                'gen_date':self.gen_date,
                'exp_date':self.exp_date,
                'img_path':self.img_path}
    
    def get_data(self):
        try:
            data = {'first_name':self.first_name.split('%')[1].replace('(', ' ('),
                    'heb_first_name':self.first_name.split('%')[0].replace(')', ' )'),
                    'last_name':self.last_name.split('%')[1].replace('(', ' ('),
                    'heb_last_name':self.last_name.split('%')[0].replace(')', ' )'),
                    'id_num':self.id_num,
                    'birth_date':datetime.strptime(self.birth_date, '%d.%m.%Y'),
                    'gen_date':datetime.strptime(self.gen_date, '%d.%m.%Y'),
                    'exp_date':datetime.strptime(self.exp_date, '%d.%m.%Y')}
        except:
            data = {'first_name':self.first_name.split('%')[1],
                    'heb_first_name':self.first_name.split('%')[0],
                    'last_name':self.last_name.split('%')[1],
                    'heb_last_name':self.last_name.split('%')[0],
                    'id_num':self.id_num,
                    'birth_date':self.birth_date,
                    'gen_date':self.gen_date,
                    'exp_date':self.exp_date}

        return data

        
    def _get_first_names(self):
        # generate name data
        file = open(os.path.join(data_dir, 'first_names.txt'), 'r', encoding='utf-8')

        line = file.readline()
        first_names_df = pd.DataFrame(columns=line.strip().split("\t"))

        while True:
            line = file.readline()
            if not line:
                break

            splitted = line.strip().split("\t")
            first_names_df = first_names_df.append({col:val for col,val in zip(first_names_df.columns, splitted)}, ignore_index=True)

        return first_names_df
    
    def _get_last_names_df(self):
        # generate last name data
        file = open(os.path.join(data_dir, 'last_names.txt'), 'r', encoding='utf-8')

        line = file.readline()
        last_names_df = pd.DataFrame(columns=line.strip().split("\t"))

        while True:
            line = file.readline()
            if not line:
                break

            splitted = line.strip().split("\t")
            last_names_df = last_names_df.append({col:val for col,val in zip(last_names_df.columns, splitted)}, ignore_index=True)

        return last_names_df

    def _gen_first_name(self):
        first_names_df = self._get_first_names()
        names_df = first_names_df[(first_names_df['gender']==self.gender) | (first_names_df['gender']=='b')]
        name = names_df.sample(n=1, weights=names_df['rank'])
        
        #print(name['hebrew'].values[0] +'%' +name['english'].values[0])
        name = name[['hebrew','english']].values[0]

        changed_name = random.randrange(10)
        if changed_name == 1:
            prev_name = names_df.sample(n=1, weights=names_df['rank'])
            prev_name = prev_name[['hebrew','english']].values[0]
            name[0] = name[0] + ')' + prev_name[0] + '('
            name[1] = name[1] + '(' + prev_name[1] + ')'
        name[1] = '%'+name[1]
        return ''.join(name)

    def _gen_last_name(self):   
        last_names_df = self._get_last_names_df()
        name = last_names_df.sample(n=1)
        name = name[['hebrew','english']].values[0]

        changed_name = random.randrange(10)
        if changed_name == 1:
            prev_name = last_names_df.sample(n=1)
            prev_name = prev_name[['hebrew','english']].values[0]
            name[0] = name[0] + ')' + prev_name[0] + '('
            name[1] = name[1] + '(' + prev_name[1] + ')'
        name[1] = '%'+name[1]
        return ''.join(name)

    def _id_validator(self, value):
        assert len(value)==9, f'A valid ID number is a sequence of 9 digits, but got {len(value)}.'
     
        seq = [1,2,1,2,1,2,1,2,1]
        result = []

        for digit1, digit2 in zip(value,seq):
            if digit1 < 0 or digit1 > 9:
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

    def _gen_id_num(self):
        id_num = []
        id_num+= [random.randrange(3),random.randrange(2),random.randrange(2)]

        digits = range(10)
        id_num+=random.sample(digits, ID_LENGTH-3)
        id_num

        while not self._id_validator(id_num):
            id_num = []
            id_num+= [random.randrange(3),random.randrange(2),random.randrange(2)]

            digits = range(10)
            id_num+=random.sample(digits, ID_LENGTH-3)
            id_num

        id_num = [str(digit) for digit in id_num] 
        return ''.join(id_num)

    def _gen_rand_date(self, start_year=None, end_year=None):
        if start_year is None:
            start_year = 2021 - random.ranrange(6)
            end_year = start_year + 10
        start_date = date(start_year, 1, 1)
        end_date = date(end_year, 1, 1)

        time_between_dates = end_date - start_date
        days_between_dates = time_between_dates.days
        random_number_of_days = random.randrange(days_between_dates)
        
        return start_date + timedelta(days=random_number_of_days)
    
    def _gen_birth_date(self):
        return self._gen_rand_date(1970, 2000).strftime("%d.%m.%Y")

    def _gen_doc_dates(self):
        today = date.today()    
        gen_date = self._gen_rand_date(today.year-9, today.year)
        exp_date = self._gen_rand_date(gen_date.year+10, gen_date.year+11)

        return gen_date.strftime("%d.%m.%Y"), exp_date.strftime("%d.%m.%Y")
    
    def _gen_num(self, num_len):
        return ''.join(random.choice(string.digits[1:10]) for i in range(num_len))

class IdGenerator(DocGenerator):
    def __init__(self, img_path, gender=None):
        super().__init__(img_path, gender)
    
    def get_data(self):
        data = super().get_data()
        data.update({'heb_birth_date':self._get_heb_date(datetime.strptime(self.birth_date, '%d.%m.%Y')),
                     'heb_gen_date':self._get_heb_date(datetime.strptime(self.gen_date, '%d.%m.%Y')),
                     'heb_exp_date':self._get_heb_date(datetime.strptime(self.exp_date, '%d.%m.%Y'))})
        
        return data
    
    def _get_heb_date(self, date_obj):
        date_obj = dates.GregorianDate(date_obj.year, date_obj.month, date_obj.day)
        return date_obj.to_heb().hebrew_date_string()

class DrivingLicenseGenerator(DocGenerator):
    def __init__(self, img_path, gender=None):
        super().__init__(img_path, gender)
        self.license_num = self._gen_num(LICENSE_NUM_LENGTH)
        self.unique_num = self._gen_num(UNIQUE_LICENSE_NUM_LENGTH)
        self.address = self._gen_address()
        self.license_type = self._gen_license_type()
    
    def generate_data(self, data=None):
        data = super().generate_data(data)
        data.update({'license_num':self.license_num,
                     'unique_num':self.unique_num,
                     'address':self.address,
                     'license_type':self.license_type})
        return data
    
    def get_data(self):
        data = super().get_data()
        data.update({'license_num':self.license_num,
                     'unique_num':self.unique_num,
                     'address':self.address.replace('%', ' ')})
        
        return data
    
    def _get_addresses_df(self):
        addresses = []

        file = open(os.path.join(data_dir, 'israel_streets.txt'), 'r', encoding='utf-8')
        line = file.readline()  # columns

        columns = line.strip().split("\t")
        street_idx = columns.index('street')
        city_idx = columns.index('city')

        while True:
            line = file.readline()
            if not line:
                break

            splitted = line.strip().split("\t")
            addresses.append(["".join(splitted[city_idx].rstrip()), "".join(splitted[street_idx].rstrip())])

        addresses_df = pd.DataFrame(addresses, columns=['city', 'street'])
        return addresses_df
    
    def _gen_address(self):
        addresses_df = self._get_addresses_df()
        address_row = addresses_df.sample(n=1)
        city = address_row['city'].values[0]
        street = address_row['street'].values[0]
        house_num = random.randrange(1,50)
        return street + "%" + str(house_num) + "%" + city
    
    def _gen_license_type(self):
        types = ['A', 'A1', 'A2', 'B', 'C', 'C1', 'D', 'D1', 'D2', 'D3', 'E', '1']

        chance = random.randrange(50)
        if chance == 1:
            num_types = random.randrange(4)
        else:
            num_types = 1
        return ' '.join(random.choices(types, k=num_types))

class PassportGenerator(DocGenerator):
    def __init__(self, img_path, gender=None):
        super().__init__(img_path, gender)
        self.country = self._gen_country()
        self.gender = self._gen_gender()
        self.passport_num = self._gen_num(PASSPORT_NUM_LENGTH)
        
    def generate_data(self, data=None):
        data = super().generate_data(data)
        data.update({'country':self.country,
                     'gender':self.gender,
                     'passport_num':self.passport_num})
        return data
    
    def get_data(self):
        data = super().get_data()
        data.update({'gender':self.gender.split('%')[1],
                     'passport_num':self.passport_num})
        
        return data
    
    def _get_countries_df(self):
        countries = []

        file = open(os.path.join(data_dir, 'countries.txt'), 'r', encoding='utf-8')
        line = file.readline()  # columns

        while True:
            line = file.readline()
            if not line:
                break

            splitted = line.strip().split(",")
            countries.append([splitted[1],splitted[0]])

        countries_df = pd.DataFrame(countries, columns=['heb_country', 'eng_country'])
        return countries_df

    def _gen_country(self):
        not_israel = random.randrange(10)
        if not_israel == 1:
            countries_df = self._get_countries_df()
            country = countries_df.sample(n=1).values[0]
            return '%'.join(country)
        else:
            return 'ישראל%ISRAEL'

    def _gen_gender(self):
        if self.gender == 'M' or self.gender == 'm':
            return 'ז%M'
        else:
            return 'נ%F'


class DrawDoc:
    def __init__(self, doc_type):
        self.doc_type = doc_type
    
    def _get_fields(self):
        templates_dir = os.path.join(root_dir, 'doc_templates')
        fields_dir = os.path.join(root_dir, 'fields')
        
        if self.doc_type == ID:
            template_path = os.path.join(templates_dir, 'id_template.jpg')
            fields_file = os.path.join(fields_dir, 'id_fields.txt')

        elif self.doc_type == DRIVING_LICENSE:
            template_path = os.path.join(templates_dir, 'driving_license_template.jpg')
            fields_file = os.path.join(fields_dir, 'driving_license_fields.txt')

        elif self.doc_type == PASSPORT:
            template_path = os.path.join(templates_dir, 'passport_template.jpg')
            fields_file = os.path.join(fields_dir, 'passport_fields.txt')

        file = open(fields_file, "r")
        contents = file.read()
        fields = ast.literal_eval(contents)
        file.close()

        return fields, template_path
    
    def gen_doc(self, gen):
        if isinstance(gen, DocGenerator):
            data = gen.generate_data()
        else:
            assert isinstance(gen, dict), f'Expected data to be of type DocGenerator or dictionary, but got {type(data)}.'
            data = gen
        
        fields, template_path = self._get_fields()

        image = Image.open(template_path) 
        draw = ImageDraw.Draw(image)

        for col in list(data.keys()):
            if col in fields:
                vals = self._get_val(data[col], date='date' in col)
                field = fields[col]
                self._write_field_to_img(draw, field, vals, fields['font_size'])

        if isinstance(data['img_path'], str):
            img = Image.open(data['img_path'])
        else:
            img = data['img_path']
        self._gen_image(image, img, fields['img_size'], fields['img_top_left'])

        if self.doc_type == PASSPORT:
            last_name = self._get_field_str(ENG_STR, self._get_val(str(data['last_name']))[1])
            first_name = self._get_field_str(ENG_STR, self._get_val(str(data['first_name']))[1])
            passport_num = self._get_val(str(data['passport_num']))
            birth_date = self._get_val(data['birth_date'], date=True)
            gender = self._get_val(str(data['gender']))
            exp_date = self._get_val(data['exp_date'], date=True)
            id_num = self._get_val(str(data['id_num']))

            mrz = self._gen_mrz(last_name,first_name, passport_num, birth_date, gender, exp_date,id_num)
            self._write_field_to_img(draw, fields['mrz'], mrz, fields['font_size'])

        doc_path = os.path.join(dest_path, data['id_num'] + '_' + self.doc_type +'.jpg')
    
        image.save(doc_path)
        return image
    
    def _get_val(self, data_val, date=False):
        if date:
            if isinstance(data_val, str):    
                vals = datetime.strptime(data_val, '%d.%m.%Y')
            else:
                vals = data_val
            assert isinstance(vals, datetime), f'Expected date to be of type str or datetime, but got {type(data_val)}.'
        elif '%' in data_val:
            vals = data_val.split('%')
        else:
            vals = data_val

        return vals

    def _gen_image(self, template, img, img_size, top_left):
        img = img.resize(img_size)
        #template.paste(img, top_left, img)
        template.paste(img, top_left)

    def _get_date_format(self, val):
        if self.doc_type == ID or self.doc_type == DRIVING_LICENSE:
            return val.strftime("%d.%m.%Y")
        if self.doc_type == PASSPORT:
            return val.strftime("%d/%m/%Y")

    def _get_id_format(self, val):
        if self.doc_type == ID:
            return val[0] + " " + val[1:-1] + " " + val[-1]
        if self.doc_type == DRIVING_LICENSE:
            return "ID "+ val
        if self.doc_type == PASSPORT:
            return val[0] + "-" + val[1:-1] + "-" + val[-1]

    def _append_name(self, names):
        names = names.split(' ')
        line = []
        if len(names)>1:
            for name in names:
                name = name.replace(')','')
                name = name.replace('(','')
                line.append(name.upper())
                line.append('<')
        else:
            return names[0].upper()
        return ''.join(line)

    def _gen_mrz(self, last_names, first_names, passport_num, birth_date, gender, exp_date, id_num):
        line1=['P<ISR']
        line1.append(self._append_name(last_names))
        line1.append('<')
        line1.append(self._append_name(first_names))
        line1 = ''.join(line1)
        while(len(line1)<44):
            line1+='<'

        line2=[passport_num, '<', str(random.randint(0,9)), 'ISR',birth_date.strftime("%y%m%d"),
              str(random.randint(0,9)), gender[1].upper(), exp_date.strftime("%y%m%d"), str(random.randint(0,9)), id_num[0], '<',
              id_num[1:-1], '<', id_num[-1], '<<<', str(random.randint(0,9)), str(random.randint(0,9))]

        line2 = ''.join(line2)

        return (' '.join(line1), ' '.join(line2))

    def _get_field_str(self, field_type, field_val):
        if field_type == ENG_STR:
            if '(' in field_val:
                if self.doc_type != PASSPORT:
                    field_val = field_val.split('(')[0]
                else:
                    field_val = field_val.replace('(', ' (')
            return field_val.upper()

        if field_type == HEB_STR:
            if ')' in field_val:
                if self.doc_type != PASSPORT:
                    field_val = field_val.split(')')[0]
                else:
                    field_val = field_val.replace(')', ' )')
            return field_val[::-1] # reverse hebrew string

        if field_type == GEORGIAN_DATE:
            return self._get_date_format(field_val)

        if field_type == HEB_DATE:
            field_val = dates.GregorianDate(field_val.year, field_val.month, field_val.day)
            return field_val.to_heb().hebrew_date_string()[::-1]

        if field_type == ID:
            field_val = str(field_val)
            while len(field_val)<9:
                field_val = '0'+field_val
            return self._get_id_format(field_val)

        if field_type == NUM:
            return str(field_val)
        
    def _write_right_to_left(self, draw, text, top_right, font, font_size, color=(0,0,0)):
        font = ImageFont.truetype(font,font_size)
        size = draw.textsize(text=text, font=font)
        top_left = (top_right[0] - size[0], top_right[1])
        draw.text(top_left, text, font=font, fill=color)

    def _write_left_to_right(self, draw, text, top_left, font, font_size, color=(0,0,0)):
        font = ImageFont.truetype(font, font_size)    
        draw.text(top_left, text, font=font, fill=color)

    def _write_field_to_img(self, draw, field, vals, font_size):
        fonts_dir = os.path.join(root_dir, 'fonts')

        for i,field_type in enumerate(field['type']):
            if isinstance(vals, list) or isinstance(vals, tuple):
                text = self._get_field_str(field_type, vals[i])
            else:
                text = self._get_field_str(field_type, vals)

            coords_pos = field['coords']['pos'][i]
            coords_point = field['coords']['point'][i]
            
            font = os.path.join(fonts_dir, field['font'][i])

            if coords_pos == TOP_LEFT:
                self._write_left_to_right(draw, text, coords_point, font, 
                                    field['font_size'] if 'font_size' in field else font_size,
                                    color=tuple(field['color'][i]) if 'color' in field else (0,0,0))
            else:
                self._write_right_to_left(draw, text, coords_point, font,
                                    field['font_size'] if 'font_size' in field else font_size,
                                    color=tuple(field['color'][i]) if 'color' in field else (0,0,0))