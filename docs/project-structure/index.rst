Project structure
=================

Project structure
*****************

Now the file structure of project looks like:

* ``harma/``  - main project directory.
    * ``apps/`` - applications directory.
        * base/ - base application. All applications should extend this.
    * ``db.py`` - db connection class.
    * ``main.py`` - project start script.
    * ``settings.py`` - projects settings. See :ref:`configuration`.
    * ``settings_test.py`` - test environment settings. See :ref:`configuration`.
    * ``static/`` - directory for static files: js, css, images, etc.
    * ``templates/`` - directory for storing templates.
        * base.html - base template. All templates should extend this.
    * ``test.py`` - test run script
    * ``utils/`` - Usefull python code to use in applications
* ``docs/`` - Project documentation
* ``requirement.txt`` - Dependency list in pip format


Application directory structure
*******************************

* ``__init__`` - required by python.
* ``forms.py`` - forms, used in application. Not required if you don't use forms in your application.
* ``handler.py`` - application handlers. All request are processed there. Required.
* ``init_db.py`` - script for initializing db: stucture, indexes, initial data. It's being run when ``--reset_db`` parameter is passed to ``main.py``. Not required.
* ``tests.py`` - application tests. Not required.
* ``urls.py`` - urls mapping settings. Required.
* ``utils.py`` - userfull code used in application. Not required.


Templates directory structure
*****************************

We recommend you to store templates in ``templates/{{your_application_name}}/``, where ``{{your_application_name}}`` is the name of your application. It should contain ``base.html`` file. All other templates files should extend it.
