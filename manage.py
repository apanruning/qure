#!/usr/bin/env python

import os
from flask import Flask, request, render_template, session, redirect, abort, url_for
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
    filename = sha1(data).hexdigest()[:12]

    qr = QRCode(
        version=2,
        border=0,
    )
    qr.add_data(data) 

    img = qr.make_image()
    img.save(os.path.join(app.config['UPLOAD_FOLDER'], filename+'.png'), 'png')

    return url_for('code', filename=filename)

@app.route('/', methods=['POST', 'GET'])
def index():
    data = request.args.get('data', None)

    if not data and request.method == 'POST' :
        data = request.form['data']

    if data:
        redir = create_qr(data)
        return redirect(redir)

    return render_template('index.html')


@app.route('/<filename>')
def code(filename):
    url = url_for('code', filename=filename, _external=True)
    return render_template(
        'qr.html', 
        filename=filename, 
        url=url
    )


if __name__ == '__main__':
    app.debug = True
    app.run()
