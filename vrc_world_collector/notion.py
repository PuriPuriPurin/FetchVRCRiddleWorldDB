import os
from dotenv import load_dotenv
from notion_database_manager import NotionDatabaseManager
from notion_property_builder import NotionPropertyBuilder as npb
import requests

def get_registered_world_id(notion_manager):
    return notion_manager.get_column_values('ID')

def add_record(notion_manager: NotionDatabaseManager,
    name: str, author:str, description: str, platform_support_pc: bool, platform_support_quest: bool,
    id: str, recommended_capacity: int, capacity: int, release_status: str, publication_date: str):

    platform = []
    if platform_support_pc:
        platform.append('PC')
    if platform_support_quest:
        platform.append('Android')

    if publication_date == 'none':
        print('Private worldなので、公開日を登録しない')
        publication_date = {}
    else:
        publication_date = {
            'PublicationDate': npb.date(publication_date),
        }

    # プロジェクト管理データベースへのレコード追加
    project_properties = {
        'Name': npb.title(name),
        'Author': npb.rich_text(author),
        'Description': npb.rich_text(description),
        'Platform': npb.multi_select(platform),
        'ID': npb.rich_text(id),
        'RecommendedCapacity': npb.number(recommended_capacity),
        'Capacity': npb.number(capacity),
        'ReleaseStatus': npb.select(release_status),
        **publication_date,
    }

    # レコードを追加
    new_record = notion_manager.add_database_record(
        properties=project_properties,
    )

    if new_record:
        print('新しいレコードが正常に追加されました')
        print(f'ページID: {new_record["id"]}')
