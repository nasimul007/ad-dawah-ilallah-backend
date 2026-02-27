# import numpy as np
# from PIL import Image
# from pdf2image import convert_from_path

# def process_image(img):
#     gray = img.convert("L")
#     arr = np.array(gray)

#     black_pixels = np.sum(arr < THRESHOLD)
#     total_pixels = arr.size

#     return black_pixels, total_pixels


# def process_pdf(path):
#     pages = convert_from_path(path, dpi=DPI,poppler_path=r"D:\Downloads\Release-25.12.0-0\poppler-25.12.0\Library\bin")

#     total_black = 0
#     total_pixels = 0

#     for page in pages:
#         black, total = process_image(page)
#         total_black += black
#         total_pixels += total

#     return total_black, total_pixels


# def process_image_file(path):
#     img = Image.open(path)
#     return process_image(img)


# def calculate_area(black_pixels, total_pixels):
#     coverage = (black_pixels / total_pixels) * 100

#     # pixel area in cm²
#     pixel_area_cm2 = (2.54 / DPI) ** 2
#     black_area_cm2 = black_pixels * pixel_area_cm2

#     return coverage, black_area_cm2
