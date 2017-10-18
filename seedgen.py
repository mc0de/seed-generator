#!/usr/bin/python3

import re, sys, os, getopt


def generate_seeds(db_values, table_name, fields):
    opath = 'output/database/migrations/seeds/'
    fname = camel_case(table_name) + 'Seed.php'
    print("Generating: {}".format(fname))
    tabsize = 4
    if not os.path.exists(opath):
        os.makedirs(opath)
    f = open(opath + fname, 'w')
    f.write("<?php\n\n")
    f.write("use Illuminate\Database\Seeder;\n")
    f.write("use DB;\n\n")
    f.write("class " + camel_case(table_name) + "Seed extends Seeder\n{\n") # class open
    f.write(' ' * tabsize + "/**\n" + ' ' * tabsize + " * Run the database seeds.\n")
    f.write(' ' * tabsize + " *\n" + ' ' * tabsize + " * @return void\n" + ' ' * tabsize + " */\n")
    f.write(' ' * tabsize + "public function run()\n" + ' ' * tabsize + "{\n")
    f.write(' ' * tabsize * 2 + "$items = [\n")
    for i, value in enumerate(db_values):
        f.write(' ' * tabsize * 3 +'[')
        for j, field in enumerate(value):
            if type(value[j]) is int:
                f.write("'{}' => {}".format(fields[j], value[j]))
            elif value[j] is None :
                f.write("'{}' => NULL".format(fields[j], value[j]))
            else:
                f.write("'{}' => '{}'".format(fields[j], value[j]))
            if j != len(fields) - 1:
                f.write(", ")
        if i == len(db_values) - 1:
            f.write(']\n')
        else:
            f.write('],\n')
    f.write(' ' * tabsize * 2 + "];\n\n")
    f.write(' ' * tabsize * 2 + "foreach ($items as $item) {\n")
    f.write(' ' * tabsize * 3 + "DB::insert('insert into " + table_name +" (")
    [f.write(field + ")") if i == len(fields) - 1 else f.write(field + ', ') for i, field in enumerate(fields)]
    f.write(' values (')
    [f.write("?)'") if i == len(fields) - 1 else f.write('?, ') for i, field in enumerate(fields)]
    f.write(", [\n")
    [f.write(' ' * tabsize * 4 + "$item['" + field + "']\n") if i == len(fields) - 1 else f.write(' ' * tabsize * 4 + "$item['" + field + "'],\n") for i, field in enumerate(fields)]
    f.write(' ' * tabsize * 3 + "]")
    f.write(');\n') # closes db insert
    f.write(' ' * tabsize * 2 + "}\n")
    f.write(' ' * tabsize + "}\n") # run end
    f.write("}\n") # class end
    f.close()


def parse_sql(f):
    db_values = []
    table_name = None
    fields = None

    in_values = None
    skip = 0
    for i, line in enumerate(f):
        if skip > 0:
            skip = skip - 1
            continue

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
            skip = 1
            in_values = True
    f.close()


def camel_case(s):
    return s.title().replace('_', '')


def usage():
    return """Usage: python"""+sys.argv[0]+""" [OPTION]...
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
