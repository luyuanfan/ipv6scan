import ipaddress

def main():
    ip_txt = "2607:5300::25b5"
    ip_obj = ipaddress.IPv6Address(ip_txt)
    print(f"{type(ip_obj)}")
    full = ip_obj.exploded.replace(":", "")
    print(f"full form {full}")

if __name__ == "__main__":
    main()