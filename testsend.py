
import smtplib
import email.utils
from email.mime.text import MIMEText
import sys

if len(sys.argv) < 2:
	print 'python testsend.py <emailaddress>'
	print 'this will try to send to yourself using server on port 1025'
	sys.exit(100)

email = sys.argv[1]

# Create the message
msg = MIMEText('This is the body of the message.')
msg['To'] = email.utils.formataddr(('Recipient', email))
msg['From'] = email.utils.formataddr(('Author', email))
msg['Subject'] = 'Simple test message'

server = smtplib.SMTP('127.0.0.1', 1025)
server.set_debuglevel(True) # show communication with the server
try:
	server.sendmail(email, [email], msg.as_string())
finally:
	server.quit()

