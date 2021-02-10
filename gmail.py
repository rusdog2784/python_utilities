import re
import smtplib
from smtplib import SMTPAuthenticationError, SMTPException
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class GmailException(Exception):
    """Custom exception raised when an error occurs inside the Gmail class."""
    pass


class Gmail(object):
    """
    Simple email module utilizing Python's built-in smtplib package and a Gmail 
    server. It allows other Python files and applications to easily send SSL 
    encrypted emails using any Gmail account.
    """

    def __init__(self, gmail_username: str, gmail_password: str) -> None:
        """
        Initializer function for the Gmail class.
        """
        self._from = gmail_username
        # self.server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        self.server = smtplib.SMTP('smtp.gmail.com', 587)
        self.server.ehlo()
        self.server.starttls()
        self.server.ehlo()
        self.server.login(gmail_username, gmail_password)
        self.msg = MIMEMultipart()
        self.msg['From'] = self._from
        self._recipients = None
        
    def set_recipients(self, recipients: list) -> None:
        """
        Sets the email's recipients value. Verifies the following criteria for the provided
        recipients parameter (raises GmailException if criteria not met):
            - Must be a list.
            - Must not be empty.
            - Each recipient inside the list must be an email address.
        :param recipients: List of valid email addresses.
        :return: None.
        """
        if type(recipients) != list or not recipients:
            raise GmailException("You must provide a valid list of email addresses.")
        email_regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
        for recipient in recipients:
            if not re.search(email_regex, recipient) or type(recipient) != str:
                raise GmailException(f"{recipient} is not a valid email.")
        self.msg['To'] = ", ".join(recipients)
        self._recipients = recipients
        
    def set_subject(self, subject: str) -> None:
        """
        Sets the email's subject value. Verifies the following criteria for the provided
        subject parameter (raises GmailException if criteria not met):
            - Must be a string.
            - Must not be empty.
        :param subject: The subject string for the email.
        :return: None.
        """
        if type(subject) != str or not subject:
            raise GmailException("You must provide a valid subject string.")
        self.msg['Subject'] = subject
        
    def add_message(self, message: str) -> None:
        """
        Adds the provided message as a plain text MIMEText object to the email body.
        :param message: A string to add to the body of the email as plain text.
        :return: None.
        """
        body = MIMEText(message, 'plain')
        self.msg.attach(body)
        
    def add_html(self, html: str) -> None:
        """
        Adds the provided html string as a html MIMEText object to the email body.
        :param html: A string to add to the body of the email as HTML.
        :return: None.
        """
        body = MIMEText(html, 'html')
        self.msg.attach(body)
        
    def send_email(self) -> bool:
        """
        Attempts to send the email. If the email's required values (i.e.: Subject, To)
        haven't been set, then a GmailException is raised.
        :return: True if email is successfully sent. False if something 
            went wrong.
        """
        if not self.msg['Subject'] or not self.msg['To']:
            raise GmailException("You must set the email's subject (set_subject(subject)) "\
                "AND recipients (set_recipients(recipients)) values before sending.")
        try:
            self.server.sendmail(self._from, self._recipients, self.msg.as_string())
            self.server.close()
            return True
        except SMTPException:
            return False
