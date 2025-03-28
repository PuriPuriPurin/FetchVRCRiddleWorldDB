import os
import json
from notion_client import Client
import datetime
import requests
import re
from PIL import Image
import io
import shutil

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

def download_image(image_url, page_id, prop_name):
    """
    画像をダウンロードし、ローカルに保存する関数
    
    Args:
        image_url (str): 画像のURL
        page_id (str): ページID
        prop_name (str): プロパティ名
    
    Returns:
        str: 保存された画像のパス
    """
    
    # 画像保存用ディレクトリ作成
    dirname = os.path.join(os.path.dirname(__file__), '../docs/images')
    os.makedirs(dirname, exist_ok=True)
    # 一時保存用ディレクトリ
    tmpdirname = os.path.join(os.path.dirname(__file__), '../tmp')
    os.makedirs(tmpdirname, exist_ok=True)
    # 余計な要素を取り除き、拡張子のみにする
    file_extension = re.findall(r'^(\.(?:png|jpe?g))', os.path.splitext(image_url)[1])[0]
    filename = os.path.join(dirname, f'{page_id}_{prop_name}{file_extension}')
    tmpfilename = os.path.join(tmpdirname, f'{page_id}_{prop_name}{file_extension}')

    # すでに画像が存在する場合
    if os.path.exists(filename):
        # ダウンロード済みの画像の場合はパスを返す
        return filename

    # 画像をダウンロード
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        
        with open(tmpfilename, 'wb') as f:
            f.write(response.content)

        # 画像を半分の解像度にリサイズ
        with Image.open(io.BytesIO(response.content)) as img:
            # 現在の幅と高さの半分にリサイズ
            half_width = img.width // 2
            half_height = img.height // 2
            half_res_img = img.resize((half_width, half_height), Image.LANCZOS)
            
            # 半解像度の画像を保存
            half_res_img.save(filename)
        
        return filename
    except Exception as e:
        print(f"画像ダウンロードエラー: {e}")
        return None

def load_downloaded_images_log():
    """
    ダウンロード済み画像の履歴を読み込む
    
    Returns:
        dict: ダウンロード済み画像の情報
    """
    dirname = os.path.join(os.path.dirname(__file__), '..')
    log_path = os.path.join(dirname, 'notion_images_log.json')
    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_downloaded_images_log(log):
    """
    ダウンロード済み画像の履歴を保存する
    
    Args:
        log (dict): ダウンロード済み画像の情報
    """
    dirname = os.path.join(os.path.dirname(__file__), '..')
    log_path = os.path.join(dirname, 'notion_images_log.json')
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

def process_database_data(results):
    """
    取得したデータを処理する関数
    
    Args:
        results (list): Notionから取得したページデータ
    
    Returns:
        list: 加工したデータ
    """
    # ダウンロード済み画像の履歴を読み込み
    downloaded_images_log = load_downloaded_images_log()

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
            processed_prop = process_property(prop_value, item['id'], downloaded_images_log)
            if processed_prop is not None:
                processed_item['properties'][prop_name] = processed_prop

        id = processed_item['properties'].get('ID', None)

        processed_data.append(processed_item)

    # ダウンロード済み画像の履歴を保存
    save_downloaded_images_log(downloaded_images_log)

    return processed_data

def process_property(prop, page_id, downloaded_images_log):
    """
    プロパティの値を適切な形式に変換
    
    Args:
        prop (dict): Notionのプロパティデータ
        page_id (str): ページのID
        downloaded_images_log (dict): ダウンロード済み画像の履歴
    
    Returns:
        変換後のプロパティ値
    """
    prop_type = prop['type']

    def handle_files(files):
        processed_files = []
        for file in files:
            file_url = file['file']['url']
            file_name = re.findall(r'^https?://.+/(.+\.(?:png|jpe?g))', file_url)[0]
            
            # すでにダウンロード済みの画像かチェック
            if file_name in downloaded_images_log:
                local_path = downloaded_images_log[file_name]
                print(f'画像ダウンロード済み: {local_path} を使用します')
            else:
                # 新規ダウンロード
                local_path = download_image(file_url, page_id, 'files')
                if local_path:
                    downloaded_images_log[file_name] = local_path
                print(f'新規画像: {local_path} を保存しました')
            
            processed_files.append({
                'name': file['name'],
                'url': file_url,
                'local_path': local_path
            })
        return processed_files if processed_files else None

    def handle_media(media):
        file_url = media['url']
        
        # すでにダウンロード済みの画像かチェック
        if file_url in downloaded_images_log:
            local_path = downloaded_images_log[file_url]
        else:
            # 新規ダウンロード
            local_path = download_image(file_url, page_id, 'media')
            if local_path:
                downloaded_images_log[file_url] = local_path
        
        return {
            'url': file_url,
            'local_path': local_path
        } if local_path else None
    
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
        # 画像プロパティ
        'files': lambda p: handle_files(p['files']) if p['files'] else None,
        'media': lambda p: handle_media(p['media']) if p['media'] else None,
    }

    handler = type_handlers.get(prop_type)
    return handler(prop) if handler else None

def remove_symlinks(directory):
    """
    指定されたディレクトリ内の0000.pngパターンのシンボリックリンクを削除する
    
    Args:
        directory (str): 検索対象のディレクトリパス
    """
    # 正規表現パターン: 4桁の数字.png
    pattern = re.compile(r'^\d{4}\.png$')
    
    # ディレクトリ内のファイルを走査
    for filename in os.listdir(directory):
        # フルパス作成
        full_path = os.path.join(directory, filename)
        
        # シンボリックリンクかつ、パターンにマッチするファイルを削除
        if os.path.islink(full_path) and pattern.match(filename):
            try:
                os.unlink(full_path)
                print(f"削除しました: {full_path}")
            except Exception as e:
                print(f"エラー: {full_path} の削除に失敗 - {e}")

def process_portal_library_data(results):

    quest_worlds = []
    pc_worlds = []
    my_worlds = []

    vrc_image_id = 0

    # シンボリックリンクを全て削除
    remove_symlinks(os.path.join(os.path.dirname(__file__), '../docs/images'))

    for result in results:
        properties = result['properties']
        is_quest_support = 'Android' in properties['Platform']
        if properties.get('ClearThumbnail', None):
            # 画像に対してアクセスしやすいように id と ファイルを紐づけるシンボリックリンクを追加
            ori_file = properties['ClearThumbnail'][0]['local_path']
            symlink_file = os.path.join(os.path.dirname(ori_file), f'{str(vrc_image_id).zfill(4)}.png')
            os.symlink(ori_file, symlink_file)
            vrc_image_id = vrc_image_id + 1
            print(f'シンボリックリンク: {symlink_file} を追加')

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
                'ImageId': vrc_image_id,
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
                'ImageId': vrc_image_id,
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
                'ImageId': vrc_image_id,
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
        os.makedirs(os.path.join(os.path.dirname(__file__), '../docs'), exist_ok=True)

        # JSONファイルに保存
        with open(os.path.join(os.path.dirname(__file__), '../docs/portal_library_data.json'), 'w', encoding='utf-8') as f:
            json.dump(portal_library_data, f, ensure_ascii=False, indent=2)

        # 一時ディレクトリ削除
        tmpdir = os.path.join(os.path.dirname(__file__), '../tmp')
        if os.path.exists(tmpdir):
            shutil.rmtree(os.path.join(os.path.dirname(__file__), '../tmp'))

        print(f"Successfully synced {len(processed_data)} pages from Notion database.")

    except Exception as e:
        print(f"Error syncing Notion database: {e}")
        raise

if __name__ == '__main__':
    main()
