from .base import *

if 'PROD' in os.environ:
    print "** DETECTED PRODUCTION ENVIRONMENT"
    from .production import *

elif 'STAGING' in os.environ:
    print "** DETECTED STAGING ENVIRONMENT"
    from .staging import *

elif 'TRAVIS' in os.environ:
    print "** DETECTED TRAVIS ENVIRONMENT"
    from .travis import *

else:
    print "** DETECTED LOCAL ENVIRONMENT"
