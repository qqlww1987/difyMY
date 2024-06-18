import re
from docx import Document
import csv
import tempfile
import io
from flask import request, jsonify, send_file
from flask_login import current_user
from flask_restful import Resource, marshal, marshal_with, reqparse
from werkzeug.exceptions import Forbidden
from docx import Document
from controllers.console import api
from controllers.console.app.error import NoFileUploadedError
from controllers.console.datasets.error import TooManyFilesError
from controllers.console.setup import setup_required
from controllers.console.wraps import account_initialization_required, cloud_edition_billing_resource_check
from extensions.ext_redis import redis_client
from fields.annotation_fields import (
    annotation_fields,
    annotation_hit_history_fields,
)
from libs.login import login_required
from services.annotation_service import AppAnnotationService


class AnnotationReplyActionApi(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    @cloud_edition_billing_resource_check('annotation')
    def post(self, app_id, action):
        # The role of the current user in the ta table must be admin or owner
        if not current_user.is_admin_or_owner:
            raise Forbidden()

        app_id = str(app_id)
        parser = reqparse.RequestParser()
        parser.add_argument('score_threshold', required=True, type=float, location='json')
        parser.add_argument('embedding_provider_name', required=True, type=str, location='json')
        parser.add_argument('embedding_model_name', required=True, type=str, location='json')
        args = parser.parse_args()
        if action == 'enable':
            result = AppAnnotationService.enable_app_annotation(args, app_id)
        elif action == 'disable':
            result = AppAnnotationService.disable_app_annotation(app_id)
        else:
            raise ValueError('Unsupported annotation reply action')
        return result, 200


class AppAnnotationSettingDetailApi(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    def get(self, app_id):
        # The role of the current user in the ta table must be admin or owner
        if not current_user.is_admin_or_owner:
            raise Forbidden()

        app_id = str(app_id)
        result = AppAnnotationService.get_app_annotation_setting_by_app_id(app_id)
        return result, 200


class AppAnnotationSettingUpdateApi(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    def post(self, app_id, annotation_setting_id):
        # The role of the current user in the ta table must be admin or owner
        if not current_user.is_admin_or_owner:
            raise Forbidden()

        app_id = str(app_id)
        annotation_setting_id = str(annotation_setting_id)

        parser = reqparse.RequestParser()
        parser.add_argument('score_threshold', required=True, type=float, location='json')
        args = parser.parse_args()

        result = AppAnnotationService.update_app_annotation_setting(app_id, annotation_setting_id, args)
        return result, 200


class AnnotationReplyActionStatusApi(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    @cloud_edition_billing_resource_check('annotation')
    def get(self, app_id, job_id, action):
        # The role of the current user in the ta table must be admin or owner
        if not current_user.is_admin_or_owner:
            raise Forbidden()

        job_id = str(job_id)
        app_annotation_job_key = '{}_app_annotation_job_{}'.format(action, str(job_id))
        cache_result = redis_client.get(app_annotation_job_key)
        if cache_result is None:
            raise ValueError("The job is not exist.")

        job_status = cache_result.decode()
        error_msg = ''
        if job_status == 'error':
            app_annotation_error_key = '{}_app_annotation_error_{}'.format(action, str(job_id))
            error_msg = redis_client.get(app_annotation_error_key).decode()

        return {
            'job_id': job_id,
            'job_status': job_status,
            'error_msg': error_msg
        }, 200


class AnnotationListApi(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    def get(self, app_id):
        # The role of the current user in the ta table must be admin or owner
        if not current_user.is_admin_or_owner:
            raise Forbidden()

        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=20, type=int)
        keyword = request.args.get('keyword', default=None, type=str)

        app_id = str(app_id)
        annotation_list, total = AppAnnotationService.get_annotation_list_by_app_id(app_id, page, limit, keyword)
        response = {
            'data': marshal(annotation_list, annotation_fields),
            'has_more': len(annotation_list) == limit,
            'limit': limit,
            'total': total,
            'page': page
        }
        return response, 200


class AnnotationExportApi(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    def get(self, app_id):
        # The role of the current user in the ta table must be admin or owner
        if not current_user.is_admin_or_owner:
            raise Forbidden()

        app_id = str(app_id)
        annotation_list = AppAnnotationService.export_annotation_list_by_app_id(app_id)
        response = {
            'data': marshal(annotation_list, annotation_fields)
        }
        return response, 200


class AnnotationCreateApi(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    @cloud_edition_billing_resource_check('annotation')
    @marshal_with(annotation_fields)
    def post(self, app_id):
        # The role of the current user in the ta table must be admin or owner
        if not current_user.is_admin_or_owner:
            raise Forbidden()

        app_id = str(app_id)
        parser = reqparse.RequestParser()
        parser.add_argument('question', required=True, type=str, location='json')
        parser.add_argument('answer', required=True, type=str, location='json')
        args = parser.parse_args()
        annotation = AppAnnotationService.insert_app_annotation_directly(args, app_id)
        return annotation


class AnnotationUpdateDeleteApi(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    @cloud_edition_billing_resource_check('annotation')
    @marshal_with(annotation_fields)
    def post(self, app_id, annotation_id):
        # The role of the current user in the ta table must be admin or owner
        if not current_user.is_admin_or_owner:
            raise Forbidden()

        app_id = str(app_id)
        annotation_id = str(annotation_id)
        parser = reqparse.RequestParser()
        parser.add_argument('question', required=True, type=str, location='json')
        parser.add_argument('answer', required=True, type=str, location='json')
        args = parser.parse_args()
        annotation = AppAnnotationService.update_app_annotation_directly(args, app_id, annotation_id)
        return annotation

    @setup_required
    @login_required
    @account_initialization_required
    def delete(self, app_id, annotation_id):
        # The role of the current user in the ta table must be admin or owner
        if not current_user.is_admin_or_owner:
            raise Forbidden()

        app_id = str(app_id)
        annotation_id = str(annotation_id)
        AppAnnotationService.delete_app_annotation(app_id, annotation_id)
        return {'result': 'success'}, 200


class AnnotationBatchImportApi(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    @cloud_edition_billing_resource_check('annotation')
    def post(self, app_id):
        # The role of the current user in the ta table must be admin or owner
        if not current_user.is_admin_or_owner:
            raise Forbidden()

        app_id = str(app_id)
        # get file from request
        file = request.files['file']
        # check file
        if 'file' not in request.files:
            raise NoFileUploadedError()

        if len(request.files) > 1:
            raise TooManyFilesError()
        # check file type
        if not file.filename.endswith('.csv'):
            raise ValueError("Invalid file type. Only CSV files are allowed")
        return AppAnnotationService.batch_import_app_annotations(app_id, file)


class AnnotationBatchImportStatusApi(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    @cloud_edition_billing_resource_check('annotation')
    def get(self, app_id, job_id):
        # The role of the current user in the ta table must be admin or owner
        if not current_user.is_admin_or_owner:
            raise Forbidden()

        job_id = str(job_id)
        indexing_cache_key = 'app_annotation_batch_import_{}'.format(str(job_id))
        cache_result = redis_client.get(indexing_cache_key)
        if cache_result is None:
            raise ValueError("The job is not exist.")
        job_status = cache_result.decode()
        error_msg = ''
        if job_status == 'error':
            indexing_error_msg_key = 'app_annotation_batch_import_error_msg_{}'.format(str(job_id))
            error_msg = redis_client.get(indexing_error_msg_key).decode()

        return {
            'job_id': job_id,
            'job_status': job_status,
            'error_msg': error_msg
        }, 200


class AnnotationHitHistoryListApi(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    def get(self, app_id, annotation_id):
        # The role of the current user in the table must be admin or owner
        if not current_user.is_admin_or_owner:
            raise Forbidden()

        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=20, type=int)
        app_id = str(app_id)
        annotation_id = str(annotation_id)
        annotation_hit_history_list, total = AppAnnotationService.get_annotation_hit_histories(app_id, annotation_id,
                                                                                               page, limit)
        response = {
            'data': marshal(annotation_hit_history_list, annotation_hit_history_fields),
            'has_more': len(annotation_hit_history_list) == limit,
            'limit': limit,
            'total': total,
            'page': page
        }
        return response
# class NewResource(Resource):
    
#     def after_request(self, resp):
#         print(888888)
#         resp.headers['Access-Control-Allow-Origin'] = '*'
#         resp.headers['Access-Control-Allow-Credentials'] = 'true'
#         return resp
# # guorq 这个是将word 转换成对应的csv的方法
# class ConvertFAQApi(NewResource):
#     @setup_required
#     @login_required
#     @account_initialization_required
#     @cloud_edition_billing_resource_check('annotation')
#     def post(self, app_id):
      
#         print("真是不好玩")
#         # The role of the current user in the ta table must be admin or owner
#         if not current_user.is_admin_or_owner:
#             raise Forbidden()

#         app_id = str(app_id)
#         # get file from request
#         file = request.files['file']
#         # check file
#         if 'file' not in request.files:
#             raise NoFileUploadedError()

#         if len(request.files) > 1:
#             raise TooManyFilesError()
#         # check file type
#         if not file.filename.endswith('.docx'):
#             raise ValueError("Invalid file type. Only docx files are allowed")
#         try:
#             # Open the Word document
#             document = Document(file)

#             # Create a CSV file object in memory
#             csv_file = create_csv_file(document)

#             # Return the CSV file for download
#             return send_file(csv_file,
#                              as_attachment=True,
#                              attachment_filename='converted.csv',
#                              mimetype='text/csv')

#         except Exception as e:
#             return jsonify({'error': str(e)}), 500
    
#         # 获取 Word 文档的编号定义列

#     # 检查段落是否为标题
#         if paragraph.style.name.startswith('Heading'):
#             # 检查段落是否设置了编号
#             if paragraph._p.pPr is not None and paragraph._p.pPr.numPr is not None:
#                 num_id = paragraph._p.pPr.numPr.numId.val
#                 if num_id==4:
#                     return True
        
#         return False
# def create_csv_file(document):
#         paragraphs = document.paragraphs
#         # Create a CSV file object in memory
#         csv_file = io.StringIO()
#         writer = csv.writer(csv_file)
#         writer.writerow(['question', 'answer', 'url'])  # 写入列名
#         for index, paragraph in enumerate(paragraphs):
#             if index == len(paragraphs) - 1:
#                  writer.writerow([current_section['title'],current_section['content'],""])
#             elif paragraph.style.name.startswith('Heading'):
#                 #判断标题是否是自动编号
#                 text = paragraph.text
#                 #判断text是否为空
                
#                 match = re.search(r'\d+', text)  # 使用正则表达式提取数字
#                 # num_pr=paragraph._p.pPr.numPr.numId.val
#                 # is not None and paragraph.style._element.numPr.numId.val == 1
#                 num_pr=is_heading_numbered(document,paragraph)           
#                 if match or num_pr==True :
#                     #判断current_section是否为空
#                     if current_section is not None:
#                         writer.writerow([current_section['title'],current_section['content'],""])
#                     current_section = {'title': text, 'content': []}
#                     # number = int(match.group())
#                     # title_numbers.append(number)
#             elif current_section is not None:
#                 # 标题下的内容
#                 #判断paragraph.text是否是空字符串
#                 if paragraph.text.strip() != "":
#                     current_section['content'].append(paragraph.text)

#         csv_file.seek(0)
#         return csv_file
# def is_heading_numbered(doc, paragraph):
#     # 获取 Word 文档的编号定义列

#     # 检查段落是否为标题
#     if paragraph.style.name.startswith('Heading'):
#         # 检查段落是否设置了编号
#         if paragraph._p.pPr is not None and paragraph._p.pPr.numPr is not None:
#             num_id = paragraph._p.pPr.numPr.numId.val
#             if num_id==4:
#                 return True
    
#     return False
# # 示例用法


api.add_resource(AnnotationReplyActionApi, '/apps/<uuid:app_id>/annotation-reply/<string:action>')
api.add_resource(AnnotationReplyActionStatusApi,
                 '/apps/<uuid:app_id>/annotation-reply/<string:action>/status/<uuid:job_id>')
api.add_resource(AnnotationListApi, '/apps/<uuid:app_id>/annotations')
api.add_resource(AnnotationExportApi, '/apps/<uuid:app_id>/annotations/export')
api.add_resource(AnnotationUpdateDeleteApi, '/apps/<uuid:app_id>/annotations/<uuid:annotation_id>')
api.add_resource(AnnotationBatchImportApi, '/apps/<uuid:app_id>/annotations/batch-import')
# api.add_resource(ConvertFAQApi, '/apps/<uuid:app_id>/annotations/convert-faq')
api.add_resource(AnnotationBatchImportStatusApi, '/apps/<uuid:app_id>/annotations/batch-import-status/<uuid:job_id>')
api.add_resource(AnnotationHitHistoryListApi, '/apps/<uuid:app_id>/annotations/<uuid:annotation_id>/hit-histories')
api.add_resource(AppAnnotationSettingDetailApi, '/apps/<uuid:app_id>/annotation-setting')
api.add_resource(AppAnnotationSettingUpdateApi, '/apps/<uuid:app_id>/annotation-settings/<uuid:annotation_setting_id>')
