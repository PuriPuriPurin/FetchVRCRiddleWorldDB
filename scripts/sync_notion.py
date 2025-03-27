import os
import json
from notion_client import Client
import datetime

def fetch_notion_database(database_id, notion_client):
    """
    Notion データベースからすべてのページを取得する関数
    
    Args:
        database_id (str): 取得対象のデータベースID
        notion_client (Client): Notion クライアント
    
    Returns:
        list: データベースのすべてのページデータ
    """
    all_results = []
    start_cursor = None
    has_more = True

    while has_more:
        # データベースをクエリ（ページネーション対応）
        response = notion_client.databases.query(
            database_id=database_id,
            start_cursor=start_cursor if start_cursor else None,
            page_size=100  # 1回のリクエストで取得するページ数（最大100）
        )

        # 結果を蓄積
        all_results.extend(response['results'])

        # 次のページ用のカーソルと継続フラグを更新
        has_more = response['has_more']
        start_cursor = response.get('next_cursor')

    return all_results

def process_database_data(results):
    """
    取得したデータを処理する関数
    
    Args:
        results (list): Notionから取得したページデータ
    
    Returns:
        list: 加工したデータ
    """
    processed_data = []
    for item in results:
        processed_item = {
            'id': item['id'],
            'created_time': item['created_time'],
            'last_edited_time': item['last_edited_time'],
            'properties': {}
        }

        # 各プロパティを解析
        for prop_name, prop_value in item['properties'].items():
            processed_prop = process_property(prop_value)
            if processed_prop is not None:
                processed_item['properties'][prop_name] = processed_prop

        processed_data.append(processed_item)

    return processed_data

def process_property(prop):
    """
    プロパティの値を適切な形式に変換
    
    Args:
        prop (dict): Notionのプロパティデータ
    
    Returns:
        変換後のプロパティ値
    """
    prop_type = prop['type']
    
    # 様々なプロパティタイプに対応
    type_handlers = {
        'title': lambda p: p['title'][0]['plain_text'] if p['title'] else None,
        'rich_text': lambda p: p['rich_text'][0]['plain_text'] if p['rich_text'] else None,
        'number': lambda p: p['number'],
        'select': lambda p: p['select']['name'] if p['select'] else None,
        'multi_select': lambda p: [item['name'] for item in p['multi_select']] if p['multi_select'] else [],
        'date': lambda p: p['date']['start'] if p['date'] else None,
        'checkbox': lambda p: p['checkbox'],
        'url': lambda p: p['url'],
        'email': lambda p: p['email'],
        'phone_number': lambda p: p['phone_number'],
    }

    handler = type_handlers.get(prop_type)
    return handler(prop) if handler else None

def process_portal_library_data(results):

    quest_worlds = []
    pc_worlds = []
    my_worlds = []

    for result in results:
        properties = result['properties']
        is_quest_support = 'Android' in properties['Platform']
        # 自作ワールド
        if properties['Author'] == 'prprpurin':
            my_worlds.append({
                'ID': properties['ID'],
                'Name': properties['Name'],
                'Author': properties['Author'],
                'RecommendedCapacity': properties['RecommendedCapacity'],
                'Capacity': properties['Capacity'],
                'Description': properties['Description'],
                'ReleaseStatus': properties['ReleaseStatus'],
                'Comment': properties.get('Comment', ''),
                'Difficulty': properties.get('Difficulty', 'unknown'),
                'Platform': {
                    'PC': True,
                    'Android': is_quest_support,
                },
            })
        # Quest 対応ワールド
        elif is_quest_support:
            quest_worlds.append({
                'ID': properties['ID'],
                'Name': properties['Name'],
                'Author': properties['Author'],
                'RecommendedCapacity': properties['RecommendedCapacity'],
                'Capacity': properties['Capacity'],
                'Description': properties['Description'],
                'ReleaseStatus': properties['ReleaseStatus'],
                'Comment': properties.get('Comment', ''),
                'Difficulty': properties.get('Difficulty', 'unknown'),
                'Platform': {
                    'PC': True,
                    'Android': is_quest_support,
                },
            })
        # PCワールド
        else:
            pc_worlds.append({
                'ID': properties['ID'],
                'Name': properties['Name'],
                'Author': properties['Author'],
                'RecommendedCapacity': properties['RecommendedCapacity'],
                'Capacity': properties['Capacity'],
                'Description': properties['Description'],
                'ReleaseStatus': properties['ReleaseStatus'],
                'Comment': properties.get('Comment', ''),
                'Difficulty': properties.get('Difficulty', 'unknown'),
                'Platform': {
                    'PC': True,
                    'Android': is_quest_support,
                },
            })

    tz_jst = datetime.timezone(datetime.timedelta(hours=9), name='JST')
    dt_now = datetime.datetime.now(tz_jst)
    lastupdate = dt_now.strftime('%Y/%m/%d %H:%M:%S(JST)')

    portal_library_data = {
        'ReverseCategorys': False,
        'ShowPrivateWorld': False,
        'LastUpdate': lastupdate,
        'Categorys': [
            {
                'Category': '攻略済み謎解きワールド(PC&QUEST)',
                'Worlds': quest_worlds,
            },
            {
                'Category': '攻略済み謎解きワールド(PC)',
                'Worlds': pc_worlds,
            },
            {
                'Category': 'ワールド製作者が作ったやつ',
                'Worlds': my_worlds,
            },
        ]
    }
    return portal_library_data

def main():
    # 環境変数から必要な情報を取得
    notion_token = os.environ['NOTION_TOKEN']
    database_id = os.environ['NOTION_DATABASE_ID']

    try:
        # Notion クライアントの初期化
        notion_client = Client(auth=notion_token)

        # データベースからすべてのページを取得
        database_results = fetch_notion_database(database_id, notion_client)

        # データの加工
        processed_data = process_database_data(database_results)
        portal_library_data = process_portal_library_data(processed_data)

        # ディレクトリ作成
        os.mkdir(os.path.join(os.path.dirname(__file__), '../docs'))

        # JSONファイルに保存
        with open(os.path.join(os.path.dirname(__file__), '../docs/portal_library_data.json'), 'w', encoding='utf-8') as f:
            json.dump(portal_library_data, f, ensure_ascii=False, indent=2)

        print(f"Successfully synced {len(processed_data)} pages from Notion database.")

    except Exception as e:
        print(f"Error syncing Notion database: {e}")
        raise

if __name__ == '__main__':
    main()
