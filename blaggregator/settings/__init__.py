from .base import *

if "PROD" in os.environ:
    print("** DETECTED PRODUCTION ENVIRONMENT")
    from .production import *

elif "STAGING" in os.environ:
    print("** DETECTED STAGING ENVIRONMENT")
    from .staging import *

elif "TRAVIS" in os.environ:
    print("** DETECTED TRAVIS ENVIRONMENT")
    from .travis import *

elif "DOCKER_ENV" in os.environ:
    print("** DETECTED DOCKER ENVIRONMENT")
    from .docker import *

else:
    print("** DETECTED LOCAL ENVIRONMENT")
