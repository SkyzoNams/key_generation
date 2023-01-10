import smtplib
from key_generation.src.Config import Config as Gc
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class TwoFA(object):
    def __init__(self, email: str = None, user_name: str = None):
        self.user_name = user_name
        self.password_salt = Gc().return_config_twoFA(twoFA_password_salt=True)
        self.secret_key = Gc().return_config_twoFA(twoFA_secret_key=True)

        """self.password_salt = Encrypt().decrypt_message(Gc().return_config_twoFA(twoFA_password_salt=True))
        self.secret_key = Encrypt().decrypt_message(Gc().return_config_twoFA(twoFA_secret_key=True))"""
        self.email_addr = email
        self.url = Gc().return_config_twoFA(twoFA_url=True)

    def email(self, mail_body: str = None, subject: str = None):
        mailserver = smtplib.SMTP(Gc().return_config_twoFA(twoFA_SMTP_URL=True), Gc().
                                  return_config_twoFA(twoFA_SMTP_port=True))
        mailserver.ehlo()
        mailserver.starttls()
        mailserver.login(Gc().return_config_twoFA(twoFA_mailserver_user=True),
                         Gc().return_config_twoFA(twoFA_mailserver_password=True))

        msg = MIMEMultipart('related')
        msg['Subject'] = subject
        msg['From'] = Gc().return_config_twoFA(twoFA_mailserver_user=True)
        msg['To'] = self.email_addr
        body = MIMEText(mail_body, 'html')
        msg.attach(body)

        mailserver.sendmail(msg['From'], msg['To'], msg.as_string())
        mailserver.quit()
        return {'Email Confirmation Sent': True}







