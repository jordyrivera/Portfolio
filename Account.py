import re
import werkzeug
import werkzeug.security



class Account:
    first_name = ""
    last_name = ""
    username = ""
    password = ""
    email = ""

    def __init__(self, first_name, last_name, username, password, email):
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.password = password
        self.email = email

    def validate_empty_inputs(self):
        if self.first_name == "" or self.last_name == "" or self.username == "" or self.password == "" or self.email == "":
            return False

    def validate_email(self):
        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        if (re.fullmatch(regex, self.email)):
            return True

    def password_hash(self):
        return werkzeug.security.generate_password_hash(self.password, method='pbkdf2:sha256', salt_length=8)


