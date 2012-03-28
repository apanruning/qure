#!/usr/bin/env python

import os
from flask import Flask, request, render_template, session, redirect, abort, url_for, send_file
from qrcode import QRCode
from hashlib import sha1

app = Flask(__name__)
app.config.from_pyfile('settings.cfg')



'''
Helpers
'''


@app.before_request
def csrf_protect():
    if request.method == "POST":
        token = session.pop('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            abort(403)

def generate_csrf_token():
    from base64 import urlsafe_b64encode
    if '_csrf_token' not in session:
        session['_csrf_token'] = urlsafe_b64encode(os.urandom(32))
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token  

def create_qr(data):
    from PIL import PngImagePlugin
    meta = PngImagePlugin.PngInfo()
    meta.add_text('message', data)
    filehash = sha1(data).hexdigest()[:12]
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filehash+'.png')
    
    if not os.path.exists(filepath):
    
        qr = QRCode(
            version=2,
            border=4,
        )
        qr.add_data(data)

        img = qr.make_image()
        img.save(filepath, 'png', pnginfo=meta)
    else :
        img = file(filepath)
    return (img, filepath, filehash)

@app.route('/', methods=['POST', 'GET'])
def index():
    data = request.args.get('data', None)

    if not data and request.method == 'POST' :
        data = request.form['data']

    if data:
        img, filepath, filehash = create_qr(data)
        return redirect(url_for('code', filehash=filehash))

    return render_template('index.html')

@app.route('/<filehash>')
def code(filehash):
    from PIL import Image
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filehash+'.png')
    url = url_for('code', filehash=filehash, _external=True)
    data = Image.open(filepath).info['message']
    image_url = url_for('qr', data=data, _external=True)
    return render_template(
        'qr.html', 
        filehash=filehash,
        url=url,
        data=data,
        image_url=image_url
    )

@app.route('/qr/<data>')
def qr(data):

    img, filepath, filehash = create_qr(data)

    return send_file(
        filepath, 
        mimetype='image/png'
    )

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.debug = True
    app.run()
