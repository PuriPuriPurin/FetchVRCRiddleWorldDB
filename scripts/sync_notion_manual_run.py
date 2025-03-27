import sync_notion
from dotenv import load_dotenv
import dotenv
import os
import shutil

def main():
    load_dotenv()

    doc_path = os.path.join(os.path.dirname(__file__), '../docs')
    if os.path.exists(doc_path):
        # 作成済みファイルを削除
        shutil.rmtree(doc_path)

    sync_notion.main()

if __name__ == '__main__':
    main()
