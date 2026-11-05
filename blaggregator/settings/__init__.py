from .base import *

if "PROD" in os.environ:
    print("** DETECTED PRODUCTION ENVIRONMENT")
    from .production import *

elif "STAGING" in os.environ:
    print("** DETECTED STAGING ENVIRONMENT")
    from .staging import *

elif "CI" in os.environ:
    print("** DETECTED CI ENVIRONMENT")
    from .ci import *

elif "DOCKER_ENV" in os.environ:
    print("** DETECTED DOCKER ENVIRONMENT")
    from .docker import *

else:
    print("** DETECTED LOCAL ENVIRONMENT")
