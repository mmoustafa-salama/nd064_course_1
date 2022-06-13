import sqlite3
import sys

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort
import logging

# Function to get a database connection.
# This function connects to database with the name `database.db`
db_connection_count = 0
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row

    global db_connection_count
    db_connection_count = db_connection_count + 1

    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Function to count posts
def get_post_count():
    connection = get_db_connection()
    results = connection.execute('SELECT COUNT(*) FROM posts').fetchone()
    connection.close()
    return results[0]

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      app.logger.info('A non-existing article is accessed and a 404 page is returned.')
      return render_template('404.html'), 404
    else:
      app.logger.info('Article "%s" retrieved!', post['title'])
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info('The "About Us" page is retrieved.')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            
            app.logger.info('A new article with title "%s" is created!', title)
            return redirect(url_for('index'))

    return render_template('create.html')

@app.route('/healthz')
def healthcheck():
    response = app.response_class(
            response=json.dumps({"result":"OK - healthy"}),
            status=200,
            mimetype='application/json'
    )

    ## log line
    app.logger.info('Status request successfull')
    return response

@app.route('/metrics')
def metrics():
    global db_connection_count
    post_count = get_post_count()
    response = app.response_class(
            response=json.dumps({"status":"success","code":0,"data":{"db_connection_count": db_connection_count, "post_count": post_count}}),
            status=200,
            mimetype='application/json'
    )

    ## log line
    app.logger.info('Metrics request successfull')
    return response

def configureLogging():
    # format output
    logFormat = '[%(asctime)s]: [%(levelname)s] %(message)s'
    
    # stream logs to app.log file
    file_handler = logging.FileHandler('app.log')

    # set logger to handle STDOUT and STDERR
    stdout_handler = logging.StreamHandler(sys.stdout)
    stderr_handler = logging.StreamHandler(sys.stderr)

    handlers = [file_handler, stderr_handler, stdout_handler]

    logging.basicConfig(level=logging.DEBUG,format=logFormat,handlers=handlers)

# start the application on port 3111
if __name__ == "__main__":
    configureLogging()
    app.run(host='0.0.0.0', port='3111')
