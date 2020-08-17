class Util:

    def print_frame(s):
        print("")
        print(" +-",end="")

        for char in s:
            print("-",end="")
        print("-+")
        print(" | " + s + " |")
        print(" +-",end="")

        for char in s:
            print("-", end="")

        print("-+")
        print("")
