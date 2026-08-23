import os
import pymysql
from pymysqlpool.pool import Pool

# コネクションプール化
_pool = Pool(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    db=os.getenv("DB_DATABASE"),
    cursorclass=pymysql.cursors.DictCursor,
    # SQLを実行するたびに、自動でcommitする
    # これが無いと、確定し忘れた接続がプールに戻ることがあり、
    # 次にその接続を使うリクエストが「古い時点のデータ」しか見えなくなる
    autocommit=True,
    min_size=2,
    max_size=5,
)
_pool.init()


def get_connection():
    """close() を差し替えている理由
    既存のコードは、すべて「finally: conn.close()」という書き方をしており
    ここでconn.closeを「プールに返す」動きに置きかえることで、
    models側のコードを1行も変更せずに済む

    返却前に rollback() している理由
    models 側には、commit() せずに return する経路がある
    （例：自分の投稿には反応できない）。
    コネクションプール化の前は接続ごとに使い捨てだったので問題なかったが、
    今は未確定のままプールに戻すと、次にこの接続を借りたリクエストが
    「古い時点のデータ」しか見えなくなってしまう
    なお、commit() 済みの場合はrollback() は何もしない
    """
    conn = _pool.get_conn()

    def _release():
        try:
            conn.rollback()  # 未確定部分の破棄
        except Exception:
            pass
        _pool.release(conn)

    conn.close = _release  # close()の差し替え
    return conn
