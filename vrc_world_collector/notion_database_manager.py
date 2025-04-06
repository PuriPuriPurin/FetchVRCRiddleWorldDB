from typing import Dict, Any, List
import requests

class NotionDatabaseManager:
    def __init__(self, database_id: str, api_key: str):
        """
        Notion データベース管理クラス

        Args:
            database_id (str): 対象のデータベースID
            api_key (str): Notion API キー
        """
        self.database_id = database_id
        self.api_key = api_key
        self.base_url = 'https://api.notion.com/v1'
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Notion-Version': '2022-06-28'
        }

    def update_page_properties(self, page_id: str, properties: Dict[str, Any], name: str = None) -> Dict[str, Any]:
        """
        指定されたページのプロパティを更新する

        Args:
            page_id (str): 更新対象のページID
            properties (dict): 更新するプロパティの辞書

        Returns:
            dict: 更新されたページの詳細
        """
        url = f'{self.base_url}/pages/{page_id}'
        
        if name:
            # 更新用のペイロード
            payload = {
                'properties': {
                    'Name': {
                        'title': [
                            {
                                'type': 'text',
                                'text': {
                                    'content': name,
                                },
                            },
                        ],
                    },
                    **properties,
                }
            }
        else:
            # 更新用のペイロード
            payload = {
                'properties': properties
            }

        try:
            response = requests.patch(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            print(f"ページ更新中にエラーが発生: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"エラーの詳細: {e.response.text}")
            return None


    def add_database_record(self, properties: Dict[str, Any], content: str = None) -> Dict[str, Any]:
        """
        データベースに新しいレコードを追加

        Args:
            properties (dict): データベースのプロパティ
            content (str, optional): ページに追加するテキストコンテンツ

        Returns:
            dict: 作成されたページの詳細
        """
        url = f'{self.base_url}/pages'
        
        # ページ作成のペイロード
        payload = {
            'parent': {'database_id': self.database_id},
            'properties': properties
        }

        # オプションでコンテンツを追加
        if content:
            payload['children'] = [
                {
                    'object': 'block',
                    'type': 'paragraph',
                    'paragraph': {
                        'rich_text': [
                            {
                                'type': 'text',
                                'text': {
                                    'content': content
                                }
                            }
                        ]
                    }
                }
            ]

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            print(f"レコード追加中にエラーが発生: {e}")
            return None

    def get_raw_values(self) -> List[Any]:
        url = f'{self.base_url}/databases/{self.database_id}/query'
        
        # ペイロードの初期設定
        payload = {
            "page_size": 100  # 1ページあたりの最大取得数
        }

        all_data = []  # すべてのデータを格納するリスト
        next_cursor = None  # ページネーション用のカーソル

        try:
            while True:
                # ペイロードにカーソルを追加（必要な場合）
                if next_cursor:
                    payload['start_cursor'] = next_cursor

                # データベースのクエリを実行
                response = requests.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                data = response.json()

                # 現在のページのデータを追加
                all_data.extend(data.get('results', []))

                # 次のカーソルがある場合は更新、なければ終了
                next_cursor = data.get('next_cursor')
                if not data.get('has_more', False):
                    break

            return all_data

        except requests.exceptions.RequestException as e:
            print(f"データ取得中にエラーが発生: {e}")
            return []

    def get_column_values(self, column_name: str) -> List[Any]:
        """
        特定のデータベース内の指定された列のすべての値を取得

        Args:
            column_name (str): 取得したい列名

        Returns:
            List[Any]: 指定された列のすべての値
        """
        try:
            # get_raw_values を利用してすべてのデータを取得
            all_data = self.get_raw_values()

            # 指定された列の値を抽出
            column_values = []
            for page in all_data:
                properties = page.get('properties', {})
                column_data = properties.get(column_name)
                
                if column_data:
                    # 列の型に応じて値を抽出
                    value = self._extract_column_value(column_data)
                    if value is not None:
                        column_values.append(value)

            return column_values

        except requests.exceptions.RequestException as e:
            print(f"データ取得中にエラーが発生: {e}")
            return []

    def _extract_column_value(self, column_data: dict) -> Any:
        """
        列の型に応じて値を抽出するヘルパーメソッド

        Args:
            column_data (dict): 列のデータ

        Returns:
            Any: 抽出された値
        """
        # 様々な列の型に対応
        if column_data.get('type') == 'title':
            # タイトル型
            titles = column_data.get('title', [])
            return titles[0]['plain_text'] if titles else None
        
        elif column_data.get('type') == 'rich_text':
            # リッチテキスト型
            rich_texts = column_data.get('rich_text', [])
            return rich_texts[0]['plain_text'] if rich_texts else None
        
        elif column_data.get('type') == 'select':
            # セレクト型
            return column_data.get('select', {}).get('name')
        
        elif column_data.get('type') == 'multi_select':
            # マルチセレクト型
            return [
                item.get('name') 
                for item in column_data.get('multi_select', [])
            ]
        
        elif column_data.get('type') == 'number':
            # 数値型
            return column_data.get('number')
        
        elif column_data.get('type') == 'date':
            # 日付型
            return column_data.get('date', {}).get('start')
        
        return None