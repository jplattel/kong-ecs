import os
import string
import sys
from typing import Dict

import requests
from requests import Response


class Kong:
    def __init__(self):
        self.defined_users = []
        self.api_key = os.getenv("APIKEY")
        api_host = os.getenv("APIHOST")

        if self.api_key is None:
            print("APIKEY env not set, please specify")
            sys.exit(-1)

        if api_host is None:
            print("APIHOST env not set, please specify")
            sys.exit(-1)

        self.base_url = "https://{}/kong".format(api_host)

    def path(self, path: string):
        return "{}{}".format(self.base_url, path)

    def get(self, path: string, params=None, **kwargs):
        args = self._add_api_key_(kwargs)
        response = requests.get(self.path(path), params, **args)
        return self._raise_on_error_(response)

    def post(self, path: string, data=None, json=None, **kwargs):
        args = self._add_api_key_(kwargs)
        response = requests.post(self.path(path), data, json, **args)
        return self._raise_on_error_(response)

    def delete(self, path: string, **kwargs):
        args = self._add_api_key_(kwargs)
        response = requests.delete(self.path(path), **args)
        return self._raise_on_error_(response)

    def put(self, path: string, data=None, **kwargs):
        args = self._add_api_key_(kwargs)
        response = requests.put(self.path(path), data, **args)
        return self._raise_on_error_(response)

    def patch(self, path: string, data=None, **kwargs):
        args = self._add_api_key_(kwargs)
        response = requests.patch(self.path(path), data, **args)
        return self._raise_on_error_(response)

    def _add_api_key_(self, kwargs: Dict):
        args = kwargs.copy()
        if args.get("headers", False):
            args["headers"].update({"apikey": self.api_key})
        else:
            args.update({"headers": {"apikey": self.api_key}})
        return args

    @staticmethod
    def _raise_on_error_(res: Response):
        if res.status_code / 100 == 5 or (res.status_code / 100 == 4 and res.status_code != 404):
            raise Exception("Error occured, http error code: {}".format(res.status_code))
        return res

    def ensure_consumer(self, consumer: string):
        self.defined_users.append(consumer)
        if self.get("/consumers/{}".format(consumer)).status_code == 404:
            print("..Creating consumer {}".format(consumer))
            self.post("/consumers", json={
                "username": consumer
            })

    def ensure_keyauth_acl(self, consumer: string, *cons_groups: string):
        print("Consumer: {}".format(consumer))
        self.ensure_consumer(consumer)
        keys = self.get("/consumers/{}/key-auth".format(consumer)).json()["data"]
        if len(keys) == 0:
            print("Creating apikey for consumer {}...".format(consumer))
            new_key = self.post("/consumers/{}/key-auth".format(consumer), json={}).json()["key"]
            print("Generated apikey: {}".format(new_key))
        groups = self.get("/consumers/{}/acls".format(consumer)).json()["data"]
        for acl in filter(lambda a: a["group"] not in cons_groups, groups):
            print("Removing wrong ACL '{}' for consumer '{}'".format(acl, consumer))
            self.delete("/consumers/{}/acls/{}".format(consumer, acl["id"]))
        cur_group_names = map(lambda x: x["group"], groups)
        for group_to_create in filter(lambda g: g not in cur_group_names, cons_groups):
            print("Creating ACL for {} on group {}".format(consumer, group_to_create))
            self.post("/consumers/{}/acls".format(consumer), json={
                "group": group_to_create
            })

    def ensure_oauth2_consumer(self, consumer: string, app_name: string, *redirect_uri: string):
        print("Consumer: {}".format(consumer))
        self.ensure_consumer(consumer)
        apps = self.get("/consumers/{}/oauth2".format(consumer)).json()
        if apps["total"] == 0:
            print("..Creating application {}".format(app_name))
            new_app = self.post("/consumers/{}/oauth2".format(consumer), json={
                "name": app_name,
                "redirect_uri": list(redirect_uri)
            }).json()
            print("...Client ID: {}, Client Secret: {}".format(new_app["client_id"], new_app["client_secret"]))
        else:
            app_id = next(iter(apps["data"]))["id"]
            print("..App ID: {}: ensuring app name = {} and redirect_uris = {}".format(app_id, app_name, redirect_uri))
            self.patch("/consumers/{}/oauth2/{}".format(consumer, app_id), json={
                "name": app_name,
                "redirect_uri": redirect_uri
            })

    def remove_undefined_users(self):
        users_to_delete = list(
            filter(lambda c: c["username"] not in self.defined_users, self.get("/consumers").json()["data"])
        )
        for user_to_delete in users_to_delete:
            username = user_to_delete["username"]
            print("Deleting undefined user: {}...".format(username))
            self.delete("/consumers/{}".format(username))
