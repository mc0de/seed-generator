#!/usr/bin/python3

import re
import sys
import os
import getopt
from collections import defaultdict
from string import Template


class SeedGenerator(object):
    """docstring for SeedGenerator"""

    def __init__(self):
        super().__init__()
        self.opath = 'output/'
        if not os.path.exists(self.opath):
            os.makedirs(self.opath)

    def template(self, classname, content, suffix='Seed'):
        t = Template(open('template.stub').read())
        return t.substitute(
            {'classname': classname, 'content': content, 'suffix': suffix})

    def table_seed(self, table, columns, rows, suffix='Seed'):
        ofile = camel_case(table) + suffix + '.php'
        content = tab(2) + "$entries = [\n"
        for row in rows:
            entries = []
            for i in range(len(columns)):
                if type(row[i]) is int:
                    entries.append("'{}' => {}".format(columns[i], row[i]))
                elif row[i] is None:
                    entries.append("'{}' => null".format(columns[i], row[i]))
                else:
                    # escape single quotes
                    entries.append("'{}' => '{}'".format(columns[i], row[i].replace("'", "\\'")))
            content += tab(3) + '[' + ', '.join(entries) + '],\n'
        content += tab(2) + "];\n\n"
        content += tab(2) + "DB::table('" + table + \
            "')->insert($entries);"
        with open(self.opath + ofile, 'w') as f:
            f.write(self.template(camel_case(
                table), content, suffix=suffix))
        print("\033[32mGenerated:\033[0m {}".format(ofile))

    def database_seeder(self, tables):
        ofile = 'DatabaseSeeder.php'
        classes = []
        for x in tables:
            classes.append(tab(2) + "$this->call(" +
                           camel_case(x) + "Seed::class)")
        content = ";\n".join(classes) + ';'
        with open(self.opath + ofile, 'w') as f:
            f.write(self.template('Database', content, 'Seeder'))
        print("\033[32mGenerated:\033[0m {}".format(ofile))

    def find_insert(self, sql):
        sql = open(sql, 'r')
        table = None
        columns = None
        rows = []
        in_values = None
        input_file = enumerate(sql)  # required for next()
        for i, line in input_file:
            if in_values:
                if re.match('\t\(', line):
                    line = re.sub('NULL', 'None', line)
                    line = eval(re.sub('(^\t|,$\n|;$\n)', '', line))
                    rows.append(line)
                else:
                    self.table_seed(table, columns, rows)
                    in_values = False
                    rows = []
            elif re.match("INSERT INTO", line):
                line = re.sub("INSERT INTO ", "", line)
                line = re.sub("(`|,|\(|\))", "", line).split()
                table = line[0]
                columns = line[1:]
                in_values = True
                next(input_file)

    def find_reference(self, sql):
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
        seeder = sorted(list(set(tables) - set(relations)))  # all - with rels
        while (relations):
            for k, v in list(relations.items()):
                for item in list(v):
                    if item in seeder:
                        v.remove(item)
            for k, v in list(relations.items()):
                if not v:
                    seeder.append(k)
                    del relations[k]
        self.database_seeder(seeder)


def tab(count=1, tabsize=4):
    return ' ' * tabsize * count


def camel_case(s):
    return s.title().replace('_', '')


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def usage():
    return """Usage: python""" + sys.argv[0] + """ [OPTION]...
Tool description

  -h, --help
        display this help and exit
  -i, --input=FILE
        SQL file to make seeds of
"""


def main(argv):
    try:
        opts, args = getopt.getopt(argv, "hi:", ['help', 'input='])
    except getopt.GetoptError as err:
        eprint(str(err) + '\n')
        eprint(usage())
        sys.exit(2)

    if not opts:
        print(usage())
        exit()

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print(usage())
        elif opt in ('-i', '--input'):
            try:
                generator = SeedGenerator()
                generator.find_insert(arg)
                generator.find_reference(arg)
            except IOError as err:
                eprint(err)


if __name__ == "__main__":
    main(sys.argv[1:])
