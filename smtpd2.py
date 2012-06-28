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

"""\
smtpd2 adds a couple of minor things to the standard smtpd module:
	* process_message_async
	* substitute your own SMTP channel class
"""

import smtpd


class SMTPChannel(smtpd.SMTPChannel):

	# Implementation of base class abstract method
	def found_terminator(self):
		line = smtpd.EMPTYSTRING.join(self.__line)
		print >> smtpd.DEBUGSTREAM, 'Data:', repr(line)
		self.__line = []
		if self.__state == self.COMMAND:
			if not line:
				self.push('500 Error: bad syntax')
				return
			method = None
			i = line.find(' ')
			if i < 0:
				command = line.upper()
				arg = None
			else:
				command = line[:i].upper()
				arg = line[i+1:].strip()
			method = getattr(self, 'smtp_' + command, None)
			if not method:
				self.push('502 Error: command "%s" not implemented' % command)
				return
			method(arg)
			return
		else:
			if self.__state != self.DATA:
				self.push('451 Internal confusion')
				return
			# Remove extraneous carriage returns and de-transparency according
			# to RFC 821, Section 4.5.2.
			data = []
			for text in line.split('\r\n'):
				if text and text[0] == '.':
					data.append(text[1:])
				else:
					data.append(text)
			self.__data = smtpd.NEWLINE.join(data)

			def process_complete(status):
				self.__rcpttos = []
				self.__mailfrom = None
				self.__state = self.COMMAND
				self.set_terminator('\r\n')
				if not status:
					self.push('250 Ok')
				else:
					self.push(status)

			self.__server.process_message_async(process_complete, self.__peer,
												   self.__mailfrom,
												   self.__rcpttos,
												   self.__data)



class SMTPServer(smtpd.SMTPServer):
	"""A (slightly) better implementation of SMTPServer that allows replacement of the channel class (for overriding etc)
		Comes preconfigured with a (slightly) better implementation of SMTPChannel"""

	def __init__(self, localaddr, remoteaddr, _channel=None):
		self.clsChannel = SMTPChannel
		if _channel:
			self.clsChannel = _channel
		smtpd.SMTPServer.__init__(self, localaddr, remoteaddr)

	def handle_accept(self):
		pair = self.accept()
		if pair is not None:
			conn, addr = pair
			print >> smtpd.DEBUGSTREAM, 'Incoming connection from %s' % repr(addr)
			channel = self.clsChannel(self, conn, addr)

	def process_message_async(self, cb, peer, mailfrom, rcpttos, data):
		# Default implementation of _async just calls process_message giving old behaviour
		cb(self.process_message(peer, mailfrom, rcpttos, data))

