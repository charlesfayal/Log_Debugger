

import random 

start_line = "start_line"
def main():
    log = open("test_log.txt", "w+")
    for i in range(100):
        log.write(start_line + "\n")
        for j in range(5):
            i = random.randint(1,10)
            if i < 4:
                log.write("first\n")
            elif i < 6:
                log.write("second\n")
            elif i < 7:
                log.write("third\n")
            else:
                log.write("fourth\n")


if __name__ == "__main__":
    main()