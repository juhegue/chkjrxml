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
    def __init__(self, fileName, dirBackup):
        self._reportPath = fileName
        self._pathPrefix = ""
        self.fields = list()
        self.fieldNames = list()
        self.variableNames = list()
        self.SortFieldsNames = list()

        try:
            with open(fileName, 'r') as f:
                self._data = f.read()

            sufijo = datetime.now().strftime('%Y%m%d%H%M%S')
            nuevo = os.path.join(dirBackup, '%s_%s' % (self.name, sufijo))
            with open(nuevo, 'w') as f:
                f.write(self._data)

        except Exception as e:
            print u'Error %s: %s' % (fileName, e)
            sys.exit(1)

    def __str__(self):
        return self._reportPath

    @property
    def path(self):
        return self._reportPath

    @property
    def name(self):
        return os.path.basename(self._reportPath)

    def save(self, fileName):
        try:
            with open(fileName, 'w') as f:
                f.write(self._data)
        except Exception as e:
            print u'Error %s: %s' % (fileName, e)

    def es_variable_report(self, nom):
        """
        Comprueba si es una variable del report como "PAGE_NUMBER"
        """
        var = nom.split("_")
        if len(var) == 2:
            if var[0] == var[0].upper() and var[1] == var[1].upper():
                return True
        return False

    def extractFields(self):
        doc = etree.parse(self._reportPath)

        # Define namespaces
        ns = 'http://jasperreports.sourceforge.net/jasperreports'
        nss = {'jr': ns}

        fieldTags = doc.xpath( '/jr:jasperReport/jr:field', namespaces=nss )
        fields = {}
        fieldNames = []
        for tag in fieldTags:
            name = tag.get('name')
            type = tag.get('class')
            children = tag.getchildren()
            path = tag.findtext('{%s}fieldDescription' % ns, '').strip()
            # Make the path relative if it isn't already
            if path.startswith('/data/record/'):
                path = self._pathPrefix + path[13:]
            # Remove language specific data from the path so:
            # Empresa-partner_id/Nom-name becomes partner_id/name
            # We need to consider the fact that the name in user's language
            # might not exist, hence the easiest thing to do is split and [-1]
            newPath = []
            for x in path.split('/'):
                newPath.append( x.split('-')[-1] )
            path = '/'.join( newPath )
            if path in fields:
                self.field_duplicados(name, fields[path]['name'])
                continue
            fields[ path ] = {
                'name': name,
                'type': type,
            }
            fieldNames.append( name )
        self.fields = fields
        self.fieldNames = fieldNames

    def extractVariables(self):
        doc = etree.parse(self._reportPath)

        # Define namespaces
        ns = 'http://jasperreports.sourceforge.net/jasperreports'
        nss = {'jr': ns}

        fieldTags = doc.xpath( '/jr:jasperReport/jr:variable', namespaces=nss )
        for tag in fieldTags:
            name = tag.get('name')
            self.variableNames.append(name)

    def extractSortFields(self):
        doc = etree.parse(self._reportPath)

        # Define namespaces
        ns = 'http://jasperreports.sourceforge.net/jasperreports'
        nss = {'jr': ns}

        fieldTags = doc.xpath( '/jr:jasperReport/jr:sortField', namespaces=nss )
        for tag in fieldTags:
            name = tag.get('name')
            self.SortFieldsNames.append(name)

    def borra_field(self, nombre):
        busca = '<field name="%s"' % nombre
        ini = self._data.find(busca)

        busca = '</field>'
        fin = self._data.find(busca, ini)
        if ini <= 0 or fin < 0:
            return False

        # borra
        fin += len(busca)
        self._data = self._data[:ini] + self._data[fin:]
        return True

    def field_duplicados(self, nombre, nombre_ok):
        print '\tPurgando campo duplicado %s por %s:' % (nombre, nombre_ok),
        if self.borra_field(nombre):
            # y lo reemplaza
            self._data = self._data.replace('$F{%s}' % nombre, '$F{%s}' % nombre_ok)
            print 'Ok'
        else:
            print 'No encotrado'

    def field_sin_definir(self):
        fields = dict()
        fin = 0
        while True:
            ini = self._data.find('$F{', fin)
            if ini < 0: break
            fin = self._data.find('}', ini)
            if fin < 0: break
            nom = self._data[ini+3:fin]
            fields[nom] = nom

        for nom in fields.values():
            if nom not in self.fieldNames:
                print "\tCampo no definido:%s" % nom

    def field_sin_uso(self):
        prime = False
        for nombre in self.fieldNames:
            busca = '$F{%s}' % nombre
            if nombre not in self.SortFieldsNames and self._data.find(busca) < 0:
                if not prime:
                    print "\tCampos sin uso"
                    prime = True
                sn = raw_input('\t  %s ¿eliminar? S/N:' % nombre)
                if sn.lower() == 's':
                    self.borra_field(nombre)

    def variable_sin_definir(self):
        variables = dict()
        fin = 0
        while True:
            ini = self._data.find('$V{', fin)
            if ini < 0: break
            fin = self._data.find('}', ini)
            if fin < 0: break
            nom = self._data[ini+3:fin]
            variables[nom] = nom

        for nom in variables.values():
            if nom not in self.variableNames and not self.es_variable_report(nom):
                print "\tVariable no definida:%s" % nom

    def variable_sin_uso(self):
        prime = False
        for nombre in self.variableNames:
            busca = '$V{%s}' % nombre
            if self._data.find(busca) < 0:
                if not prime:
                    prime = True
                    print '\tVariables sin uso:'
                print '\t  %s' % nombre


class Jasper(object):
    def __init__(self, file_path):
        jrs = list()
        if os.path.isdir(file_path):
            # solo los .jrxml
            for fic in os.listdir(file_path):
                if fic.lower().endswith('.jrxml'):
                    nom = os.path.join(file_path, fic)
                    jrs.append(CheckReport(nom, self.dir_reports()))
        else:
            jrs.append(CheckReport(file_path, self.dir_reports()))

        for jr in jrs:
            print jr.name
            jr.extractFields()
            jr.extractVariables()
            jr.extractSortFields()
            jr.variable_sin_definir()
            jr.variable_sin_uso()
            jr.field_sin_definir()
            jr.field_sin_uso()
            jr.save(jr.path)

    def dir_reports(self):
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


def main():
    if not sys.argv[1:]:
        print __doc__
        sys.exit(2)

    Jasper(sys.argv[1])


if __name__ == '__main__':
    main()


#no borrar campos que esten el sort