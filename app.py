import os
import argparse
from utils import *
from pathlib import Path
from classes import *
import pandas as pd
from flask import Flask, render_template, Response, request, redirect, url_for, make_response, jsonify, send_file


app = Flask(__name__)
# TODO: clear session data by timeout
sessions = {}


# def check_session(user_ip):
#     session = sessions.get(user_ip)
#     if not session:
#         return redirect('/login')
#     else:
#         return session


@app.route('/get_labels', methods=['POST'])
def get_labels():
    session = sessions.get(request.remote_addr)
    if not session:
        return redirect('/login')

    json = request.get_json()
    image_indexes = json.get('indexes')
    print('images', image_indexes)

    labels = []
    for index in image_indexes:
        image = session.images[int(index)]
        labels.append(image.labels)
        print(index, image.labels)

    print('all labels', labels[:10])
    common_labels = set(labels[0]).intersection(*labels[1:])
    print('intersect', common_labels)

    return make_response(jsonify(list(common_labels)), 200)


@app.route('/add_labels', methods=['POST'])
def add_labels():
    session = sessions.get(request.remote_addr)
    if not session:
        return redirect('/login')

    json = request.get_json()
    image_indexes = json.get('indexes')
    labels = json.get('labels').split(' ')
    print('adding', labels)
    print('images', image_indexes)

    for index in image_indexes:
        index = int(index)
        session.add_labels_to_image(index, labels)

    labels_count = [0] * (len(labels) + 1)

    for image in session.images:
        for index, label in enumerate(labels):
            if label in image.labels:
                labels_count[index] += 1

    response_data = [f'Labels added successfully', labels_count]
    return make_response(jsonify(response_data), 200)


@app.route('/remove_labels', methods=['POST'])
def remove_labels():
    session = sessions.get(request.remote_addr)
    if not session:
        return redirect('/login')

    json = request.get_json()
    image_indexes = json.get('indexes')
    labels = json.get('labels').split(' ')
    print('removing', labels, 'from', image_indexes)

    for index in image_indexes:
        index = int(index)
        session.remove_labels_from_image(index, labels)

    return make_response(jsonify([f'Labels removed successfully', ]), 200)


@app.route('/export_imagenames', methods=['POST'])
def export_imagenames():
    session = sessions.get(request.remote_addr)
    if not session:
        return redirect('/login')

    json = request.get_json()
    image_indexes = json.get('indexes')
    export_path = json.get('path').rstrip('/')

    Path(export_path).parent.mkdir(parents=True, exist_ok=True)

    if not export_path.endswith('.txt'):
        export_path += '/image-names.txt'

    names = []

    for index in image_indexes:
        index = int(index)
        image = session.images[index]
        names.append(image.location + '\n')

    with open(export_path, 'w') as f:
        f.writelines(names)

    return make_response(jsonify(f'Names successfully saved to {export_path}'), 200)


@app.route('/export_labels', methods=['POST'])
def export_labels():
    session = sessions.get(request.remote_addr)
    if not session:
        return redirect('/login')

    json = request.get_json()
    image_indexes = json.get('indexes')
    export_path = json.get('path').rstrip('/')

    Path(export_path).parent.mkdir(parents=True, exist_ok=True)

    if not export_path.endswith('.csv'):
        export_path += '/labels.csv'

    names = []
    labels = []

    for index in image_indexes:
        index = int(index)
        image = session.images[index]
        names.append(image.location)
        labels.append(' '.join(image.labels))

    df = pd.DataFrame({"names": names, "labels": labels})
    df.to_csv(export_path, index=False)

    return make_response(jsonify(f'Labels successfully saved to {export_path}'), 200)


@app.route('/export_labels_local')
def export_labels_local():
    session = sessions.get(request.remote_addr)
    if not session:
        return redirect('/login')

    images = session.images

    rows = [['images', 'labels']]

    for i in images:
        labels = ' '.join(i.labels)
        name = i.location
        rows.append([name, labels])
    return make_response(jsonify(rows), 200)


@app.route('/get_images', methods=['POST'])
def get_image():
    session = sessions.get(request.remote_addr)
    if not session:
        return redirect('/login')

    json = request.get_json()
    image_pathes = json.get('pathList')
    files = []
    for path in image_pathes:
        image = session.get_image_by_path(path)
        image.load()
        files.append([image.image_data, image.size])

    return make_response(jsonify(files), 200)


@app.route('/get_fullsize_image', methods=['POST'])
def get_fullsize_image():
    session = sessions.get(request.remote_addr)
    if not session:
        return redirect('/login')

    json = request.get_json()
    image_path = json.get('path')
    image = session.get_image_by_path(image_path)
    image.load_fullres()
    return make_response(jsonify(image.image_data), 200)


@app.route('/load')
def load():
    images = sessions.get(
        request.remote_addr).images

    files = []
    for image in images:
        files.append([image.location])

    return make_response(jsonify(files), 200)


@app.route('/move', methods=['POST'])
def move_images():
    session = sessions.get(request.remote_addr)
    if not session:
        return redirect('/login')

    json = request.get_json()
    destination_path = json.get('destination')
    image_indexes = json.get('indexes')

    if not os.path.isdir(destination_path):
        os.makedirs(destination_path)
        print(f'Creating {destination_path} directory')

    moved_counter = 0
    for index in image_indexes:
        image = session.images[int(index)]
        if image.change_location(destination_path):
            moved_counter += 1

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

    user_ip = request.remote_addr

    session = sessions.get(user_ip)
    session.set_directory(directory_path)

    return redirect('/directory_view')


@app.route('/directory_view')
def main_view():
    # TODO: add check
    session = sessions.get(request.remote_addr)
    if not session:
        return redirect('/login')

    total = session.total
    current_directory = session.current_directory
    return render_template('directory.html', current_directory=current_directory, total=total)


@app.route('/')
def index():
    session = sessions.get(request.remote_addr)
    if not session or not session.password:
        return render_template('login.html')
    session.message = ''
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    user_ip = request.remote_addr
    password = request.form.get('password')
    session = ImageSession(user_ip)
    sessions[user_ip] = session
    if password != app.secret_key:
        session.message = 'Wrong code, try again'
        return render_template('login.html', message=session.message)
    session.password = password
    return redirect('/')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', default=8080, type=int)

    args = parser.parse_args()
    port_number = args.port

    app.secret_key = generate_session_password()
    print('Current session code:', app.secret_key)
    # debug is set to true to avoid jinja templates caching
    app.run(debug=True, host='0.0.0.0', port=port_number)
