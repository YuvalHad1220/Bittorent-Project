import sqlite3
from dataclasses import fields, is_dataclass, dataclass
import builtins
from typing import Type, Any, Dict, Tuple, Union, List
import datetime

def _create_connection(db_filename) -> sqlite3.Connection:
    return sqlite3.connect(db_filename)

def _split_fields(dc) -> Tuple[List[Any]]:
    basic_fields = []
    either_dc_or_list_fields = []
    for field in fields(dc):
        if is_dataclass(field.type):
            either_dc_or_list_fields.append(field)
            continue
        if isinstance(field.type, list):
            either_dc_or_list_fields.append(field)
            continue

        basic_fields.append(field)
    return basic_fields, either_dc_or_list_fields

def _sql_represent(name, type) -> str:
    match type:
        case builtins.int:
            return f"{name} integer"

        case builtins.str:
            return f"{name} text"

        case builtins.bool:
            return f"{name} boolean"

        case builtins.bytes:
            return f"{name} binary"

        case datetime.datetime:
            return f"{name} smalldatetime"

        case builtins.float:
            return f"{name} float"

        case _:
            raise Exception(f"Unrecognized type: {type}")

class dctodb:
    @property
    def table_name(self) -> str:
        return self.dc.__name__
    
    # a way for our childs to recognize us
    @property
    def identifier(self) -> str:
        return self.dc.__name__ + "index"

    def _execute(self, command, args = None) -> Tuple():
        conn = _create_connection(self.db_filename)
        cur = conn.cursor()
        if args:
            res = cur.execute(command, args)
        else:
            res = cur.execute(command)

        return res, conn


    def __init__(self, dc: Type[Any], db_filename: str, extra_columns: Dict[str, Any] = dict()):
        self.dc: Type[Any] = dc
        self.db_filename: str = db_filename
        self.extra_columns = extra_columns  # won't be returned inside an object but in a dict next to the object
        self.basic_fields, self.possible_dcs_or_lists = _split_fields(self.dc) # only fields that are not dcs or lists
        self.dc_in_class_mappings = dict()
        if self.possible_dcs_or_lists:
            self._create_sub_conn(self.possible_dcs_or_lists)
        
        self.create_table()

    def create_table(self):
        command = "CREATE TABLE IF NOT EXISTS {} (id integer PRIMARY KEY AUTOINCREMENT, {});"
        # might remove index from basic_fields but unsure
        args = [_sql_represent(field.name, field.value) for field in self.basic_fields if field.name != 'index'] + [_sql_represent(col_name, col_type) for col_name, col_type in self.extra_columns.keys()]
        _, conn = self._execute(command)
        conn.close()

    def _get_count(self) -> int:
        res, conn = self._execute(f"SELECT COUNT(*) FROM {self.dc.__name__}")
        res = res.fetchone()[0]
        conn.close()
        return res

    def _create_sub_conn(self, dcs_or_classes_in_class):
        """
        Essentially, Before we insert self, we need to create sub-connections to every complicated object we need to store, like sub-dataclasses and lists.
        That connection is creating connection to our sub-dataclasses, however we create extra columns that are not part of the object but rather an identifier to their parent class

        NEED TO ADD SUPPORT FOR: LIST

        """
        for dc_in_class in dcs_or_classes_in_class:
            self.dc_in_class_mappings[dc_in_class.type] = dctodb(dc_in_class.type, self.db_filename, {self.identifier: int})


    def _insert_list(self):
        pass

    def _insert_dcs(self, instance):
        sub_dcs = filter(lambda x: is_dataclass(x.type), self.possible_dcs_or_lists)
        for field in sub_dcs:
            instance_dc_value = getattr(instance, field.name)
            self.dc_in_class_mappings[field.type].insert_one(instance_dc_value,{self.identifier:instance.index})

    
    def insert_many(self, *instances):
        """
        Mega function that consists of multiple child functions.
        1. We will insert our dataclasses and lists
        2. We will insert ourselves, MEANWHILE updating our indexes as fitted in the db itself.
        
        """



    def insert_one(self, instance, extra_columns: Dict[str, Any] = dict()):
        """
        A potentially mega function, we want that function to insert one item (and update its value). if it has extra columns, obviously we need to insert them as well.
        Extra columns is a dict: {col_name: col_value}
        After we updated our own index, we can proceed to enter fields like dcs and lists
        """

        command = "INSERT INTO {} ({}) VALUES ({});"
        # Remember, we will need to handle dataclasses and lists seperatley so we exclude them from now
        variable_names = [field.name for field in self.basic_fields if field.name != "index"]
        variable_values = [getattr(instance, field_name) for field_name in variable_names]
        for col_name, col_value in extra_columns.items():
            variable_names.append(col_name)
            variable_values.append(col_value)

        command = command.format(self.table_name, ', '.join(variable_names), ','.join(['?'] * len(variable_names)))
        _, conn = self._execute(command, variable_values)
        res = conn.commit()
        instance.index = self._get_count()

        conn.close()

        if self.dc_in_class_mappings:
            self._insert_dcs(instance)
        
    def fetch_where(condition) -> List[Tuple[Any, Union[Dict, None]]]:
        """
        A cute function that returns a list where condition is met.
        condition looks like that:
        FIELD_NAME OPERATOR VALUE

        We will have to make sure that we also fetch sub-classes \ lists if there are any
        
        Each row will be dismantled into columns and we will put the columns as needed in args and then return
        If there are extra_columns, than we return it in a seperate dict
        """
        fetched = []

        command = "SELECT * FROM {} WHERE {};"

        
    def _fetch_from_sub_table(self, self_index, item_to_fetch):
            """
            1. Fetch all sub-items from a specific table. We remember that because we know these items have extra columns (AS they are dependent on their parent to be identified)
            2. if their "parent_index" equals self.index, than it's a child of us that needs to be fetched and returned.

            NEED TO ADD SUPPORT FOR: LIST

            """
            child_items = self.dc_in_class_mappings[item_to_fetch].fetch_all()

            # currently supporting only one item and not lists
            for item, extra_columns in child_items:
                if extra_columns[self.identifier] == self_index:
                    return item

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
