#!/usr/bin/env python

import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import random
import json
import os
from PyPDF2 import PdfMerger, PdfReader

def is_valid_pdf(file):
    try:
        PdfReader(file)
        return True
    except Exception:
        return False
        
if __name__ == "__main__":
    pdfs = [a for a in os.listdir() if a.endswith(".pdf") and a != "results.pdf" and is_valid_pdf(a)]
    merger = PdfMerger()
    for pdf in pdfs:
        with open(pdf, 'rb') as f:
            merger.append(f)

    with open("results.pdf", "wb") as fout:
        merger.write(fout)
    merger.close()
