import sqlite3
from dataclasses import fields, is_dataclass
import builtins
from typing import Type, Any, Dict
import datetime


def _create_connection(db_filename):
    return sqlite3.connect(db_filename)


class dctodb:
    def _get_dc_fields(self):
        return [field.type for field in fields(self.dc) if is_dataclass(field.type)]

    def _get_count(self):
        conn = _create_connection(self.db_filename)
        cur = conn.cursor()
        res = cur.execute(f"SELECT COUNT(*) FROM {self.dc.__name__}").fetchone()[0]
        return res

    def _create_sub_table(self, dcs_in_class):
        # we will iterate over each item in dcs we have and create a table accordingly, attaching our id
        for dc_in_class in dcs_in_class:
            # we will need to create a table to each, with extra column that is the id of self.
            self.dc_in_class_mappings[dc_in_class] = dctodb(
                dc_in_class, self.db_filename, {self.dc.__name__ + "index": int}
            )

    def _fetch_from_sub_table(self, self_index, item_to_fetch):
        # will return all the items with matching self_index.
        # obviously that means that we will have to fetch self first
        possible_items = self.dc_in_class_mappings[
            item_to_fetch
        ].fetch_all()  # returns a tuple with extra columns: (item, extracolumn:Value)

        # currently supporting only one item and not lists
        for item, extra_columns in possible_items:
            if extra_columns[self.dc.__name__ + "index"] == self_index:
                return item

    def __init__(
        self, dc: Type[Any], db_filename: str, extra_columns: Dict[str, Any] = None
    ):
        self.dc: Type[Any] = dc
        self.db_filename: str = db_filename
        self.dc_in_class_mappings = dict()
        self.extra_columns = extra_columns  # won't be returned inside an object but in a dict next to the object
        possible_dcs = self._get_dc_fields()
        if possible_dcs:
            self._create_sub_table(possible_dcs)

        self.create_table()

    def create_table(self):
        command = f"CREATE TABLE IF NOT EXISTS {self.dc.__name__} (id integer PRIMARY KEY AUTOINCREMENT, "

        for field in fields(self.dc):
            if field.name == "index":
                continue

            match field.type:
                case builtins.int:
                    command += f"{field.name} integer, "

                case builtins.str:
                    command += f"{field.name} text, "

                case builtins.bool:
                    command += f"{field.name} boolean, "

                case builtins.bytes:
                    command += f"{field.name} binary, "

                case datetime.datetime:
                    command += f"{field.name} smalldatetime, "

                case builtins.float:
                    command += f"{field.name} float, "

                case _:
                    if field.type in self.dc_in_class_mappings:
                        continue
                    raise Exception(f"unsupported data type: {field.type}")

        if self.extra_columns:
            for col_name, col_type in self.extra_columns.items():
                match col_type:
                    case builtins.int:
                        command += f"{col_name} integer, "

                    case builtins.str:
                        command += f"{col_name} text, "

                    case builtins.bool:
                        command += f"{col_name} boolean, "

                    case builtins.bytes:
                        command += f"{col_name} binary, "

                    case datetime.datetime:
                        command += f"{col_name} smalldatetime, "

                    case builtins.float:
                        command += f"{col_name} float, "

                    case _:
                        raise Exception(f"unsupported data type: {field.type}")

        command = command[:-2]  # removing ', ' from command
        command += ");"  # closing the command
        conn = _create_connection(self.db_filename)
        cur = conn.cursor()
        cur.execute(command)
        conn.close()

    def insert(self, *instances_of_dc):
        # before any inserting, we need to verify the indexes of our current.
        curr_items = (
            self._get_count()
        )  # because the counting starts from 1, 4 items means than the next item we need to insert is five.

        if self.extra_columns:
            for instance, dic in instances_of_dc:
                instance.index = curr_items + 1
                curr_items += 1
        else:
            for instance in instances_of_dc:
                instance.index = curr_items + 1
                curr_items += 1
        # before inserting self, we will call the insert the method of our subclasses
        if self.dc_in_class_mappings:
            for instance in instances_of_dc:
                for field in fields(instance):
                    if field.type in self.dc_in_class_mappings:
                        self.dc_in_class_mappings[field.type].insert(
                            (
                                getattr(instance, field.name),
                                {self.dc.__name__ + "index": instance.index},
                            )
                        )
                        break

        if not self.extra_columns:
            var_names = []
            for field in fields(self.dc):
                if field.name == "index":
                    continue
                if field.type in self.dc_in_class_mappings:
                    continue
                var_names.append(field.name)


            command = f"INSERT INTO {self.dc.__name__} ({','.join(var_names)}) VALUES ({'?,' * len(var_names)}"
            command = command[:-1]  # strip ','
            command += ")"

            val_list = [
                tuple(getattr(instance, var_name) for var_name in var_names)
                for instance in instances_of_dc
            ]

            val_instance_list = []
            
        if self.extra_columns:
            var_names = [field.name for field in fields(self.dc)] + list(
                self.extra_columns.keys()
            )
            var_names.remove("index")
            command = f"INSERT INTO {self.dc.__name__} ({','.join(var_names)}) VALUES ({'?,' * len(var_names)}"
            command = command[:-1]  # strip ','
            command += ")"
            val_list = [
                tuple(
                    getattr(instance, var_name)
                    for var_name in var_names
                    if var_name not in self.extra_columns.keys()
                )
                + tuple(extra_columns.values())
                for instance, extra_columns in instances_of_dc
            ]

        conn = _create_connection(self.db_filename)
        cur = conn.cursor()
        cur.executemany(command, val_list)
        conn.commit()
        conn.close()

    def fetch_all(self):
        conn = _create_connection(self.db_filename)
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM {self.dc.__name__}")
        rows = cur.fetchall()
        conn.close()

        fetched = []
        # for each row we will iterate over every column and make sure the correct type in inserted

        # we also know that if extra.columns, than we need to fetch them in a different dict
        for row in rows:
            args = []

            # before checking for extra columns, we need to fetch subtables.
            # we know that for each row theres an object that needs to be fetched first and assigned
            # before we continue with that we need a method to fetch one
            row = list(row)
            index = int(row.pop(0))

            for field in fields(self.dc):
                if field.type in self.dc_in_class_mappings:
                    args.append(self._fetch_from_sub_table(index, field.type))
                    continue

                if field.name == "index":
                    args.append(index)
                    continue

                if field.type == datetime.datetime:
                    col = row.pop(0)
                    col = col.split(".")[0]
                    col = datetime.datetime.strptime(col, "%Y-%m-%d %H:%M:%S")
                    args.append(col)
                    continue

                args.append(field.type(row.pop(0)))

            # now if we have extra coulmns we should have more in row, that we return as dict
            if self.extra_columns:
                extra_columns = {}
                for col_name, col_type in self.extra_columns.items():
                    extra_columns[col_name] = col_type(row.pop())
                fetched.append((self.dc(*args), extra_columns))

            else:
                fetched.append(self.dc(*args))

        return fetched

    def update(self, find_by_field, *instances_of_dc):
        var_names = [field.name for field in fields(self.dc) if field.name != "index"]
        command = f"UPDATE {self.dc.__name__} SET {''.join(f'{name} = ?,' for name in var_names)}"
        command = command[:-1]  # remove ','

        command += f" WHERE {find_by_field} = ?"

        # arg_list contains a tuple of values of all objects data to update COMBINED with the key
        arg_list = []
        for instance in instances_of_dc:
            vals = tuple(getattr(instance, field.name) for field in fields(self.dc))
            find_by = (getattr(instance, find_by_field),)

            arg_list.append(vals + find_by)

        conn = _create_connection(self.db_filename)
        c = conn.cursor()
        c.executemany(command, arg_list)
        conn.commit()
        conn.close()

    def delete(self, *instances_of_dc):
        var_names = [field.name for field in fields(self.dc) if field.name != "index"]
        command = f"DELETE FROM {self.dc.__name__} WHERE {''.join(f'{name} = ? AND ' for name in var_names)}"
        command = command[:-4]  # remove '? AND' from query

        # a list of the tuples containing the value of all objects we want to remove
        val_list = [
            tuple(getattr(instance, var_name) for var_name in var_names)
            for instance in instances_of_dc
        ]
        conn = _create_connection(self.db_filename)
        c = conn.cursor()
        c.executemany(command, val_list)
        conn.commit()
        conn.close()
