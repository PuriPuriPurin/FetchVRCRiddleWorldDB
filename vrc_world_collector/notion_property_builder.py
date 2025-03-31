class NotionPropertyBuilder:
    """
    Notionのプロパティを簡単に作成するユーティリティクラス
    """
    @staticmethod
    def title(text):
        """タイトルプロパティを作成"""
        return {
            'title': [
                {
                    'type': 'text',
                    'text': {'content': text}
                }
            ]
        }

    @staticmethod
    def rich_text(text):
        """リッチテキストプロパティを作成"""
        return {
            'rich_text': [
                {
                    'type': 'text',
                    'text': {'content': text}
                }
            ]
        }

    @staticmethod
    def select(option):
        """セレクトプロパティを作成"""
        return {
            'select': {'name': option}
        }

    @staticmethod
    def multi_select(options):
        """マルチセレクトプロパティを作成"""
        return {
            'multi_select': [
                {'name': option} for option in options
            ]
        }

    @staticmethod
    def number(value):
        """数値プロパティを作成"""
        return {
            'number': value
        }

    @staticmethod
    def date(start_date, end_date=None):
        """日付プロパティを作成"""
        date_prop = {'start': start_date}
        if end_date:
            date_prop['end'] = end_date
        return {
            'date': date_prop
        }

    @staticmethod
    def people(user_ids):
        """担当者プロパティを作成"""
        return {
            'people': [
                {
                    'object': 'user',
                    'id': user_id
                } for user_id in user_ids
            ]
        }
