import os
import time
import sqlite3

from inputimeout import inputimeout, TimeoutOccurred


def get_id(cur, table, column):
    cur.execute(f"SELECT MAX({column}) FROM {table}")
    prev_id = cur.fetchone()[0]

    if prev_id:
        id = prev_id + 1
    else:
        id = 1

    return id


def open_session(con, cur):
    session_id = get_id(cur, 'sessions', 'session_id')
    cur.execute(f"INSERT INTO sessions VALUES ({session_id}, {time.time()}, NULL)")
    con.commit()
    # print('session_id:', session_id)
    return session_id


def close_session(con, cur, session_id):
    cur.execute(f"UPDATE sessions SET ending_time = {time.time()} WHERE session_id = {session_id}")
    con.commit()
    return 0


def is_happy(message):
    # happy 😀 😃 😄 😁 😆 😂 😊 🤩 🥳
    happy = {'\U0001F600', '\U0001F603', '\U0001F604', '\U0001F601',
             '\U0001F606', '\U0001F602', '\U0001F60A', '\U0001F929', '\U0001F973'}
    return message in happy


def is_sad(message):
    # sad 😞 🥺 😔 😟 😕 🙁 😩 😫 😓
    sad = {'\U0001F61E', '\U0001F97A', '\U0001F614', '\U0001F61F',
           '\U0001F615', '\U0001F641', '\U0001F629', '\U0001F62B', '\U0001F613'}
    return message in sad


def is_angry(message):
    # angry 👿 😬 😤 😡 👺 💀 😠 🤯 🤨
    angry = {'\U0001F47F', '\U0001F62C', '\U0001F624', '\U0001F621',
             '\U0001F47A', '\U0001F480', '\U0001F620', '\U0001F92F', '\U0001F928'}
    return message in angry


def is_emoji(message):
    return is_happy(message) or is_angry(message) or is_sad(message)


def get_bot_response(message, prev_message):
    if is_emoji(message) and (is_emoji(prev_message) or prev_message is None):
        if prev_message:
            if is_happy(prev_message):
                if is_happy(message):
                    return 'Я рад, что ты всё ещё в хорошем настроении!'
                elif is_sad(message):
                    return 'Минуту назад ты был весёлый, а теперь грустный. Что случилось?'
                else:
                    return 'Минуту назад ты был весёлый, а теперь злой. Что случилось?'
            elif is_sad(prev_message):
                if is_happy(message):
                    return 'Рад, что ты повеселел! Тяжело было видеть тебя грустным!'
                elif is_sad(message):
                    return 'Жаль, что тебе всё ещё грустно! Давай расскажу анекдот!'
                else:
                    return 'Тебе было грустно, а теперь ты злишься. Что случилось?'
            else:
                if is_happy(message):
                    return 'Хорошо, что ты больше не злишься! Радуюсь вместе с тобой!'
                elif is_sad(message):
                    return 'Ты злился, а теперь грустишь. Что случилось?'
                else:
                    return 'Жаль, что ты всё ещё злишься. Я могу чем-то помочь?'
        else:
            if is_happy(message):
                return 'Привет! Я рад, что ты в хорошем настроении!'
            elif is_sad(message):
                return 'Привет! Не грусти!'
            else:
                return 'Привет! Не злись!'
    else:
        return None


def main():
    con = sqlite3.connect('bot.db')
    cur = con.cursor()

    # check if the 'sessions' table exists
    cur.execute(''' SELECT count(name)
                    FROM sqlite_master
                    WHERE type='table' AND name='sessions' ''')
    # create if not
    if cur.fetchone()[0] == 0:
        cur.execute(''' CREATE TABLE sessions
                        (session_id integer PRIMARY KEY, starting_time real, ending_time real)''')

    # check if the 'messages' table exists
    cur.execute(''' SELECT count(name)
                    FROM sqlite_master
                    WHERE type='table' AND name='messages' ''')
    # create if not
    if cur.fetchone()[0] == 0:
        cur.execute(''' CREATE TABLE messages
                        (message_id integer PRIMARY KEY, time integer, session_id integer, message text, client_id integer,
                        FOREIGN KEY (session_id) REFERENCES sessions (session_id))''')

    # since I had to write a CLI applcation, I've decided identify unique
    # clients using process ID; this allows one to lauch this script in
    # several shells and get different IDs.
    client_id = os.getpid()
    # print('client_id:', client_id)

    prev_message = None
    session_id = open_session(con, cur)

    while True:
        try:
            message = inputimeout('> ', 60)
            message_id = get_id(cur, 'messages', 'message_id')

            # insert current message info to corresponding table
            cur.execute(f"INSERT INTO messages VALUES ({message_id}, {time.time()}, {session_id}, '{message}', {client_id})")
            con.commit()

            response = get_bot_response(message, prev_message)

            if response:
                print(response)
                prev_message = message
            else:
                print('Я тебя не понимаю! Давай начнём с самого начала!')
                close_session(con, cur, session_id)
                
                prev_message = None
                session_id = open_session(con, cur)

        except TimeoutOccurred:
            print('Тебя долго не было! Давай начнём заново!')
            close_session(con, cur, session_id)

            prev_message = None
            session_id = open_session(con, cur)
        except:
            close_session(con, cur, session_id)
            con.close()
            break

    return 0


if __name__ == '__main__':
    main()