#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Filename: i2cydbclient
# Created on: 2021/5/29

import json
from i2cylib.database.I2DB.i2cydbserver import ModLogger
from i2cylib.utils.logger import *
from i2cylib.utils.stdout import *
from i2cylib.network.i2tcp_basic.base_client import *
from i2cylib.database.sqlite.sqlitedb import Sqlimit, NewSqlTable, SqlDtype
from i2cylib.crypto.iccode import *
from i2cylib.utils.bytes.random_bytesgen import *


class SqliteDB:

    def __init__(self, host=None, dyn_key=None, logger=None):
        self.host = host
        self.database = None
        self.dyn_key = dyn_key

        if logger is None:
            logger = ModLogger(logger=Logger(), echo=Echo())

        self.logger = logger
        self.autocommit = False
        self.cursors = []
        self.head = "[I2DB]"
        self.encrypt_key = random_keygen(64)

    def _connection_check(self):
        if self.database is None:
            raise Exception("connection has not been built yet, "
                            "you have to connect to a database first")

    def connect(self, host=None, watchdog_timeout=5, dyn_key=None,
                logger=None):
        if host is None:
            host = self.host
        if dyn_key is None:
            if self.dyn_key is None:
                dyn_key = "basic"
            else:
                dyn_key = self.dyn_key
        else:
            self.dyn_key = dyn_key
        if logger is None:
            logger = self.logger

        host = host.split(":")
        hostname = host[0]
        port = int(host[1])

        self.database = I2TCPclient(hostname, port=port,
                                    key=dyn_key, logger=logger,
                                    watchdog_timeout=watchdog_timeout)

        coder = Iccode(self.dyn_key)
        data = coder.encode(self.encrypt_key)
        self.database.send(data)
        feedback = self.database.recv()
        coder = Iccode(self.encrypt_key)
        feedback = coder.decode(feedback)
        if feedback != self.encrypt_key:
            self.logger.ERROR("{} authentication failure".format(self.head))
            self.database.reset()
            self.database = None

    def switch_autocommit(self):
        self._connection_check()
        try:
            coder = Iccode(self.encrypt_key)
            cmd = {"type": "db",
                   "table": "",
                   "cmd": "switch_autocommit",
                   "args": ""}
            cmd = json.dumps(cmd).encode("utf-8")
            cmd = coder.encode(cmd)
            self.database.send(cmd)
            feedback = self.database.recv().decode("utf-8")
            feedback = json.loads(feedback)
            if feedback == True:
                self.autocommit = True
            elif feedback == False:
                self.autocommit = False
            else:
                raise Exception("feedback {}".format(feedback))
        except Exception as err:
            self.logger.ERROR("{} failed to switch autocommit mode on/off,"
                              "{}".format(self.head, err))

        return self.autocommit

    def create_table(self, table_object):
        self._connection_check()
        if not isinstance(table_object, NewSqlTable):
            raise TypeError("table_object must be an NewSqlTable object")
        try:
            coder = Iccode(self.encrypt_key)
            cmd = {"type": "db",
                   "table": "",
                   "cmd": "switch_autocommit",
                   "args": {"name": table_object.name,
                            "table": table_object.table}}
            cmd = json.dumps(cmd).encode("utf-8")
            cmd = coder.encode(cmd)
            self.database.send(cmd)
            feedback = self.database.recv().decode("utf-8")
            feedback = json.loads(feedback)
            if feedback == "OK":
                pass
            else:
                raise Exception("feedback {}".format(feedback))
        except Exception as err:
            self.logger.ERROR("{} failed to create table,"
                              "{}".format(self.head, err))

    def drop_table(self, table_name):
        self._connection_check()
        try:
            coder = Iccode(self.encrypt_key)
            cmd = {"type": "db",
                   "table": "",
                   "cmd": "drop_table",
                   "args": table_name}
            cmd = json.dumps(cmd).encode("utf-8")
            cmd = coder.encode(cmd)
            self.database.send(cmd)
            feedback = self.database.recv().decode("utf-8")
            feedback = json.loads(feedback)
            if feedback == "OK":
                pass
            else:
                raise Exception("feedback {}".format(feedback))
        except Exception as err:
            self.logger.ERROR("{} failed to drop table,"
                              "{}".format(self.head, err))

    def list_all_tables(self):
        self._connection_check()
        feedback = None
        try:
            coder = Iccode(self.encrypt_key)
            cmd = {"type": "db",
                   "table": "",
                   "cmd": "list_all_tables",
                   "args": ""}
            cmd = json.dumps(cmd).encode("utf-8")
            cmd = coder.encode(cmd)
            self.database.send(cmd)
            feedback = self.database.recv().decode("utf-8")
            feedback = json.loads(feedback)
            if isinstance(feedback, list):
                pass
            else:
                raise Exception("feedback {}".format(feedback))
        except Exception as err:
            self.logger.ERROR("{} failed to get all table name,"
                              "{}".format(self.head, err))

        return feedback

    def select_table(self, table_name):
        table_name = table_name.upper()
        self._connection_check()
        if not table_name in self.list_all_tables():
            raise Exception("cannot find table \"{}\" in database".format(table_name))
        ret = SqliteTableCursor(self, table_name)
        return ret

    def undo(self):
        self._connection_check()
        if self.autocommit:
            raise Exception("cannot undo since the autocommit mode is on")
        try:
            coder = Iccode(self.encrypt_key)
            cmd = {"type": "db",
                   "table": "",
                   "cmd": "undo",
                   "args": ""}
            cmd = json.dumps(cmd).encode("utf-8")
            cmd = coder.encode(cmd)
            self.database.send(cmd)
            feedback = self.database.recv().decode("utf-8")
            feedback = json.loads(feedback)
            if feedback == "OK":
                pass
            else:
                raise Exception("feedback {}".format(feedback))
        except Exception as err:
            self.logger.ERROR("{} failed to undo,"
                              "{}".format(self.head, err))

    def commit(self):
        self._connection_check()
        try:
            coder = Iccode(self.encrypt_key)
            cmd = {"type": "db",
                   "table": "",
                   "cmd": "commit",
                   "args": ""}
            cmd = json.dumps(cmd).encode("utf-8")
            cmd = coder.encode(cmd)
            self.database.send(cmd)
            feedback = self.database.recv().decode("utf-8")
            feedback = json.loads(feedback)
            if feedback == "OK":
                pass
            else:
                raise Exception("feedback {}".format(feedback))
        except Exception as err:
            self.logger.ERROR("{} failed to commit,"
                              "{}".format(self.head, err))

    def close(self):
        self._connection_check()
        self.commit()
        try:
            self.autocommit = False
            coder = Iccode(self.encrypt_key)
            cmd = {"type": "db",
                   "table": "",
                   "cmd": "close",
                   "args": ""}
            cmd = json.dumps(cmd).encode("utf-8")
            cmd = coder.encode(cmd)
            self.database.send(cmd)
            feedback = self.database.recv().decode("utf-8")
            feedback = json.loads(feedback)
            if feedback == "OK":
                pass
            else:
                raise Exception("feedback {}".format(feedback))
        except Exception as err:
            self.logger.ERROR("{} failed to close,"
                              "{}".format(self.head, err))
            return False
        self.database.reset()
        self.database = None
        return True


class SqliteTableCursor:

    def __init__(self, upper, table_name):
        self.upper = upper
        self.database = self.upper.database
        self.encrypt_key = self.upper.encrypt_key
        self.logger = self.upper.Logger
        self.name = table_name
        self.table_info = None
        self.length = 0
        self.get_table_info()
        self.offset = 0
        self.head = "[I2DB] [{}]".format(self.name)

    def __len__(self):
        feedback = self.length
        try:
            self.autocommit = False
            coder = Iccode(self.encrypt_key)
            cmd = {"type": "tb",
                   "table": self.name,
                   "cmd": "__len__",
                   "args": ""}
            cmd = json.dumps(cmd).encode("utf-8")
            cmd = coder.encode(cmd)
            self.database.send(cmd)
            feedback = self.database.recv().decode("utf-8")
            feedback = json.loads(feedback)
            if isinstance(feedback, int):
                pass
            else:
                raise Exception("feedback {}".format(feedback))
            self.length = feedback
        except Exception as err:
            self.logger.ERROR("{} failed to get table length,"
                              "{}".format(self.head, err))

        return feedback

    def __iter__(self):
        self.__len__()
        return self

    def __next__(self):
        ret = None
        if self.offset >= self.length:
            raise StopIteration
        try:
            self.autocommit = False
            coder = Iccode(self.encrypt_key)
            cmd = {"type": "tb",
                   "table": self.name,
                   "cmd": "__getitem__",
                   "args": self.offset}
            cmd = json.dumps(cmd).encode("utf-8")
            cmd = coder.encode(cmd)
            self.database.send(cmd)
            feedback = self.database.recv().decode("utf-8")
            feedback = json.loads(feedback)
            if isinstance(feedback, str):
                raise Exception("feedback {}".format(feedback))
            ret = feedback
            self.offset += 1
        except Exception as err:
            self.logger.ERROR("{} failed to get data,"
                              "{}".format(self.head, err))

        return ret

    def __getitem__(self, item):
        valid = isinstance(item, int) or isinstance(item, slice)
        if not valid:
            raise KeyError("index must be integrate or slices")

        ret = None

        try:
            self.autocommit = False
            coder = Iccode(self.encrypt_key)
            args = item
            if isinstance(item, slice):
                args = [item.start, item.stop, item.step]
            cmd = {"type": "tb",
                   "table": self.name,
                   "cmd": "__getitem__",
                   "args": args}
            cmd = json.dumps(cmd).encode("utf-8")
            cmd = coder.encode(cmd)
            self.database.send(cmd)
            feedback = self.database.recv().decode("utf-8")
            feedback = json.loads(feedback)
            if isinstance(feedback, str):
                raise Exception("feedback {}".format(feedback))
            ret = feedback
        except Exception as err:
            self.logger.ERROR("{} failed to get data,"
                              "{}".format(self.head, err))

        return ret

    def __setitem__(self, key, value):
        if not isinstance(key, int):
            raise KeyError("index must be integrate")

        try:
            self.autocommit = False
            coder = Iccode(self.encrypt_key)
            args = {"key": key,
                    "value": value}
            cmd = {"type": "tb",
                   "table": self.name,
                   "cmd": "__getitem__",
                   "args": args}
            cmd = json.dumps(cmd).encode("utf-8")
            cmd = coder.encode(cmd)
            self.database.send(cmd)
            feedback = self.database.recv().decode("utf-8")
            feedback = json.loads(feedback)
            if not feedback == "OK":
                raise Exception("feedback {}".format(feedback))
        except Exception as err:
            self.logger.ERROR("{} failed to set data,"
                              "{}".format(self.head, err))

    def seek(self, offset):
        if offset < 0:
            offset = len(self) + offset
        self.offset = offset

    def undo(self):
        if self.upper.autocommit:
            raise Exception("cannot undo since the autocommit mode is on")
        self.length = None

    def _data2sqlstr(self, data):
        key = None
        if isinstance(data, int):
            key = str(data)
        if isinstance(data, float):
            key = str(data)
        if isinstance(data, str):
            key = "'{}'".format(data)
        if isinstance(data, bool):
            key = str(int(data))

        return key

    def get_table_info(self):
        cursor = self.upper.database.cursor()

        cursor.execute("PRAGMA table_info({})".format(self.name))
        data = cursor.fetchall()
        ret = []
        for ele in data:
            ret.append({"ID": ele[0],
                        "name": ele[1].upper(),
                        "is_primary_key": bool(ele[5]),
                        "dtype": ele[2].upper(),
                        "is_not_null": bool(ele[3])})
        self.table_info = ret
        cursor.close()
        return ret

    def append(self, data):
        cursor = self.upper.database.cursor()

        columns = ""
        for ele in data:
            if isinstance(ele, bool):
                columns += "{}, ".format(int(ele))
                continue
            if isinstance(ele, int):
                columns += "{}, ".format(ele)
                continue
            if isinstance(ele, str):
                columns += "'{}', ".format(ele)
                continue
            if isinstance(ele, float):
                columns += "{}, ".format(ele)
                continue
        if len(columns) == 0:
            cursor.close()
            return
        columns = columns[:-2]

        cmd = "INSERT INTO {} VALUES ({});".format(self.name, columns)
        cursor.execute(cmd)
        self.upper._auto_commit()
        cursor.close()
        self.length += 1

    def empty(self):  # delete all values in table
        cursor = self.upper.database.cursor()

        cmd = "DELETE FROM {}".format(self.name)

        cursor.execute(cmd)
        self.upper._auto_commit()
        cursor.close()

    # index_name can be automatically set as the primary key in table.
    # Or you can define it as it follows the SQLite3 WHERE logic
    def pop(self, key, primary_index_column=None):
        cursor = self.upper.database.cursor()

        if primary_index_column is None:
            primary_key = None
            for ele in self.table_info:
                if ele["is_primary_key"]:
                    primary_key = ele["name"]
                    break
            if primary_key is None:
                cursor.close()
                raise KeyError("no primary key defined in table,"
                               " input index_name manually")
            primary_index_column = primary_key

        key = self._data2sqlstr(key)

        cmd = "DELETE FROM {} WHERE {}={};".format(self.name,
                                                   primary_index_column, key)
        cursor.execute(cmd)
        self.upper._auto_commit()
        cursor.close()

    def get(self, key=None, column_name="*", primary_index_column=None,
            orderby=None, asc_order=True):
        cursor = self.upper.database.cursor()

        if asc_order:
            order = "ASC"
        else:
            order = "DESC"

        if primary_index_column is None and not key is None:
            primary_key = None
            for ele in self.table_info:
                if ele["is_primary_key"]:
                    primary_key = ele["name"]
                    break
            if primary_key is None:
                cursor.close()
                raise KeyError("no primary key defined in table,"
                               " input primary_index_column manually")
            primary_index_column = primary_key

        if orderby is None:
            if primary_index_column is None:
                orderby = self.table_info[0]["name"]
            else:
                orderby = primary_index_column

        if key is None:
            cmd = "SELECT {} from {} ORDER BY {} {}".format(column_name,
                                                            self.name,
                                                            orderby,
                                                            order
                                                            )

        elif isinstance(key, tuple):
            if len(key) != 2:
                cursor.close()
                raise KeyError("index range tuple must have 2 elements")
            cmd = "SELECT {} from {} WHERE {} BETWEEN {} AND {} ORDER BY {} {}".format(column_name,
                                                                                       self.name,
                                                                                       primary_index_column,
                                                                                       self._data2sqlstr(key[0]),
                                                                                       self._data2sqlstr(key[1]),
                                                                                       orderby,
                                                                                       order)

        elif isinstance(key, list):
            if len(key) < 1:
                cursor.close()
                raise KeyError("index element list must have at least 1 element")
            key_str = ""
            for ele in key:
                key_str += "{}, ".format(self._data2sqlstr(ele))
            key_str = key_str[:-2]
            cmd = "SELECT {} from {} WHERE {} IN ({}) ORDER BY {} {}".format(column_name,
                                                                             self.name,
                                                                             primary_index_column,
                                                                             key_str,
                                                                             orderby,
                                                                             order)

        else:
            key = self._data2sqlstr(key)
            cmd = "SELECT {} FROM {} WHERE {}={} ORDER BY {} {}".format(column_name,
                                                                        self.name,
                                                                        primary_index_column,
                                                                        key,
                                                                        orderby,
                                                                        order
                                                                        )

        cursor.execute(cmd)
        ret = cursor.fetchall()
        cursor.close()
        return ret

    def update(self, data,
               index_key=None,
               column_names=None,
               primary_index_column=None):
        cursor = self.upper.database.cursor()

        cmd = "UPDATE {} SET ".format(self.name)

        if column_names is None:
            column_names = [ele["name"] for ele in self.table_info]

        if not isinstance(column_names, list):
            column_names = [column_names]

        valid = isinstance(data, list) or isinstance(data, tuple)

        if not valid:
            data = [data]

        if len(data) == 0:
            return

        for i, ele in enumerate(data):
            if i >= len(column_names):
                break
            ele = self._data2sqlstr(ele)
            cmd += "{}={}, ".format(column_names[i], ele)

        cmd = cmd[:-2]

        if not index_key is None:
            if primary_index_column is None:
                primary_key = None
                for ele in self.table_info:
                    if ele["is_primary_key"]:
                        primary_key = ele["name"]
                        break
                if primary_key is None:
                    raise KeyError("no primary key defined in table,"
                                   " input primary_index_column manually")
                primary_index_column = primary_key

            index_key = self._data2sqlstr(index_key)
            cmd += " WHERE {}={}".format(primary_index_column, index_key)

        cursor.execute(cmd)
        self.upper._auto_commit()
        cursor.close()