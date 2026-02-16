from code_preprocess.clean_code import clean_code
from code_preprocess.language_tokenizer import tokenize_code, normalize_identifiers

# Java Example
java_code = """
public class Test {
    public static void main(String[] args) {
        int x = 10;
        int y = 20;
        System.out.println(x + y);
    }
}
"""

# C++ Example
cpp_code = """
#include <iostream>
using namespace std;
int main() {
    int a = 5;
    int b = 10;
    cout << a + b;
}
"""

# Java Test
clean_java = clean_code(java_code)
tokens_java = tokenize_code(clean_java)
norm_java = normalize_identifiers(tokens_java, lang="java")

print("JAVA NORMALIZED:", norm_java)

# C++ Test
clean_cpp = clean_code(cpp_code)
tokens_cpp = tokenize_code(clean_cpp)
norm_cpp = normalize_identifiers(tokens_cpp, lang="cpp")

print("CPP NORMALIZED:", norm_cpp)
