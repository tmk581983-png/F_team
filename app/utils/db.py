import os
import pymysql
from pymysqlpool.pool import Pool

# アプリ起動時に1回だけ、接続をあらかじめ複数用意しておく（プール）。
# 毎回 pymysql.connect() すると、Docker環境では接続確立が
# ランダムに数秒かかることがある（既知の問題）。
# プールから使い回すことで、通常時はこの問題を避けられる。
_pool = Pool(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    db=os.getenv("DB_DATABASE"),
    cursorclass=pymysql.cursors.DictCursor,
    min_size=2,
    max_size=5,
)
_pool.init()


def get_connection():
    """DBへの接続を、プールから借りて返す

    【close() を差し替えている理由】
    既存のコードは、すべて「finally: conn.close()」という書き方をしている。
    ここで conn.close を「プールに返却する」動きに置きかえることで、
    models 側のコードを1行も変更せずに済む。

    【返却前に rollback() している理由】
    models 側には、commit() せずに return する経路がある
    （例：自分の投稿には反応できない、という早期終了）。
    プールが無かった頃は接続ごと使い捨てだったので問題なかったが、
    使い回す今は、未確定のままプールに戻すと、次にこの接続を
    借りたリクエストが「古い時点のデータ」しか見えなくなってしまう。
    commit() 済みの場合、rollback() は何もしないので安全。
    """
    conn = _pool.get_conn()

    def _release():
        try:
            conn.rollback()
        except Exception:
            pass
        _pool.release(conn)

    conn.close = _release
    return conn
