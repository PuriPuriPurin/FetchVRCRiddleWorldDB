#!/usr/bin/env python3

import argparse
from dotenv import load_dotenv
import register
import update

def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description='VRChat World Collector')
    parser.add_argument('command', choices=['register', 'update'], help='Command to execute')
    args = parser.parse_args()

    if args.command == 'register':
        register.main()
    elif args.command == 'update':
        update.main()

if __name__ == '__main__':
    main()
