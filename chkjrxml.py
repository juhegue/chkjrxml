# -*- encoding: utf-8 -*-
"""
    Elimina fields repetidos de un jrxml

    @juhegue (vie dic 29 18:44:04 CET 2017)

    El argumento a pasar puede ser un fichero o un directorio
    (se crea una copiar en .report)

"""
from datetime import datetime
from lxml import etree
import os
import sys

__version__ = "0.0.1"


class CheckReport(object):
    def __init__(self, fileName, dirBackup):
        self._reportPath = fileName
        self._pathPrefix = ""

        try:
            with open(fileName, "r") as f:
                self._data = f.read()

            sufijo = datetime.now().strftime("%Y%m%d%H%M%S")
            nuevo = os.path.join(dirBackup, "%s_%s" % (self.name, sufijo))
            with open(nuevo, "w") as f:
                f.write(self._data)

        except Exception as e:
            print u"Error %s: %s" % (fileName, e)
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
            with open(fileName, "w") as f:
                f.write(self._data)
        except Exception as e:
            print u"Error %s: %s" % (fileName, e)

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

        # borra el field
        fin += len(busca)
        self._data = self._data[:ini] + self._data[fin:]

        # y lo reemplaza
        self._data = self._data.replace('$F{%s}' % nombre, '$F{%s}' % nombre_ok)
        print "Ok"


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
            jr.save(jr.path)

    def dir_reports(self):
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


if __name__ == "__main__":
    main()
