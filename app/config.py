import os
APP_ROOT = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))


class Config(object):
    root_path = os.path.abspath(os.path.join(
        os.path.dirname(os.path.realpath(__file__)), ".."))
    SECRET_KEY = "36b55012ad818250b91b270e02efafc04db3151707709fac"
    # print(SECRET_KEY)
    USER_APP_NAME = "Mask-detector-App"
