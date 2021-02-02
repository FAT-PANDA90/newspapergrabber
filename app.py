from flask import Flask, render_template, request, redirect, url_for, send_file, session
import methods_file
from urllib.parse import urlparse
from selenium import webdriver
import base64
import pdfkit

app = Flask(__name__, template_folder='./frontend/templates', static_folder='./frontend/static')
app.secret_key = 'bhaisa'


@app.route('/', methods=['POST', 'GET'])
def hello_world():
    if request.method == 'POST' and request.form['password'] == 'p@ss':
        session['get_pdf'] = request.form
        return redirect(url_for("get_pdf"))
    else:
        return render_template('index.html')


@app.route("/get_pdf", methods=['POST', 'GET'])
def get_pdf():
    url = session['get_pdf']['url']
    method_object = methods_file.GetResourceMethods()
    parsed_uri = urlparse(url)
    result = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
    html_str, title_txt = method_object.select_parser(input_url_host_only=result, url_full=url, url_index=1)
    # return html_str
    if html_str and title_txt:
        make_html_pdf(html_str)
        return send_file('output.pdf', attachment_filename='output.pdf')


def make_html_pdf(html_str):
    """Download the currently displayed page to target_path."""
    driver = webdriver.PhantomJS('phantomjs')
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
    render = '''this.render("{}")'''.format('output.pdf')
    execute(render, [])


if __name__ == '__main__':
    app.run()
