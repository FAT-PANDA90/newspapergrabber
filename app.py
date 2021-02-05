from flask import Flask, render_template, request, redirect, url_for, send_file, session
import methods_file
from urllib.parse import urlparse
from selenium import webdriver
import base64
from datetime import timezone, datetime
import io
import os
import sys
from bs4 import BeautifulSoup

app = Flask(__name__, template_folder='./frontend/templates', static_folder='./frontend/static')
app.secret_key = 'bhaisa'


@app.route('/', methods=['POST', 'GET'])
def hello_world():
    if request.method == 'POST' and request.form['password'] == 'p@ss':
        session['get_pdf'] = request.form
        if request.form['action'] == 'pdf':
            return redirect(url_for("get_pdf"))
        else:
            return '<h1> UNDER CONSTRUCTION</h1>'
    else:
        return render_template('index.html')


@app.route("/get_pdf", methods=['POST', 'GET'])
def get_pdf():
    url = session['get_pdf']['url']
    method_object = methods_file.GetResourceMethods()
    parsed_uri = urlparse(url)
    result = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
    html_str, title_txt = method_object.select_parser(input_url_host_only=result, url_full=url)
    # return html_str
    if html_str and title_txt:
        outfile = make_html_pdf(html_str)
        print(f'{outfile} created', file=sys.stdout)
        # return send_file(outfile, attachment_filename='title_txt.pdf')
        return_data = io.BytesIO()
        with open(outfile, 'rb') as fo:
            return_data.write(fo.read())
        # (after writing, cursor will be at last byte, so move it to start)
        return_data.seek(0)
        os.remove(outfile)
        print(f'{outfile} deleted', file=sys.stdout)
        return send_file(return_data, mimetype='application/pdf',
                         attachment_filename=f'{title_txt}.pdf')


# @app.route("/get_summary", methods=['POST', 'GET'])
# def get_summary():
#     url = session['get_pdf']['url']
#     method_object = methods_file.GetResourceMethods()
#     parsed_uri = urlparse(url)
#     result = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
#     html_str, title_txt = method_object.select_parser(input_url_host_only=result, url_full=url)
#     soup = BeautifulSoup(html_str, 'lxml')
#     text = soup.findAll('p')
#     return_html = ''
#     for item in text:
#         return_html += item.text
#     return return_html

def make_html_pdf(html_str):
    """Download the currently displayed page to target_path."""
    dt = datetime.now()
    utc_time = dt.replace(tzinfo=timezone.utc)
    utc_timestamp = utc_time.timestamp()
    driver = webdriver.PhantomJS()
    html_bs64 = base64.b64encode(html_str.encode('utf-8')).decode()
    driver.get("data:text/html;base64," + html_bs64)

    def execute(script, args):
        driver.execute('executePhantomScript', {'script': script, 'args': args})

    # hack while the python interface lags
    driver.command_executor._commands['executePhantomScript'] = ('POST', '/session/$sessionId/phantom/execute')
    # set page format
    # inside the execution script, web_page is "this"
    with open('papersize.js', 'r') as gu:
        temp_script = gu.read()
    page_format = f'this.{temp_script};'
    execute(page_format, [])

    # render current page
    render = '''this.render("{}")'''.format(f'{utc_timestamp}.pdf')
    execute(render, [])
    return f'{utc_timestamp}.pdf'


if __name__ == '__main__':
    app.run()
