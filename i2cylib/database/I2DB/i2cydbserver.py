#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Filename: i2cydbserver
# Created on: 2021/4/28

import sys
from i2cylib.network.i2tcp_basic.base_server import *
from i2cylib.crypto.iccode import *
from i2cylib.utils.stdout import *
from i2cylib.utils.logger import *
from i2cylib.utils.path.path_fixer import *
from i2cylib.database.sqlite import *
from i2cylib.utils.args import *
import time
import json
import threading


DEFAULT_CONFIG = {
  "database_file": "sqlite3.db",
  "log_filename": "logs/database_service.log",
  "log_level" : "DEBUG",
  "server_port": 36881,
  "dyn_key": "*HAU__SCN+C=biasdiua#sd71asd"
}

DATABASE = None
ECHO = Echo()
LOGGER = None
MODLOGGER = None
KEY = None

class ModLogger:

    def __init__(self, logger, echo):
        self.logger = logger
        self.echo = echo

    def DEBUG(self, msg):
        ret = self.logger.DEBUG(msg)
        if ret is not None:
            self.echo(ret[:-1])

        return ret

    def INFO(self, msg):
        ret = self.logger.INFO(msg)
        if ret is not None:
            self.echo(ret[:-1])

        return ret

    def WARNING(self, msg):
        ret = self.logger.WARNING(msg)
        if ret is not None:
            self.echo(ret[:-1])

        return ret

    def ERROR(self, msg):
        ret = self.logger.ERROR(msg)
        if ret is not None:
            self.echo(ret[:-1])

        return ret

    def CRITICAL(self, msg):
        ret = self.logger.CRITICAL(msg)
        if ret is not None:
            self.echo(ret[:-1])

        return ret


def hander(con):
    global MODLOGGER
    head = "[handler] [{}]".format(con.addr)
    if not isinstance(MODLOGGER, ModLogger):
        echo = Echo()
        log = Logger()
        MODLOGGER = ModLogger(logger=log, echo=echo)
    if not isinstance(DATABASE, SqliteDB):
        MODLOGGER.CRITICAL("{} database is not ready".format(head))
        raise Exception("database is not ready")
    if not isinstance(con, I2TCPhandler):
        MODLOGGER.ERROR("[handler] type error. con must be an I2CTCPhandler object")
        return 1
    MODLOGGER.DEBUG("{} new connection handled".format(head))
    cryptor = Iccode(KEY)
    encrypt_key = None
    while con.live:
        data = con.recv()
        if data is not None:
            encrypt_key = cryptor.decode(data).hex()
            break
        time.sleep(0.1)
    if not con.live:
        return 1
    else:
        cryptor = Iccode(encrypt_key)
        con.send(cryptor.encode(encrypt_key))

#command: {"type": (database -> "db", table -> "tb"),
#          "table": (database -> IGNORED, table -> Table_Name),
#          "cmd": command name -> function name,
#          "args": {dict type object}}

    stop = False

    while con.live:
        try:
            data = con.recv()
            cryptor.reset()
            if data is not None:
                try:
                    data = cryptor.decode(data)
                    data = data.decode("utf-8")
                    data = json.loads(data)
                    type = data["type"]
                    table = data["table"]
                    cmd = data["cmd"]
                    args = data["args"]
                    ret = None
                    if type == "db":
                        if cmd == "switch_autocommit":
                            ret = DATABASE.switch_autocommit()

                        elif cmd == "create_table":
                            table_object = SqlTable(args["name"])
                            table_object.table = args["table"]
                            DATABASE.create_table(table_object)

                        elif cmd == "drop_table":
                            DATABASE.drop_table(args)

                        elif cmd == "list_all_tables":
                            ret = DATABASE.list_all_tables()

                        elif cmd == "undo":
                            DATABASE.undo()

                        elif cmd == "commit":
                            DATABASE.commit()

                        elif cmd == "close":
                            stop = True

                        else:
                            ret = "\"unexpected command \"{}\"\"".format(cmd)

                    elif type == "tb":
                        tb = DATABASE.select_table(table)
                        if cmd == "__len__":
                            ret = len(tb)

                        elif cmd == "__getitem__":
                            args = args["item"]
                            if isinstance(args, list):
                                start = args[0]
                                stop = args[1]
                                step = args[2]
                                ret = tb[start:stop:step]
                            else:
                                ret = tb[args]

                        elif cmd == "__setitem__":
                            tb[args["key"]] = args["value"]

                        elif cmd == "undo":
                            tb.undo()

                        elif cmd == "get_table_info":
                            ret = tb.get_table_info()

                        elif cmd == "append":
                            tb.append(args["data"])

                        elif cmd == "empty":
                            tb.empty()

                        elif cmd == "pop":
                            tb.pop(args["key"], args["primary_index_column"])

                        elif cmd == "get":
                            ret = tb.get(key=args["key"],
                                         column_name=args["column_name"],
                                         primary_index_column=args["primary_index_column"],
                                         orderby=args["orderby"],
                                         asc_order=args["asc_order"])

                        elif cmd == "update":
                            tb.update(data=args["data"],
                                      index_key=args["index_key"],
                                      column_names=args["column_names"],
                                      primary_index_column=args["primary_index_column"])

                        else:
                            ret = "\"unexpected command \"{}\"\"".format(cmd)

                    else:
                        continue

                    if ret is None:
                        ret = "OK"

                    ret = json.dumps(ret).encode("utf-8")

                except Exception as err:
                    MODLOGGER.ERROR("{} error while processing: {}".format(head, err))
                    ret = json.dumps(str(err)).encode("utf-8")

                try:
                    con.send(ret)

                except Exception as err:
                    MODLOGGER.ERROR("{} error while sending data: {}".format(head, err))

            else:
                time.sleep(0.1)

            if stop:
                con.kill()
                break

        except Exception as err:
            MODLOGGER.ERROR("{} error while handling connection, {}".format(head, err))




def main():
    global LOGGER, MODLOGGER, DATABSE, KEY
    head = "main"
    args = get_args()
    conf = None
    log_level = "DEBUG"
    log_file = None
    port = None
    dkey = None
    db_file = None

    for key in args.keys():

        if key in ("-h", "--help", "--usage"):
            print("""I2cylib SQLite Database Server

Usage:
i2cydbserver [-h] [-c --config FILNAME] [-k --key PASSWORD] [-p --port PORT]
             [-l --log FILENAME] [-level --log-level LOG_LEVEL]
             [-d --database FILENAME]

Options:
    -c --config FILENAME    - set config file to run with
                              (will create one if it does not exist)
    -k --key PASSWORD       - set the key for dynamic auth and encryption
                              (override config)
    -p --port PORT          - set the port to bind for database server
                              (override config)
    -l --log FILENAME       - set the log file
                              (override config)
    -d --database FILENAME  - set the database file to connect with
                              (override config)
    -level --log-level      - set the log level, default DEBUG
                              (override config)

Examples:
> i2cydbserver -c config/database_srv.json
> i2cydbserver -p 21882 -k ABCDEFG -d test.db
> i2cydbserver -c config/database_srv.json -p 20000
""")
            return 1
        elif key in ("-c", "--config"):
            status = False
            if os.path.exists(args[key]):
                try:
                    with open(args[key], "r") as f:
                        conf = json.load(f)
                    if log_level == "DEBUG":
                        log_level = conf["log_level"]
                    if log_file is None:
                        log_file = conf["log_filname"]
                    if port is None:
                        port = conf["port"]
                    if dkey is None:
                        dkey = conf["dyn_key"]
                    if db_file is None:
                        db_file = conf["database_file"]
                except:
                    status = True
            else:
                status = True
            if status:
                conf = DEFAULT_CONFIG
                with open(args[key], "w") as f:
                    json.dump(conf, f, indent=2)

        elif key in ("-p", "--port"):
            port = int(args[key])

        elif key in ("-l", "--log"):
            log_file = args[key]

        elif key in ("-level", "--log-level"):
            log_level = args[key]

        elif key in ("-k", "--key"):
            dkey = args[key]

        elif key in ("-d", "--database"):
            db_file = args[key]

        else:
            print("unhandled option {}, use -h for help".format(key))
            return 1
    if port is None:
        ECHO.print(
            "[{}] [WARN] [{}] port undefined, using default value".format(
                time.strftime("%Y-%m-%d %H:%M:%S"), head))
        port = DEFAULT_CONFIG["server_port"]
    if dkey is None:
        ECHO.print(
            "[{}] [WARN] [{}] dynamic key undefined, using default value".format(
                time.strftime("%Y-%m-%d %H:%M:%S"), head))
        dkey = DEFAULT_CONFIG["dyn_key"]
    if db_file is None:
        ECHO.print(
            "[{}] [WARN] [{}] database file undefined, using default value".format(
                time.strftime("%Y-%m-%d %H:%M:%S"), head))
        db_file = DEFAULT_CONFIG["database_file"]

    ECHO.print("[{}] [INFO] [{}] initializing environment".format(time.strftime("%Y-%m-%d %H:%M:%S"), head))
    ECHO.buttom_print("initializing environment...")
    if log_file is not None:
        path_fixer(log_file)
    LOGGER = Logger(filename=log_file, echo=False, level=log_level)
    LOGGER.INFO("[{}] initializing".format(head))

    MODLOGGER = ModLogger(logger=LOGGER, echo=ECHO.print)

    MODLOGGER.DEBUG("[{}] building database connection...".format(head))
    ECHO.buttom_print("initializing database connection...")
    DATABSE = SqliteDB(database=db_file)
    MODLOGGER.INFO("[{}] successfully built connection with \"{}\"".format(head, db_file))

    MODLOGGER.DEBUG("[{}] starting server...".format(head))
    KEY = dkey
    server = I2TCPserver(key=KEY, port=port, logger=MODLOGGER)
    server.start()

    tick = 0

    while True:
        try:
            if tick % 10 == 0:
                alive_con = 0
                for i in range(server.max_con):
                    if server.connections[i] is None:
                        continue
                    if server.connections[i]["handler"].live:
                        alive_con += 1
                ECHO.buttom_print("{} handling {} connections".format(
                    time.strftime("%H:%M:%S"), alive_con))

            con = server.get_connection()
            if con is not None:
                threading.Thread(target=hander, args=(con,)).start()
            time.sleep(0.1)
            tick += 1

        except KeyboardInterrupt:
            MODLOGGER.INFO("[{}] stop signal received, stopping...".format(head))
            ECHO.buttom_print("stopping server...")
            server.kill()
            print("")
            break


if __name__ == '__main__':
    code = main()
    if not isinstance(code, int):
        code = -2
    sys.exit(code)