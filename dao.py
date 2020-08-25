import datetime

import psycopg2
from psycopg2._psycopg import OperationalError, InterfaceError


def is_conn_alive(conn):
    from app import DATABASE_URL
    print("checking connection is alive")
    try:
        c = conn.cursor()
        c.execute("SELECT 1")
        print("conn alive")
        return conn
    except InterfaceError as oe:
        print("connection is closed, reopening")
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        return conn


def get_subs_data(conn):
    conn = is_conn_alive(conn)
    try:
        cursor = conn.cursor()
        select_subs_query = "select * from subscription"
        cursor.execute(select_subs_query)
        subs = cursor.fetchall()

        sub_obj = {}

        for k in subs:
            sub_obj[k[1]] = {}
            sub_obj[k[1]]["channel_id"] = k[1]
            if k[2] is not None:
                sub_obj[k[1]]["lease_date"] = k[2].strftime("%m/%d/%Y, %H:%M:%S")
            if k[3] is not None:
                sub_obj[k[1]]["last_event"] = k[3].strftime("%m/%d/%Y, %H:%M:%S")
            if k[4] is not None:
                sub_obj[k[1]]["last_video"] = k[4].strip()
            if k[5] is not None:
                sub_obj[k[1]]["video_title"] = k[5].strip()
            if k[6] is not None:
                sub_obj[k[1]]["nick"] = k[6]
            if k[7] is not None:
                sub_obj[k[1]]["video_type"] = k[7]

        return sub_obj

    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data from PostgreSQL", error)

    finally:
        # closing database connection.
        if (conn):
            cursor.close()
            print("cursor closed")


def persist_sub(conn, channel_id, lease):
    print("saving subscription of channel {}".format(channel_id))

    conn = is_conn_alive(conn)

    try:

        cursor = conn.cursor()

        select_subs_query = "select * from subscription where channel_id = %s"
        cursor.execute(select_subs_query, (channel_id,))
        subs_for_channel = cursor.fetchall()
        if len(subs_for_channel) != 0:
            print("sub already present for channel")
            updqry = "update subscription set lease_date = %s where channel_id = %s"
            cursor.execute(updqry, (lease, channel_id))
            print("updated")
        else:
            print("no sub, inserting one")
            print(lease.isoformat())
            insert_query = "insert into subscription (channel_id,lease_date) values (%s,%s)"
            cursor.execute(insert_query, (channel_id, lease))
            print("inserted")

    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data from PostgreSQL", error)

    finally:
        # closing database connection.
        if (conn):
            cursor.close()
            print("cursor closed")


def persist_event(conn, evt):
    print("persisting event")
    print("channel: {} - {}, videoid: {}, videotitle: {}".format(
        evt["name"], evt["channelId"], evt["videoId"], evt["videoTitle"]))
    conn = is_conn_alive(conn)
    try:
        cursor = conn.cursor()

        updqry = """update subscription 
        set last_id = %s, last_event = %s, video_title = %s, video_type = %s
        where channel_id = %s"""
        cursor.execute(updqry,
                       (evt["videoId"], datetime.datetime.now(), evt["videoTitle"], evt["type"], evt["channelId"]))

    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data from PostgreSQL", error)

    finally:
        if (conn):
            cursor.close()
            print("cursor closed")
