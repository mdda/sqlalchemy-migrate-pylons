This simple script pulls in the relavant database and model parameters from pylons .INI

It relies on the 'migrate' egg for the 'diff' and 'applyModel' functions, and also makes use of the ConfigParser embedded in paste.deploy.loadwsgi.

Within the .INI file, it looks for a section called [app] :
    the typical value is [app:main]

The database URL is found from ``sqlalchemy.url`` :
    ``sqlalchemy.url = sqlite:///%(here)s/development.db``

The metadata for SQLalchemy is taken from a new entry : ``migrate.metadata`` :
    ``migrate.metadata = MYPROJ.model.meta:metadata``
 
 
Where the file model/meta.py contains the following : 

``
    from sqlalchemy import schema
    metadata = schema.MetaData()

    # The declarative DataBase base Object
    Base = declarative_base(metadata=metadata)
``

Syntax : ::

    (python-local) $ python sqlalchemy-migrate-pylons.py --help

    Usage: sqlalchemy-migrate-pylons.py [options] STANDALONE.ini 

    Options:
      -h, --help     show this help message and exit
      -a, --app      section to parse in ini file (default=app:main)
      -c, --commit   Use diffs to update database (default=False)
      -v, --verbose  Show debug messages

Normal usage :

1. To check what needs to be changed: 
``python sqlalchemy-migrate-pylons.py development.ini`` 

2. To implement the changes and report back:
``python sqlalchemy-migrate-pylons.py --commit development.ini`` 
