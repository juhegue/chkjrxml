#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
    @juhegue (vie dic 29 18:44:04 CET 2017)

    Chequeo jrxml

    El argumento a pasar puede ser un fichero o un directorio
    (se crea una copiar en .report)

"""
from datetime import datetime
from lxml import etree
import os
import sys

__version__ = '0.0.1'


class CheckReport(object):
    def __init__(self, file_name, dir_backup):
        try:
            with open(file_name, 'r') as f:
                self.data = f.read()

            # graba el backup
            prefijo = datetime.now().strftime('%Y%m%d%H%M%S')
            nuevo = os.path.join(dir_backup, '%s_%s' % (prefijo, os.path.basename(file_name)))
            with open(nuevo, 'w') as f:
                f.write(self.data)

            self.doc = etree.parse(file_name)

        except Exception as e:
            print u'Error %s: %s' % (file_name, e)
            sys.exit(1)

        self.nameespace = 'http://jasperreports.sourceforge.net/jasperreports'
        self.nameespaces = {'jr': self.nameespace}
        self.variables_internas = ['PAGE_NUMBER', 'COLUMN_NUMBER', 'REPORT_COUNT', 'PAGE_COUNT', 'COLUMN_COUNT']

        self.fields = list()

        self.non_fields = list()
        self.propertys = list()
        self.parameters = list()
        self.sort_fields = list()
        self.variables = list()
        self.groups = list()

        self.extrae()
        self.purga_fields()
        self.parametro_sin_definir()
        self.parametro_sin_uso()
        self.variable_sin_definir()
        self.variable_sin_uso()
        self.field_sin_definir()
        self.field_sin_uso()

        # graba la modificación
        try:
            with open(file_name, 'w') as f:
                f.write(self.data)
        except Exception as e:
            print u'Error %s: %s' % (file_name, e)


    @staticmethod
    def print_sin_uso(titulo, nombres):
        print '\t%s:' % titulo
        for nombre in nombres:
            print '\t\t%s' % nombre

    def busca_dato(self, letra):
        dato = dict()
        fin = 0
        while True:
            ini = self.data.find('$%s{' % letra, fin)
            if ini < 0: break
            fin = self.data.find('}', ini)
            if fin < 0: break
            nom = self.data[ini+3:fin]
            dato[nom] = nom
        return dato.values()

    def parametro_sin_uso(self):
        sin_uso = list()
        for nombre in self.parameters:
            busca = '$P{%s}' % nombre
            if self.data.find(busca) < 0:
                sin_uso.append(nombre)

        self.print_sin_uso('Parámetros sin uso', sin_uso)

    def parametro_sin_definir(self):
        for nom in self.busca_dato('P'):
            if nom not in self.parameters:
                print u"\tERROR. Parámetro no definido:%s" % nom

    def borra_field(self, nombre):
        busca = '<field name="%s"' % nombre
        ini = self.data.find(busca)

        busca = '</field>'
        fin = self.data.find(busca, ini)
        if ini <= 0 or fin < 0:
            return False

        # borra
        fin += len(busca)
        self.data = self.data[:ini] + self.data[fin:]
        return True

    def field_sin_uso(self):
        todos = False
        prime = False
        for nombre in self.non_fields:
            busca = '$F{%s}' % nombre
            if nombre not in self.sort_fields and self.data.find(busca) < 0:
                tmp = nombre.split('-')
                tmp = tmp[-1] if len(tmp) > 1 else tmp[0]
                if tmp not in self.groups:
                    if not prime:
                        print '\tCampos sin uso'
                        prime = True

                    if todos:
                        snt = 'S'
                        print '\t  %s ¿eliminar? S/N/T: S' % nombre
                    else:
                        try:
                            snt = raw_input('\t  %s ¿eliminar? S/N/T:' % nombre)
                        except KeyboardInterrupt:
                            print
                            sys.exit()

                        snt = snt.upper()

                    if snt == 'S' or snt == 'T':
                        self.borra_field(nombre)

                    if snt == 'T':
                        todos = True

    def field_sin_definir(self):
        for nom in self.busca_dato('F'):
            if nom not in self.non_fields:
                print "\tERROR. Campo no definido:%s" % nom

    def variable_sin_uso(self):
        sin_uso = list()
        for nombre in self.variables:
            busca = '$V{%s}' % nombre
            if self.data.find(busca) < 0:
                sin_uso.append(nombre)

        self.print_sin_uso('Variables sin uso', sin_uso)

    def variable_sin_definir(self):
        for nom in self.busca_dato('V'):
            if nom not in self.variables and not self.variables_internas:
                if nom.endswith('_COUNT'):
                    nom = nom[:-6]      # quita _COUNT
                    if nom not in self.groups:
                        print '\tERROR. Variable no definida:%s' % nom
                else:
                    print '\tERROR. Variable no definida:%s' % nom

    def purga_fields(self):
        def field_duplicados(nombre, nombre_ok):
            if self.borra_field(nombre):
                # y lo reemplaza
                print '\tOk. Purgando campo duplicado %s por %s:' % (nombre, nombre_ok)
                self.data = self.data.replace('$F{%s}' % nombre, '$F{%s}' % nombre_ok)
            else:
                print '\tERROR(No encotrado). Purgando campo duplicado %s por %s:' % (nombre, nombre_ok)

        fields = dict()
        for field in self.fields:
            for key, value in field.iteritems():
                path = list()
                value = value[13:]      # quita /data/record/
                for x in value.split('/'):
                    path.append(x.split('-')[-1])
                path = '/'.join(path)

                if path in fields:
                    field_duplicados(key, fields[path])
                else:
                    fields[path] = key
                    self.non_fields.append(key)

    def extrae(self):
        tags = self.doc.xpath('/jr:jasperReport/jr:property', namespaces=self.nameespaces)
        for tag in tags:
            nombre = tag.get('name')
            self.propertys.append(nombre)

        tags = self.doc.xpath('/jr:jasperReport/jr:parameter', namespaces=self.nameespaces)
        for tag in tags:
            nombre = tag.get('name')
            self.parameters.append(nombre)

        tags = self.doc.xpath('/jr:jasperReport/jr:field', namespaces=self.nameespaces)
        for tag in tags:
            nombre = tag.get('name')
            valor = tag.findtext('{%s}fieldDescription' % self.nameespace, '').strip()
            self.fields.append({nombre: valor})

        tags = self.doc.xpath('/jr:jasperReport/jr:sortField', namespaces=self.nameespaces)
        for tag in tags:
            nombre = tag.get('name')
            self.sort_fields.append(nombre)

        tags = self.doc.xpath('/jr:jasperReport/jr:variable', namespaces=self.nameespaces)
        for tag in tags:
            nombre = tag.get('name')
            self.variables.append(nombre)

        tags = self.doc.xpath('/jr:jasperReport/jr:group', namespaces=self.nameespaces)
        for tag in tags:
            nombre = tag.get('name')
            self.groups.append(nombre)


class Report(object):
    def __init__(self, file_path):
        jrs = list()
        if os.path.isdir(file_path):
            # solo los .jrxml
            for fic in os.listdir(file_path):
                if fic.lower().endswith('.jrxml'):
                    nom = os.path.join(file_path, fic)
                    jrs.append(nom)
        else:
            jrs.append(file_path)

        for jr in jrs:
            CheckReport(jr, self.dir_backup())

    def dir_backup(self):
        """
        Directorio backup
        :return:  str
        """
        f = os.path.realpath(__file__)
        p = os.path.dirname(f)
        directorio = os.path.join(p, '.report')
        try:
            os.stat(directorio)
        except:
            os.mkdir(directorio)
        return directorio


if __name__ == '__main__':
    if not sys.argv[1:]:
        print __doc__
        sys.exit(2)

    Report(sys.argv[1])



