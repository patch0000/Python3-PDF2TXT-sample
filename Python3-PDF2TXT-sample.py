# -*- coding: utf-8 -*-
"""
Created on Thu Jan 18 14:36:53 2018

@author: patch0000
2018/04/28

Python3-PDF2TXT-sample

As far as I have investigated, There are 4 pdfminer in the world.
 (1)pdfminer for python2.x
 (2)pdfminer.six for python2.x and python3.x
 (3)pdfminer3k for python3.x
 (4)pdfminer2 python2.x and python3.x

They are same name but function arguments and library tree is different.
This program used pdfminer.six.

For windows Anaconda users.
conda config --show
conda config --set remote_read_timeout_secs 6000
conda config --show
conda install -c conda-forge pdfminer.six
and wait long time.


There are two ways to extract text from PDF.

(1)PDFPage.create_pages
This program uses PDFPage.create_pages.
Maybe there are sentences that can not be extracted occasionally.
PDF has a different structure depending on the author and software.
Unfortunately I could not make this program versatile.
This program is a hint for cases where TextBox is not used.
If this program does not work for you, please refer to the See Also section.

(2)PDFPage.get_pages
Since it is output at once, I can not recognize a page break.
Also, in the case of English PDF, the space between words disappears
in some cases. So I didn't use this function.

See Also.
https://euske.github.io/pdfminer/programming.html
http://denis.papathanasiou.org/archive/2010.08.04.post.pdf
http://a244.hateblo.jp/entry/2017/08/26/001050
http://irukanobox.blogspot.jp/2017/03/python3pdf.html

"""

from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTFigure, LTChar, LTImage
from pdfminer.pdfpage import PDFPage
import glob
import re
import os
import binascii as bia

# Please change for your environment
inputPDFDir = r'C:\work\git\Python3-PDF2TXT-sample\sample\\'
outputTXTDir = r'C:\work\git\Python3-PDF2TXT-sample\sample\\'


def save_image(lt_image, page_number, images_folder):
    """ from http://denis.papathanasiou.org/archive/2010.08.04.post.pdf """
    """Try to save the image data from this LTImage object"""
    result = None
    if lt_image.stream:
        file_stream = lt_image.stream.get_rawdata()
        file_ext = determine_image_type(file_stream[0:4])
        if file_ext:
            file_name = ''.join([str(page_number), '_',
                                 lt_image.name, file_ext])
            if write_file(images_folder, file_name,
                          lt_image.stream.get_rawdata(), flags='wb'):
                result = file_name
    return result


def determine_image_type(stream_first_4_bytes):
    """ from http://denis.papathanasiou.org/archive/2010.08.04.post.pdf """
    """Find out the image file type based on the magic number
    comparison of the first 4 (or 2) bytes"""
    file_type = None
    bytes_as_hex = bia.b2a_hex(stream_first_4_bytes)

    # pdfminer support only jpeg format.
    if bytes_as_hex.startswith(b'ffd8'):
        # print("jpg")
        file_type = '.jpg'
    elif bytes_as_hex == '89504e47':
        # print("png") not implemented.
        file_type = '.png'
    elif bytes_as_hex == '47494638':
        # print("gif") not implemented.
        file_type = '.gif'
    elif bytes_as_hex.startswith(b'424d'):
        # print("bmp") not implemented.
        file_type = '.bmp'
    # 78da and 789c is ZLIB header. not implemented.
    return file_type


def write_file(folder, filename, filedata, flags='w'):
    """ from http://denis.papathanasiou.org/archive/2010.08.04.post.pdf """
    """Write the file data to the folder and filename combination
    (flags: 'w' for write text, 'wb' for write binary,
    use 'a' instead of 'w' for append)"""
    result = False
    if os.path.isdir(folder):
        try:
            file_obj = open(os.path.join(folder, filename), flags)
            file_obj.write(filedata)
            file_obj.close()
            result = True
        except IOError:
            pass
    return result


# Guess the length of blanks and the height of line breaks
def calcSpace(objs):
    spaceList = list()
    wordHeightList = list()
    xpos = 0
    for i in objs:
        if (issubclass(i.__class__, LTChar)):
            # first charcter
            if xpos == 0:
                xpos = i.x1
                continue

            # maybe crlf
            if xpos > i.x1:
                xpos = i.x1
                continue

            spaceList.append(i.x0 - xpos)
            xpos = i.x1
            wordHeightList.append(i.y1 - i.y0)

    maxWordHeight = 0
    if len(wordHeightList) != 0:
        maxWordHeight = max(wordHeightList)

    minSpace = 0
    if len(spaceList) != 0:
        avg = sum(spaceList)/len(spaceList)
        for i in spaceList:
            if i > avg:
                if minSpace == 0:
                    minSpace = i
                elif minSpace > i:
                    minSpace = i

    return(minSpace, maxWordHeight)

def checkLtFigure(obj, pageNum, charBuf):

    LtCharList = []
    if (hasattr(obj, "get_text")):
        charBuf.append(str(obj.get_text().rstrip("\n")))
        charBuf.append("\n")
        return
    elif (isinstance(obj, LTImage)):
        # an image
        saved_file = save_image(obj, pageNum, outputTXTDir)
    elif (isinstance(obj, LTFigure)):
        if (hasattr(obj, "_objs")):
            for i in obj._objs:
                # print(i)
                if (isinstance(i, LTChar)):
                    # check after
                    LtCharList.append(i)
                    # print(i)
                else:
                    # print("else")
                    # print(i)
                    checkLtFigure(i, pageNum, charBuf)
                    charBuf.append("\n")

    # chech LtCharList
    if (len(LtCharList) > 0):
        xpos = 0
        ypos = 0
        (minSpace, maxWordHeight) = calcSpace(LtCharList)
        for i in LtCharList:
            if (issubclass(i.__class__, LTChar)):
                # first char
                if xpos == 0 and ypos == 0:
                    xpos = i.x1
                    ypos = i.y0
                # between charcters.
                # We may need to arrange the space.
                if ypos < i.y1 and i.x0 - xpos > minSpace:
                    charBuf.append(" ")
                xpos = i.x1
                # crlf
                if ypos > i.y1:
                    # print("\n")
                    cr = ypos - i.y1
                    while(cr > 0):
                        charBuf.append("\n")
                        cr -= maxWordHeight
                    ypos = i.y0
                charBuf.append(i.get_text())
        # next layout
        charBuf.append("\n")

    return


def outputText(inputPDFFile, outputTXTFile):
    # Open a PDF file.
    pageNum = 1
    fp = open(inputPDFFile, 'rb')

    rsrcmgr = PDFResourceManager()
#    rettxt = output = StringIO()
    laparams = LAParams()
    # Output vertical writing characters horizontally
    laparams.detect_vertical = True
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    parser = PDFParser(fp)
    document = PDFDocument(parser, password)

    charBuf = []
    for page in PDFPage.create_pages(document):
        interpreter.process_page(page)
        layout = device.get_result()
        for l in layout:
            # print(l)            
            checkLtFigure(l, pageNum, charBuf)
        # next page
        charBuf.append("\n\n")
        pageNum += 1
    # End of for page in PDFPage.create
    wfp = open(outputTXTFile, 'wt', encoding='UTF-8')
    buf = ''.join(charBuf)
    wfp.write(buf)
    wfp.close()

    fp.close()
    device.close()


for file in glob.glob(inputPDFDir + '*.pdf'):
    m = re.search(r'(.*)\.pdf$', file)
    print("extract txt from " + file)
    outputText(file, m.group(1) + '.txt')
