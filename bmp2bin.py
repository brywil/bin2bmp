#!/usr/bin/python
#"Copyright 2009-2017 Bryan Harris"
#
#This file is part of bin2bmp.py.
#
#    bin2bmp.py is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    bin2bmp.py is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with bin2bmp.py; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

from bin2bmp import bin2bmp

class bmp2bin(bin2bmp):
    def __init__(self, output_file, input_file, output_type, width, *args, **kwargs):
        bin2bmp.__init__(self, output_file, input_file, output_type, width, *args, **kwargs)
        
    
    def extract_bin(self):
        print(self.input_file)
        self.im = Image.open(self.input_file)
        pixeldata = self.im.tobytes()
        self.chunks=len(pixeldata)*self.bpp/8
        print self.bpp
        print(self.chunks)
        if self.sign==False:
            print ("We cannot guarantee file integrity without a signature");
        else:
            sz_start = pixeldata.find('SIZE')
            sz_end = pixeldata[sz_start+4:].find('SIZE')
            if sz_start != -1 and sz_end != -1:
                size = str(pixeldata[sz_start+4:sz_start+sz_end+4])
                print size
                my_hash = pixeldata[sz_start-64:sz_start]
                pixeldata = pixeldata[:sz_start-64]
            #print repr(pixeldata)
            print my_hash
            new_hash = b.hash_file(pixeldata)
            print new_hash
            if my_hash == new_hash: print ("OK")
            else: print("Hashes don't match.  File has changed")
        print len(pixeldata)
        return pixeldata
        
if __name__ == '__main__' :
    import os, sys, array,  getopt
    from PIL import Image
    
    sign = False
    verbose = False
    output_file, input_file, output_type, width = None, None, 'JPEG', 128 
    compress = False
    
    def usage(filename):
        print "usage:", filename, "<options> ... <filename>"
        print "-i, --input       \tfilename to visualize  [mandatory] "
        print "-w, --width       \twidth of output image"
        print "-o, --output      \toutput filename (default is <input_filename>.jpg)"
        print "-V, --verbose     \tprint lots of extra stuff"
        print "-b, --bmp        \treverts to the old bitmap style output(jpg is default)"
        print "-m, --monochrome \tone bit per pixel"
        print "-c, --compress   \thighly compressed jpeg"
        print "-p, --png        \toutput in png format"
        print "-s, --sign       \tappend an SHA256 signature to the image"
    
    try:                                
        opts, args = getopt.getopt(sys.argv[1:], 'w:ho:i:Vjbmvcps', ["width=","help", "output=", "input=","verbose", "bmp","monochrome","version","compress","png","sign"]) 
    except getopt.GetoptError,  err:
        print str(err) 
        usage(sys.argv[0])
        sys.exit(2)
    for o, a in opts:
        if o in ("-V", "--verbose"):
            print "Verbose"
            verbose = True
            print opts
            print args
        elif o in ("-v", "--version"):
            print sys.argv[0]+' '+version
            exit(0)
        elif o in ("-w", "--width"):
            if verbose==True :print "Width =", a
            try:
                width=int(a)
            except:
                print a+" does not appear to be an integer!"
                exit(2)
        elif o in ("-h", "--help"):
            if verbose == True : print "Help!"
            usage(sys.argv[0])
            exit(1)
        elif o in ("-o", "--output"):
            if verbose == True : print "Output =",  a
            output_file = a
        elif o in ("-i", "--input") :
            if verbose == True : print "Input =",  a
            input_file = a
        elif o in ("-b", "--bmp"):
            if verbose == True : print "Switching to bitmap format."
            output_type='BMP'
            if compress == True: 
                print "Bitmap compression not supported."
                compress = False
        elif o in ("-m","--monochrome"):
        	if verbose == True : print "Switching to monochrome."
        	output_type='GIF'
    	elif o in ("-c","--compress"):
    	    compress = True
    	    if output_type!='JPEG':print "compress implies JPEG, overriding"
    	    output_type='JPEG'
        elif o in ("-p","--png"):
            output_type='PNG'
        elif o in ("-s", "--sign"):
            sign = True
        else:
            assert False, "unhandled option"
    
    b = bmp2bin(output_file, input_file, output_type, width)
    
    if b.input_file == None:
        if len(args) !=0:
            b.input_file = args[0]
        else :
            print "**Error. No input filename specified.**"
            usage(sys.argv[0])
            exit(2)
    
    if sign==True: b.sign=True
    contents = b.extract_bin()
    #print b.extract_bin()
    fileobj = open(b.input_file[:-4], mode='w')
    
    fileobj.write(contents)
    print("Finished")
    
    
    
