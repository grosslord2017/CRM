import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings

class MailSender(object):

    def __init__(self, to, subject, body):
        self.msg = MIMEMultipart("alternative")
        self.email = "corpcrm.info@gmail.com"
        self.password = settings.EMAIL_PASSWORD
        self.sent_from = self.email
        self.to = to
        self.subject = subject
        self.body = MIMEText(body)

        self.create_massage()

    def create_massage(self):
        self.msg["From"] = self.sent_from
        self.msg["To"] = self.to
        self.msg["Subject"] = self.subject
        self.msg.attach(self.body)

    def connect_server(self):
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(self.email, self.password)
        server.sendmail(self.sent_from, self.to, self.msg.as_string())
        server.quit()

def send_mail(to, subject, body):
        create = MailSender(to, subject, body)
        create.connect_server()


