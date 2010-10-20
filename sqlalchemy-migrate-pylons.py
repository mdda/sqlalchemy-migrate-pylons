# python sqlalchemy-migrate-pylons.py development.ini 0

import optparse
import os

from sqlalchemy.engine import Engine

#TEST
import sqlalchemy

from migrate.versioning import genmodel, schemadiff
from migrate.versioning.util import load_model, construct_engine #, with_engine

from paste.deploy.loadwsgi import NicerConfigParser

# This is the inspiration for this simple script :
# migrate update_db_from_model sqlite:///development.db migrate_repository web2mobile.model.meta:metadata

# default_url   = 'sqlite:///development.db'
# default_model = 'MYPROJ.model.meta:metadata'

_debug_messages=False

# @with_engine
def update_pylons_db_from_model(url, model_str, commit=False):
    """update_pylons_db_from_model URL MODEL_STR COMMIT

    Modify the database to match the structure of the current Pylons
    model. 

    NOTE: This is EXPERIMENTAL.
    """  # TODO: get rid of EXPERIMENTAL label
    
    global _debug_messages
    
#    engine = opts.pop('engine')  # relies on @with_engine, and url being first argument
    engine = construct_engine(url) # direct approach
    if _debug_messages:
        print "engine= ", engine
    
    if _debug_messages:
        print "sqlalchemy-migrate-pylons : engine created"
    
    model = load_model(model_str)
    if _debug_messages:
        print "sqlalchemy-migrate-pylons : model loaded from model_str"
    
    #model.init_model(engine)
    
    diff = schemadiff.getDiffOfModelAgainstDatabase(model, engine)
    print "\n====== sqlalchemy-migrate-pylons : Model vs. Database ======\n", diff, "\n"
    
    if commit:
#        genmodel.ModelGenerator(diff).applyModel()
        print "\n Engine : ", diff.conn.engine, "\n"

        print "\n Meta Internal: ", model.metadata, "\n"
        print "\n Meta Migrate : ", sqlalchemy.MetaData(diff.conn.engine), "\n"
        
        genmodel.ModelGenerator(diff).applyModel()
        print "====== sqlalchemy-migrate-pylons : Database Migrated ======\n"

        diff = schemadiff.getDiffOfModelAgainstDatabase(model, engine)
        print "\n====== sqlalchemy-migrate-pylons : Model vs. Database (after migration) ======\n", diff, "\n"
    
    if isinstance(engine, Engine):
        engine.dispose()


def get_config(cp, section, expected_use_value=None):
    """Get a section from an INI-style config file as a dict.

    ``cp`` -- NicerConfigParser.
    ``section`` -- the section to read.
    ``expected_use_value`` -- expected value of ``use`` option in the section.

    Aborts if the value of ``use`` doesn't equal the expected value.  This
    indicates Paster would instantiate a different object than we're expecting.

    The ``use`` key is removed from the dict before returning.
    """
    defaults = cp.defaults()
    ret = {}
    for option in cp.options(section):
        if option.startswith("set "):  # Override a global option.
            option = option[4:]
        elif option in defaults:       # Don't carry over other global options.
            continue
        ret[option] = cp.get(section, option)
    if expected_use_value is not None :
       use = ret.pop("use", "")
       if use != expected_use_value:
           msg = ("unexpected value for 'use=' in section '%s': "
                  "expected '%s', found '%s'")
           msg %= (section, expected_use_value, use)
           raise EnvironmentError(msg)
    return ret

def update_from_ini(ini_file, app, commit):
    """ Pull in the relavant database and model parameters from pylons .INI
    
    This makes use of the ConfigParser embedded in paste.deploy.loadwsgi.
    
    It looks for a section called [app] 
     -- the typical value is [app:main]
    
    The database URL is found from ``sqlalchemy.url`` 
     -- eg:  ``sqlalchemy.url = sqlite:///%(here)s/development.db``
    
    The metadata for SQLalchemy is taken from a new entry : ``migrate.metadata`` 
     -- eg: ``migrate.metadata = MYPROJ.model.meta:metadata``
     
     
    Where the file model/meta.py contains the following : 
    
    ``
    from sqlalchemy import schema
    metadata = schema.MetaData()
    
    # The declarative DataBase base Object
    Base = declarative_base(metadata=metadata)
    ``
    """
    global _debug_messages
    
    ini_file = os.path.abspath(ini_file)
    if not os.path.exists(ini_file):
        raise OSError("File %s not found" % ini_file)
    config_dir = os.path.dirname(ini_file)

    cp = NicerConfigParser(ini_file)
    cp.read(ini_file)
    global_conf = cp.defaults()
    cp._defaults.setdefault("here", config_dir)
    cp._defaults.setdefault("__file__", ini_file)
    
    app_main = get_config(cp, app, None)
    
    url = app_main['sqlalchemy.url']
    
#    model_egg = app_main['use']
#    model = model_egg.replace('egg:', '') + '.model.meta:metadata'
    
    model = app_main['migrate.metadata']
    
    if _debug_messages:
        print "url   = '%s'" % url
        print "model = '%s'" % model
    
    update_pylons_db_from_model(url, model, commit)
    


def main():
    parser = optparse.OptionParser(usage="%prog [options] STANDALONE.ini ")
    parser.add_option("-a", "--app", action="store_true", dest="app", help="section to parse in ini file (default=%default)", default='app:main')
    parser.add_option("-c", "--commit", action="store_true", dest="commit", help="Use diffs to update database (default=%default)", default=False)
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", help="Show debug messages")

    (options, args) = parser.parse_args()
    
    if len(args)<1:
        parser.error("wrong number of command-line arguments")
    ini_file=args[0]
    
    global _debug_messages
    _debug_messages = options.verbose
    
    update_from_ini(ini_file, options.app, options.commit)

if __name__ == "__main__":
    main()


"""

I've been having a play with sqlalchemy-migrate, and decided that it's overkill compared to the simplicity of the migration tool that people love for Ruby. (In addition, sqlalchemy-migrate is fiddly to set up with Pylons. )

There's also a project call miruku, but that is also a little illusive, somehow.

I've created a 150 line script that parses the Pylons INI file (augmented with a line that points to the model.metadata variable definition), and allows just two actions :

a) diff the current database vs. the what the models want

b) commit the changes required to bring the two into sync.

It's dependent on sqlalchemy-migrate, but seems to me it would sit better as a Paster-Pylons plug-in. But that's not really my call.

Would anyone like to see the code? Since I've still got training wheels on, it probably isn't very Pythonesque - but it works for me...

Martin :-)

"""