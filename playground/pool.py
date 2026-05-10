from collections import Counter
def main():
    # these are from FAMILY NET JAPAN INCORPORATED
    ids = ["14be634a956a621f","803618405dadcab6","a8dfb6c7f45b3859","b8e4042869bd3695","d16013cd92eafe18"]
    letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    hexs = "0123456789abcdef"
    for h in hexs:
        b = bin(int(h, 16))
        c = Counter(b[2:])
        print(h, b, c.keys(), c.values())
    # # low_letters = letters.lower()
    # # all = letters + low_letters
    # binaries = ''.join(format(ord(char), '08b') for char in hexs)
    # # for id in ids:
    # #     print("".join(sorted(id)))
    # print(c.keys(), c.values())
    # print(f"percentage of 0 over all = {c['0'] / sum(c.values())}")
    # vowels = "aeiou"
    # binary_vowels = ''.join(format(ord(char), '08b') for char in vowels)
    # c = Counter(binary_vowels)
    # print(f"percentage of 0 over all = {c['0'] / sum(c.values())}")
    
if __name__ == "__main__":
    main()