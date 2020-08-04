import os
import glob
from PIL import Image
from tqdm import tqdm
from io import BytesIO
from random import choice
from base64 import b64encode
from string import ascii_lowercase, digits


thumbnail_maxsize = (200, 200)


def generate_session_password():
    return ''.join([choice(ascii_lowercase + digits) for i in range(15)])


def get_bytes(image):
    with BytesIO() as output:
        image.save(output, 'jpeg')
        return output.getvalue()


def open_image(image_path):
    try:
        image = Image.open(image_path).convert('RGB')
        size = image.size
        image.thumbnail(thumbnail_maxsize, Image.ANTIALIAS)
    except Exception as e:
        print(e)
        return None, None

    image_bytes = get_bytes(image)
    return image_bytes, size


def get_images_data(directory, files_list):
    files = []

    for name in tqdm(files_list):
        path = os.path.join(directory, name)
        image_bytes, image_size = open_image(path)
        if not image_bytes:
            continue

        image_source = f"data:image/png;base64,{b64encode(image_bytes).decode('utf-8')}"
        files.append([path, image_source, image_size])

    return files


def get_files_list(directory_path):
    return [i for i in sorted(os.listdir(
        directory_path)) if os.path.isfile(os.path.join(directory_path, i))]


def get_directories_list(path):
    return [os.path.join(path, i) for i in os.listdir(path) if os.path.isdir(i)]


def path_completer(text):
    if text == '~' or text == '/':
        text = os.path.expanduser('~')

    if os.path.isdir(text):
        text += '/'

    return [x for x in glob.glob(text + '*/') if os.path.isdir(x)]