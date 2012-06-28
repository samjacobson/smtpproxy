
import smtplib
import email.utils
from email.mime.text import MIMEText
import sys

if len(sys.argv) < 4:
	print 'python testsend.py <port> <from> <to>'
	print 'this will try to send to yourself using server on port 1025'
	sys.exit(100)

port, frm, to = sys.argv[1:4]
int(port)

# Create the message
msg = MIMEText('This is the body of the message.')
msg['To'] = email.utils.formataddr(('Recipient', frm))
msg['From'] = email.utils.formataddr(('Author', to))
msg['Subject'] = 'Simple test message'

server = smtplib.SMTP('127.0.0.1', port)
server.set_debuglevel(True) # show communication with the server
try:
	server.sendmail(frm, [to], msg.as_string())
finally:
	server.quit()

