from tree_sitter import Language, Parser
import tree_sitter_python
import tree_sitter_java
import tree_sitter_cpp

class CodePlagiarismChecker:
    def __init__(self):
        # Initialize parsers for supported languages
        # We map the string names to the official imported modules
        self.languages = {
            'python': tree_sitter_python,
            'java': tree_sitter_java,
            'cpp': tree_sitter_cpp
        }

        # Added Ignore List
        # We skip root nodes (containers) and errors to ensure we compare actual logic.
        self.IGNORE_TYPES = {
            'translation_unit', # C++ root
            'module',           # Python root
            'program',          # Java root
            'ERROR',            # Syntax errors
            'comment',          # Comments 
            'string_literal',   # Strings aren't structural logic
        }

    def _get_ast_nodes(self, code: str, language_name: str) -> list:
        """
        Parses code and returns a list of 'named' AST node types.
        We skip punctuation (anonymous nodes) to focus on structure.
        """
        try:
            # 1. Get the module for the requested language
            lang_module = self.languages.get(language_name)
            if not lang_module:
                raise ValueError(f"Language {language_name} not supported")

            # 2. LOAD THE LANGUAGE
            # We use the official binding's .language() method to get the native object
            # wrapping it in the Language class to ensure it works with the Parser
            try:
                LANGUAGE = Language(lang_module.language())
            except Exception:
                # Fallback for some specific version mismatches
                LANGUAGE = lang_module.language()

            # 3. Create the parser and set the language
            parser = Parser(LANGUAGE)
            
            # 4. Parse the code (must be bytes)
            tree = parser.parse(bytes(code, "utf8"))
            
            # 5. Efficiently walk the tree using a cursor
            cursor = tree.walk()
            nodes = []
            
            visited_children = False
            while True:
                # We only care about "named" nodes (e.g., 'function_definition', 'if_statement')
                # We ignore anonymous nodes like '{', '}', ';', '('
                if cursor.node.is_named and cursor.node.type not in self.IGNORE_TYPES:
                    nodes.append(cursor.node.type)

                # Depth-first traversal logic
                if not visited_children and cursor.goto_first_child():
                    visited_children = False
                elif cursor.goto_next_sibling():
                    visited_children = False
                elif cursor.goto_parent():
                    visited_children = True
                else:
                    break
            
            return nodes
            
        except Exception as e:
            print(f"Error parsing {language_name}: {e}")
            return []

    def _generate_ngrams(self, nodes: list, n: int = 3):
        """Generates N-grams from the list of node types"""
        if len(nodes) < n:
            return [tuple(nodes)]
        return list(zip(*[nodes[i:] for i in range(n)]))

    def calculate_similarity(self, code1: str, code2: str, language: str) -> float:
        """
        Computes Jaccard similarity of AST N-grams
        """
        nodes1 = self._get_ast_nodes(code1, language)
        nodes2 = self._get_ast_nodes(code2, language)

        if not nodes1 or not nodes2:
            return 0.0

        ngrams1 = set(self._generate_ngrams(nodes1))
        ngrams2 = set(self._generate_ngrams(nodes2))

        intersection = len(ngrams1 & ngrams2)
        union = len(ngrams1 | ngrams2)

        return intersection / union if union != 0 else 0.0

# --- EXPORTED FUNCTION ---

# Create a single instance to be reused
_checker_instance = CodePlagiarismChecker()

def ast_similarity(code1: str, code2: str, lang: str) -> float:
    """
    Wrapper function to be imported by the engine.
    Calculates structural similarity based on AST N-grams.
    Arguments:
        code1 (str): Source code of file 1
        code2 (str): Source code of file 2
        lang (str): 'python', 'java', or 'cpp' (REQUIRED)
    """
    return _checker_instance.calculate_similarity(code1, code2, lang)