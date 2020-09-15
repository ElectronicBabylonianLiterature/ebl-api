class Util:

    @staticmethod
    def print_frame(s):
        r = "\n"
        r+=(" +-")

        for i in range(len(s)):
            r+=("-")
        r+=("-+\n")
        r+=(" | " + s + " |\n")
        r+=(" +-")

        for i in range(len(s)):
            r+=("-")

        r+=("-+\n")
        r+=("\n")
        return r
