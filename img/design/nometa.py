from pypdf import PdfReader, PdfWriter
from PIL import Image
import xaeian as xn

def clean_pdf_metadata(input_path: str, output_path: str):
  reader = PdfReader(input_path)
  writer = PdfWriter()
  for page in reader.pages: writer.add_page(page)
  writer.add_metadata({})
  with open(output_path, "wb") as f: writer.write(f)

def clean_img_metadata(input_path: str, output_path: str):
  image = Image.open(input_path)
  data = list(image.getdata())
  clean = Image.new(image.mode, image.size)
  clean.putdata(data)
  clean.save(output_path)

SRC = "./"
DSC = "../"

# pdf_files = xn.DIR.FileList(SRC, "pdf")
# for pdf_file in pdf_files:
#   output_path = DSC + "/" + xn.LocalPath(pdf_file, SRC)
#   clean_pdf_metadata(pdf_file, output_path)

img_files = xn.DIR.FileList(SRC, ["jpg", "jpeg", "png", "webp"])




for img_file in img_files:
  output_path = DSC + "/" + xn.LocalPath(img_file, SRC)
  clean_img_metadata(img_file, output_path)
