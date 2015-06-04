Installation
============

Requirements
************

* Python_ 2.6 or higher
* MongoDB_ 1.6 or higher (not tested on lower versions)
* pip python packages manager (for installation other required modules)

.. _Python: http://python.org/
.. _MongoDB: http://www.mongodb.org/


Installation
************
1. We recommend you to create virtualenv using python virtualenv module.
2. Clone our respository:

   ``hg clone ssh://hg@codebasehq.com/djangostars/harma/harma.hg harma``

3. Go to project directory.
4. Install dependencies:

   ``pip install -r ./requirement.txt``

5. That's all. Now you can run project in test environment::

     cd harma
     main.py --env=test

   Go to http://localhost:8888 in your browser and check if it works
