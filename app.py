import os
from utils import *
from pathlib import Path
from flask import Flask, render_template, Response, request, redirect, url_for, make_response, jsonify


app = Flask(__name__)
session = {}
images_per_scroll = 16
limit = 30000


@app.route('/get_fullsize_image', methods=['POST'])
def get_fullsize_image():
    json = request.get_json()

    image_path = json.get('path')
    try:
        image = Image.open(image_path).convert('RGB')
    except Exception as e:
        print(e)
        return make_response(jsonify(f'Error while opening image, {image_path}'), 404)

    image_data = f"data:image/png;base64,{b64encode(get_bytes(image)).decode('utf-8')}"

    return make_response(jsonify(image_data), 200)


@app.route('/load')
def load():
    if not request.args:
        return make_response(jsonify("No arguments"), 400)

    counter = int(request.args.get("counter"))

    if counter >= limit:
        print("No more images")
        res = make_response(jsonify({}), 200)

    else:
        print(
            f'Returning images from {counter} to {counter + images_per_scroll}')

        file_names = session.get('files')[counter: counter + images_per_scroll]
        res = make_response(
            jsonify(get_images_data(session.get('start_directory'), file_names)), 200)

    return res


@app.route('/move', methods=['POST'])
def move_images():
    current_path = session.get('start_directory')

    json = request.get_json()
    destination_path = json.get('destination')
    checkbox_values = json.get('items')

    print('Checkbox values', checkbox_values)
    if not os.path.isdir(destination_path):
        os.mkdir(destination_path)
        print(f'Creating {destination_path} directory')

    moved_counter = 0
    for image_path in checkbox_values:
        image_name = os.path.basename(image_path)
        new_path = os.path.join(destination_path, image_name)
        print(f'Moving {image_name} to {destination_path}')
        try:
            Path(image_path).rename(new_path)
        except Exception as e:
            print(image_path, e)
            continue

        moved_counter += 1

    session['files'] = get_files_list(current_path)

    return make_response(jsonify(f'{moved_counter} image(s) successfully moved to {destination_path}'), 200)


@app.route('/get_path_options', methods=['GET'])
def get_path_options():
    directory_path = request.args.get('path')
    path_options = path_completer(directory_path)

    return make_response(jsonify(path_options), 200)


@app.route('/enter', methods=['GET'])
def get_directory_path():
    directory_path = request.args.get('directory')

    if not directory_path or not os.path.isdir(directory_path):
        print('Cannot find such directory')
        return make_response(jsonify('Cannot find such directory'), 400)

    session['start_directory'] = directory_path
    session['files'] = get_files_list(directory_path)

    return redirect('/directory_view')


@app.route('/directory_view')
def main_view():
    total = 0
    if session.get('files'):
        total = len(session.get('files'))
    return render_template('directory.html', current_directory=session.get('start_directory'),
                           images_per_scroll=images_per_scroll, total=total)


@app.route('/')
def index():
    if not session.get('password'):
        return render_template('login.html', message=session.get('message'))
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    password = request.form.get('password')
    if password != app.secret_key:
        session['message'] = 'You shall not pass'
        return redirect('/')
    session['password'] = password
    return redirect('/')


if __name__ == "__main__":
    app.secret_key = generate_session_password()
    print('Current session code:', app.secret_key)
    # debug is set to true to avoid jinja templates caching
    app.run(debug=True, host='0.0.0.0', port=8888)
