import string

from kong import Kong


def create_meteor_api(name: string, request_path: string):
    print("Creating {} API...".format(name))
    kong.post("/apis", json={
        "name": name,
        "preserve_host": True,
        "request_path": request_path,
        "strip_request_path": False,
        "upstream_url": "http://api.partup.local"
    })
    add_meteor_acl(name)


def add_meteor_acl(name: string):
    print("Setting ACL on {} API...".format(name))
    kong.post("/apis/{}/plugins".format(name), json={
        "name": "acl",
        "config": {
            "whitelist": ["meteor"]
        }
    })
    print("Activating apikey auth on {} API...".format(name))
    kong.post("/apis/{}/plugins".format(name), json={
        "name": "key-auth",
        "config": {
            "hide_credentials": True
        }
    })


kong = Kong()
apis = kong.get("/apis")

api_names = set(map(lambda a: a["name"], apis.json()["data"]))

print("API: events")
if "events" not in api_names:
    create_meteor_api("events", "/events")

print("API: recommendations")
if "recommendations" not in api_names:
    create_meteor_api("recommendations", "/partups/recommended/for")

print("API: oauth_info")
if "oauth_info" not in api_names:
    print("Creating oauth_info API...")
    kong.post("/apis", json={
        "name": "oauth_info",
        "preserve_host": True,
        "request_path": "/kong/oauth2",
        "strip_request_path": True,
        "upstream_url": "http://localhost:8001/oauth2"
    })
    add_meteor_acl("oauth_info")

print("API: root_api")
if "root_api" not in api_names:
    print("Creating root_api API...")
    kong.post("/apis", json={
        "name": "root_api",
        "preserve_host": "false",
        "request_path": "/",
        "strip_request_path": False,
        "upstream_url": "http://user-api.partup.local"
    })
    print("Setting up oauth2 on root_api API...")
    result = kong.post("/apis/root_api/plugins", json={
        "name": "oauth2",
        "config": {
            "accept_http_if_already_terminated": True,
            "enable_authorization_code": True,
            "enable_client_credentials": False,
            "enable_implicit_grant": False,
            "enable_password_grant": False,
            "hide_credentials": True,
            "mandatory_scope": True,
            "scopes": ["openid"]
        }
    })
    if result.status_code == 404:
        raise Exception("404 on create call, should be 200 OK.")
    provision_key = result.json()["config"]["provision_key"]
    print("Provision key for oauth2: {}".format(provision_key))

all_api_names = ["kong", "events", "recommendations", "oauth_info", "root_api"]
for api in api_names.difference(all_api_names):
    print("Deleting unknown API '{}'".format(api))
    kong.delete("/apis/{}".format(api))

kong.ensure_keyauth_acl("meteor", "meteor")
kong.ensure_keyauth_acl("admin", "admin")
kong.ensure_oauth2_consumer("partupy", "Apper McAppface", "https://example.com/oauth2")
kong.ensure_oauth2_consumer("jplattel", "Joost Plattel", "http://localhost:8000/callback")

kong.remove_undefined_users()
