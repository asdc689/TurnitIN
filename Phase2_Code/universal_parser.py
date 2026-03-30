import tree_sitter
import tree_sitter_python
import tree_sitter_java
import tree_sitter_cpp
import tree_sitter_javascript
from typing import Dict, List, Tuple

class UniversalParser:
    def __init__(self):
        # Initialize official grammars
        self.languages = {
            'python': tree_sitter.Language(tree_sitter_python.language()),
            'java': tree_sitter.Language(tree_sitter_java.language()),
            'cpp': tree_sitter.Language(tree_sitter_cpp.language()),
            'javascript': tree_sitter.Language(tree_sitter_javascript.language())
        }
        
        # Noise nodes to completely ignore (formatting, comments, syntax errors)
        self.ignore_types = {'comment', 'line_comment', 'block_comment', 'ERROR'}

        # Nodes that signify control flow blocks (for Cross-Language signatures)
        self.cf_nodes = {
            'if_statement', 'for_statement', 'while_statement', 
            'function_definition', 'method_declaration', 'try_statement',
            'catch_clause', 'switch_statement'
        }

    def parse(self, code: str, lang: str) -> Dict:
        """
        Parses code and returns the holy trinity of plagiarism detection:
        1. Normalized Tokens (for Winnowing/Smith-Waterman)
        2. AST Sequence (for Sequence Edit Distance)
        3. Control Flow Signature (for Cross-Language AI validation)
        """
        lang = lang.lower()
        if lang not in self.languages:
            lang = 'python' # Safe fallback

        parser = tree_sitter.Parser(self.languages[lang])
        
        # bytes conversion with 'replace' prevents crashing on weird student copy-pastes
        tree = parser.parse(bytes(code, "utf8", errors="replace")) 
        
        normalized_tokens = []
        ast_sequence = []
        cf_signature = []
        
        identifier_map = {}
        counters = {'var': 0}

        def walk(node):
            if node.type in self.ignore_types:
                return

            # 1. AST Sequence extraction
            if node.is_named:
                ast_sequence.append(node.type)
                
            # 2. Control Flow Extraction
            if node.type in self.cf_nodes:
                cf_signature.append(node.type + "_START")

            # 3. Leaf node processing (Token Normalization & Line Tracking)
            if not node.children:
                token_text = node.text.decode('utf8', errors='replace')

                # Tree-sitter is 0-indexed for rows, but code editors/frontends are 1-indexed
                line_num = node.start_point[0] + 1 
                
                # Defeat Variable Masking: Standardize all identifiers
                if node.type == 'identifier':
                    if token_text not in identifier_map:
                        counters['var'] += 1
                        identifier_map[token_text] = f"var_{counters['var']}"
                    normalized_tokens.append((identifier_map[token_text], line_num))
                
                # Defeat String/Number manipulation (Robust substring matching)
                elif 'string' in node.type:
                    normalized_tokens.append(("STR_LITERAL", line_num))
                elif 'number' in node.type or 'integer' in node.type or 'float' in node.type:
                    normalized_tokens.append(("NUM_LITERAL", line_num))
                else:
                    # Keep structural operators and keywords as-is
                    normalized_tokens.append((token_text, line_num))

            for child in node.children:
                walk(child)

            if node.type in self.cf_nodes:
                cf_signature.append(node.type + "_END")

        walk(tree.root_node)

        return {
            "tokens": normalized_tokens,
            "ast_sequence": ast_sequence,
            "cf_signature": cf_signature,
            "raw_lines": code.splitlines() # Needed later for exact line highlighting
        }