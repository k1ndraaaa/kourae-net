from request_template import Request, Client, Auth
from flask import Request as FlaskRequest

def translate_flask_request(flask_req: FlaskRequest) -> Request:
    return Request(
        method=flask_req.method,
        url=flask_req.url,
        path=flask_req.path,
        headers=dict(flask_req.headers),
        query_params=dict(flask_req.args),
        path_params={},
        body=flask_req.get_data(),
        form=dict(flask_req.form),
        files={k: v for k, v in flask_req.files.items()},
        cookies=dict(flask_req.cookies),
        client=Client(ip=flask_req.remote_addr, user_agent=flask_req.headers.get("User-Agent")),
        auth=Auth(
            type=flask_req.authorization.type if flask_req.authorization else None,
            credentials=flask_req.authorization
        ),
        meta={}
    )