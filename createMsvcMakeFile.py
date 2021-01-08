#!/usr/bin/env python

import os
import sys

MISC_PROGRAMS = 'MISC_PROGRAMS = misc/ace2sam\n'
CONFIG_MK = [
  'config.mk:\n',
  '\t@sed -e \'/^prefix/,/^LIBS/d;s/@Hsource@//;s/@Hinstall@/#/;s#@HTSDIR@#../htslib#g;s/@HTSLIB_CPPFLAGS@/-I$$(HTSDIR)/g;s/@CURSES_LIB@//g\' config.mk.in > $@\n\n'
]

class Args:
  def __init__(self, argv):
    if '-h' in argv[ -1 ]:
      msg = 'usage: {0} [--static]'.format( argv[ 0 ] )
      sys.exit( msg )

    self.m_static = '--static' in argv
    self.m_output = 'Makefile.msvc'

    if self.m_static:
      self.m_output += '.static'

class Makefile:
  def __init__(self):
    self.__parse()

  def appendSuffix(self, pattern, delim, suffix):
    oldText = pattern + delim
    for i,line in enumerate( self.m_lines ):
      begin = line.find( oldText )
      if begin < 0:
        continue
      end = begin + len( oldText )
      newText = pattern + suffix + delim
      self.m_lines[ i ] = line[ : begin ] + newText + line[ end : ] 

  def dump(self):
    n = len( self.m_lines )
    for i in xrange( n ):
      print( i,self.m_lines[ i ] ),

  def dumpRange(self, begin, end):
    for i in xrange( begin, end + 1 ):
      print( i,self.m_lines[ i ] ),

  def findLineIndex(self, pattern):
    for i,line in enumerate( self.m_lines ):
      if line.startswith( pattern ):
        return i
    return -1

  def getFilesInSection(self, pattern):
    n = len( self.m_lines )
    i = 0
    result = []
    begin,end = None,None

    while i < n:
      if not self.m_lines[ i ].startswith( pattern ):
        i += 1
        continue
      begin = i
      while i < n:
        if self.m_lines[ i ].startswith( '\n' ):
          end = i
          break
        i += 1

    i = begin + 1
    while i < end:
      result.append( self.m_lines[ i ] )
      i += 1

    return result, begin, end

  def insertLineList(self, index, lines):
    n = len( lines )
    i = n - 1
    while i >= 0:
      self.m_lines.insert( index, lines[ i ] )
      i -= 1
  
  def prepend(self, text):
    i = 0
    while self.m_lines[ i ].startswith( '#' ):
      i += 1

    self.m_lines.insert( i + 1, text )
 
  def removeLineStartsWith(self, pattern):
    i = len( self.m_lines ) - 1
    while i >= 0:
      if self.m_lines[ i ].startswith( pattern ):
        self.m_lines.pop( i )
      i -= 1

  def removeRange(self, begin, end):
    i = end
    while i >= begin:
      self.m_lines.pop( i )
      i -= 1

  def removeRecipe(self, pattern):
    begin,end = None,None
    n = len( self.m_lines )
    i = 0
    while i < n:
      if not self.m_lines[ i ].startswith( pattern ):
        i += 1
        continue

      begin = i
      while i < n:
        if self.m_lines[ i ].startswith( '\n' ):
          end = i
          break
        i += 1
      break

    if begin and end:
      while end >= begin:
        self.m_lines.pop( end )
        end -= 1

  def replaceAssign(self, name, value):
    i = len( self.m_lines ) - 1
    while i >= 0:
      if self.m_lines[ i ].startswith( name + ' ' ):
        line = self.m_lines[ i ]
        j = line.index( '=' ) + 1
        self.m_lines[ i ] = line[ :j ] + ' ' + value + '\n'
        break
      i -= 1

  def replaceLineStartsWith(self, old, new):
    for i,line in enumerate( self.m_lines ):
      if old in line:
        self.m_lines[ i ] = new       

  def replaceString(self, old, new):
    for i,line in enumerate( self.m_lines ):
      if old in line:
        self.m_lines[ i ] = line.replace( old, new )       
   
  def write(self, name):
    with open( name, 'w' ) as f:
      f.write( ''.join( self.m_lines ) )
        
  def __parse(self):
    self.m_lines = []
    with open( 'Makefile' ) as f:
      for line in f:
        self.m_lines.append( line )

def getCflags(static):
  result = r'/MD /O2 /TC /I$(TPS)\zlib\include /I$(TPS)\pthreads4w\include /I$(TPS)\wingetopt\include /I$(TPS)\pcre2\include /DWINGETOPT_SHARED_LIB'
  if static:
    result = result.replace( '/MD', '/MT' )
    result = result.replace( '\\include', '\\static\\include' )
    result = result.replace( 'WINGETOPT_SHARED_LIB', 'PTW32_STATIC_LIB /DLZMA_API_STATIC  /DPCRE2_STATIC' )
  return result

def getLdflags(static):
  result = r'/libpath:$(TPS)\pcre2\lib /libpath:$(TPS)\pthreads4w\lib /libpath:$(TPS)\wingetopt\lib /libpath:$(TPS)\zlib\lib /libpath:$(TPS)\bzip2\lib /libpath:$(TPS)\xz\lib'
  if static:
    result = result.replace( '\\lib', '\\static\\lib' )
  return result

def createMakefile( args ):
  makefile = Makefile()
  makefile.replaceAssign( 'CC', 'cl' )

  cflags = getCflags( args.m_static )
  makefile.replaceAssign( 'CFLAGS', cflags )

  ldflags = getLdflags( args.m_static )
  makefile.replaceAssign( 'LDFLAGS', ldflags )

  makefile.replaceAssign( 'LIBS', r'ws2_32.lib pcre2-posix.lib pcre2-8.lib zlib.lib pthreadVC2.lib wingetopt.lib libbz2.lib liblzma.lib' )

  makefile.replaceAssign( 'LZ4DIR', 'lz4' )
  makefile.replaceAssign( 'LZ4_LDFLAGS', '/libpath:$(LZ4DIR)' )

  makefile.removeRecipe( 'MISC_PROGRAMS =' )
  makefile.prepend( MISC_PROGRAMS )

  makefile.replaceAssign( 'ALL_LIBS', '$(LIBS)' )
  makefile.replaceString( 'bam_reheader.o ', 'bam_reheader.o sam_msvc.o ' )

  configMk = 'config.mk:'
  index = makefile.findLineIndex( configMk )
  makefile.removeRecipe( configMk )
  makefile.insertLineList( index, CONFIG_MK )

  makefile.removeLineStartsWith( '\techo \'#define HAVE_CURSES' )

  makefile.replaceString( '-c -o $@ $<', '/c /Fo$@ $<' )
  makefile.replaceString( '$(AR) -csru $@ $(LOBJS)', 'lib $(LOBJS) /out:$@' )
  makefile.replaceString( '$(CC) $(ALL_LDFLAGS) -o $@', 'link $(ALL_LDFLAGS) /out:$@.exe' )
  makefile.replaceString( '-lpthread', '' )
  makefile.replaceString( '$(AR) -rcs $@ $(LIBST_OBJS)', 'lib $(LIBST_OBJS) /out:$@' )

  makefile.replaceString( '$(CC) $(ALL_LDFLAGS)', 'link $(ALL_LDFLAGS)' )
  makefile.replaceString( '$(CC) $(LDFLAGS)', 'link $(LDFLAGS)' )
  makefile.replaceString( '-o $@', '/out:$@' )
  makefile.replaceString( '.o', '.obj' )
  makefile.replaceString( '.a', '.lib' )
  makefile.write( args.m_output )

def main( argv ):
  args = Args( argv )
  createMakefile( args )  

if '__main__' == __name__:
  main( sys.argv )
