#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Filename: sqlitedb
# Created on: 2021/2/16
# Description: A pythonfied sqlite3 database control api class
##VERSION: 1.0


import sqlite3


class SqliteDB:

    def __init__(self, database=None):
        self.filename = database
        self.database = None

        self.autocommit = False

    def _connection_check(self):
        if self.database is None:
            raise Exception("connection has not been built yet, "
                            "you have to connect to a database first")

    def _auto_commit(self):
        if self.autocommit:
            self.database.commit()

    def connect(self, database=None, timeout=5):
        if database is None:
            database = self.filename

        self.database = sqlite3.connect(database, timeout=timeout)

    def switch_autocommit(self):
        if self.autocommit:
            self.autocommit = False
        else:
            self.autocommit = True

        return self.autocommit

    def create_table(self, table_object):
        self._connection_check()
        if not isinstance(table_object, SqlTable):
            raise TypeError("table_object must be a SqlTableFrame object")
        cursor = self.database.cursor()

        table_str = "{} (".format(table_object.name)
        for ele in table_object.table:
            table_str += "{} {}, ".format(ele[0], ele[1])
        table_str = table_str[:-2] + ")"
        cmd = "CREATE TABLE {}".format(table_str)
        cursor.execute(cmd)
        self._auto_commit()

    def drop_table(self, table_name):
        self._connection_check()
        cursor = self.database.cursor()

        cmd = "DROP TABLE {}".format(table_name)
        cursor.execute(cmd)
        self._auto_commit()

    def list_all_tables(self):
        self._connection_check()
        cursor = self.database.cursor()

        cursor.execute("select name from sqlite_master where type='table' order by name")

        ret = cursor.fetchall()
        ret = [ele[0].upper() for ele in ret]
        cursor.close()

        return ret

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
        self.database.rollback()

    def commit(self):
        self._connection_check()
        self.database.commit()

    def close(self):
        self._connection_check()
        self.commit()
        self.database.close()
        self.database = None


class SqliteTableCursor:

    def __init__(self, upper, table_name):
        self.upper = upper
        self.name = table_name
        self.table_info = None
        self.get_table_info()

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
            orderby="", asc_order=True):
        cursor = self.upper.database.cursor()

        if asc_order:
            order = "ASC"
        else:
            order = "DESC"
        if orderby == "":
            orderby = self.table_info[0]["name"]

        if key is None:
            key = "*"
            cmd = "SELECT {} from {} ORDER BY {} {}".format(key,
                                                            self.name,
                                                            orderby,
                                                            order
                                                            )
        else:
            if primary_index_column is None:
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

        if not isinstance(data, list):
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



class SqlTable(object):

    def __init__(self, tableName):
        self.name = tableName
        self.table = []

    def __str__(self):
        out = "{}({} column):\n".format(self.name, len(self.table))
        line0 = "+"
        line1 = "|"
        line2 = "|"
        for ele in self.table:
            line1_len = len(ele[0])
            for i in ele[0]:
                if ord(i) >= 256:
                    line1_len += 1
            max_unit_len = line1_len
            line2_len = len(ele[1])
            for i in ele[1]:
                if ord(i) >= 256:
                    line2_len += 1
            if line2_len > max_unit_len:
                max_unit_len = line2_len

            line0 += "-" * (max_unit_len + 2) + "+"
            line1 += " {}".format(ele[0]) \
                     + " " * (max_unit_len - line1_len) + " |"
            line2 += " {}".format(ele[1]) \
                     + " " * (max_unit_len - line2_len) + " |"
        out += line0 + "\n"
        out += line1 + "\n"
        out += line0 + "\n"
        out += line2 + "\n"
        out += line0 + "\n"

        return out

    def add_column(self, name, dtype):
        self.table.append([str(name), dtype])

    def remove_column(self, index):
        self.table.pop(index)

    def add_limit(self, index, limit):
        if index not in range(len(self.table)):
            raise IndexError("column {} not found".format(index))
        if not isinstance(limit, str):
            raise TypeError("limit must be str")
        self.table[index][1] += " {}".format(limit)

    def insert_column(self, index, name, dtype):
        self.table.insert(index, [name, dtype])


class Sqlimit(object):

    NOT_NULL    = "NOT NULL"
    DEFAULT     = "DEFAULT"
    UNIQUE      = "UNIQUE"
    PRIMARY_KEY = "PRIMARY KEY"

    def CHECK(sentence):
        ret = "CHECK({})".format(sentence)
        return ret


class SqlDtype(object):

    NULL    = "NULL"
    TEXT    = "TEXT"
    INTEGER = "INTEGER"
    REAL    = "REAL"
    BLOB    = "BLOB"


def test():
    import random
    t = SqliteDB("test.db")
    t.connect()
    tables = t.list_all_tables()
    print("Tables in DB:\n{}".format(tables))
    tc = t.select_table("company")
    tc.pop(4)
    data = tc.get()
    print("1. data in COMPANY:\n{}".format(data))
    tc.append([4, "Icy", 20])
    data = tc.get()
    t.commit()
    print("2. data in COMPANY:\n{}".format(data))
    tc.pop(4)
    data = tc.get()
    print("3. data in COMPANY:\n{}".format(data))
    t.close()
    t.connect()
    t.switch_autocommit()
    tc = t.select_table("company")
    tc.pop(4)
    tc.append([4, "Icy", 20])
    data = tc.get()
    print("4. data in COMPANY:\n{}".format(data))
    tc.update(random.randint(18,30), 4, "AGE")
    data = tc.get()
    print("5. data in COMPANY:\n{}".format(data))
    tc.pop(4)


if __name__ == '__main__':
    test()