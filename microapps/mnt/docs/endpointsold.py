@blueprint.route('/upload', methods=["POST"])
@guarded_endpoint(
    expected_mimetype="multipart/form-data", 
    auth=True
)
def upload_file(*args, **kwargs):
    ip = "unknown"
    try:
        headers = kwargs["headers"]
        ip = headers.get("ip")
        resp = kwargs["response"]

        expected_data = {
            "title": {
                "min-length": int(mnt.env.get("min_post_title_length")),
                "max-length": int(mnt.env.get("max_post_title_length")),
                "scanner": "title"
            },
            "privacy": {
                "scanner": ("public", "private")
            },
            "description": {
                "min-length": 0,
                "max-length": int(mnt.env.get("max_post_description_length")),
                "scanner": "text"
            }
        }
        expected_files = {
            "file": {
                "size": 0
            }
        }
        ok, code, msg, data = web_client.request_has_formdatacontent(
            request=request, #type:ignore
            expected_data=expected_data,
            expected_files=expected_files
        )
        if not ok:
            return log_manager.http_response(
                resp.fail(msg, status=401, code=code)
            )
        
        form_data = data["form"]
        files_data = data["files"]

        ok, code, msg, fdata = web_client.formdata_request_safe(
            form_data=form_data,
            files_data=files_data,
            expected_data=expected_data,
            expected_files=expected_files
        )
        if not ok:
            return log_manager.http_response(
                resp.fail(msg, status=400, code=code)
            )    

        form_data = fdata.get("form")
        files_data = fdata.get("files")

        # Continuar con el flujo

        file = files_data["file"]  # único archivo enviado
        username = auth_manager.jwt.whois(token=request.cookies.get("sessionID"))  # type:ignore
        user_id = int(auth_manager.db.get_user_id(username=username))

        #upload_post última versión pide post: PostMeta, file: StorageObject

        mnt.upload_post(
            post = PostMeta(
                user_id=user_id,
                author=username,
                privacy=form_data.get("privacy", ""),
                post_title=file.get("filename", ""),
                post_description=form_data.get("description", ""),
                bucket=mnt.bucket,
                object_key=f"{username}/{file.get('filename')}",
                mime_type=file.get("mime-type", ""),
                size=int(file.get("size", ""))
            ),
            file = StorageObject(
                bucket=mnt.bucket,
                object_key=f"{username}/{file.get('filename')}",
                length=int(file.get("size", "")),
                mime_type=file.get("mime-type", ""),
                data=file.get("file-object", "") #ese fileobject me parece que es un file object de flask, pero data está pidiendo BinaryIO
            )
        )

        return log_manager.http_response(
            resp.success(data={"message": "Post subido correctamente."})
        )
    except Exception as e:
        return web_client.failed_request(
            log_manager=log_manager, 
            e=e, 
            ip=ip, 
            resp=resp
        )
    
@blueprint.route('/delete', methods=["POST"])
@guarded_endpoint(
    expected_mimetype="application/json", 
    auth=True
)
def delete_file(*args, **kwargs):
    ip = "unknown"
    try:
        headers = kwargs["headers"]
        ip = headers.get("ip")
        resp = kwargs["response"]

        expected_data = {
            "filename": {
                "min-length": int(mnt.env.get("min_post_title_length")),
                "max-length": int(mnt.env.get("max_post_title_length")),
                "scanner": "title"
            }
        }

        ok, code, msg, data = web_client.request_has_jsoncontent(
            request=request, #type:ignore
            expected_data=expected_data
        )
        if not ok:
            return log_manager.http_response(
                resp.fail(msg, status=401, code=code)
            )
        
        json_data = data["json"]

        ok, code, msg, jdata = web_client.json_request_safe(
            json_data=json_data,
            expected_data=expected_data
        )
        if not ok:
            return log_manager.http_response(
                resp.fail(msg, status=400, code=code)
            )    

        json_data = jdata.get("json")

        #continuar con el flujo

        filename = json_data.get("filename")
        username = auth_manager.jwt.whois(token=request.cookies.get("sessionID"))  # type:ignore

        mnt.delete_post(
            user=username,
            post_title=filename
        )

        return log_manager.http_response(
            resp.success(data={"message": "Post eliminado correctamente."})
        )
    
    except Exception as e:
        return web_client.failed_request(
            log_manager=log_manager, 
            e=e, 
            ip=ip, 
            resp=resp
        )