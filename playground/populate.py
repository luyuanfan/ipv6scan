import psycopg2

def main():
    conn = psycopg2.connect(
        dbname="tinyRouterIPs",
        user="lyspfan",
        password="lyspfan",
        host="localhost"
    )

if __name__ == "__main__":
    main()