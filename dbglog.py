#
# Copyright 2009, Josef Kyrian <josef.kyrian@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import inspect
import datetime
import sys
import traceback


class dbglog:
	filename = None
	
	def log(self, s, args = None):
		"""
		Logs some text
		"""
		if (args):
			try:
				s = s % args
			except Exception, e:
				s  = str(e)
			#endtry
		#endif
		
		stack = inspect.stack()
		stack.reverse()
		frame = stack[-2]
		src = filter(lambda p: p not in('', '.'), frame[1].split('/'))
		if (src[-1][-3:] == '.py'):
			src[-1] = src[-1][:-3]
		#endif
		params = inspect.getargvalues(frame[0])
		srcFunctionName = '.'.join(src) + '.' + frame[3]
		srcLine = frame[2]
		
		dt = datetime.datetime.today()
		logEntry = '[%04d/%02d/%02d %02d:%02d:%02d] %s {%s():%s}\n' % (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, s, srcFunctionName, srcLine)
		if (self.filename):
			f = open(self.filename, 'a+')
			f.write(logEntry)
			f.close()
		else:
			print logEntry
		#endif
	#enddef
	
	
	def logTB(self):
		"""
		Fce zaloguje a vrati text vyjimky, ktera nam probublava
		z nizsi urovne a my ji zachycujeme v try except
		@return string formatovany text z tracebacku
		"""
	
		(type_exc, value, tb) = sys.exc_info()
		exc_info = ''.join(traceback.format_exception(type_exc, value, tb))
	
		self.log("Exception: %s", str(exc_info))
	
		del tb
		return exc_info
	#enddef
#endclass

dbg = dbglog()