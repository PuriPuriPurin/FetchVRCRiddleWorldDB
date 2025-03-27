import sync_notion
from dotenv import load_dotenv
import dotenv

def main():
    load_dotenv()
    sync_notion.main()

if __name__ == '__main__':
    main()
