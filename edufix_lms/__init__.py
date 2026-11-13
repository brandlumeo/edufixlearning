try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass  # PyMySQL not installed (e.g. local dev using SQLite) — fine, mysql backend isn't used