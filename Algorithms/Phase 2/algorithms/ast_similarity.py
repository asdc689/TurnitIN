import ast

def extract_ast_nodes(code: str):
    """
    Parse Python code and extract AST node types
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    nodes = []
    for node in ast.walk(tree):
        nodes.append(type(node).__name__)
    return nodes


def ast_similarity(code1: str, code2: str):
    """ 
    Compute similarity between two Python codes based on AST node overlap
    """
    nodes1 = extract_ast_nodes(code1)
    nodes2 = extract_ast_nodes(code2)

    if not nodes1 or not nodes2:
        return 0.0

    set1 = set(nodes1)
    set2 = set(nodes2)

    return len(set1 & set2) / len(set1 | set2)