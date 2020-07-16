import os
from tqdm import tqdm
from PIL import Image
from io import BytesIO
from pathlib import Path
from base64 import b64encode
from flask import Flask, render_template, Response, request, redirect, url_for, make_response, jsonify


app = Flask(__name__)
session = {}
images_per_scroll = 16
limit = 300000
thumbnail_maxsize = (200, 200)


def open_image(image_path):
    try:
        image = Image.open(image_path).convert('RGB')
        image.thumbnail(thumbnail_maxsize, Image.ANTIALIAS)
    except Exception as e:
        print(e)
        return

    with BytesIO() as output:
        image.save(output, 'jpeg')
        image_bytes = output.getvalue()
    return image_bytes


def get_files_list(files_list):
    files = []

    for path in tqdm(files_list):
        image_bytes = open_image(path)
        if not image_bytes:
            continue

        image_source = f"data:image/png;base64,{b64encode(image_bytes).decode('utf-8')}"
        files.append([path, image_source])

    return files


def get_files(directory_path):
    return [os.path.join(directory_path, i) for i in os.listdir(
        directory_path) if os.path.isfile(os.path.join(directory_path, i))]


@app.route("/load")
def load():
    if not request.args:
        return

    counter = int(request.args.get("counter"))

    if counter >= limit:
        print("No more posts")
        res = make_response(jsonify({}), 200)

    else:
        print(f"Returning posts {counter} to {counter + images_per_scroll}")

        files = session['files'][counter: counter + images_per_scroll]
        res = make_response(
            jsonify(get_files_list(files)), 200)

    return res


@app.route("/move", methods=['GET'])
def move_images():
    if not request.args:
        return make_response(jsonify({'Argument list is empty'}), 400)

    current_path = session.get('start_directory')
    destination_path = request.args.get('destination')
    checkbox_values = request.args.get('items').split(',')

    print('Checkbox values', checkbox_values)
    if not os.path.isdir(destination_path):
        os.mkdir(destination_path)
        print(f'Creating {destination_path} directory')

    print(current_path, destination_path)

    for image_path in checkbox_values:
        new_path = image_path.replace(current_path, destination_path)
        print(f'Moving to {new_path}')
        Path(image_path).rename(new_path)

    return make_response(jsonify(f'Images successfully moved to {destination_path}'), 200)


@app.route('/enter', methods=['GET'])
def get_directory_path():
    directory_path = request.args.get('directory')

    if not directory_path or not os.path.isdir(directory_path):
        print('Cannot find such directory')
        return make_response(jsonify('Cannot find such directory'), 400)

    session["start_directory"] = directory_path
    session['files'] = get_files(directory_path)

    return redirect('/directory_view')


@app.route("/directory_view")
def main_view():
    return render_template('directory.html', current_directory=session.get('start_directory'), images_per_scroll=images_per_scroll)


@app.route("/")
def index():
    return render_template('index.html')


if __name__ == "__main__":
    # debug is set to true to avoid jinja templates caching
    app.run(debug=True, host='0.0.0.0', port=8888)
