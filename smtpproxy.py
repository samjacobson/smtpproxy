#
# Copyright Sam Jacobson 2012
#
# This file is part of smtpproxy
#
# Smtpproxy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#

import smtplib
import smtpd2
import asyncore
import sendmail
import optparse
import logging
import sys
from logging.handlers import RotatingFileHandler


class SmtpProxy(smtpd2.SMTPServer):
	"""An Smtp Proxy that is similar to smtpd.PureProxy with a few exceptions:
		 * Support for SSL/TLS upstream STMP server
		 * No addition of X-Peer header (intended to be used on local LAN from naive clients to communicate with a modern server)
		 * Support for async relaying (TBD): use process_message_async which takes a callback with the result
		 """

	def __init__(self, localaddr, remoteaddr, starttls=False, credentials=None, logger=None):
		self._starttls = starttls
		self._credentials = credentials
		self._log = logger
		smtpd2.SMTPServer.__init__(self, localaddr, remoteaddr)

	def process_message(self, peer, mailfrom, rcpttos, data):
		self._log.info('%r - Forwarding message from sender %r, to %r (raw size %d)', peer, mailfrom, rcpttos, len(data))
		try:
			s = smtplib.SMTP()
			s.connect(*self._remoteaddr)
			if self._starttls:
				s.ehlo()		# a googleism
				s.starttls()
				s.ehlo()		# a googleism
			if self._credentials:
				s.login(*self._credentials)
			s.sendmail(mailfrom, rcpttos, data)
		except smtplib.SMTPRecipientsRefused, e:
			s.quit()
			self._log.info('%r - All recipients refused', peer)
			return '450 Upstream refused: %r' % repr(e.recipients)
		except smtplib.SMTPHeloError, e:
			s.quit()
			self._log.info('%r - Helo Error', peer)
			return '450 Upstream helo error'
		except smtplib.SMTPSenderRefused, e:
			s.quit()
			self._log.info('%r - Sender Refused', peer)
			return '450 Upstream refused sender'
		except smtplib.SMTPDataError, e:
			s.quit()
			self._log.info('%r - Data Error', peer)
			return '450 Upstream data error'
		self._log.info('%r - OK', peer)


if __name__ == '__main__':
	parser = optparse.OptionParser(usage='usage: %prog [options] <localport> <remoteaddr> <remoteport>', version='%prog 1.00')
	parser.add_option('-s', '--starttls', action='store_true', help='Use starttls with server', default=False)
	parser.add_option('-c', '--credentials', help='Specify credentials file (user on first line, password on second)', default=None)
	parser.add_option('-l', '--logpath', help='Specify logfile name', default=None)
	(options, args) = parser.parse_args()

	if len(args) < 3:
		parser.print_usage()
		raise SystemExit
	else:
		try:
			localport = int(args[0])
			remoteaddr = args[1]
			remoteport = int(args[2])
		except ValueError:
			print 'localport and remoteport must be integers'
			raise SystemExit

	if options.credentials:
		lines = file(options.credentials).read().split('\n')[:2]
		if len(lines) < 2:
			print 'Error in credentials file'
			raise SystemExit
		options.credentials = (lines[0], lines[1])

	formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
	logger = logging.getLogger('logs')
	if options.logpath:
		filehandler = RotatingFileHandler(options.logpath, maxBytes=1048576, backupCount=5)
		filehandler.setLevel(logging.getLevelName('DEBUG'))
		filehandler.setFormatter(formatter)
		logger.addHandler(filehandler)
	screenhandler = logging.StreamHandler(sys.stderr)
	screenhandler.setLevel(logging.getLevelName('DEBUG'))
	screenhandler.setFormatter(formatter)
	logger.addHandler(screenhandler)
	logger.setLevel(logging.DEBUG)

	server = SmtpProxy(('', localport), (remoteaddr, remoteport), starttls=options.starttls, credentials=options.credentials, logger=logger)
	try:
		logger.info('Ready')
		asyncore.loop()
	except KeyboardInterrupt:
		pass
	logger.info('Shutdown')

