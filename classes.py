# from utils import open_image, get_files_list
from base64 import b64encode
from tqdm import tqdm
from pathlib import Path
from PIL import Image
from io import BytesIO
from time import time
import os

thumbnail_maxsize = (200, 200)


def get_files_list(directory_path):
    directory_path = Path(directory_path)
    return [str(directory_path / i) for i in sorted(os.listdir(
        directory_path)) if os.path.isfile(directory_path/i)]


def get_bytes(image, suffix):
    with BytesIO() as output:
        image.save(output, suffix)
        return output.getvalue()


def open_image(image_path, resize=True):
    is_png = Path(image_path).suffix == '.png'
    try:
        convert_mode = 'RGBA' if is_png else 'RGB'
        image = Image.open(image_path).convert(convert_mode)
        size = image.size
        if resize:
            image.thumbnail(thumbnail_maxsize, Image.ANTIALIAS)
    except Exception as e:
        print(e)
        return None, None

    suffix = 'png' if is_png else 'jpeg'
    image_bytes = get_bytes(image, suffix)
    return image_bytes, size


class ImageFile:
    def __init__(self, path):
        self.location = path
        self.labels = set()
        self.is_loaded = False
        self.is_fullres = False
        # self.id =

    def load(self):
        if self.is_loaded:
            return
        image_bytes, self.size = open_image(self.location)
        self.image_data = f"data:image/png;base64,{b64encode(image_bytes).decode('utf-8')}"

    def add_labels(self, labels):
        for label in labels:
            self.labels.add(label)

    def remove_labels(self, labels):
        for label in labels:
            if label in self.labels:
                self.labels.remove(label)

    def load_fullres(self):
        if self.is_fullres:
            return
        image_bytes, size = open_image(self.location, resize=False)
        self.image_data = f"data:image/png;base64,{b64encode(image_bytes).decode('utf-8')}"
        self.is_fullres = True

    def change_location(self, new_directory):
        current_path = Path(self.location)
        name = current_path.name
        new_path = Path(new_directory)/name
        try:
            current_path.rename(new_path)
        except Exception as e:
            print(image_path, e)
            return False

        # TODO: implement ctrl+z for move
        self.previous_location = self.location
        self.location = new_path
        print(f'Moving {name} to {new_directory}')
        return True


class ImageSession:
    def __init__(self, user_ip):
        self.user_ip = user_ip
        self.images = []
        self.message = ''
        self.password = ''

    def set_directory(self, path):
        self.images.clear()
        self.current_directory = path
        files_list = get_files_list(path)
        self.total = len(files_list)
        for name in tqdm(files_list):
            self.images.append(ImageFile(name))

    def get_image_by_path(self, path):
        start = time()
        # locations = set(image.location for image in self.images)
        for image in self.images:
            if image.location == path:
                print('Image search time ', time() - start)
                return image

    def add_labels_to_image(self, image_index, labels):
        self.images[image_index].add_labels(labels)

    def remove_labels_from_image(self, image_index, labels):
        self.images[image_index].remove_labels(labels)
