import os
from dotenv import load_dotenv
import notion
from notion_database_manager import NotionDatabaseManager
import vrchat
from vrchatapi import (WorldsApi, ApiClient, NotFoundException)
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
    load_dotenv()
    notion_manager = get_notion_manager()

    print('Step1. 登録済みワールド一覧のIDを取得')
    registered_world_id = notion.get_registered_world_id(notion_manager)

    with ApiClient() as api_client:
        world_api = get_world_api(api_client)

        print('Step2. Quest対応ワールドを登録')
        with open('./world_list/cross_platform_list.txt') as f:
            urls = f.readlines()
            for url in urls:
                try:
                    id = parse_world_id(url)
                    if id in registered_world_id:
                        print('登録済み。スキップする。')
                        continue
                    world_info = vrchat.get_world_info(world_api, id)
                    notion.add_record(notion_manager, platform_support_pc=True, platform_support_quest=True, **world_info)
                except NotFoundException:
                    print(f'{id.strip()} のワールドが見つかりません。スキップ。')
                    continue

        print('Step3. PCワールドを登録')
        with open('./world_list/pc_only_list.txt') as f:
            urls = f.readlines()
            for url in urls:
                try:
                    id = parse_world_id(url)
                    if id in registered_world_id:
                        print('登録済み。スキップする。')
                        continue
                    world_info = vrchat.get_world_info(world_api, id)
                    notion.add_record(notion_manager, platform_support_pc=True, platform_support_quest=False, **world_info)
                except NotFoundException:
                    print(f'{id.strip()} のワールドが見つかりません。スキップ。')
                    continue


if __name__ == '__main__':
    main()
