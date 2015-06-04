Running
=======

``main.py`` file runs project. By default you can access it on ``http://localhost:8888/`` 

Parameters
**********

* ``--help`` - Display help message.
* ``--env={{env}}`` - Run project using environtmen ``{{env}}``. You can modify settings for this environment in ``settings_{{env}}`` file, where ``{{env}} is the name of the environment.
* ``--port={{port}}`` - Port to run project on, where ``{{port}}`` is the number of port.
* ``--reset_db`` - Will run all ``init_db.py`` files in applications before startup.

Examples
********

Run application on 9999 port using  test environment with reseting db::

    ./main.py --env=test --port=9999 --reset_db
