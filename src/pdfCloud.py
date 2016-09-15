from __future__ import unicode_literals

from cStringIO import StringIO

from PIL import Image
from PIL import ImageFont, ImageDraw

from operator import itemgetter
from os.path import abspath
from nltk.corpus import stopwords

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage

import regex as re

def convert(fname, pages=None):
    if not pages:
        pagenums = set()
    else:
        pagenums = set(pages)

    output = StringIO()
    manager = PDFResourceManager()
    converter = TextConverter(manager, output, laparams=LAParams())
    interpreter = PDFPageInterpreter(manager, converter)

    infile = file(fname, 'rb')
    for page in PDFPage.get_pages(infile, pagenums):
        interpreter.process_page(page)
    infile.close()
    converter.close()
    text = output.getvalue()
    output.close
    return text

def notNumeric(str):
    try: 
        float(str)
        return False
    except ValueError:
        return True

txt = unicode(convert("demo.pdf"), 'utf-8').lower()
txt = re.sub(ur"-[\r\n]+", "", txt)    # Try and 'glue' hyphenated line-broken words back together
txt = re.sub(ur"[\r?\n]+", " ", txt)   # Get rid of newline characters
txt = re.sub(ur"[^\P{P}-']+", "", txt) # Get rid of punctuation classes
txt = txt.split(" ")
ignore = stopwords.words("english")
txt = filter(lambda w: not w in ignore and len(w) > 1 and notNumeric(w), txt)

chart = {}
for i, word in enumerate(txt):
    if word in chart:
        chart[word][0] += 1
        try:
            chart[word][1][txt[i+1]] = chart[word][1].get(txt[i+1], 0) + 1
        except IndexError: #Last one
            pass
    else:
        try:
            chart[word] = [1, {txt[i+1]: 1}]
        except IndexError: #Last one
            chart[word] = [1, {}]

image=Image.new("RGB",[1024,240])
draw = ImageDraw.Draw(image)

i=0
for (word, freq) in sorted(chart.items(), key=lambda(w,f): f[0], reverse=True): #max(f[1].values()) if f[1].values() else 0
    out = word + u" (" + str(freq[0]) + u") " + u" ".join([k + u": " + str(v) for k,v in sorted(freq[1].items(), key=lambda(k,v):v, reverse=True)])
    if i < 5:
        draw.text((50, 50+(i*15)), out, font=ImageFont.truetype("Arial_Unicode.ttf",18))
    i+=1

image.show()