__copyright__ = "Copyright 2020, 3Liz"
__license__ = "GPL version 3"
__email__ = "info@3liz.org"
__revision__ = "$Format:%H$"

import os
import psycopg2

from db_manager.db_plugins.plugin import BaseError
from db_manager.db_plugins import createDbPlugin
from db_manager.db_plugins.postgis.connector import PostGisDBConnector

from qgis.core import Qgis, QgsProviderRegistry

from .i18n import tr
from .resources import plugin_path
from .version import format_version_integer


def available_migrations(minimum_version: int):
    """Get all the upgrade SQL files since the provided version."""
    upgrade_dir = plugin_path("install", "sql", "upgrade")
    get_files = [
        f for f in os.listdir(upgrade_dir) if os.path.isfile(os.path.join(upgrade_dir, f))
    ]
    files = []

    for f in get_files:
        k = format_version_integer(f.replace("upgrade_to_", "").replace(".sql", "").strip())
        if k > minimum_version:
            files.append([k, f])

    def getKey(item):
        return item[0]

    sfiles = sorted(files, key=getKey)
    sql_files = [s[1] for s in sfiles]
    return sql_files


def get_uri_from_connection_name(connection_name, must_connect=True):
    # Otherwise check QGIS QGIS3.ini settings for connection name
    status = True
    uri = None
    error_message = ""
    connection = None
    try:
        dbpluginclass = createDbPlugin("postgis", connection_name)
        connection = dbpluginclass.connect()
    except BaseError as e:
        status = False
        error_message = e.msg
    except Exception as e:
        print(e)
        status = False
        error_message = tr("Cannot connect to database with") + " " + connection_name

    if not connection and must_connect:
        return status, uri, error_message

    db = dbpluginclass.database()
    if not db:
        status = False
        error_message = tr("Unable to get database from connection")
        return status, uri, error_message

    uri = db.uri()
    return status, uri, ""


def fetch_data_from_sql_query(connection_name, sql):

    data = []
    header = []
    rowCount = 0

    # Get URI
    status, uri, error_message = get_uri_from_connection_name(connection_name)

    if not uri:
        return header, data, rowCount, False, error_message
    try:
        if Qgis.QGIS_VERSION_INT >= 31400:
            metadata = QgsProviderRegistry.instance().providerMetadata('postgres')
            connector = metadata.findConnection(connection_name)
            # connection.connectionName = lambda: connection_name
            # connection.providerName = lambda: 'postgres'
            # connector_db = PostGisDBConnector(uri, connection)
            # print("CONNECTOR")
            # print(type(connector_db))
            # print(connector_db.uri())
            # if connector_db.uri().service():
            #     connector = psycopg2.connect(
            #         service=uri.service(),
            #     )
            # else:
            #     connector_db = psycopg2.connect(
            #         host=uri.host(), database=uri.database(),
            #         user=uri.username(), password=uri.password(),
            #     )
        else:
            connector = PostGisDBConnector(uri)
    except ZeroDivisionError:
        error_message = tr("Cannot connect to database")
        return header, data, rowCount, False, error_message

    c = None
    ok = True
    # print "run query"
    try:
        if Qgis.QGIS_VERSION_INT() >= 31400:
            # TODO
            pass
        else:
            c = connector._execute(None, str(sql))
            data = []
            header = connector._get_cursor_columns(c)
            if header is None:
                header = []
            if len(header) > 0:
                data = connector._fetchall(c)
            rowCount = c.rowcount
            if rowCount == -1:
                rowCount = len(data)

    except BaseError as e:
        error_message = e.msg
        return header, data, rowCount, False, error_message
    finally:
        if c:
            c.close()
            del c

    # Log errors
    if not ok:
        error_message = tr("Unknown error occurred while fetching data")
        return header, data, rowCount, ok, error_message

    return header, data, rowCount, ok, error_message
