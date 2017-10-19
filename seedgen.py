#!/usr/bin/python3

import re
import sys
import os
import getopt
from collections import defaultdict


def template(classname, suffix='Seed', content=''):
    return """<?php

use Illuminate\Database\Seeder;

class """ + classname + suffix + """ extends Seeder
{
    /**
     * Run the database seeds.
     *
     * @return void
     */
    public function run()
    {
""" + content + """    }
}
"""


def generate_seeds(db_values, table_name, fields):
    opath = 'output/'
    fname = camel_case(table_name) + 'Seed.php'  # add suffix here too

    if not os.path.exists(opath):  # do not check everytime this, pls
        os.makedirs(opath)

    content = tab(2) + "$items = [\n"

    for value in db_values:
        seed = []
        for i in range(len(fields)):
            if type(value[i]) is int:
                seed.append("'{}' => {}".format(fields[i], value[i]))
            elif value[i] is None:
                seed.append("'{}' => NULL".format(fields[i], value[i]))
            else:
                seed.append("'{}' => '{}'".format(fields[i], value[i]))
        content += tab(3) + '[' + ', '.join(seed) + '],\n'
    content += tab(2) + "];\n\n"
    content += tab(2) + "DB::table('" + table_name + "')->insert($items);\n"

    with open(opath + fname, 'w') as file:
        file.write(template(camel_case(table_name), content=content))
    print("\033[32mGenerated:\033[0m {}".format(fname))


def parse_sql(sql):
    sql = open(sql, 'r')
    db_values = []
    table_name = None
    fields = None

    in_values = None
    input_file = enumerate(sql)
    for i, line in input_file:
        if in_values:
            if re.match('\t\(', line):
                line = re.sub('NULL', 'None', line)
                line = eval(re.sub('(^\t|,$\n|;$\n)', '', line))
                db_values.append(line)
            else:
                generate_seeds(db_values, table_name, fields)
                in_values = False
                db_values = []
        elif re.match("INSERT INTO", line):
            line = re.sub("INSERT INTO ", "", line)
            line = re.sub("(`|,|\(|\))", "", line).split()
            table_name = line[0]
            fields = line[1:]
            in_values = True
            next(input_file)


def tab(count=1, tabsize=4):
    return ' ' * tabsize * count


def camel_case(s):
    return s.title().replace('_', '')


def usage():
    return """Usage: python""" + sys.argv[0] + """ [OPTION]...
Tool description

  -h, --help
        display this help and exit
  -i, --input=FILE
        SQL file to make seeds of
"""


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def build_relationships(sql):
    sql = open(sql, 'r')
    search_references = False
    relations = defaultdict(list)
    tables = []
    table = None
    for line in sql:
        if search_references:
            references = re.match("(.*)(REFERENCES `)(.*.)(` \()", line)
            if references:
                relations[table[2]].append(references[3])
            elif re.match("LOCK TABLES", line):
                search_references = False
        else:
            table = re.match("(CREATE TABLE `)(.*.)(`)", line)
            if table:
                tables.append(table[2])
                search_references = True
    seeder = sorted(list(set(tables) - set(relations)))
    while (relations):
        for k, v in list(relations.items()):
            for item in list(v):
                if item in seeder:
                    v.remove(item)
        for k, v in list(relations.items()):
            if not v:
                seeder.append(k)
                del relations[k]
    opath = 'output/'
    fname = 'DatabaseSeeder.php'
    if not os.path.exists(opath):
        os.makedirs(opath)

    content = ''
    for i in seeder:
        content += tab(2) + "$this->call(" + camel_case(i) + "Seed::class);\n"
    with open(opath + fname, 'w') as file:
        file.write(template('Database', 'Seeder', content))
    print("\033[32mGenerated:\033[0m {}".format(fname))


def main(argv):
    # print(template('SomeClass', 'whole things'))
    try:
        opts, args = getopt.getopt(argv, "hi:", ['help', 'input='])
    except getopt.GetoptError as err:
        eprint(str(err) + '\n')
        eprint(usage())
        sys.exit(2)

    if not opts:
        eprint(usage())
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print(usage())
        elif opt in ('-i', '--input'):
            try:
                f = open(arg, 'r')
                parse_sql(arg)
                build_relationships(arg)
            except IOError as err:
                eprint(err)


if __name__ == "__main__":
    main(sys.argv[1:])
