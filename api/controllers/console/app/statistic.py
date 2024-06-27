from datetime import datetime
from decimal import Decimal
import ast
import jieba
from collections import Counter
import pytz
from sqlalchemy import text
from flask import jsonify
from flask_login import current_user
from flask_restful import Resource, reqparse
from core.rag.datasource.entity.embedding import Embeddings
from core.embedding.cached_embedding import CacheEmbedding
from core.model_manager import ModelManager
from core.model_runtime.entities.model_entities import ModelType
from controllers.console import api
from controllers.console.app.wraps import get_app_model
from controllers.console.setup import setup_required
from controllers.console.wraps import account_initialization_required
from extensions.ext_database import db
from libs.helper import datetime_string
from libs.login import login_required
from models.model import AppMode
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import numpy as np
from flask import request, url_for, current_app
from collections import defaultdict
from models.model import App, AppMode, AppModelConfig, Conversation, EndUser, Message, MessageFile
import numpy as np

from scipy.cluster.hierarchy import linkage, fcluster

class DailyConversationStatistic(Resource):

    @setup_required
    @login_required
    @account_initialization_required
    @get_app_model
    def get(self, app_model):
        account = current_user

        parser = reqparse.RequestParser()
        parser.add_argument('start', type=datetime_string('%Y-%m-%d %H:%M'), location='args')
        parser.add_argument('end', type=datetime_string('%Y-%m-%d %H:%M'), location='args')
        args = parser.parse_args()

        sql_query = '''
        SELECT date(DATE_TRUNC('day', created_at AT TIME ZONE 'UTC' AT TIME ZONE :tz )) AS date, count(distinct messages.conversation_id) AS conversation_count
            FROM messages where app_id = :app_id 
        '''
        arg_dict = {'tz': account.timezone, 'app_id': app_model.id}

        timezone = pytz.timezone(account.timezone)
        utc_timezone = pytz.utc

        if args['start']:
            start_datetime = datetime.strptime(args['start'], '%Y-%m-%d %H:%M')
            start_datetime = start_datetime.replace(second=0)

            start_datetime_timezone = timezone.localize(start_datetime)
            start_datetime_utc = start_datetime_timezone.astimezone(utc_timezone)

            sql_query += ' and created_at >= :start'
            arg_dict['start'] = start_datetime_utc

        if args['end']:
            end_datetime = datetime.strptime(args['end'], '%Y-%m-%d %H:%M')
            end_datetime = end_datetime.replace(second=0)

            end_datetime_timezone = timezone.localize(end_datetime)
            end_datetime_utc = end_datetime_timezone.astimezone(utc_timezone)

            sql_query += ' and created_at < :end'
            arg_dict['end'] = end_datetime_utc

        sql_query += ' GROUP BY date order by date'

        response_data = []

        with db.engine.begin() as conn:
            rs = conn.execute(db.text(sql_query), arg_dict)
            for i in rs:
                response_data.append({
                    'date': str(i.date),
                    'conversation_count': i.conversation_count
                })

        return jsonify({
            'data': response_data
        })


class DailyTerminalsStatistic(Resource):

    @setup_required
    @login_required
    @account_initialization_required
    @get_app_model
    def get(self, app_model):
        account = current_user

        parser = reqparse.RequestParser()
        parser.add_argument('start', type=datetime_string('%Y-%m-%d %H:%M'), location='args')
        parser.add_argument('end', type=datetime_string('%Y-%m-%d %H:%M'), location='args')
        args = parser.parse_args()

        sql_query = '''
                SELECT date(DATE_TRUNC('day', created_at AT TIME ZONE 'UTC' AT TIME ZONE :tz )) AS date, count(distinct messages.from_end_user_id) AS terminal_count
                    FROM messages where app_id = :app_id 
                '''
        arg_dict = {'tz': account.timezone, 'app_id': app_model.id}

        timezone = pytz.timezone(account.timezone)
        utc_timezone = pytz.utc

        if args['start']:
            start_datetime = datetime.strptime(args['start'], '%Y-%m-%d %H:%M')
            start_datetime = start_datetime.replace(second=0)

            start_datetime_timezone = timezone.localize(start_datetime)
            start_datetime_utc = start_datetime_timezone.astimezone(utc_timezone)

            sql_query += ' and created_at >= :start'
            arg_dict['start'] = start_datetime_utc

        if args['end']:
            end_datetime = datetime.strptime(args['end'], '%Y-%m-%d %H:%M')
            end_datetime = end_datetime.replace(second=0)

            end_datetime_timezone = timezone.localize(end_datetime)
            end_datetime_utc = end_datetime_timezone.astimezone(utc_timezone)

            sql_query += ' and created_at < :end'
            arg_dict['end'] = end_datetime_utc

        sql_query += ' GROUP BY date order by date'

        response_data = []

        with db.engine.begin() as conn:
            rs = conn.execute(db.text(sql_query), arg_dict)            
            for i in rs:
                response_data.append({
                    'date': str(i.date),
                    'terminal_count': i.terminal_count
                })

        return jsonify({
            'data': response_data
        })


class DailyTokenCostStatistic(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    @get_app_model
    def get(self, app_model):
        account = current_user

        parser = reqparse.RequestParser()
        parser.add_argument('start', type=datetime_string('%Y-%m-%d %H:%M'), location='args')
        parser.add_argument('end', type=datetime_string('%Y-%m-%d %H:%M'), location='args')
        args = parser.parse_args()

        sql_query = '''
                SELECT date(DATE_TRUNC('day', created_at AT TIME ZONE 'UTC' AT TIME ZONE :tz )) AS date, 
                    (sum(messages.message_tokens) + sum(messages.answer_tokens)) as token_count,
                    sum(total_price) as total_price
                    FROM messages where app_id = :app_id 
                '''
        arg_dict = {'tz': account.timezone, 'app_id': app_model.id}

        timezone = pytz.timezone(account.timezone)
        utc_timezone = pytz.utc

        if args['start']:
            start_datetime = datetime.strptime(args['start'], '%Y-%m-%d %H:%M')
            start_datetime = start_datetime.replace(second=0)

            start_datetime_timezone = timezone.localize(start_datetime)
            start_datetime_utc = start_datetime_timezone.astimezone(utc_timezone)

            sql_query += ' and created_at >= :start'
            arg_dict['start'] = start_datetime_utc

        if args['end']:
            end_datetime = datetime.strptime(args['end'], '%Y-%m-%d %H:%M')
            end_datetime = end_datetime.replace(second=0)

            end_datetime_timezone = timezone.localize(end_datetime)
            end_datetime_utc = end_datetime_timezone.astimezone(utc_timezone)

            sql_query += ' and created_at < :end'
            arg_dict['end'] = end_datetime_utc

        sql_query += ' GROUP BY date order by date'

        response_data = []

        with db.engine.begin() as conn:
            rs = conn.execute(db.text(sql_query), arg_dict)
            for i in rs:
                response_data.append({
                    'date': str(i.date),
                    'token_count': i.token_count,
                    'total_price': i.total_price,
                    'currency': 'USD'
                })

        return jsonify({
            'data': response_data
        })


class AverageSessionInteractionStatistic(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    @get_app_model(mode=[AppMode.CHAT, AppMode.AGENT_CHAT, AppMode.ADVANCED_CHAT])
    def get(self, app_model):
        account = current_user

        parser = reqparse.RequestParser()
        parser.add_argument('start', type=datetime_string('%Y-%m-%d %H:%M'), location='args')
        parser.add_argument('end', type=datetime_string('%Y-%m-%d %H:%M'), location='args')
        args = parser.parse_args()

        sql_query = """SELECT date(DATE_TRUNC('day', c.created_at AT TIME ZONE 'UTC' AT TIME ZONE :tz )) AS date, 
AVG(subquery.message_count) AS interactions
FROM (SELECT m.conversation_id, COUNT(m.id) AS message_count
    FROM conversations c
    JOIN messages m ON c.id = m.conversation_id
    WHERE c.override_model_configs IS NULL AND c.app_id = :app_id"""
        arg_dict = {'tz': account.timezone, 'app_id': app_model.id}

        timezone = pytz.timezone(account.timezone)
        utc_timezone = pytz.utc

        if args['start']:
            start_datetime = datetime.strptime(args['start'], '%Y-%m-%d %H:%M')
            start_datetime = start_datetime.replace(second=0)

            start_datetime_timezone = timezone.localize(start_datetime)
            start_datetime_utc = start_datetime_timezone.astimezone(utc_timezone)

            sql_query += ' and c.created_at >= :start'
            arg_dict['start'] = start_datetime_utc

        if args['end']:
            end_datetime = datetime.strptime(args['end'], '%Y-%m-%d %H:%M')
            end_datetime = end_datetime.replace(second=0)

            end_datetime_timezone = timezone.localize(end_datetime)
            end_datetime_utc = end_datetime_timezone.astimezone(utc_timezone)

            sql_query += ' and c.created_at < :end'
            arg_dict['end'] = end_datetime_utc

        sql_query += """
        GROUP BY m.conversation_id) subquery
LEFT JOIN conversations c on c.id=subquery.conversation_id
GROUP BY date
ORDER BY date"""

        response_data = []
        
        with db.engine.begin() as conn:
            rs = conn.execute(db.text(sql_query), arg_dict)
            for i in rs:
                response_data.append({
                    'date': str(i.date),
                    'interactions': float(i.interactions.quantize(Decimal('0.01')))
                })

        return jsonify({
            'data': response_data
        })


class UserSatisfactionRateStatistic(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    @get_app_model
    def get(self, app_model):
        account = current_user

        parser = reqparse.RequestParser()
        parser.add_argument('start', type=datetime_string('%Y-%m-%d %H:%M'), location='args')
        parser.add_argument('end', type=datetime_string('%Y-%m-%d %H:%M'), location='args')
        args = parser.parse_args()

        sql_query = '''
                        SELECT date(DATE_TRUNC('day', m.created_at AT TIME ZONE 'UTC' AT TIME ZONE :tz )) AS date, 
                            COUNT(m.id) as message_count, COUNT(mf.id) as feedback_count 
                            FROM messages m
                            LEFT JOIN message_feedbacks mf on mf.message_id=m.id
                            WHERE m.app_id = :app_id 
                        '''
        arg_dict = {'tz': account.timezone, 'app_id': app_model.id}

        timezone = pytz.timezone(account.timezone)
        utc_timezone = pytz.utc

        if args['start']:
            start_datetime = datetime.strptime(args['start'], '%Y-%m-%d %H:%M')
            start_datetime = start_datetime.replace(second=0)

            start_datetime_timezone = timezone.localize(start_datetime)
            start_datetime_utc = start_datetime_timezone.astimezone(utc_timezone)

            sql_query += ' and m.created_at >= :start'
            arg_dict['start'] = start_datetime_utc

        if args['end']:
            end_datetime = datetime.strptime(args['end'], '%Y-%m-%d %H:%M')
            end_datetime = end_datetime.replace(second=0)

            end_datetime_timezone = timezone.localize(end_datetime)
            end_datetime_utc = end_datetime_timezone.astimezone(utc_timezone)

            sql_query += ' and m.created_at < :end'
            arg_dict['end'] = end_datetime_utc

        sql_query += ' GROUP BY date order by date'

        response_data = []

        with db.engine.begin() as conn:
            rs = conn.execute(db.text(sql_query), arg_dict)
            for i in rs:
                response_data.append({
                    'date': str(i.date),
                    'rate': round((i.feedback_count * 1000 / i.message_count) if i.message_count > 0 else 0, 2),
                })

        return jsonify({
            'data': response_data
        })


class AverageResponseTimeStatistic(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    @get_app_model(mode=AppMode.COMPLETION)
    def get(self, app_model):
        account = current_user

        parser = reqparse.RequestParser()
        parser.add_argument('start', type=datetime_string('%Y-%m-%d %H:%M'), location='args')
        parser.add_argument('end', type=datetime_string('%Y-%m-%d %H:%M'), location='args')
        args = parser.parse_args()

        sql_query = '''
                SELECT date(DATE_TRUNC('day', created_at AT TIME ZONE 'UTC' AT TIME ZONE :tz )) AS date, 
                    AVG(provider_response_latency) as latency
                    FROM messages
                    WHERE app_id = :app_id
                '''
        arg_dict = {'tz': account.timezone, 'app_id': app_model.id}

        timezone = pytz.timezone(account.timezone)
        utc_timezone = pytz.utc

        if args['start']:
            start_datetime = datetime.strptime(args['start'], '%Y-%m-%d %H:%M')
            start_datetime = start_datetime.replace(second=0)

            start_datetime_timezone = timezone.localize(start_datetime)
            start_datetime_utc = start_datetime_timezone.astimezone(utc_timezone)

            sql_query += ' and created_at >= :start'
            arg_dict['start'] = start_datetime_utc

        if args['end']:
            end_datetime = datetime.strptime(args['end'], '%Y-%m-%d %H:%M')
            end_datetime = end_datetime.replace(second=0)

            end_datetime_timezone = timezone.localize(end_datetime)
            end_datetime_utc = end_datetime_timezone.astimezone(utc_timezone)

            sql_query += ' and created_at < :end'
            arg_dict['end'] = end_datetime_utc

        sql_query += ' GROUP BY date order by date'

        response_data = []

        with db.engine.begin() as conn:
            rs = conn.execute(db.text(sql_query), arg_dict)            
            for i in rs:
                response_data.append({
                    'date': str(i.date),
                    'latency': round(i.latency * 1000, 4)
                })

        return jsonify({
            'data': response_data
        })


class TokensPerSecondStatistic(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    @get_app_model
    def get(self, app_model):
        account = current_user

        parser = reqparse.RequestParser()
        parser.add_argument('start', type=datetime_string('%Y-%m-%d %H:%M'), location='args')
        parser.add_argument('end', type=datetime_string('%Y-%m-%d %H:%M'), location='args')
        args = parser.parse_args()

        sql_query = '''SELECT date(DATE_TRUNC('day', created_at AT TIME ZONE 'UTC' AT TIME ZONE :tz )) AS date, 
    CASE 
        WHEN SUM(provider_response_latency) = 0 THEN 0
        ELSE (SUM(answer_tokens) / SUM(provider_response_latency))
    END as tokens_per_second
FROM messages
WHERE app_id = :app_id'''
        arg_dict = {'tz': account.timezone, 'app_id': app_model.id}

        timezone = pytz.timezone(account.timezone)
        utc_timezone = pytz.utc

        if args['start']:
            start_datetime = datetime.strptime(args['start'], '%Y-%m-%d %H:%M')
            start_datetime = start_datetime.replace(second=0)

            start_datetime_timezone = timezone.localize(start_datetime)
            start_datetime_utc = start_datetime_timezone.astimezone(utc_timezone)

            sql_query += ' and created_at >= :start'
            arg_dict['start'] = start_datetime_utc

        if args['end']:
            end_datetime = datetime.strptime(args['end'], '%Y-%m-%d %H:%M')
            end_datetime = end_datetime.replace(second=0)

            end_datetime_timezone = timezone.localize(end_datetime)
            end_datetime_utc = end_datetime_timezone.astimezone(utc_timezone)

            sql_query += ' and created_at < :end'
            arg_dict['end'] = end_datetime_utc

        sql_query += ' GROUP BY date order by date'

        response_data = []

        with db.engine.begin() as conn:
            rs = conn.execute(db.text(sql_query), arg_dict)
            for i in rs:
                response_data.append({
                    'date': str(i.date),
                    'tps': round(i.tokens_per_second, 4)
                })

        return jsonify({
            'data': response_data
        })
        
class FrequentKeywordsStatistic(Resource):
    
    @setup_required
    @login_required
    @account_initialization_required
    @get_app_model
    def get(self, app_model):
        account = current_user
        def _get_embeddings(tenaid:str) -> Embeddings:
            model_manager = ModelManager()

            embedding_model = model_manager.get_model_instance(
            tenant_id=tenaid,
            provider="xinference",
            model_type=ModelType.TEXT_EMBEDDING,
            model="bge-large-zh-v1.5"

        )
            return CacheEmbedding(embedding_model)

        def update_embeddings(embeddings:CacheEmbedding):
        # 你的更新逻辑
                exists_query = text("SELECT EXISTS(SELECT 1 FROM public.messages WHERE query_embedding IS NULL)")

                # 执行查询
                result = db.session.execute(exists_query).scalar()
                if result:
                    updates = [(id, embeddings.embed_query(query)) for id, query in db.session.query(Message.id, Message.query).filter(Message.query_embedding == None).all()]
                    for id, value in updates:
                        db.session.query(Message).filter_by(id=id).update({Message.query_embedding: value})
                    db.session.commit()
        parser = reqparse.RequestParser()
        parser.add_argument('start', type=datetime_string('%Y-%m-%d %H:%M'), location='args')
        parser.add_argument('end', type=datetime_string('%Y-%m-%d %H:%M'), location='args')
        args = parser.parse_args()

        sql_query = '''
                SELECT created_at AS date,query, query_embedding
                    FROM messages where app_id = :app_id 
                '''
        arg_dict = { 'app_id': app_model.id}

        timezone = pytz.timezone(account.timezone)
        utc_timezone = pytz.utc
        embeddings= _get_embeddings(current_app.config['EMBEDDINGTENANT_ID'])
        if args['start']:
            start_datetime = datetime.strptime(args['start'], '%Y-%m-%d %H:%M')
            start_datetime = start_datetime.replace(second=0)

            start_datetime_timezone = timezone.localize(start_datetime)
            start_datetime_utc = start_datetime_timezone.astimezone(utc_timezone)

            sql_query += ' and created_at >= :start'
            arg_dict['start'] = start_datetime_utc

        if args['end']:
            end_datetime = datetime.strptime(args['end'], '%Y-%m-%d %H:%M')
            end_datetime = end_datetime.replace(second=0)

            end_datetime_timezone = timezone.localize(end_datetime)
            end_datetime_utc = end_datetime_timezone.astimezone(utc_timezone)

            sql_query += ' and created_at < :end'
            arg_dict['end'] = end_datetime_utc

        sql_query += ' GROUP BY date,messages.query,messages.query_embedding order by date'
        update_embeddings(embeddings)
        # 方法1提取关键字
        allCount=0
        all_keywords = {}
        with db.engine.begin() as conn:
            rs = conn.execute(db.text(sql_query), arg_dict) 
            df = pd.DataFrame(rs.fetchall())
            query_embedding = [np.array(x) for x in df['query_embedding']]
            # allCount等于query_embedding的个数
            allCount = len(query_embedding)
        similarity_threshold = 0.8
        top_n_similar_queries = 10

        # 计算余弦相似度
        query_similarity = cosine_similarity(query_embedding, query_embedding)

        # calculated_pairs = set()
        # top_similar_queries = []

        # # 找到相似度大于阈值的查询对
        # for i in range(len(df)):
        #     for j in range(i + 1, len(df)):
        #         if (i, j) not in calculated_pairs and (j, i) not in calculated_pairs:
        #             calculated_pairs.add((i, j))
        #             sim = query_similarity[i][j]
        #             if sim > similarity_threshold:
        #                 top_similar_queries.append((i, j, sim, df['query'].iloc[i], df['query'].iloc[j], df['date'].iloc[i], df['date'].iloc[j]))

        # # 获取前 top_n_similar_queries 个相似查询
        # top_similar_queries = sorted(top_similar_queries, key=lambda x: x[2], reverse=True)[:top_n_similar_queries]
        keyword_similarity_count = {}
        calculated_pairs = set()
        calculated_j = []

        for i in range(len(df)):
            if i in calculated_j:
                continue
            keyword_similarity_count[i] = {'merged_query': df['query'].iloc[i], 'count': 1, 'dates': []}
            for j in range(i + 1, len(df)):
             
                if (i, j) in calculated_pairs or (j, i) in calculated_pairs:
                    continue
                calculated_pairs.add((i, j))
               
                sim = query_similarity[i][j]
                if sim > similarity_threshold:
                    # 这里把匹配的记录下
                    calculated_j.append(j)
                    query1 = df['query'].iloc[i]
                    query2 = df['query'].iloc[j]
                    merged_query = min(query1, query2, key=len)
                    if len(merged_query) < len(keyword_similarity_count[i]['merged_query']):
                        # if keyword_similarity_count[i]['merged_query'] in keyword_similarity_count:
                        #     del keyword_similarity_count[keyword_similarity_count[i]['merged_query']]
                        keyword_similarity_count[i]['merged_query'] = merged_query
                        keyword_similarity_count[i]['count'] += 1
                        keyword_similarity_count[i]['dates'].append(df['date'].iloc[j])
                    else:
                        keyword_similarity_count[i]['count'] += 1
                        keyword_similarity_count[i]['dates'].append(df['date'].iloc[j])

        # 按 count 降序排序并选取前 top_n_similar_queries 
        resultsList = sorted(keyword_similarity_count.items(), key=lambda x: x[1]['count'], reverse=True)[:top_n_similar_queries]
        results = []
        for keyword, info in resultsList:
            results.append({'word': info['merged_query'], 'count': info['count'], 'dates': info['dates']})
        # with db.engine.begin() as conn:
        #     rs = conn.execute(db.text(sql_query), arg_dict) 
        #     df = pd.DataFrame(rs.fetchall())
        #     # df['embeddingValue'] = df['query'].apply(lambda x: embeddings.embed_query(x))
        #     query_embedding = [np.array(x) for x in df['query_embedding']]
    
        #     similarity_threshold = 0.7
        #     top_n_similar_queries = 10
        #     # 计算余弦相似度
        #     query_similarity = cosine_similarity(query_embedding, query_embedding)
        #      # 计算层次聚类
        #     Z = linkage(query_similarity, method='complete')

        #     # 根据聚类结果将查询分组
        #     clusters = fcluster(Z, t=similarity_threshold, criterion='distance')
        #     calculated_pairs = set()
        #     # 找到每个组中相似度最大的查询
        #     top_similar_queries = []
        #     for i in range(len(df)):
        #         for j in range(i + 1, len(df)):
        #             if (i, j) not in calculated_pairs and (j, i) not in calculated_pairs:
        #                 calculated_pairs.add((i, j))
        #                 sim = query_similarity[i][j]
        #                 if sim > similarity_threshold:
        #                     top_similar_queries.append((i, j, sim, df['query'].iloc[i], df['query'].iloc[j], df['date'].iloc[i], df['date'].iloc[j]))
            
        #     for cluster_id in np.unique(clusters):
        #         cluster_indices = np.where(clusters == cluster_id)[0]
        #         if len(cluster_indices) > 0:
        #             max_similarity = -1
        #             max_pair = None
        #             for i in cluster_indices:
        #                 for j in cluster_indices:
        #                     if i != j:
        #                         similarity = query_similarity[i][j]
        #                         if similarity > max_similarity:
        #                             max_similarity = similarity
        #                             max_pair = (i, j)
        #             top_similar_queries.append((*max_pair, max_similarity, df['query'].iloc[max_pair[0]], df['query'].iloc[max_pair[1]]))

        #         # 获取前 top_n_similar_queries 个相似查询
        #         top_similar_queries = sorted(top_similar_queries, key=lambda x: x[2], reverse=True)[:top_n_similar_queries]

        #         # 计算每个关键词的相似查询对的数量
        #         keyword_similarity_count = {}
        #         for (i, j), sim in calculated_pairs.items():
        #             keyword1 = df['query'].iloc[i]
        #             keyword2 = df['query'].iloc[j]
        #             if keyword1 not in keyword_similarity_count:
        #                 keyword_similarity_count[keyword1] = 0
        #             if keyword2 not in keyword_similarity_count:
        #                 keyword_similarity_count[keyword2] = 0
        #             keyword_similarity_count[keyword1] += 1
        #             keyword_similarity_count[keyword2] += 1

        #     # 找到数量最多的前10个关键词
        #     top_10_keywords = sorted(keyword_similarity_count.items(), key=lambda x: x[1], reverse=True)[:10]
        #       # 打印结果
        #     for keyword, count in top_10_keywords:
        #         print(f"{keyword}: {count}")
        
       
        #     # similarity_threshold = 0.7
        #     # top_n_similar_queries = 10
        #     # # 找出所有相似度大于阈值的查询对
        #     # sim_pairs =  set()
        #     # for i in range(len(df)):
        #     #     for j in range(i+1, len(df)):
        #     #         if query_similarity[i][j] > similarity_threshold:
        #     #             sim_pairs.add((i, j, query_similarity[i][j], df['query'].iloc[i], df['query'].iloc[j], df['date'].iloc[i], df['date'].iloc[j]))

        #     # # 按相似度排序并取前top_n_similar_queries个
        #     # sim_pairs = list(sim_pairs)
        #     # sim_pairs.sort(key=lambda x: x[2], reverse=True)
        #     # top_similar_queries = sim_pairs[:top_n_similar_queries]

        #     # # 整理结果
        #     # result = []
        #     # for i, j, sim, q1, q2, d1, d2 in top_similar_queries:
        #     #     result.append({
        #     #         'query1': q1,
        #     #         'query2': q2,
        #     #         'similarity': sim,
        #     #         'data1': d1,
        #     #         'data2': d2
        #     #     })

        #     # print(result)
        #     embedding_values = np.array(list(df['query_embedding']))
        #     # embedding_values = np.array([x for x in df['query_embedding']])
        #     # embedding_values = np.array(df['query_embedding']).reshape(-1, 1)
        #     normalized_embedding_values = embedding_values / np.linalg.norm(embedding_values, axis=1, keepdims=True)
        #     # similarity = np.dot(normalized_embedding_values, normalized_embedding_values.T)
        #     similarity = np.einsum('ij,kj->ik', normalized_embedding_values, normalized_embedding_values)
        #     groups = []
        #     used_queries = set()
        #     for i in range(len(df)):
        #         if df['query'].iloc[i] in used_queries:
        #             continue
        #         group = [df['query'].iloc[i], df['date'].iloc[i]]
        #         used_queries.add(df['query'].iloc[i])
        #         for j in range(i+1, len(df)):
        #             if similarity[i,j] >= 0.65:
        #                 group.append(df['query'].iloc[j])
        #                 group.append(df['date'].iloc[j])
        #                 used_queries.add(df['query'].iloc[j])
        #         groups.append(group)
        #     # group_counts = [len(group)//2 for group in groups]
        #     group_counts = [len(group) for group in groups]
        #     group_counts_dict = {i: group_counts[i] for i in range(len(group_counts))}
            
        #     # 获取数量最多的前5个分组
        #     top_groups = sorted(group_counts_dict.items(), key=lambda x: x[1], reverse=True)[:5]

        #     top_groups_with_data = []
        #     for group, count in top_groups:
        #         queries = [groups[group][i] for i in range(0, len(groups[group]), 2)]
        #         dates = [groups[group][i] for i in range(1, len(groups[group]), 2)]
        #         top_groups_with_data.append((group, queries, dates)) 
           
        #     results = []
        #     for group, queries, dates in top_groups_with_data:
        #         # 取queries中长度最短的作为Keyword
        #         keyword = min(queries, key=len)
        #         # keyword = queries[0]  # 获取关键词
        #         # 输出queries的长度
        #         info = {'count': len(queries), 'dates': dates}
        #         results.append({'word': keyword, 'count': info['count'], 'dates': info['dates']})
    
        return jsonify({
                'data': results,
                'count':allCount
            })
        
   
api.add_resource(DailyConversationStatistic, '/apps/<uuid:app_id>/statistics/daily-conversations')
api.add_resource(DailyTerminalsStatistic, '/apps/<uuid:app_id>/statistics/daily-end-users')
api.add_resource(DailyTokenCostStatistic, '/apps/<uuid:app_id>/statistics/token-costs')
api.add_resource(AverageSessionInteractionStatistic, '/apps/<uuid:app_id>/statistics/average-session-interactions')
api.add_resource(UserSatisfactionRateStatistic, '/apps/<uuid:app_id>/statistics/user-satisfaction-rate')
api.add_resource(AverageResponseTimeStatistic, '/apps/<uuid:app_id>/statistics/average-response-time')
api.add_resource(TokensPerSecondStatistic, '/apps/<uuid:app_id>/statistics/tokens-per-second')
api.add_resource(FrequentKeywordsStatistic, '/apps/<uuid:app_id>/statistics/frequent-keywords')
