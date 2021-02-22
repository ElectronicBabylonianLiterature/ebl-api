class Util:
    @staticmethod
    def print_frame(s):
        r = "\n"
        r += " +-"

        for _i in range(len(s)):
            r += "-"
        r += "-+\n"
        r += " | " + s + " |\n"
        r += " +-"

        for _ in range(len(s)):
            r += "-"

        r += "-+\n"
        r += "\n"
        return r
