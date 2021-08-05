import re
from rich import print
import os


def email_validator(email_string):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if(re.match(regex, email_string)):
        return True
    return False


def url_validator(url_string):
    re_url = re.match('https?://.*', url_string)
    return True if re_url else False


def mail_subject_generator(subject_string):
    if '$$datetime$$' in subject_string:
        subject_string = subject_string.replace('$$datetime$$', "{time.strftime('%Y-%m-%d')}")
    return subject_string


class ConfigHandler:
    def __init__(self) -> None:
        self.receivers = []
        self.mail_host = ''
        self.mail_user = ''
        self.mail_password = ''
        self.mail_port = -1
        self.mail_subject = ''

        self.proxy_url = ''

    def config_setter(self) -> bool:
        is_email = input('whether to configure email?(y or n, default n):') or 'n'
        if is_email == 'y':
            receivers = input(
                'email addresses will receive these email?(use "," to split. e.g. "abc@163.com, abc@gmail.com"):')
            self.receivers = [foo.strip() for foo in receivers.split(',')]
            for receiver in self.receivers:
                if not email_validator(receiver.strip()):
                    print(f'{receiver} is invalid email')
                    return False
            self.mail_host = input('emali server host (e.g. "smtp.163.com"): ') or "smtp.163.com"
            self.mail_user = input("email user: ")
            self.mail_password = input("email password: ")
            self.mail_port = int(input("email server port: "))
            mail_subject = input(
                'subject of each mail(you can use "$$datetime$$" to set daily mail subject, e.g. $$datetime$$ monitor report): ')
            self.mail_subject = mail_subject_generator(mail_subject)

        is_proxy = input('whether to configure proxy?(y or n, default n):') or 'n'
        if is_proxy == 'y':
            url_string = input('config your proxy pool url(read README.md first to confirm format of proxy dict.): ')
            if url_validator(url_string):
                self.proxy_url = url_string
            else:
                print('url format is invaid')
        return True

    def file_generator(self):
        if os.path.isfile('./config.py'):
            overwrite = input('config.py is existed, overwrite it? (y/n, default is n)') or 'n'
            if overwrite == 'n':
                return True

        with open('./config.py', 'w') as f:
            f.write('import time\n\n')
            f.write('RECEIVERS = ["{}"]\n'.format('", "'.join(self.receivers)))
            f.write(f'MAIL_HOST = "{self.mail_host}"\n')
            f.write(f'MAIL_USER = "{self.mail_user}"\n')
            f.write(f'MAIL_PASS = "{self.mail_password}"\n')
            f.write(f'MAIL_PORT = {self.mail_port}\n')
            f.write('MAIL_SUBJECT = f"' + self.mail_subject + '"\n')
            f.write('\n')
            f.write(f'PROXY_URL = "{self.proxy_url}"')

    @staticmethod
    def check_config_file():
        if os.path.isfile('./config.py'):
            try:
                import config
                return True
            except Exception as _e:
                ...
        else:
            print('config file is invalid, please check the content about config in README.md')
            return False

    def main(self):
        while True:
            if not self.config_setter():
                print('generator filed, retry. (you can use ^c to finish this loop.)')
                continue
            else:
                self.file_generator()
                return
