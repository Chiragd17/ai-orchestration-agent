from PIL import Image; import pytesseract
text = pytesseract.image_to_string(Image.open('dataset/media/images/image_01.png'))
print(text[:500])
