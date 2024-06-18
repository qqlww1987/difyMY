import re
import logging
import os
from docx import Document
import csv
import tempfile
from werkzeug.local import LocalProxy
from flask import current_app
from flask import g
from io import BytesIO
from flask_restful import Resource, reqparse
from flask import request, jsonify, send_file
from controllers.console import api
from events.tenant_event import tenant_was_created
from models.account import Account
from services.account_service import TenantService
from controllers.console.datasets.error import TooManyFilesError
from controllers.console.app.error import NoFileUploadedError
from flask import has_request_context
logger = logging.getLogger(__name__)
current_user = LocalProxy(lambda: _get_user())

class EnterpriseWorkspaceNew(Resource):
    
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True, location='json')
        parser.add_argument('owner_email', type=str, required=True, location='json')
        args = parser.parse_args()
        account = Account.query.filter_by(email=args['owner_email']).first()
        if account is None:
            return {
                'message': 'owner account not found.'
            }, 404

        tenant = TenantService.create_tenant(args['name'])
        TenantService.create_tenant_member(tenant, account, role='owner')
        # TenantService.create_tenant_provider_models(tenant,  role='owner')
        tenant_was_created.send(tenant)

        return {
            'message': 'enterprise workspace created.'
        }

class EnterpriseWorkspaceDelete(Resource):
    
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('tenant_id', type=str, required=True, location='json')
        args = parser.parse_args()
        
        TenantService.archive_tenant(args['tenant_id'],current_user)
        # tenant_was_created.send(tenant)
        return {
            'message': '工作空间已删除.'
        }

class NewResource(Resource):
    
    def after_request(self, resp):
        print(888888)
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Credentials'] = 'true'
        return resp
# guorq 这个是将word 转换成对应的csv的方法
class ConvertFAQApi(NewResource):
    def post(self):
        # get file from request
        file = request.files['file']
        # check file
        if 'file' not in request.files:
            raise NoFileUploadedError()
        if len(request.files) > 1:
            raise TooManyFilesError()
        # check file type
        if not file.filename.endswith('.docx'):
            raise ValueError("Invalid file type. Only docx files are allowed")
        try:
            # Open the Word document
            document = Document(file)
            temp_dir = tempfile.gettempdir()
            temp_file_pathCsv = os.path.join(temp_dir, "converted.csv")
            # Create a CSV file object in memory
            csv_file = create_csv_file(document,temp_file_pathCsv)
            print(12345676)
            # Return the CSV file for download
            return send_file(temp_file_pathCsv,
                             as_attachment=True,
                             download_name='converted.csv',
                             mimetype='text/csv')
            # return {
            # 'message': '转换完成.',
            # 'filePath': temp_file_pathCsv}

        except Exception as e:
            print(e)
            return jsonify({'error': str(e)}), 500
    
        # 获取 Word 文档的编号定义列

    # 检查段落是否为标题
        if paragraph.style.name.startswith('Heading'):
            # 检查段落是否设置了编号
            if paragraph._p.pPr is not None and paragraph._p.pPr.numPr is not None:
                num_id = paragraph._p.pPr.numPr.numId.val
                if num_id==4:
                    return True
        
        return False
def create_csv_file(document,temp_file_pathCsv):
    try:
        # Create a CSV file object in memory
        current_section = None
        current_section = None
      
        with open(temp_file_pathCsv, 'w',encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['question', 'answer', 'url'])  # 写入列名
            paragraphs = document.paragraphs
            for index, paragraph in enumerate(paragraphs):
                if index == len(paragraphs) - 1:
                    writer.writerow([current_section['title'],current_section['content'],""])
                elif paragraph.style.name.startswith('Heading'):
                    #判断标题是否是自动编号
                    text = paragraph.text
                    #判断text是否为空
                    
                    match = re.search(r'\d+', text)  # 使用正则表达式提取数字
                    # num_pr=paragraph._p.pPr.numPr.numId.val
                    # is not None and paragraph.style._element.numPr.numId.val == 1
                    num_pr=is_heading_numbered(document,paragraph)           
                    if match or num_pr==True :
                        #判断current_section是否为空
                        if current_section is not None:
                            writer.writerow([current_section['title'],current_section['content'],""])
                        current_section = {'title': text, 'content': []}
                        # number = int(match.group())
                        # title_numbers.append(number)
                elif current_section is not None:
                    # 标题下的内容
                    #判断paragraph.text是否是空字符串
                    if paragraph.text.strip() != "":
                        current_section['content'].append(paragraph.text)
                    #如何是最后一个循环则直接添加
                
                    # my_dict.update(current_section)
                    # current_section = None        
        print(888888)
        # with open(temp_file_pathCsv, 'rb') as file:
        #     csv_data = file.read()
        #     return csv_data
    except Exception as e:
            logger.error(f"Error creating CSV file: {e}")
            raise
def is_heading_numbered(doc, paragraph):
    # 获取 Word 文档的编号定义列

    # 检查段落是否为标题
    if paragraph.style.name.startswith('Heading'):
        # 检查段落是否设置了编号
        if paragraph._p.pPr is not None and paragraph._p.pPr.numPr is not None:
            num_id = paragraph._p.pPr.numPr.numId.val
            if num_id==4:
                return True
    
    return False

def _get_user():
    if has_request_context():
        if "_login_user" not in g:
            current_app.login_manager._load_user()

        return g._login_user

    return None

# # 示例用法
api.add_resource(EnterpriseWorkspaceNew, '/enterprise/workspace')
api.add_resource(EnterpriseWorkspaceDelete, '/enterprise/workspaceRemove')
api.add_resource(ConvertFAQApi, '/enterprise/convert-faq')

