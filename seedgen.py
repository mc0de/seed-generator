#!/usr/bin/python3

import re
import sys
import os
import getopt


def generate_seeds(db_values, table_name, fields):
    opath = 'output/'
    fname = camel_case(table_name) + 'Seed.php'
    print("Generating: {}".format(fname))
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
        for j, field in enumerate(value):
            if type(value[j]) is int:
                seed.append("'{}' => {}".format(fields[j], value[j]))
            elif value[j] is None:
                seed.append("'{}' => NULL".format(fields[j], value[j]))
            else:
                seed.append("'{}' => '{}'".format(fields[j], value[j]))
        f.write(tab(3) + '[' + ', '.join(seed) + '],\n')
    f.write(tab(2) + "];\n\n")
    f.write(tab(2) + "DB::table('" + table_name + "')->insert($items);\n")
    f.write(tab() + "}\n")  # run end
    f.write("}\n")  # class end
    f.close()


def parse_sql(f):
    db_values = []
    table_name = None
    fields = None

    in_values = None
    input_file = enumerate(f)
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
    f.close()


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
                parse_sql(f)
            except IOError as err:
                eprint(err)


if __name__ == "__main__":
    main(sys.argv[1:])
