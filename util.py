import logging

def logger(submodule=None):
    return logging.getLogger("nodes_graphviz_arrange" +
                             ("." + submodule if submodule is not None else ""))


def write_line(line, f):
    logger("gv_input").debug(line)
    print(line, file=f)