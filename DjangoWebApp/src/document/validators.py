from django.core.exceptions import ValidationError
from functools import reduce        
    
class LicenseValidators:
    def unique_num_validator(self, value):
        if len(value)!=4:
            raise ValidationError("Unique number should be of 4 digits.")
        
class PassPortValidators:
    def gender_validator(value):
        if value.upper() != 'F' or value.upper() != 'M':
            raise ValidationError("Gender should be 'F' (Female) or 'M' (Male).")
        return value