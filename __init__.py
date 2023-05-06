import os
from flask import Flask, render_template, request
from . import db


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    script_dir = os.path.dirname(os.path.abspath(__file__))

    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(script_dir, 'db.sqlite'),
    )

    from . import stats
    app.register_blueprint(stats.bp)
    app.add_url_rule('/', endpoint='index')

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    
    app.add_url_rule('/groupe', endpoint='groupe')
    app.add_url_rule('/copyright', endpoint='copyright')

    
    from . import db
    db.init_app(app)

    @app.route('/groupe')
    def groupe():
        return render_template('devs/groupe.html')
    
    @app.route('/')
    def index():
        return render_template('base.html')
    
    @app.route('/copyright')
    def copyright():
        return render_template('copyright.html')

    from . import db
    db.init_app(app)

    with app.app_context():
        db.init_db()    

    
    return app
