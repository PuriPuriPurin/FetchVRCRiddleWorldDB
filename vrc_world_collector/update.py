import os
# from dotenv import load_dotenv
from notion_database_manager import NotionDatabaseManager
from notion_property_builder import NotionPropertyBuilder
import vrchat
import vrchatapi
from vrchatapi import WorldsApi
import re

def get_world_api(api_client):
    vrc_app_name = os.getenv('VRC_APP_NAME')
    vrc_app_version = os.getenv('VRC_APP_VERSION')
    vrc_mail = os.getenv('VRC_MAIL')

    api_client.user_agent = f'{vrc_app_name}/{vrc_app_version} {vrc_mail}'
    world_api = WorldsApi(api_client)

    return world_api

def get_notion_manager():
    api_key = os.getenv('NOTION_API_KEY')
    db_id = os.getenv('NOTION_DB_ID')

    notion_manager = NotionDatabaseManager(db_id, api_key)
    return notion_manager

def parse_world_id(url: str):
    return re.findall('^https://vrchat.com/home/world/(.*)', url)[0]


def main():
    # TODO: 専用のコマンドを作成して、環境変数を読み込むようにする
    # load_dotenv()

    try:
        print('Step1. 登録済みワールド一覧のIDを取得')
        notion_manager = get_notion_manager()
        pages = notion_manager.get_raw_values()
    except Exception as e:
        # 中断しないようにする
        print(f"Notion API からページを取得できませんでした: {e}")
        return

    try:
        with vrchatapi.ApiClient() as api_client:
            print('Step2. VRChat API から Notion に登録済みワールドの情報を取得')
            for page in pages:
                properties = page.get('properties', {})
                page_id = page.get('id')
                world_id = properties.get('ID', {}).get('rich_text', [])[0]['plain_text']
                world_api = get_world_api(api_client)
                world_info = vrchat.get_world_info(world_api, world_id)

                update_properties = {
                    'Description': NotionPropertyBuilder.rich_text(world_info['description']),
                    'Author': NotionPropertyBuilder.rich_text(world_info['author']),
                    'PublicationDate': NotionPropertyBuilder.date(world_info['publicationDate']),
                }
                updated_page = notion_manager.update_page_properties(page_id, update_properties, world_info['name'])
                if updated_page:
                    print(f"ページID: {updated_page['id']} を更新しました")
    except Exception as e:
        # 中断しないようにする
        print(f"エラーが発生しました: {e}")
        return


if __name__ == '__main__':
    main()

