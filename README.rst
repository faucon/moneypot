Moneypot
========

This is an open-source, easy-to-use "who has to pay how much?"-service.
You can create new "pots" to collect your and your friends expenses.



Developement
------------

Should be
 * test driven
 * aim for 100% code coverage

uses the following technologies:

 * Pyramid Web framework
 * SQLAlchemy as ORM 
 * Bootstrap CSS-Library

Developement Set-Up
^^^^^^^^^^^^^^^^^^^

create new virtualenv

checkout this repository
check out development branch::

    git checkout -b develop origin/develop

install it (as develop egg)::
    
    python setup.py install --develop

this should fetch all dependencies, then you can run moneypot on your local machine with::

    pserve development.ini

Ideas for new features
^^^^^^^^^^^^^^^^^^^^^^

 * Mouseover-Tip in Overview: who are other participants in this pot?
 * Solver: how to solve the open debts with the least transactions
 * Manage payments (from solver): Open, transfer, received
 * Edit expenses
