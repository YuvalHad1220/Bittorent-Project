import sqlite3
from dataclasses import fields, is_dataclass, make_dataclass
import builtins
from typing import Type, Any, Dict, Tuple, Union, List, get_args, get_origin
import datetime


def _create_connection(db_filename) -> sqlite3.Connection:
    return sqlite3.connect(db_filename)


def _split_fields(dc) -> Tuple[List[Any]]:
    basic_fields = []
    dc_fields = []
    list_fields = []
    for field in fields(dc):
        if is_dataclass(field.type):
            dc_fields.append(field)

        elif get_origin(field.type) == list:
            list_fields.append(field)

        else:
            basic_fields.append(field)

    return basic_fields, dc_fields, list_fields

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

    def _create_class(self, field, item_type: Type):
        """
        helper class to store lists
        """
        cls_name = self.dc.__name__ + field.name.capitalize() + "List"
        return make_dataclass(cls_name,
                              [(self.identifier, str), ('item_val', item_type), ('index', int, 0)])


    def _init_sub_class_connections(self):
        """
        Essentially, Before we create our self table,
        we need to create sub-tables to every complicated object we need to store, like sub-dataclasses and lists.
        That connection is creating connection to our sub-dataclasses when inserting them to the DB.
        however we create extra columns that are not part of the object but rather an identifier to their parent class
          - so we could "reach" the parent class in the database
        """
        for dc_in_class in self.dc_fields:
            self.dc_in_class_mappings[dc_in_class] = dctodb(dc_in_class.type, self.db_filename, {self.identifier: int})

        for list_in_class in self.list_fields:
            custom_class = self._create_class(list_in_class, get_args(list_in_class.type)[0])
            self.lists_in_class_mappings[list_in_class] = dctodb(custom_class, self.db_filename)


    def create_table(self):
        command = "CREATE TABLE IF NOT EXISTS {} (id integer PRIMARY KEY AUTOINCREMENT, {});"
        # might remove index from basic_fields but unsure
        args = [_sql_represent(field.name, field.type) for field in self.basic_fields if field.name != 'index'] + [
            _sql_represent(col_name, col_type) for col_name, col_type in self.extra_columns.items()]
        args = ', '.join(args)
        command = command.format(self.table_name, args)
        _ = self._execute(command)
        self.conn.close()
        self.conn = None


    def __init__(self, dc: Type[Any], db_filename: str, extra_columns: Dict[str, Any] = dict()):
        self.dc: Type[Any] = dc
        self.db_filename: str = db_filename
        self.extra_columns = extra_columns  # won't be returned inside an object but in a dict next to the object
        self.identifier = self.dc.__name__ + "index"
        self.table_name = self.dc.__name__
        self.basic_fields, self.dc_fields, self.list_fields = _split_fields(self.dc)  # only fields that are not dcs or lists
        self.dc_in_class_mappings = dict()
        self.lists_in_class_mappings = dict()
        self.conn = None

        self._init_sub_class_connections()
        self.create_table()




        

    def _execute(self, command, args=None):
        if not self.conn:
            self.conn = _create_connection(self.db_filename)
        cur = self.conn.cursor()
        if args:
            res = cur.execute(command, args)
        else:
            res = cur.execute(command)

        return res


    def _get_count(self) -> int:
        res = self._execute(f"SELECT COUNT(*) FROM {self.dc.__name__}")
        res = res.fetchone()[0]
        self.conn.close()
        self.conn = None
        return res



    def _insert_list(self, instance, update_id):
        for list_field in self.list_fields:
            list_of_items = getattr(instance, list_field.name)
            for item in list_of_items:
                item_as_obj = self.lists_in_class_mappings[list_field].dc(instance.index, item)
                self.lists_in_class_mappings[list_field].insert_one(item_as_obj, update_id)

    def _insert_dcs(self, instance, update_id):
        for field in self.dc_fields:
            instance_dc_value = getattr(instance, field.name)
            self.dc_in_class_mappings[field].insert_one(instance_dc_value, update_id, {self.identifier: instance.index})

    def insert_one(self, instance, update_id = True, extra_columns: Dict[str, Any] = dict()):
        """
        A potentially mega function, we want that function to insert one item (and update its value). if it has extra columns, obviously we need to insert them as well.
        Extra columns is a dict: {col_name: col_value}
        After we updated our own index, we can proceed to enter fields like dcs and lists
        """

        command = "INSERT INTO {} ({}) VALUES ({});"
        # Remember, we will need to handle dataclasses and lists seperatley so we exclude them from now
        variable_names = []
        for field in self.basic_fields:
            if field.name == "index":
                if not update_id:
                    variable_names.append("id")
            else:
                variable_names.append(field.name)

        variable_values = []
        for field_name in variable_names:
            if field_name == "id":
                variable_values.append(getattr(instance, "index"))

            else:
                variable_values.append(getattr(instance, field_name))

        
        for var_name, var_value in extra_columns.items():
            variable_names.append(var_name)
            variable_values.append(var_value)

        command = command.format(self.table_name, ', '.join(variable_names), ','.join(['?'] * len(variable_names)))

        _ = self._execute(command, variable_values)
        res = self.conn.commit()
        if update_id:
            instance.index = self._get_count()

        if self.dc_in_class_mappings:
            self._insert_dcs(instance, update_id)
        if self.lists_in_class_mappings:
            self._insert_list(instance, update_id)

        if self.conn:
            self.conn.close()
            self.conn = None

    def _fetch_lists_from_subtable(self, index):
        # we know what's the table name, so we will just fetch_where id is the same as ours
        list_fields_values_mappings = dict()
        for list_field in self.list_fields:
            list_items_as_obj = self.lists_in_class_mappings[list_field].fetch_where(f'{self.identifier} == {index}')
            list_items_as_original_type = [row.item_val for row in list_items_as_obj]
            list_fields_values_mappings[list_field] = list_items_as_original_type
        return list_fields_values_mappings

    def fetch_all(self) -> List[Tuple[Any, Union[Dict, None]]]:
        """
        A cute function that returns a list where condition is met.
        condition looks like that:
        FIELD_NAME OPERATOR VALUE

        We will have to make sure that we also fetch sub-classes \ lists if there are any
        
        Each row will be dismantled into columns and we will put the columns as needed in args and then return
        If there are extra_columns, than we return it in a seperate dict
        """
        fetched = []

        command = "SELECT * FROM {};"
        command = command.format(self.table_name)
        res = self._execute(command)
        rows = res.fetchall()
        self.conn.close()
        self.conn = None

        for row in rows:
            index = row[0]
            basic_args = row[1:]
            child_dc_values = self._fetch_dcs_from_sub_table(index)
            list_values = self._fetch_lists_from_subtable(index)

            item = self._build_item_from_values(index, basic_args, child_dc_values, list_values)
            fetched.append(item)

        return fetched
    

    

    def fetch_where(self, condition) -> List[Tuple[Any, Union[Dict, None]]]:
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
        command = command.format(self.table_name, condition)
        res = self._execute(command)
        rows = res.fetchall()

        self.conn.close()
        self.conn = None

        for row in rows:
            index = row[0]
            basic_args = row[1:]
            child_dc_values = self._fetch_dcs_from_sub_table(index)
            list_values = self._fetch_lists_from_subtable(index)

            item = self._build_item_from_values(index, basic_args, child_dc_values, list_values)
            fetched.append(item)

        return fetched

    def _build_item_from_values(self, index, basic_args, child_dc_values: Dict, child_list_values: Dict):
        """
        We'll iterate over each value and append it into an args and then create an object through it
        """

        basic_args = list(basic_args)
        args = []
        for field in fields(self.dc):
            if field in child_dc_values:
                args.append(child_dc_values[field])
                continue

            if field in child_list_values:
                args.append(child_list_values[field])
                continue

            if field.name == "index":
                args.append(int(index))
                continue

            if field.type == datetime.datetime:
                date = basic_args.pop(0)
                date = date.split(".")[0]
                date = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
                args.append(date)
                continue

            args.append(field.type(basic_args.pop(0)))

        return self.dc(*args)

    def _fetch_dcs_from_sub_table(self, self_index) -> Dict:
        """
        We will fetch every sub-item using our self.index.
        Each field in our subclass is just one item, so it will always return only one item (one to one relationship)
        """
        dc_childs = dict()

        for dc_field, connector in self.dc_in_class_mappings.items():
            dc_childs[dc_field] = connector.fetch_where(f'{self.identifier} == {self_index}')[0]

        return dc_childs


    def delete(self, instance, parent_indentifier = None, parent_id = None):
        # we will find the object sub lists and sub dataclasses and delete them.
        # then we will remove self

        for list_field in self.list_fields:
            list_of_items = getattr(instance, list_field.name)
            for item in list_of_items:
                item_as_obj = self.lists_in_class_mappings[list_field].dc(instance.index, item)
                self.lists_in_class_mappings[list_field].delete(item_as_obj, self.identifier, instance.index)


        for field in self.dc_fields:
            instance_dc_value = getattr(instance, field.name)
            self.dc_in_class_mappings[field].delete(instance_dc_value)

        
        if parent_indentifier:
            self._execute(f"DELETE FROM {self.table_name} WHERE {parent_indentifier} = ?", (parent_id,))
        else:
            self._execute(f"DELETE FROM {self.table_name} WHERE id = ?", (instance.index,))
        self.conn.commit()
        self.conn.close()
        self.conn = None


    def update(self, instance):
        
        self.delete(instance)
        self.insert_one(instance, False)
        


        pass

    # def update(self, find_by_field, *instances_of_dc):
    #     var_names = [field.name for field in fields(self.dc) if field.name != "index"]
    #     command = f"UPDATE {self.dc.__name__} SET {''.join(f'{name} = ?,' for name in var_names)}"
    #     command = command[:-1]  # remove ','

    #     command += f" WHERE {find_by_field} = ?"

    #     # arg_list contains a tuple of values of all objects data to update COMBINED with the key
    #     arg_list = []
    #     for instance in instances_of_dc:
    #         vals = tuple(getattr(instance, field.name) for field in fields(self.dc))
    #         find_by = (getattr(instance, find_by_field),)

    #         arg_list.append(vals + find_by)

    #     conn = _create_connection(self.db_filename)
    #     c = conn.cursor()
    #     c.executemany(command, arg_list)
    #     conn.commit()
    #     conn.close()

    # def delete(self, *instances_of_dc):
    #     var_names = [field.name for field in fields(self.dc) if field.name != "index"]
    #     command = f"DELETE FROM {self.dc.__name__} WHERE {''.join(f'{name} = ? AND ' for name in var_names)}"
    #     command = command[:-4]  # remove '? AND' from query

    #     # a list of the tuples containing the value of all objects we want to remove
    #     val_list = [
    #         tuple(getattr(instance, var_name) for var_name in var_names)
    #         for instance in instances_of_dc
    #     ]
    #     conn = _create_connection(self.db_filename)
    #     c = conn.cursor()
    #     c.executemany(command, val_list)
    #     conn.commit()
    #     conn.close()
