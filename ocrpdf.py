import os
import sys
import argparse
import subprocess
from PyPDF2 import PdfReader, PdfMerger
from pdf2image import convert_from_path
import pytesseract
from PIL import Image

def has_embedded_text(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PdfReader(file)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                return True
        return False

def ocr_pdf(input_path, temp_output_path):
    directory, filename = os.path.split(input_path)
    name, ext = os.path.splitext(filename)
    images = convert_from_path(input_path)
    merger = PdfMerger()
    for image in images:
        pdf_bytes = pytesseract.image_to_pdf_or_hocr(image, extension='pdf')
        temp_pdf_path = f"temp_page_{images.index(image)}.pdf"
        with open(temp_pdf_path, "wb") as temp_file:
            temp_file.write(pdf_bytes)
        merger.append(temp_pdf_path)
        print(f"Processed page {images.index(image) + 1}")
    merger.write(temp_output_path)
    merger.close()
    for i in range(len(images)):
        os.remove(f"temp_page_{i}.pdf")
    print(f"OCR completed. Temporary file saved as: {temp_output_path}")

def extract_text(input_path, output_text_path):
    try:
        subprocess.run(['/usr/bin/pdftotext', '-layout', input_path, output_text_path], check=True)
        print(f"Text extraction completed. Text file saved as: {output_text_path}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred during text extraction: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Perform OCR on a PDF file')
    parser.add_argument('pdf_path', help='Path to the PDF file')
    parser.add_argument('--force', action='store_true', help='Force OCR even if the file already has embedded text')
    parser.add_argument('--delete', action='store_true', help='Delete the original file after OCR is completed')
    parser.add_argument('--as-text', action='store_true', help='Output only a text file using pdftotext with -layout flag')
    args = parser.parse_args()

    pdf_path = args.pdf_path
    delete_original = args.delete
    as_text = args.as_text

    if not os.path.exists(pdf_path):
        print("The specified file does not exist.")
        sys.exit(1)

    if has_embedded_text(pdf_path) and not args.force:
        print(f"File already has embedded text. {pdf_path}")
        input_for_text_extraction = pdf_path
    else:
        # Perform OCR and save to a temporary file
        temp_output_path = os.path.join(os.path.dirname(pdf_path), "temp_ocr_output.pdf")
        ocr_pdf(pdf_path, temp_output_path)
        input_for_text_extraction = temp_output_path

    if as_text:
        output_text_path = os.path.join(os.path.dirname(pdf_path), os.path.splitext(os.path.basename(pdf_path))[0] + '.txt')
        extract_text(input_for_text_extraction, output_text_path)
        if input_for_text_extraction != pdf_path:
            os.remove(input_for_text_extraction)  # Remove the temporary OCR file
    else:
        # If not --as-text, perform the original behavior (OCR and save as PDF)
        output_pdf = os.path.join(os.path.dirname(pdf_path), os.path.basename(pdf_path))
        directory, filename = os.path.split(pdf_path)
        name, ext = os.path.splitext(filename)
        original_pdf = os.path.join(directory, f"{name}-orig{ext}")
        os.rename(pdf_path, original_pdf)
        ocr_pdf(original_pdf, output_pdf)
        if delete_original:
            os.remove(original_pdf)
            print(f"Original file deleted: {original_pdf}")


