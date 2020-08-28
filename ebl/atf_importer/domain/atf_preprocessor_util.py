class Util:

    def print_frame(s):
        r = "\n"
        r+=(" +-")

        for char in s:
            r+=("-")
        r+=("-+\n")
        r+=(" | " + s + " |\n")
        r+=(" +-")

        for char in s:
            r+=("-")

        r+=("-+\n")
        r+=("\n")
        return r
