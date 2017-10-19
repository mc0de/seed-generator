#!/usr/bin/python3

import re
import sys
import os
import getopt
from collections import defaultdict


def generate_seeds(db_values, table_name, fields):
    opath = 'output/'
    fname = camel_case(table_name) + 'Seed.php'
    flen = len(fields)
    if not os.path.exists(opath):
        os.makedirs(opath)
    f = open(opath + fname, 'w')
    f.write("<?php\n\n")
    f.write("use Illuminate\Database\Seeder;\n\n")
    f.write("class " + camel_case(table_name) +
            "Seed extends Seeder\n{\n")  # class open
    f.write(tab() + "/**\n" + tab() + " * Run the database seeds.\n")
    f.write(tab() + " *\n" + tab() + " * @return void\n" + tab() + " */\n")
    f.write(tab() + "public function run()\n" + tab() + "{\n")
    f.write(tab(2) + "$items = [\n")
    for value in db_values:
        seed = []
        for i in range(flen):
            if type(value[i]) is int:
                seed.append("'{}' => {}".format(fields[i], value[i]))
            elif value[i] is None:
                seed.append("'{}' => NULL".format(fields[i], value[i]))
            else:
                seed.append("'{}' => '{}'".format(fields[i], value[i]))
        f.write(tab(3) + '[' + ', '.join(seed) + '],\n')
    f.write(tab(2) + "];\n\n")
    f.write(tab(2) + "DB::table('" + table_name + "')->insert($items);\n")
    f.write(tab() + "}\n")  # run end
    f.write("}\n")  # class end
    f.close()
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
    d = open(opath + fname, 'w')
    d.write("<?php\n\n")
    d.write("use Illuminate\Database\Seeder;\n\n")
    d.write("class DatabaseSeeder extends Seeder\n{\n")
    d.write(tab() + "/**\n" + tab() + " * Run the database seeds.\n")
    d.write(tab() + " *\n" + tab() + " * @return void\n" + tab() + " */\n")
    d.write(tab() + "public function run()\n" + tab() + "{\n")
    for i in seeder:
        d.write(tab(2) + "$this->call(" + camel_case(i) + "Seed::class);\n")
    d.write(tab() + "}\n")  # run end
    d.write("}\n")  # class end
    d.close()
    print("\033[32mGenerated:\033[0m {}".format(fname))


def main(argv):
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
