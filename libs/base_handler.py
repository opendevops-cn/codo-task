#!/usr/bin/env python
# -*-coding:utf-8-*-

import shortuuid
from websdk.cache import get_cache
from websdk.base_handler import BaseHandler as SDKBaseHandler
from tornado.web import HTTPError
from websdk.jwt_token import AuthToken


class BaseHandler(SDKBaseHandler):
    def __init__(self, *args, **kwargs):
        self.new_csrf_key = str(shortuuid.uuid())
        super(BaseHandler, self).__init__(*args, **kwargs)

