# -*- coding: utf-8 -*-
"""
Created on Thu Jan 18 14:36:53 2018

@author: patch0000
2018/01/21

Python3-PDF2TXT-sample

As far as I have investigated, There are 4 pdfminer in the world.
 1.pdfminer for python2.x
 2.pdfminer.six for python2.x and python3.x
 3.pdfminer3k for python3.x
 4.pdfminer2 python2.x and python3.x

They are same name but function argument and library tree is different.
This program used pdfminer.six.

For windows Anconda users.
conda config --show
conda config --set remote_read_timeout_secs 6000
conda config --show
conda install -c conda-forge pdfminer.six
and wait long long time.


There are two ways to extract text from PDF.

1.PDFPage.create_pages
There are sentences that can not be extracted occasionally.
PDF has a different structure depending on the author and software.
Unfortunately I could not make this program versatile.
This program is a hint for cases where TextBox is not used.
If this program does not work for you, please refer to the See Also section.

2.PDFPage.get_pages
Text comes out in one stroke, even the page break is not understood.
Also, in the case of English PDF, the space between words disappears
in some cases.

See Also.
https://euske.github.io/pdfminer/programming.html
http://a244.hateblo.jp/entry/2017/08/26/001050
http://irukanobox.blogspot.jp/2017/03/python3pdf.html

"""

from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTFigure, LTChar
from pdfminer.pdfpage import PDFPage
from io import StringIO

inputPDFFile = r'C:\work\py\test\my.pdf'
outputTxtFile = r'C:\work\py\test\my.txt'

# Open a PDF file.
fp = open(inputPDFFile, 'rb')

rsrcmgr = PDFResourceManager()
rettxt = output = StringIO()
laparams = LAParams()
# Output vertical writing characters horizontally
laparams.detect_vertical = True
device = PDFPageAggregator(rsrcmgr, laparams=laparams)
interpreter = PDFPageInterpreter(rsrcmgr, device)

password = ""
parser = PDFParser(fp)
document = PDFDocument(parser, password)


# Guess the length of blanks and the height of line breaks
def calcSpace(objs):
    spaceList = list()
    wordHeight = list()
    xpos = 0
    for i in objs:
        if (issubclass(i.__class__, LTChar)):
            # first charcter
            if xpos == 0 and ypos == 0:
                xpos = i.x1
                continue

            # maybe crlf
            if xpos > i.x1:
                xpos = i.x1
                continue

            spaceList.append(i.x0 - xpos)
            xpos = i.x1
            wordHeight.append(i.y1 - i.y0)

    avg = sum(spaceList)/len(spaceList)
    minSpace = 0
    for i in spaceList:
        if i > avg:
            if minSpace == 0:
                minSpace = i
            elif minSpace > i:
                minSpace = i

    return(minSpace, max(wordHeight))


buf = ''
for page in PDFPage.create_pages(document):
    interpreter.process_page(page)
    layout = device.get_result()
    for l in layout:

        if (not hasattr(l, "get_text")):
            if (isinstance(l, LTFigure)):
                xpos = 0
                ypos = 0
                (minSpace, maxWordHeight) = calcSpace(l._objs)
                for i in l._objs:
                    if (issubclass(i.__class__, LTChar)):
                        # first char
                        if xpos == 0 and ypos == 0:
                            xpos = i.x1
                            ypos = i.y0

                        # between charcter. We may need to arrange the space.
                        if ypos < i.y1 and i.x0 - xpos > minSpace:
                            buf += " "

                        xpos = i.x1

                        # crlf
                        if ypos > i.y1:
                            # print("\n")
                            cr = ypos - i.y1
                            while(cr > 0):
                                buf += "\n"
                                cr -= maxWordHeight
                            ypos = i.y0

                        buf += i.get_text()
                # next layout
                buf += "\n"
            continue
        else:
            temp_str = l.get_text().rstrip("\n")
            buf += str(temp_str) + "\n"

    # next page
    buf += "\n\n"

wfp = open(outputTxtFile, 'wt', encoding='UTF-8')
wfp.write(buf)
wfp.close()

fp.close()
device.close()
rettxt.close()
