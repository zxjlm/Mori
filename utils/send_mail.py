# -*- coding: utf-8 -*-
"""
    :time: 2021/4/7 9:30
    :author: Harumonia
    :url: http://harumonia.moe
    :project: Mori
    :file: send_mail.py
    :copyright: © 2021 harumonia<zxjlm233@gmail.com>
    :license: MIT, see LICENSE for more details.
"""
from io import BytesIO


def send_mail(
    receivers: list,
    file_content: BytesIO,
    html: str,
    subject: str,
    mail_host: str,
    mail_user: str,
    mail_pass: str,
    mail_port: int = 0,
):
    """
    Send mail.
    Read necessary configuration from config.py.
    The mean of each argument can be found in README.md.
    Args:
        receivers: a list in which store receivers` email address.
                    such as [zxjlm233@gamil.com].
        file_content: a BytesIO type. Because when send email, mori also
                        send a CSV file of detail result.
                    The content is not absolutely generated but read from
                        the workbook of xlwt.
        html: it`s a html5 table of CSV, for more intuitive display.
        subject: literal meaning
        mail_host: literal meaning
        mail_user: username of mail sender.
        mail_pass: password of mail senders.
        mail_port: depend on your service.

    Returns:
        None

    Notes: It`s a universal function can use in other scene by a little
            modification.
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    sender = mail_user
    message = MIMEMultipart()
    message["From"] = sender
    message["To"] = ";".join(receivers)
    message["Subject"] = subject

    if html:
        message.attach(MIMEText(html, "html", "utf-8"))

    part = MIMEText(file_content.getvalue(), "vnd.ms-excel", "utf-8")
    part.add_header("Content-Disposition", "attachment", filename=f"{subject}.xls")
    message.attach(part)

    for count in range(4):
        try:
            if mail_port == 0:
                smtp = smtplib.SMTP()
                smtp.connect(mail_host)
            else:
                smtp = smtplib.SMTP_SSL(mail_host, mail_port)
            smtp.ehlo()
            smtp.login(mail_user, mail_pass)
            smtp.sendmail(sender, receivers, message.as_string())
            smtp.close()
            break
        except Exception as _e:
            print(_e)
            if count == 3:
                raise Exception("failed to send email")
