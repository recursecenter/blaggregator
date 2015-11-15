import os

if 'PROD' in os.environ:
    print "** DETECTED PRODUCTION ENVIRONMENT"
    from production import *
elif 'STAGING' in os.environ:
    print "** DETECTED STAGING ENVIRONMENT"
    from staging import *
else:
    print "** DETECTED LOCAL ENVIRONMENT"
    from development import *
