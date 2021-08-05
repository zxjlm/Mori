import re
from rich import print
import os


def email_validator(email_string):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if(re.match(regex, email_string)):
        return True
    return False


def mail_subject_generator(subject_string):
    if '$$datetime$$' in subject_string:
        subject_string = subject_string.replace('$$datetime$$', "{time.strftime('%Y-%m-%d')}")
    return subject_string


def config_generator():
    is_email = input('whether to configure email?(y or n, default n):') or 'n'
    receivers = []
    mail_host = ''
    mail_user = ''
    mail_password = ''
    mail_port = -1
    mail_subject = ''

    if is_email == 'y':
        receivers = input(
            'email addresses will receive these email?(use "," to split. e.g. "abc@163.com, abc@gmail.com"):')
        receivers = [foo.strip() for foo in receivers.split(',')]
        for receiver in receivers:
            if not email_validator(receiver.strip()):
                print(f'{receiver} is invalid email')
                return False
        mail_host = input('emali server host (e.g. "smtp.163.com"): ') or "smtp.163.com"
        mail_user = input("email user: ")
        mail_password = input("email password: ")
        mail_port = int(input("email server port: "))
        mail_subject = input(
            'subject of each mail(you can use "$$datetime$$" to set daily mail subject, e.g. $$datetime$$ monitor report): ')
        mail_subject = mail_subject_generator(mail_subject)

    if os.path.isfile('./config.py'):
        overwrite = input('config.py is existed, overwrite it? (y/n, default is n)') or 'n'
        if overwrite == 'n':
            return True

    with open('./config.py', 'w') as f:
        f.write('import time\n\n')
        f.write('RECEIVERS = ["{}"]\n'.format('", "'.join(receivers)))
        f.write(f'MAIL_HOST = "{mail_host}"\n')
        f.write(f'MAIL_USER = "{mail_user}"\n')
        f.write(f'MAIL_PASS = "{mail_password}"\n')
        f.write(f'MAIL_PORT = {mail_port}\n')
        f.write('MAIL_SUBJECT = f"' + mail_subject + '"\n')

    return True
