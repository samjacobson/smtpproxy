
import smtplib
import email.utils
from email.mime.text import MIMEText

# Create the message
msg = MIMEText('This is the body of the message.')
msg['To'] = email.utils.formataddr(('Recipient', 'sam@eversoft.co.nz'))
msg['From'] = email.utils.formataddr(('Author', 'sam@eversoft.co.nz'))
msg['Subject'] = 'Simple test message'

server = smtplib.SMTP('127.0.0.1', 1025)
server.set_debuglevel(True) # show communication with the server
try:
	server.sendmail('sam@eversoft.co.nz', ['sam@eversoft.co.nz'], msg.as_string())
finally:
	server.quit()

