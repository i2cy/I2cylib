#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: i2cy(i2cy@outlook.com)
# Filename: sqlitedb
# Created on: 2021/2/16
# Description: A pythonfied sqlite3 database control api class
##VERSION: 1.2


from typing import Any, Union
import sqlite3


class Sqlimit(object):
    """
    sqlite data limits
    """
    NOT_NULL = "NOT NULL"
    DEFAULT = "DEFAULT"
    UNIQUE = "UNIQUE"
    PRIMARY_KEY = "PRIMARY KEY"

    def CHECK(sentence):
        ret = "CHECK({})".format(sentence)
        return ret


class SqlDtype(object):
    """
    sqlite data types
    """
    NULL = "NULL"
    TEXT = "TEXT"
    INTEGER = "INTEGER"
    REAL = "REAL"
    BLOB = "BLOB"


class NewSqlTable(object):

    def __init__(self, tableName: str):
        """
        initialize an NewSqlTable object

        :param tableName: str
        """
        self.name = tableName
        self.table = []

    def __str__(self) -> str:
        """
        print table details
        :return: str
        """
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

    def add_column(self, name: str, dtype: SqlDtype):
        """
        add one column to the current table, with increased index

        :param name: str, column name
        :param dtype: SqlDtype
        :return: None
        """
        self.table.append([str(name), dtype])

    def remove_column(self, index: int):
        """
        remove one column from the current table

        :param index: int, column index
        :return: None
        """
        self.table.pop(index)

    def add_limit(self, index: int, limit: Sqlimit):
        """
        add limit to one column with specified index

        :param index: int, column index
        :param limit: Sqlimit
        :return: None
        """
        if index not in range(len(self.table)):
            raise IndexError("column {} not found".format(index))
        if not isinstance(limit, str):
            raise TypeError("limit must be str")
        self.table[index][1] += " {}".format(limit)

    def insert_column(self, index: int, name: str, dtype: SqlDtype):
        """
        insert a column to the specified column

        :param index: int, column index
        :param name: str, column name
        :param dtype: SqlDtype
        :return: None
        """
        self.table.insert(index, [name, dtype])


class SqlTable:

    def __init__(self, upper, table_name: str):
        """
        a Table object of Sqlite database, iterable, subscriptable
        :param upper: SqliteDB
        :param table_name: str, name of table
        """
        self.upper = upper
        self.name = table_name
        self.table_info = None
        self.length = 0
        self.get_table_info()
        self.cursor = self.upper.database.cursor()
        self.offset = 0

    def __len__(self) -> int:
        """
        get length of current table
        :return: int
        """
        cursor = self.upper.database.cursor()
        cmd = "SELECT COUNT(*) FROM {}".format(self.name)
        cursor.execute(cmd)
        data = cursor.fetchall()
        self.length = int(data[0][0])
        cursor.close()
        return self.length

    def __iter__(self):
        """
        return iterables
        :return:
        """
        self.cursor.execute("SELECT * FROM {}".format(self.name))
        if self.offset > 0:
            self.cursor.fetchmany(self.offset)

        return self

    def __next__(self):
        """
        return next item of iterables
        :return:
        """
        ret = self.cursor.fetchone()
        if ret is None:
            raise StopIteration
        self.offset += 1
        return ret

    def __delitem__(self, key):
        """
        delete an item by using 'del' operator
        :param key: Any
        :return:
        """
        self.pop(key)

    def __contains__(self, item) -> bool:
        """
        return weather if a table named as given exists
        :param item: str
        :return:
        """
        self.upper._connection_check()
        cursor = self.upper.database.cursor()
        p_id, p_name = self.get_primary_index_name()
        key = self._data2sqlstr(item)

        cursor.execute("SELECT EXISTS(SELECT {} from {} where {}={} limit 1);".format(p_name, self.name, p_name, key))

        ret = cursor.fetchone()
        ret = ret[0] > 0
        cursor.close()
        return ret

    def __getitem__(self, item) -> list:
        """
        get item(s) from current table
        :param item: int or slice(), index
        :return: list, one item or list of items
        """
        valid = isinstance(item, int) or isinstance(item, slice)
        if not valid:
            raise KeyError("index must be integrate or slices")

        length = len(self)
        step = None
        stop = -1

        if isinstance(item, slice):
            offset = item.start
            if offset is None:
                offset = 0
            step = item.step
            if step is None:
                step = 1
            stop = item.stop
            if stop is None:
                stop = length
            if stop < 0:
                stop = length + stop
        else:
            offset = item

        if offset < 0:
            offset = length + offset

        if offset >= length or stop > length:
            raise KeyError("index out of range")

        cursor = self.upper.database.cursor()

        if isinstance(item, slice):
            cursor.execute("SELECT * FROM {} LIMIT {} OFFSET {}".format(self.name,
                                                                        stop - offset,
                                                                        offset))
            ret = cursor.fetchall()
            ret = ret[::step]

        else:
            cursor.execute("SELECT * FROM {} LIMIT 1 OFFSET {}".format(self.name, offset))
            ret = cursor.fetchone()

        cursor.close()

        return ret

    def __setitem__(self, key: int, value):
        """
        set an item with specific index and value
        :param key: int, index
        :param value: Any
        :return:
        """
        if not isinstance(key, int):
            raise KeyError("index must be integrate")

        pi, primary_key = self.get_primary_index_name()

        length = len(self)
        offset = key

        if offset < 0:
            offset = length + offset

        if offset >= length:
            raise KeyError("index out of range")

        cursor = self.upper.database.cursor()

        cursor.execute("SELECT {} FROM {}".format(primary_key, self.name))
        if offset > 0:
            cursor.fetchmany(offset)

        target = cursor.fetchone()[0]
        cursor.close()

        self.update(data=value, index_key=target)

    def get_primary_index_name(self) -> (int, str):
        """
        return primary index column of current table
        :return: (inr, str), index of primary key and string of primary key
        """
        primary_key = None
        p_index = 0
        for index, ele in enumerate(self.table_info):
            if ele["is_primary_key"]:
                primary_key = ele["name"]
                p_index = ele['ID']
                break
        if primary_key is None:
            raise KeyError("no primary key defined in table,"
                           " invalid operation.")
        return p_index, primary_key

    def seek(self, offset: int):
        """
        set current offset when iterate
        :param offset: int
        :return:
        """
        self.cursor = self.upper.database.cursor()
        if offset < 0:
            offset = len(self) + offset
        self.offset = offset

    def undo(self):
        """
        attempt to undo all changes that have not been committed yet
        :return:
        """
        if self.upper.autocommit:
            raise Exception("cannot undo since the autocommit mode is on")
        self.length = None
        self.upper.database.rollback()

    def _data2sqlstr(self, data):
        """
        convert python items to SQL data string
        :param data: Any
        :return: str, converted SQL data string
        """
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
        """
        get current table information of columns. Will also update values in self.table_info
        :return: list, list of information of columns
        """
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
        """
        append a line of data into current table list.
        :param data: list, tuple, iterable object
        :return:
        """
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
        """
        delete all values in table including lines and data
        :return:
        """
        cursor = self.upper.database.cursor()

        cmd = "DELETE FROM {};".format(self.name)

        cursor.execute(cmd)
        self.upper._auto_commit()
        cursor.close()

    def pop(self, key: Union[int, bool, str, float], use_primary_index: bool = False,
            primary_index_column=None) -> list:
        """
        remove line(s) of data from current table and return
        :param key: int or Any(int, bool, str, float)
        :param use_primary_index: bool (optional, default=True), the indexer will use primary index column to select
        data, otherwise it will use default index of lines starts from 0 which stands for the first line
        :param primary_index_column: str (optional), index_name can be automatically set as the primary key in table.
        Or you can define it as it follows the SQLite3 WHERE logic
        :return: list, list of item(s)
        """
        cursor = self.upper.database.cursor()
        primary_column_number = -1

        if primary_index_column is None or use_primary_index:
            primary_column_number, primary_index_column = self.get_primary_index_name()

        if use_primary_index:
            ret = self.get(key=key, primary_index_column=primary_index_column)
            key = self._data2sqlstr(key)

        else:
            ret = self[key]
            key = ret[primary_column_number]

        cmd = "DELETE FROM {} WHERE {}={};".format(self.name,
                                                   primary_index_column, key)

        cursor.execute(cmd)
        self.upper._auto_commit()
        cursor.close()

        return ret

    def get(self, key: Any = None, column_names: str = "*",
            primary_index_column: str = None,
            orderby: str = None, asc_order: bool = True) -> list:
        """
        get lines of data with specified config
        :param key: int(or str, tuple), index(s) (e.g. 1, (1, 3, 5), ("male", "female"))
        :param column_names: str, standard SQL (e.g. "Name, ID, GENDER, AGE", "Name")
        :param primary_index_column: int or str (optional, default: default primary index column
        in table), column to be indexed
        :param orderby: str (optional, default: first column), sort lines by this column
        :param asc_order: bool (optional, default: True), whether returned value should be ordered by ascending or descending
        :return: list, list of item(s)
        """

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
            cmd = "SELECT {} from {} ORDER BY {} {}".format(column_names,
                                                            self.name,
                                                            orderby,
                                                            order
                                                            )

        elif isinstance(key, tuple):
            if len(key) != 2:
                cursor.close()
                raise KeyError("index range tuple must have 2 elements")
            cmd = "SELECT {} from {} WHERE {} BETWEEN {} AND {} ORDER BY {} {}".format(column_names,
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
            cmd = "SELECT {} from {} WHERE {} IN ({}) ORDER BY {} {}".format(column_names,
                                                                             self.name,
                                                                             primary_index_column,
                                                                             key_str,
                                                                             orderby,
                                                                             order)

        else:
            key = self._data2sqlstr(key)
            cmd = "SELECT {} FROM {} WHERE {}={} ORDER BY {} {}".format(column_names,
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
               column_names: Union[str, list] = None,
               primary_index_column: str = None):
        """
        update data with specified search values
        :param data: list(or tuple)
        :param index_key: int(or str), index
        :param column_names: list(or str), column(s) to be fetched
        :param primary_index_column: str, the column to be indexed
        :return: None
        """

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


class SqliteDB:

    def __init__(self, database: str = None):
        """
        Create a SqliteDB class with specific filename (optional)
        :param database: str (optional), database filename
        """
        self.filename = database
        self.database = None

        self.autocommit = False

        self.cursors = []

        self.__index = 0
        self.__length = -1
        self.__iter_table_list_cache = []

    def __len__(self) -> int:
        """
        return counts of tables
        :return:
        """
        self._connection_check()
        if self.__length < 0:
            self.__length = len(self.list_all_tables())
        return self.__length

    def __contains__(self, item):
        """
        return weather if a table named as given exists
        :param item: str
        :return:
        """
        self._connection_check()
        cursor = self.database.cursor()

        cursor.execute(
            "SELECT EXISTS(SELECT name from sqlite_master where type='table' and name='{}' limit 1)".format(item))

        ret = cursor.fetchone()
        ret = ret[0] > 0
        cursor.close()
        return ret

    def __getitem__(self, item: Union[str, int]) -> SqlTable:
        """
        return an SqlTable with specific name as key
        :param item: str or int, table name or index of table
        :return: SqlTable
        """
        self._connection_check()
        if isinstance(item, int):
            item = self.list_all_tables()[item]
        return self.select_table(item)

    def __delitem__(self, key: Union[str, int]):
        """
        drop a table from current database by calling 'del' operator
        :param key: str or int, table name or index of table
        :return:
        """
        self._connection_check()
        if isinstance(key, int):
            key = self.list_all_tables()[key]
        self.drop_table(key)

    def __iter__(self):
        """
        return an iterable object which is itself
        :return: SqliteDB
        """
        self._connection_check()
        self.__iter_table_list_cache = self.list_all_tables()
        return self

    def __next__(self) -> SqlTable:
        """
        return each table when iterate
        :return: SqlTable
        """
        if self.offset >= len(self):
            raise StopIteration
        self.offset += 1
        return self.select_table(self.__iter_table_list_cache[self.offset])

    def _connection_check(self):
        """
        check if the connection to database if valid, otherwise throw out an exception
        :return:
        """
        if self.database is None:
            raise Exception("connection has not been built yet, "
                            "you have to connect to a database first")

    def _undo_cursors(self):
        """
        attempt undo every changes
        :return:
        """
        valids = []
        for ele in self.cursors:
            try:
                ele.undo()
                valids.append(ele)
            except:
                pass
        self.cursors = valids

    def _auto_commit(self):
        """
        auto commit if auto-commit mode is enabled
        :return:
        """
        if self.autocommit:
            self.database.commit()

    def seek(self, offset: int):
        """
        set current offset when iterate
        :param offset: int
        :return:
        """
        if offset < 0:
            offset = len(self) + offset
        self.offset = offset

    def connect(self, database: str = None, timeout: int = 5):
        """
        Connect to a database, specify a database filename otherwise it will use the default value set by init
        :param database: str (optional), database filename
        :param timeout: int (optional, default: 5), timeout value of sqliteDB in seconds
        :return:
        """
        if database is None:
            database = self.filename

        self.database = sqlite3.connect(database, timeout=timeout)
        self.__iter_cursor = self.database.cursor()

    def switch_autocommit(self, enabled: bool = None) -> bool:
        """
        Switch auto-commit mode on or off. If auto commit is on, everything you do will commit to database
        immediately.
        :param enabled: bool (optional), if unset, calling this method will toggle the autoswitch mode on and off,
        if enabled is set, then mode will set to the value of enabled
        :return: bool, auto-commit current value of enabled
        """
        if enabled is None:
            if self.autocommit:
                self.autocommit = False
            else:
                self.autocommit = True
        else:
            self.autocommit = enabled

        return self.autocommit

    def create_table(self, table_object: NewSqlTable):
        """
        Create a Table in database
        :param table_object: NewSqlTable, table object
        :return:
        """
        self._connection_check()
        if not isinstance(table_object, NewSqlTable):
            raise TypeError("table_object must be a SqlTableFrame object")
        cursor = self.database.cursor()

        table_str = "{} (".format(table_object.name)
        for ele in table_object.table:
            table_str += "{} {}, ".format(ele[0], ele[1])
        table_str = table_str[:-2] + ")"
        cmd = "CREATE TABLE {}".format(table_str)
        cursor.execute(cmd)
        self._auto_commit()

    def drop_table(self, table_name: str):
        """
        delete a table with specific name
        :param table_name: str
        :return:
        """
        self._connection_check()
        cursor = self.database.cursor()

        cmd = "DROP TABLE {}".format(table_name)
        cursor.execute(cmd)
        self._auto_commit()

    def list_all_tables(self) -> list:
        """
        list all tables in database
        :return: list, list of names
        """
        self._connection_check()
        cursor = self.database.cursor()

        cursor.execute("select name from sqlite_master where type='table' order by name")

        ret = cursor.fetchall()
        ret = [ele[0].upper() for ele in ret]
        cursor.close()

        return ret

    def select_table(self, table_name: str) -> SqlTable:
        """
        select a table and return SqlTable object
        :param table_name: str
        :return: SqlTable
        """
        table_name = table_name.upper()
        self._connection_check()
        if not table_name in self.list_all_tables():
            raise Exception("cannot find table \"{}\" in database".format(table_name))
        ret = SqlTable(self, table_name)
        return ret

    def undo(self):
        """
        attempt to undo changes that haven't been committed
        :return:
        """
        self._connection_check()
        if self.autocommit:
            raise Exception("cannot undo since the autocommit mode is on")
        self.database.rollback()
        self._undo_cursors()

    def commit(self):
        """
        commit current changes to database
        :return:
        """
        self._connection_check()
        self.database.commit()

    def close(self):
        """
        close connection to database
        :return:
        """
        self._connection_check()
        self.commit()
        self.database.close()
        self.database = None


def test():
    import random, os
    create = False
    if not os.path.exists("test.db"):
        create = True
    t = SqliteDB("test.db")
    t.connect()
    tables = t.list_all_tables()
    print("checking if table COMPANY exists: {}".format("COMPANY" in t))
    print("Tables in DB:\n{}".format(tables))
    if create:
        print("creating table COMPANY")
        tb = NewSqlTable("COMPANY")
        tb.add_column("ID", SqlDtype.INTEGER)
        tb.add_column("name", SqlDtype.TEXT)
        tb.add_column("index_1", SqlDtype.REAL)
        tb.add_column("is_adult", SqlDtype.INTEGER)
        tb.add_limit(0, Sqlimit.PRIMARY_KEY)
        tb.add_limit(1, Sqlimit.NOT_NULL)
        tb.add_limit(2, Sqlimit.NOT_NULL)
        tb.add_limit(3, Sqlimit.NOT_NULL)
        t.create_table(tb)
    print("checking if table COMPANY exists: {}".format("COMPANY" in t))
    print("checking if table COMPANY_2 exists: {}".format("COMPANY_2" in t))
    print("selecting table COMPANY")
    tc = t.select_table("company")
    print("erasing all data in table")
    tc.empty()
    data = tc.get()
    print("0. column info in COMPANY:\n{}".format(tc.get_table_info()))

    print("1. data in COMPANY:\n{}".format(data))
    print("appending data to table COMPANY")
    tc.append([1, "Icy", 0.03, True])
    tc.append([2, "Cody", 0.38, True])
    tc.append([4, "RSauce", 0.96, True])
    tc.append([3, "Aurora", 0.76, True])
    tc.append([5, "Zero", 0.00, True])
    tc.append([6, "Ash", 0.99, True])
    data = tc.get()
    print("committing changes")
    t.commit()
    print("2. data in COMPANY:\n{}".format(data))
    print("checking if lines with ID 1 exists: {}".format(1 in tc))
    print("checking if lines with ID 2 exists: {}".format(2 in tc))
    print("checking if lines with ID 6 exists: {}".format(2 in tc))

    print("deleting data line 1 from table COMPANY")
    tc.pop(1)
    print("checking if lines with ID 1 exists: {}".format(1 in tc))
    print("checking if lines with ID 2 exists: {}".format(2 in tc))
    print("checking if lines with ID 6 exists: {}".format(6 in tc))

    print("deleting data with ID 6 from table COMPANY")
    tc.pop(6, use_primary_index=True)
    data = tc.get()
    print("checking if lines with ID 1 exists: {}".format(1 in tc))
    print("checking if lines with ID 2 exists: {}".format(2 in tc))
    print("checking if lines with ID 6 exists: {}".format(6 in tc))

    print("3. data in COMPANY:\n{}".format(data))
    print("undo changes")
    tc.undo()
    data = tc.get()
    print("4. data in COMPANY:\n{}".format(data))
    print("reconnecting database")
    t.close()
    t.connect()
    print("autocommit mode on")
    t.switch_autocommit()
    tc = t.select_table("company")
    print("deleting data with ID 4 from table COMPANY")
    tc.pop(4, use_primary_index=True)
    print("appending data to table COMPANY")
    tc.append([4, "RSauce", 0.66, True])
    data = tc.get()
    print("5. data in COMPANY:\n{}".format(data))
    print("updating data in table COMPANY")
    tc.update(1 / random.randint(18, 30), 4, "index_1")
    data = tc.get()
    print("6. data in COMPANY:\n{}".format(data))
    data = tc.get((1, 4))
    print("7. data within ID between 1 and 4 in COMPANY:\n{}".format(data))
    data = tc.get((3, 5))
    print("8. data within ID between 3 and 5 in COMPANY:\n{}".format(data))
    data = tc.get([1, 3, 5])
    print("9. data within ID 1, 3, 5 in COMPANY:\n{}".format(data))
    print("table length: {}".format(len(tc)))
    print("iteration test:")
    for ele in tc:
        print(ele)
    print("iteration test with seek(2):")
    tc.seek(2)
    for ele in tc:
        print(ele)
    print("get item test:")
    for i in range(len(tc)):
        print(tc[i])
        print(tc[-i - 1])
    print("get item test[2:4]:")
    print(tc[2:4])
    print("get item test[2:-1]:")
    print(tc[2:-1])
    print("get item test[:-1]:")
    print(tc[:-1])
    print("get item test[2:]:")
    print(tc[2:])
    print("get item test[-3:]:")
    print(tc[-3:])
    print("get item test[0:3:2]:")
    print(tc[0:3:2])
    print("get item test[::-1]:")
    print(tc[::-1])
    print("set item test:")
    for i in range(len(tc)):
        tc[i] = (i, 'Cody', 1 / random.randint(18, 30), 1)
        print(tc[i])

    t.close()
    os.remove('test.db')


if __name__ == '__main__':
    test()
