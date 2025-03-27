import os
import json
from notion_client import Client

def fetch_notion_database():
    # Notion クライアントの初期化
    notion = Client(auth=os.environ['NOTION_TOKEN'])
    
    # データベースのクエリ
    database_id = os.environ['DATABASE_ID']
    results = notion.databases.query(database_id=database_id)
    
    # データの抽出と整形
    processed_data = []
    for item in results['results']:
        processed_item = {
            'id': item['id'],
            'properties': item['properties']
        }
        processed_data.append(processed_item)
    
    # JSONファイルに保存
    with open('notion_data.json', 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    fetch_notion_database()
