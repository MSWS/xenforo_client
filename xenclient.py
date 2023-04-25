import requests
from dotenv import load_dotenv
import os
import time
import re

# Load environment variables from .env file
load_dotenv()

# Configuration
XENFORO_API_KEY = os.getenv('XENFORO_API_KEY')
BASE_URL = os.getenv('BASE_URL')
SOURCE_FORUM_ID = os.getenv('SOURCE_FORUM_ID')
COMPLETED_FORUM_ID = os.getenv('COMPLETED_FORUM_ID')
LEADERSHIP_FORUM_ID = os.getenv('LEADERSHIP_FORUM_ID')

PREFIXES = {
    'cs': 222,
    'discord': 261,
    'fivem': 224,
    'forums': 262,
    'mc': 225,
    'ow': 226,
    'rust': 227,
    'tf2': 228,
    'jb': 256,
    'ttt': 257,
    'rotation': 263,
    'dust2': 253,
    'surf': 254,
    'bhop': 258,
    'awp': 259,
    'kz': 260,
    'delivered': 252,
    'duplicate': 243,
    'notbug': 246,
    'notplanned': 247,
    'existing': 245,
    'indev': 249,
    'inbeta': 250
}

MOVE_TARGETS = {
    'bugs': 1294,
    'bugcomplete': 1295,
    'bc': 1295,
    'suggestions': 1344
}

RESPONSES = {
    'notplanned': 'Marking this as not planned',
    'newgame': """Please read the steps for requesting new supported games [URL='https://www.edgegamers.com/threads/378532/']here[/URL].

Marking as Not Planned."""
}

def get_processed_threads():
    try:
        with open('processed_threads.txt', 'r') as f:
            return set(map(int, f.read().splitlines()))
    except FileNotFoundError:
        return set()

def save_processed_thread(thread_id):
    with open('processed_threads.txt', 'a') as f:
        f.write(f'{thread_id}\n')

def get_threads(page = 0):
    url = f'{BASE_URL}/api/forums/{SOURCE_FORUM_ID}/threads'
    headers = {'XF-Api-Key': XENFORO_API_KEY, 'User-Agent': 'XenClient/1.0'}
    params = {'page': page}
    response = requests.get(url, headers=headers, params=params)
    return response.json()

def get_thread_with_posts(thread_id):
    url = f'{BASE_URL}/api/threads/{thread_id}'
    headers = {'XF-Api-Key': XENFORO_API_KEY, 'User-Agent': 'XenClient/1.0'}
    params = {'with_posts': 'true'}
    response = requests.get(url, headers=headers, params=params)
    return response.json()

def apply_prefix(thread_id, prefix):
    thread_data = get_thread_with_posts(thread_id)
    current_prefix = thread_data['thread']['prefix_id']

    # if current_prefix:
    #     new_prefix = f"{current_prefix} {prefix}"
    # else:
        # new_prefix = prefix

    url = f'{BASE_URL}/api/threads/{thread_id}'
    headers = {'XF-Api-Key': XENFORO_API_KEY, 'Content-Type': 'application/x-www-form-urlencoded', 'User-Agent': 'XenClient/1.0'}
    data = {'prefix_id': prefix}
    response = requests.post(url, headers=headers, data=data)
    return response.json()

def move_thread(thread_id, destination_forum_id):
    url = f'{BASE_URL}/api/threads/{thread_id}/move'
    headers = {'XF-Api-Key': XENFORO_API_KEY, 'Content-Type': 'application/x-www-form-urlencoded', 'User-Agent': 'XenClient/1.0'}
    data = {'target_node_id': destination_forum_id}
    response = requests.post(url, headers=headers, data=data)
    return response.json()

def respond(thread_id, message):
    url = f'{BASE_URL}/api/posts'
    headers = {'XF-Api-Key': XENFORO_API_KEY, 'Content-Type': 'application/x-www-form-urlencoded', 'User-Agent': 'XenClient/1.0'}
    data = {'message': message, 'thread_id': thread_id}
    response = requests.post(url, headers=headers, data=data)
    return response.json()

def parse_bbcode(bbcode):
    # Remove quote blocks and their contents
    bbcode = re.sub(r'\[QUOTE(.*?)\].*?\[/QUOTE\]', '', bbcode, flags=re.DOTALL)
    bbcode = re.sub(r'\[QUOTE.+\n*.+\n*\[/QUOTE\]', '', bbcode, flags=re.DOTALL)
    # Remove block elements and their closing tags
    bbcode = re.sub(r'\[(SIZE|B|I|COLOR)(.*?)\]', '', bbcode)
    bbcode = re.sub(r'\[/SIZE\]|\[/B\]|\[/I\]|\[/COLOR\]', '', bbcode)
    # Remove attach blocks
    bbcode = re.sub(r'\[ATTACH(.*?)\].*?\[/ATTACH\]', '', bbcode, flags=re.DOTALL)
    # Remove remaining tags
    bbcode = re.sub(r'\[(.*?)\]', '', bbcode)
    # Remove extra spaces and new lines
    bbcode = re.sub(r'[\r\n\s]+', ' ', bbcode)
    return bbcode.strip()

def main():
    page = 0
    while True:
        processed_threads = get_processed_threads()
        threads = get_threads(page)
        for thread in threads['threads']:
            if not thread['discussion_open']:
                continue
            if thread['thread_id'] in processed_threads:
                continue
            # print(f'Title: {thread["title"]}')
            thread_with_posts = get_thread_with_posts(thread['thread_id'])
            posts = thread_with_posts['posts']
            os.system('clear')
            print(f'{thread["title"]} - {thread["view_url"]}')
            print(f'{parse_bbcode(posts[0]["message"])}')
            print()
            time.sleep(1)
            for post in posts[1:]:
                print(f'{post["username"]}: {parse_bbcode(post["message"])[:150]}')
                # print(f'{post["username"]}: {post["message"]}')
                # time.sleep(0.2)
            print('')

            while True:
                user_input = input('move, prefix, reply: ').strip()
                input_parts = user_input.split()

                if len(input_parts) >= 2:
                    # action, target = input_parts[0], input_parts[1:]
                    action = input_parts[0]

                    if (action == 'prefix' or action == 'p') and input_parts[1] in PREFIXES:
                        apply_prefix(thread['thread_id'], PREFIXES[input_parts[1]])
                        print(f'Applied prefix.')
                    elif (action == 'move' or action == 'mv') and input_parts[1] in MOVE_TARGETS:
                        move_thread(thread['thread_id'], MOVE_TARGETS[input_parts[1]])
                        print(f'Moved thread.')
                    elif action == 'reply' or action == 'r':
                        response = ""
                        if input_parts[1] in RESPONSES:
                            response = RESPONSES[input_parts[1]]
                        else:
                            response = " ".join(input_parts[1:])
                        respond(thread['thread_id'], response)
                        print(f'Replied to thread: {response}')
                    else:
                        print(f'Invalid action or target: {user_input}')
                elif user_input == 's' or user_input == 'skip':
                    break
                elif user_input != '':
                    print(f'Invalid command: {user_input}')
            # if user_input != '':
            save_processed_thread(thread['thread_id'])
            # os.system('clear')
        page+=1

if __name__ == '__main__':
    main()
