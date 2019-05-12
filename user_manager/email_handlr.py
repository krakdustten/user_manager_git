import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

smtp_server = "smtp.gmail.com"
port = 587
sender_email = "usermanager.info@gmail.com"
password = "Info1234"
context = ssl.create_default_context()


def sendEmail(receiver, subject="info", content="information", contenttyp="plain"):
    try:
        server = smtplib.SMTP(smtp_server,port)
        server.ehlo() # Can be omitted
        server.starttls(context=context) # Secure the connection
        server.ehlo() # Can be omitted
        server.login(sender_email, password)

        message = MIMEMultipart("alternative")
        message['Subject'] = subject
        message["From"] = sender_email
        message["To"] = receiver
        message.attach(MIMEText(content, contenttyp))
        server.sendmail(sender_email, receiver, message.as_string())
    except Exception as e:
        # Print any error messages to stdout
        print(e)
    finally:
        server.quit()


def sendConfirmation(userID, username, email):
    link = "http://127.0.0.1:5000/user/register/confirm?username=" + username + "&confirmID=" + userID
    html = "<p>Hi,<br>\n" \
           "<br>\n" \
           "Click this <a href=\"{link}\">link</a> to confirm your account.<br>\n" \
           "If the link doesn't show, copy \"" + link + "\" into your webbrowser." \
           "<br>\n" \
           "Greetings<br></p>"
    sendEmail(email, subject="Confirmation of account", content=html, contenttyp="html")
