import vrchatapi
import re

from vrchatapi.api.worlds_api import WorldsApi

def fix_text(text: str):
    # VRC上の表示が崩れるため、一部文字を通常のASCIIに変換する。
    fixed_text = re.sub('․', '.', text)
    fixed_text = re.sub('⁄', '/', fixed_text)
    fixed_text = re.sub('˸', ':', fixed_text)
    # これはワールドのフォントが対応していないのでやっている。
    fixed_text = re.sub('～', '~', fixed_text)
    return fixed_text


def get_world_info(world_api: WorldsApi, world_id: str):
    print(f'{world_id} の情報を取得するよ')
    with vrchatapi.ApiClient() as api_client:

        world = world_api.get_world(world_id)

        return {
            'name': fix_text(world.name),
            'author': fix_text(world.author_name),
            'id': world.id,
            'recommended_capacity': world.recommended_capacity,
            'capacity': world.capacity,
            'description': fix_text(world.description),
            'release_status': world.release_status,
            'publicationDate': world.publication_date,
        }
