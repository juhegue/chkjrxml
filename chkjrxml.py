# -*- encoding: utf-8 -*-

import os
from lxml import etree
import re

dataSourceExpressionRegExp = re.compile( r"""\$P\{(\w+)\}""" )


class CheckReport:
    def __init__(self, fileName, pathPrefix=''):
        self._reportPath = fileName
        self._pathPrefix = pathPrefix.strip()
        if self._pathPrefix and self._pathPrefix[-1] != '/':
            self._pathPrefix += '/'

        self._language = 'xpath'

        with open(fileName, "r") as f:
            self._data = f.read()

    def __str__(self):
        return self._reportPath

    @property
    def path(self):
        return self._reportPath

    @property
    def name(self):
        return os.path.basename(self._reportPath)

    def save(self, nombre):
        with open(nombre, "w") as f:
            f.write(self._data)

    def extractFields(self):
        doc = etree.parse(self._reportPath)

        # Define namespaces
        ns = 'http://jasperreports.sourceforge.net/jasperreports'
        nss = {'jr': ns}

        fieldTags = doc.xpath( '/jr:jasperReport/jr:field', namespaces=nss )

        # fields and fieldNames
        fields = {}
        fieldNames = []
        #fieldTags = doc.xpath( '/jr:jasperReport/jr:field', namespaces=nss )
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
                # print "WARNING: path '%s' already exists in report. This is not supported by the module. Offending fields: %s, %s" % (path, fields[path]['name'], name)
                self.purga_field(name, fields[path]['name'])
                continue
            fields[ path ] = {
                'name': name,
                'type': type,
            }
            fieldNames.append( name )
        return fields, fieldNames

    def purga_field(self, nombre, nombre_ok):
        print "\tPurgando %s por %s:" % (nombre, nombre_ok),
        #	<field name="Nombre_impuesto-name" class="java.lang.String">
        #		<fieldDescription><![CDATA[/data/record/Lineas_de_factura-invoice_line/Impuestos-invoice_line_tax_id/Nombre_impuesto-name]]></fieldDescription>
        #	</field>

        busca = '<field name="%s"' % nombre
        ini = self._data.find(busca)

        busca = '</field>'
        fin = self._data.find(busca, ini)
        if ini <= 0 or fin <0:
            print "ERROR no encontrado"
            return

        fin += len(busca)
        self._data = self._data[:ini] + self._data[fin:]

        self._data = self._data.replace('$F{%s}' % nombre, '$F{%s}' % nombre_ok)
        print "Ok"






class Jasper(object):

    def __init__(self):
        dir_reports = self.dir_reports()

        # solo los .jrxml
        jrs = list()
        for fic in os.listdir(dir_reports):
            if fic.lower().endswith('.jrxml'):
                nom = os.path.join(dir_reports, fic)
                jrs.append(CheckReport(nom))

        for jr in jrs:
            print jr.name
            jr.extractFields()
            jr.save("/tmp/p.jrxml")


    def dir_reports(self):
        f = os.path.realpath(__file__)
        p = os.path.dirname(f)
        return os.path.join(p, 'report')


def main():
    Jasper()


if __name__ == "__main__":
    #kk()
    main()
