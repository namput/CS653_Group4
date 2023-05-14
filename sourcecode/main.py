from pythainlp.util import normalize
from pythainlp import sent_tokenize
from PyPDF2 import PdfReader
import re
def read_pdf_file(pdf_file_path):
    pdf_reader = PdfReader(pdf_file_path)
    text = ''
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        normalized_text = normalize(page_text)  # normalize Thai text
        text += normalized_text
    return text

def extract_sentences(text, keyword):
    sentences = sent_tokenize(text)
    return [sentence for sentence in sentences if keyword in sentence]

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    text = read_pdf_file('12seedproduction.pdf')
    keyword = "คุณภาพทางพันธุกรรม"
    sentences_with_keyword = extract_sentences(text, keyword)
    for sentence in sentences_with_keyword:
        print(sentence)