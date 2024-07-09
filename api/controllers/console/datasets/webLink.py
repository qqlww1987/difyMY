from flask import current_app, request
from flask_login import current_user
from flask_restful import Resource, marshal_with

import services
from controllers.console import api
from controllers.console.datasets.error import (
    FileTooLargeError,
    NoFileUploadedError,
    TooManyFilesError,
    UnsupportedFileTypeError,
)
from controllers.console.setup import setup_required
from controllers.console.wraps import account_initialization_required, cloud_edition_billing_resource_check
from fields.file_fields import file_fields, upload_config_fields
from libs.login import login_required
from services.file_service import ALLOWED_EXTENSIONS, UNSTRUSTURED_ALLOWED_EXTENSIONS, FileService

PREVIEW_WORDS_LIMIT = 3000


class WebLinkApi(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    def post(self):

        # get file from request
        file = request.files['file']

        # check file
        if 'file' not in request.files:
            raise NoFileUploadedError()

        if len(request.files) > 1:
            raise TooManyFilesError()
        try:
            upload_file,htmlDocUrl = FileService.upload_file(file, current_user)
        except services.errors.file.FileTooLargeError as file_too_large_error:
            raise FileTooLargeError(file_too_large_error.description)
        except services.errors.file.UnsupportedFileTypeError:
            raise UnsupportedFileTypeError()

        return upload_file, 201


    @setup_required
    @login_required
    @account_initialization_required
    def get(self):
        etl_type = current_app.config['ETL_TYPE']
        allowed_extensions = UNSTRUSTURED_ALLOWED_EXTENSIONS if etl_type == 'Unstructured' else ALLOWED_EXTENSIONS
        return {'allowed_extensions': allowed_extensions}


api.add_resource(WebLinkApi, '/webLink/upload')

