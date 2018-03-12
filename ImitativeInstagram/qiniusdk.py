# -*- encoding:utf-8 -*-
from qiniu import Auth, put_data, put_stream
from ImitativeInstagram import app

access_key = app.config["QINIU_ACCESSKEY"]
secret_key = app.config["QINIU_SECRETKEY"]
q = Auth(access_key=access_key, secret_key=secret_key)

bucket_name = app.config["QINIU_BUCKET_NAME"]
domain_prefix = app.config["QINIU_DOMAIN"]

def qiniu_upload_file(source_file, save_file_name):
    # generate upload token.
    token = q.upload_token(bucket_name, save_file_name)
    ret, info = put_data(token, save_file_name, source_file.stream)
    print type(info.status_code), info
    if info.status_code == 200:
        return domain_prefix + save_file_name
    return None
