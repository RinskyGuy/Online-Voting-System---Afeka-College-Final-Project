from utils.recognition.document_recognition.regex import StringValidator

def unique_code_validator(value:str):
    if StringValidator.hex_chars(value, 64):
        return True
    return False

def party_code_validator(value):
    if StringValidator.hex_chars(value, 6):
        return True
    return False