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

version = '0.1.6.6'

import hashlib

class bin2bmp:
    'Make an image file representation of any other file'
    output_file = None
    input_file = None
    width = 128
    im = None
    
    def __init__(self, output_file, input_file, output_type, width, *args, **kwargs):
    	self.chunks=0
    	self.output_type=output_type
    	self.width=width
    	self.bpp=32
    	self.basename=None
        self.set_output_type(output_type)
        self.compress=False
        self.sha2=""
        self.sign=False
    	   	    
    def set_output_file(self, basename):
        self.basename=basename
        if basename!=None:self.output_file=basename+'.'+b.output_ext
        
    def set_compressed(self):
        self.compress=True
        self.set_output_type('JPEG')
        
    def set_signed(self):
        self.sign=True
        
        
    def set_output_type(self, output_type):
        if output_type=='JPEG':
            self.output_type='JPEG'
            self.output_ext='jpg'
            self.input_colors='CMYK'
            self.white=(0,0,0,0)
    	    self.black=(0,0,0,255)  
            self.bpp=32
            self.white=(0,0,0,0)
            self.black=(0,0,0,255)
        elif output_type=='PNG':
            self.output_type='PNG'
            self.output_ext='png'
            self.input_colors='RGB'
            self.bpp=24
            self.black=(0,0,0)
            self.white=(255,255,255)
        elif output_type=='BMP':
            self.output_type='BMP'
            self.output_ext='bmp'
            self.input_colors='RGB'
            self.bpp=24
            self.black=(0,0,0)
            self.white=(255,255,255)
        elif output_type=='GIF':
            self.output_type='GIF'
            self.output_ext='gif'
            self.input_colors='1'
            self.bpp=1
            self.white=1
        else :
    	    print "Error. bin2bmp: Unrecognized type."
    	    exit(-1)
        self.set_output_file(self.basename)
	
    def create_image(self, buff):
        self.chunks=len(buff)*8/self.bpp
        print(self.chunks)
        if self.chunks%self.width==0 : height=self.chunks/self.width
        else : height=self.chunks/self.width+1
        self.im = Image.new(self.input_colors,(self.width,height),self.white)
        
        for i in range(self.chunks):
            x=i%(self.width)
            y=i/(self.width)
            #print x,y,i
            if self.output_type=='JPEG' :
                    color=(buff.pop(),buff.pop(),buff.pop(),buff.pop())
            elif self.output_type=='BMP' or self.output_type=='PNG':
                color=(buff.pop(),buff.pop(),buff.pop())
            elif self.output_type=='GIF':
            	if i%8==0:
            		color_byte=buff.pop()
        		color=1-((color_byte >> (7-i)%8) & 1)
            self.im.putpixel((x,y),color)

    def write_image(self):
        if self.compress==False:
            self.im.save(self.output_file,self.output_type,quality=100)
        else:
            self.im.save(self.output_file,self.output_type,quality=10)

    def hash_file(self, buff):
        h = hashlib.new('SHA256')
        h.update(buff)
        self.sha2 = h.hexdigest()
        return self.sha2

if __name__ == '__main__' :
    import os, sys, array,  getopt
    from PIL import Image
    
    verbose, compress, sign = False, False, False
    output_file, input_file, output_type, width = None, None, 'JPEG', 128 

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
        
    b=bin2bmp(output_file, input_file, output_type, width)
    

    if b.input_file == None:
        if len(args) !=0:
            b.input_file = args[0]
        else :
            print "**Error. No input filename specified.**"
            usage(sys.argv[0])
            exit(2)
            
    filename = os.path.split(b.input_file)[1]
    try:
        fileobj = open(b.input_file, mode='rb')
    except:
        print "Can't open "+sys.argv[1]+" for some reason."
        exit(-1)
    try:
        buff=array.array('B',fileobj.read())
        if sign == True:
            b.hash_file(buff)
            print (b.sha2+" *"+b.input_file)
            print len(buff)
            #print buff.itemsize
            hash_buffer = array.array('B',b.sha2+"SIZE"+str(len(buff))+"SIZE")
            #print repr(hash_buffer.tostring())
            #print hash_buffer.tostring()
            buff.extend(hash_buffer)
            #buff += hash_buffer
            #print repr(buff.tostring())
        for each in range(b.bpp/8-len(buff)%(b.bpp/8)):
            buff.extend(array.array('B','\xff'))
        buff.reverse()
    except:
        print "Could not read file into buffer.  File size too big?"
        exit(2) 
        
    print filename+':',len(buff),"bytes"
    
    if compress == True: b.set_compressed()
    if sign == True: b.set_signed()
    b.create_image(buff)
    if b.output_file == None : 
        b.output_file = filename+'.'+b.output_ext
    
    b.write_image()
    
    

