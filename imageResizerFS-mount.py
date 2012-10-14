#!/usr/bin/python
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

import fuse
fuse.fuse_python_api = (0, 2)

from time import time

import stat    # for file properties
import os      # for filesystem modes (O_RDONLY, etc)
import errno   # for error number codes (ENOENT, etc)
               # - note: these must be returned as negatives

from dbglog import dbg
from PIL import Image
import hashlib


"""
Image resizer file system that provides generation thumbnails for images
in given directory tree
"""

def isImage(path):
	"""
	Returns weather given node is image
	"""
	p = path.rfind('.')
	if (p != -1):
		ext = path[p + 1 : ].lower()
		return ext in ('jpg', 'jpeg', 'png')
	#endif
	return False
#enddef


def resizeImage(src, dest, width, height, quality):
	"""
	Resizes images
	"""
	try:
		im = Image.open(src)
		im.thumbnail((width, height), Image.ANTIALIAS)
		p = src.rfind('.')
		if (p != -1):
			ext = src[p + 1 : ].lower()
			im.save(dest, {'jpg' : 'JPEG', 'jpeg' : 'JPEG', 'png' : 'PNG'}[ext], quality = int(quality))
		else:
			raise Exception('Unknown extension')
		#endif
	except:
		dbg.logTB()
		raise
	#endtry
#enddef


class ImageResizerFS(fuse.Fuse):
	"""
	ImageResizerFS
	"""
	_openedFiles = None
	
	
	def __init__(self, *args, **kw):
		"""
		Init
		"""
		fuse.Fuse.__init__(self, *args, **kw)

		print 'Init complete.'
		
		self._openedFiles = {}
	#enddef
	
	
	def _getCacheFilename(self, path):
		"""
		Returns cache filename
		"""
		return self.cache_dir + ('/%sx%s_' % (self.width, self.height)) + hashlib.md5(path).hexdigest()
	#enddef
	
	
	def main(self, *a, **kw):
		"""
		main
		"""
		dbg.filename = self.log
		dbg.log('Root: %s', self.root)
		dbg.log('Cache dir: %s', self.cache_dir)
		if (not os.path.exists(self.cache_dir)):
			os.makedirs(self.cache_dir)
		#endif
		self.width = int(self.width)
		self.height = int(self.height)
		dbg.log('Size: %sx%s', (self.width, self.height))
		dbg.log('Init complete.')
		
		return fuse.Fuse.main(self, *a, **kw)
	#enddef
	
	
	def getattr(self, path):
		"""
		Returns node attributes
		"""

		dbg.log('*** getattr %s', path)

		try:
			if (isImage(path)):
				fname = self._getCacheFilename(path)
				dbg.log('fname: %s', fname)
				
				if (not os.path.exists(fname)):
					st = os.stat(self.root + path)
				else:
					st = os.stat(fname)
				#endif
			else:
				st = os.stat(self.root + path)
			#endif
		except:
			dbg.logTB()
		#endtry
		
		return st
	#enddef


	def readdir(self, path, offset):
		"""
		Returns list of nodes in directory
		"""
		dbg.log('*** readdir %s, %s', (path, offset))
		for entry in os.listdir(self.root + path):
			if (isImage(entry) or os.path.isdir(self.root + path + '/' + entry)):
				yield fuse.Direntry(entry)
			#endif
		#endfor
	#enddef


	def open(self, path, flags):
		"""
		Opens given file
		"""
		dbg.log('*** open %s, %s', (path, flags))
		if (not self._openedFiles.has_key(path)):
			if (not isImage(path)):
				self._openedFiles[path] = open(self.root + path, 'rb')
			else:
				fname = self._getCacheFilename(path)
				dbg.log('fname: %s', fname)
				
				if (not os.path.exists(fname)):
					dbg.log('Write thumbnail %s for path %s' % (fname, path))
					resizeImage(self.root + path, fname, self.width, self.height, self.quality)
				#endif
				
				self._openedFiles[path] = open(fname, 'rb')
			#endif
		#endif
		return 0
	#enddef


	def read(self, path, length, offset):
		"""
		Reads given file
		"""
		dbg.log('*** read %s, %s, %s', (path, length, offset))
		self._openedFiles[path].seek(offset)
		return self._openedFiles[path].read(length)
	#enddef


	def release(self, path, flags):
		"""
		Release given file
		"""
		dbg.log('*** release %s, %s', (path, flags))
		self._openedFiles[path].close()
		del self._openedFiles[path]
		return 0
	#enddef
#endclass


if __name__ == '__main__':
	usage = """ImageResizerFS: image resizer file system that provides generation thumbnails for images in given directory tree\n""" + fuse.Fuse.fusage

	fs = ImageResizerFS(version = "%prog " + fuse.__version__, usage = usage, dash_s_do = 'setsingle')
	fs.parser.add_option(mountopt = "root", dest = "root", metavar = "PATH", default = "/", help = "Root directory")
	fs.parser.add_option(mountopt = "log", dest = "log", metavar = "PATH", default = "/tmp/imageResizerFS.log", help = "Log filename")
	fs.parser.add_option(mountopt = "cache_dir", dest = "cache_dir", metavar = "PATH", default = "/tmp/imcache", help = "Cache dir")
	fs.parser.add_option(mountopt = "width", dest = "width", metavar = " ", default = "1024", help = "Width")
	fs.parser.add_option(mountopt = "height", dest = "height", metavar = " ", default = "768", help = "Height")
	fs.parser.add_option(mountopt = "quality", dest = "quality", metavar = " ", default = "85", help = "Quality")
	if (not fs.parse(values = fs, errex = 1).getmod('showhelp')):
		fs.flags = 0
		fs.multithreaded = 0
		fs.main()
	#endif
#endif
